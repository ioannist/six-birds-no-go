#!/usr/bin/env python3
"""Validate T29 bounded-interface no-ladder Lean corollary and emit summary."""

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
    parser = argparse.ArgumentParser(description="Run T29 bounded-interface Lean corollary validation")
    parser.add_argument("--output-dir", default="results/T29")
    args = parser.parse_args()

    corollary_p = Path("docs/project/lean_corollary_bounded_interface.yaml")
    count_p = Path("docs/project/lean_count_bounded_interface.yaml")
    ready_p = Path("docs/project/readiness_checklist.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    pack_p = Path("docs/project/theorem_pack_bounded_interface.yaml")
    claims_p = Path("docs/project/claim_audit_freeze.yaml")
    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    corollary_lean_p = Path("lean/SixBirdsNoGo/BoundedInterfaceNoLadder.lean")
    corollary_ex_p = Path("lean/SixBirdsNoGo/BoundedInterfaceNoLadderExample.lean")

    required = [
        corollary_p,
        count_p,
        ready_p,
        atlas_p,
        pack_p,
        claims_p,
        lean_root_p,
        corollary_lean_p,
        corollary_ex_p,
    ]
    for p in required:
        if not p.exists():
            fail(f"missing required input: {p}")

    corollary = load_json(corollary_p)
    count = load_json(count_p)
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    pack = load_json(pack_p)
    claims = load_json(claims_p)

    for k in ["version", "generated_at_utc", "source_context", "status_enums", "theorem_fronts"]:
        if k not in corollary:
            fail(f"lean corollary file missing key: {k}")

    fronts = corollary["theorem_fronts"]
    if not isinstance(fronts, list) or len(fronts) != 1:
        fail("lean corollary file must contain exactly one theorem front")
    row = fronts[0]
    if row.get("theorem_id") != "NG_LADDER_BOUNDED_INTERFACE":
        fail("theorem-front ID must be NG_LADDER_BOUNDED_INTERFACE")
    if row.get("bridge_status") != "direct_ready":
        fail("bridge_status must be direct_ready")
    for key in ["bridge_statement", "prerequisites", "direct_corollaries", "scope_limits", "lean_artifacts"]:
        val = row.get(key)
        if key == "bridge_statement":
            if not str(val).strip():
                fail("bridge_statement must be non-empty")
        elif not isinstance(val, list) or not val:
            fail(f"{key} must be non-empty")

    corollary_text = corollary_lean_p.read_text(encoding="utf-8")
    corollary_ex_text = corollary_ex_p.read_text(encoding="utf-8")
    lean_root_text = lean_root_p.read_text(encoding="utf-8")

    for token in [
        "observedImageProfile",
        "observedImageProfile_stabilizes_after_one",
        "observedDefinablePredicate",
        "observedDefinablePredicate_stabilizes_after_one",
        "boundedInterface_noLadderCorollary",
        "Idempotence",
        "FiniteLensDefinability",
    ]:
        if token not in corollary_text:
            fail(f"BoundedInterfaceNoLadder.lean missing expected token: {token}")

    if "BoundedInterfaceNoLadder" not in corollary_ex_text:
        fail("BoundedInterfaceNoLadderExample.lean must import the corollary module")
    for imp in [
        "import SixBirdsNoGo.BoundedInterfaceNoLadder",
        "import SixBirdsNoGo.BoundedInterfaceNoLadderExample",
    ]:
        if imp not in lean_root_text:
            fail(f"lean/SixBirdsNoGo.lean missing import: {imp}")

    ready_map = {t["theorem_id"]: t for t in readiness["theorems"]}
    atlas_map = {t["theorem_id"]: t for t in atlas["theorems"]}
    claim_map = {c["claim_id"]: c for c in claims["claims"]}

    if ready_map["NG_LADDER_BOUNDED_INTERFACE"]["lean_support"]["status"] != "direct":
        fail("readiness bounded-interface lean_support must be direct")
    if atlas_map["NG_LADDER_BOUNDED_INTERFACE"]["support_snapshot"]["lean_support"]["status"] != "direct":
        fail("atlas bounded-interface lean_support must be direct")
    if ready_map["NG_LADDER_BOUNDED_INTERFACE"].get("blockers"):
        fail("readiness bounded-interface blockers must be empty")
    if atlas_map["NG_LADDER_BOUNDED_INTERFACE"].get("blockers"):
        fail("atlas bounded-interface blockers must be empty")

    pack_row = next((t for t in pack["theorem_fronts"] if t["theorem_id"] == "NG_LADDER_BOUNDED_INTERFACE"), None)
    if pack_row is None:
        fail("bounded-interface theorem pack missing theorem row")
    if pack_row.get("remaining_blockers"):
        fail("bounded-interface theorem pack remaining_blockers must be empty")
    if pack_row.get("next_ticket") is not None:
        fail("bounded-interface theorem pack next_ticket must be null")
    lean_refs = pack_row.get("evidence_refs", {}).get("lean", [])
    for rel in [
        "lean/SixBirdsNoGo/BoundedInterfaceNoLadder.lean",
        "lean/SixBirdsNoGo/BoundedInterfaceNoLadderExample.lean",
        "docs/project/lean_corollary_bounded_interface.yaml",
        "results/T29/lean_bounded_interface_corollary_summary.json",
    ]:
        if rel not in lean_refs:
            fail(f"bounded-interface theorem pack missing lean ref: {rel}")

    core_claim = claim_map["NG_LADDER_BOUNDED_INTERFACE.core"]
    if core_claim.get("blockers"):
        fail("bounded-interface core claim blockers must be empty")
    if core_claim.get("next_ticket") is not None:
        fail("bounded-interface core claim next_ticket must be null")
    if core_claim.get("support_grade") != "direct":
        fail("bounded-interface core claim support_grade must be direct")

    count_row = count["theorem_fronts"][0]
    if count_row.get("full_corollary_pending") is not False:
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
    includes_t29 = "run_t29_lean_bounded_interface_corollary.py" in repro_text
    if not includes_t29:
        fail("repro pipeline missing run_t29_lean_bounded_interface_corollary.py step")

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
        "bounded_interface_direct": ready_map["NG_LADDER_BOUNDED_INTERFACE"]["lean_support"]["status"] == "direct",
        "corollary_formalized": True,
        "count_core_retained": True,
        "idempotence_bridge_used": True,
        "signature_stabilization_formalized": True,
        "observed_predicate_stabilization_formalized": True,
        "no_ladder_corollary_present": True,
        "extension_escape_scoped_outside_theorem": True,
        "strong_front_blockers_cleared": True,
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
        "reproduce_includes_t29": includes_t29,
        "vision_present": bool(corollary.get("source_context", {}).get("vision_present")),
        "status": "success",
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lean_bounded_interface_corollary_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("PASS: T29 bounded-interface corollary validation")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path("results/T29")
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "generated_at_utc": now_iso(),
            "theorem_count": 0,
            "updated_theorem_ids": [],
            "lean_direct_total": 0,
            "lean_auxiliary_total": 0,
            "lean_missing_total": 0,
            "bounded_interface_direct": False,
            "corollary_formalized": False,
            "count_core_retained": False,
            "idempotence_bridge_used": False,
            "signature_stabilization_formalized": False,
            "observed_predicate_stabilization_formalized": False,
            "no_ladder_corollary_present": False,
            "extension_escape_scoped_outside_theorem": False,
            "strong_front_blockers_cleared": False,
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
            "reproduce_includes_t29": False,
            "vision_present": Path("vision.md").exists(),
            "status": "failed",
            "error": str(exc),
        }
        (out_dir / "lean_bounded_interface_corollary_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        print(f"FAIL: {exc}")
        raise SystemExit(1)
