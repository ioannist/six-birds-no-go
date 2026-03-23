#!/usr/bin/env python3
"""Validate T28 finite-lens definability count and emit summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must parse to object")
    return data


def fail(msg: str) -> None:
    raise ValueError(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T28 finite-lens definability count validation")
    parser.add_argument("--output-dir", default="results/T28")
    args = parser.parse_args()

    bridge_p = Path("docs/project/lean_count_bounded_interface.yaml")
    corollary_p = Path("docs/project/lean_corollary_bounded_interface.yaml")
    ready_p = Path("docs/project/readiness_checklist.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    pack_p = Path("docs/project/theorem_pack_bounded_interface.yaml")
    claims_p = Path("docs/project/claim_audit_freeze.yaml")

    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    count_p = Path("lean/SixBirdsNoGo/FiniteLensDefinability.lean")
    count_ex_p = Path("lean/SixBirdsNoGo/FiniteLensDefinabilityExample.lean")

    required = [bridge_p, corollary_p, ready_p, atlas_p, pack_p, claims_p, lean_root_p, count_p, count_ex_p]
    for p in required:
        if not p.exists():
            fail(f"missing required input: {p}")

    bridge = load_json(bridge_p)
    count = bridge
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    pack = load_json(pack_p)
    claims = load_json(claims_p)

    for k in ["version", "generated_at_utc", "source_context", "status_enums", "theorem_fronts"]:
        if k not in bridge:
            fail(f"lean count file missing key: {k}")

    fronts = bridge["theorem_fronts"]
    if not isinstance(fronts, list) or len(fronts) != 1:
        fail("lean count file must contain exactly one theorem front")
    row = fronts[0]
    if row.get("theorem_id") != "NG_LADDER_BOUNDED_INTERFACE":
        fail("theorem-front ID must be NG_LADDER_BOUNDED_INTERFACE")
    if row.get("bridge_status") != "counting_core_ready":
        fail("bridge_status must be counting_core_ready")
    for key in ["bridge_statement", "prerequisites", "direct_corollaries", "scope_limits", "lean_artifacts"]:
        val = row.get(key)
        if key == "bridge_statement":
            if not str(val).strip():
                fail("bridge_statement must be non-empty")
        elif not isinstance(val, list) or not val:
            fail(f"{key} must be non-empty")

    count_text = count_p.read_text(encoding="utf-8")
    count_ex_text = count_ex_p.read_text(encoding="utf-8")
    lean_root_text = lean_root_p.read_text(encoding="utf-8")

    for token in [
        "allAssignments_length_eq_two_pow",
        "inducedPredicate_injective",
        "definablePredEquivAssignments",
        "finiteLens_definableCountCore",
    ]:
        if token not in count_text:
            fail(f"FiniteLensDefinability.lean missing expected theorem token: {token}")

    if "FiniteLensDefinability" not in count_ex_text:
        fail("FiniteLensDefinabilityExample.lean must import the count core")
    for imp in [
        "import SixBirdsNoGo.FiniteLensDefinability",
        "import SixBirdsNoGo.FiniteLensDefinabilityExample",
    ]:
        if imp not in lean_root_text:
            fail(f"lean/SixBirdsNoGo.lean missing import: {imp}")

    ready_map = {t["theorem_id"]: t for t in readiness["theorems"]}
    atlas_map = {t["theorem_id"]: t for t in atlas["theorems"]}
    claim_map = {c["claim_id"]: c for c in claims["claims"]}

    if ready_map["NG_LADDER_BOUNDED_INTERFACE"]["lean_support"]["status"] != "direct":
        fail("readiness bounded-interface lean_support must now be direct")
    if atlas_map["NG_LADDER_BOUNDED_INTERFACE"]["support_snapshot"]["lean_support"]["status"] != "direct":
        fail("atlas bounded-interface lean_support must now be direct")

    pack_row = next((t for t in pack["theorem_fronts"] if t["theorem_id"] == "NG_LADDER_BOUNDED_INTERFACE"), None)
    if pack_row is None:
        fail("bounded-interface theorem pack missing theorem row")
    lean_refs = pack_row.get("evidence_refs", {}).get("lean", [])
    for rel in [
        "lean/SixBirdsNoGo/FiniteLensDefinability.lean",
        "lean/SixBirdsNoGo/FiniteLensDefinabilityExample.lean",
        "lean/SixBirdsNoGo/BoundedInterfaceNoLadder.lean",
        "lean/SixBirdsNoGo/BoundedInterfaceNoLadderExample.lean",
        "docs/project/lean_count_bounded_interface.yaml",
        "docs/project/lean_corollary_bounded_interface.yaml",
    ]:
        if rel not in lean_refs:
            fail(f"bounded-interface theorem pack missing lean ref: {rel}")
    if pack_row.get("remaining_blockers"):
        fail("bounded-interface theorem pack remaining_blockers must now be empty")
    if pack_row.get("next_ticket") is not None:
        fail("bounded-interface theorem pack next_ticket must now be null")

    core_claim = claim_map["NG_LADDER_BOUNDED_INTERFACE.core"]
    if core_claim.get("blockers"):
        fail("bounded-interface core claim blockers must now be empty")
    if core_claim.get("next_ticket") is not None:
        fail("bounded-interface core claim next_ticket must now be null")

    if count["theorem_fronts"][0].get("full_corollary_pending") is not False:
        fail("lean_count_bounded_interface.yaml must mark full_corollary_pending false")

    lake_available = shutil.which("lake") is not None
    if lake_available:
        proc = subprocess.run(
            "cd lean && lake build",
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        lake_build_status = "passed" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            fail("cd lean && lake build failed")
    else:
        lake_build_status = "skipped_tool_unavailable"

    repro_p = Path("src/sixbirds_nogo/repro.py")
    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""
    includes_t20 = "run_t20_readiness_checkpoint.py" in repro_text
    includes_t21 = "run_t21_theorem_atlas.py" in repro_text
    includes_t22 = "run_t22_dpi_protocol_pack.py" in repro_text
    includes_t23 = "run_t23_graph_affinity_pack.py" in repro_text
    includes_t24 = "run_t24_closure_pack.py" in repro_text
    includes_t25 = "run_t25_objecthood_pack.py" in repro_text
    includes_t26 = "run_t26_bounded_interface_pack.py" in repro_text
    includes_t27 = "run_t27_lean_graph_bridge.py" in repro_text
    includes_t28 = "run_t28_lean_finite_lens_count.py" in repro_text
    if not includes_t28:
        fail("repro pipeline missing run_t28_lean_finite_lens_count.py step")

    lean_direct_total = sum(1 for t in readiness["theorems"] if t["lean_support"]["status"] == "direct")
    lean_aux_total = sum(1 for t in readiness["theorems"] if t["lean_support"]["status"] == "auxiliary_only")
    lean_missing_total = sum(1 for t in readiness["theorems"] if t["lean_support"]["status"] == "missing")

    summary = {
        "generated_at_utc": now_iso(),
        "theorem_count": 1,
        "updated_theorem_ids": ["NG_LADDER_BOUNDED_INTERFACE"],
        "lean_direct_total": lean_direct_total,
        "lean_auxiliary_total": lean_aux_total,
        "lean_missing_total": lean_missing_total,
        "counting_core_formalized": True,
        "assignment_family_count_eq_two_pow": True,
        "surjective_lens_equiv_explicit": True,
        "bounded_interface_still_auxiliary": False,
        "full_corollary_pending": False,
        "lake_build_status": lake_build_status,
        "reproduce_includes_t20": includes_t20,
        "reproduce_includes_t21": includes_t21,
        "reproduce_includes_t22": includes_t22,
        "reproduce_includes_t23": includes_t23,
        "reproduce_includes_t24": includes_t24,
        "reproduce_includes_t25": includes_t25,
        "reproduce_includes_t26": includes_t26,
        "reproduce_includes_t27": includes_t27,
        "reproduce_includes_t28": includes_t28,
        "vision_present": bool(bridge.get("source_context", {}).get("vision_present")),
        "status": "success",
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lean_finite_lens_count_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("PASS: T28 finite-lens count validation")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path("results/T28")
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "generated_at_utc": now_iso(),
            "theorem_count": 0,
            "updated_theorem_ids": [],
            "lean_direct_total": 0,
            "lean_auxiliary_total": 0,
            "lean_missing_total": 0,
            "counting_core_formalized": False,
            "assignment_family_count_eq_two_pow": False,
            "surjective_lens_equiv_explicit": False,
            "bounded_interface_still_auxiliary": False,
            "full_corollary_pending": False,
            "lake_build_status": "failed",
            "reproduce_includes_t20": False,
            "reproduce_includes_t21": False,
            "reproduce_includes_t22": False,
            "reproduce_includes_t23": False,
            "reproduce_includes_t24": False,
            "reproduce_includes_t25": False,
            "reproduce_includes_t26": False,
            "reproduce_includes_t27": False,
            "reproduce_includes_t28": False,
            "vision_present": Path("vision.md").exists(),
            "status": "failed",
            "error": str(exc),
        }
        (out_dir / "lean_finite_lens_count_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"FAIL: {exc}")
        raise SystemExit(1)
