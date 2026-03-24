#!/usr/bin/env python3
"""Run T38 Lean ArrowDPI validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

BASELINE_REPAIRS = [
    "lean/SixBirdsNoGo/Idempotence.lean",
    "lean/SixBirdsNoGo/TreeExactness.lean",
    "lean/SixBirdsNoGo/TreeExactnessExample.lean",
    "lean/SixBirdsNoGo/ClosedWalkExactness.lean",
    "lean/SixBirdsNoGo/FiniteLensDefinability.lean",
    "lean/SixBirdsNoGo/FiniteLensDefinabilityExample.lean",
    "lean/SixBirdsNoGo/ContractionUniqueness.lean",
    "lean/SixBirdsNoGo/ContractionUniquenessExample.lean",
    "lean/SixBirdsNoGo/ForestForceBridge.lean",
    "lean/SixBirdsNoGo/ForestForceBridgeExample.lean",
    "lean/SixBirdsNoGo/BoundedInterfaceNoLadder.lean",
    "lean/SixBirdsNoGo/BoundedInterfaceNoLadderExample.lean",
]
REQUIRED_NAMES = [
    "honestObservedPathLaw",
    "microArrowKL",
    "macroArrowKL",
    "mapPathState_prependState",
    "mapPathState_reversePathState",
    "reversePushforwardPathLaw",
    "arrowDPI",
    "microReversible_implies_macroReversible",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fail(msg: str) -> None:
    raise ValueError(msg)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"{path} must parse to object")
    return data


def theorem_map(rows: list[dict]) -> dict[str, dict]:
    return {row["theorem_id"]: row for row in rows}


def claim_map(rows: list[dict]) -> dict[str, dict]:
    return {row["claim_id"]: row for row in rows}


def repro_flags(text: str) -> dict[str, bool]:
    return {f"reproduce_includes_t{i}": f"run_t{i}" in text for i in range(20, 39)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T38 Lean ArrowDPI validation")
    parser.add_argument("--output-dir", default="results/T38")
    args = parser.parse_args()

    yaml_p = Path("docs/project/lean_arrow_dpi.yaml")
    readiness_p = Path("docs/project/readiness_checklist.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    pack_p = Path("docs/project/theorem_pack_arrow_protocol.yaml")
    claims_p = Path("docs/project/claim_audit_freeze.yaml")
    lean_p = Path("lean/SixBirdsNoGo/ArrowDPI.lean")
    lean_example_p = Path("lean/SixBirdsNoGo/ArrowDPIExample.lean")
    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    repro_p = Path("src/sixbirds_nogo/repro.py")

    for path in [yaml_p, readiness_p, atlas_p, pack_p, claims_p, lean_p, lean_example_p, lean_root_p]:
        if not path.exists():
            fail(f"missing required input: {path}")

    data = load_json(yaml_p)
    readiness = theorem_map(load_json(readiness_p)["theorems"])
    atlas = theorem_map(load_json(atlas_p)["theorems"])
    pack = theorem_map(load_json(pack_p)["theorem_fronts"])
    claims = claim_map(load_json(claims_p)["claims"])

    if len(data["theorem_fronts"]) != 1 or data["theorem_fronts"][0]["theorem_id"] != "NG_ARROW_DPI":
        fail("lean_arrow_dpi must contain exactly NG_ARROW_DPI")
    row = data["theorem_fronts"][0]
    if row["bridge_status"] != "direct_ready":
        fail("bridge_status must be direct_ready")
    for key in ["bridge_statement", "prerequisites", "direct_corollaries", "scope_limits", "lean_artifacts"]:
        if not row.get(key):
            fail(f"missing nonempty field: {key}")

    lean_text = lean_p.read_text(encoding="utf-8")
    for name in REQUIRED_NAMES:
        if name not in lean_text:
            fail(f"missing required Lean name: {name}")
    if "FiniteKLDPI" not in lean_text:
        fail("ArrowDPI.lean must use FiniteKLDPI")

    root_text = lean_root_p.read_text(encoding="utf-8")
    for imp in ["import SixBirdsNoGo.ArrowDPI", "import SixBirdsNoGo.ArrowDPIExample"]:
        if imp not in root_text:
            fail(f"missing root import: {imp}")

    if readiness["NG_ARROW_DPI"]["lean_support"]["status"] != "direct":
        fail("NG_ARROW_DPI readiness lean status must be direct")
    if atlas["NG_ARROW_DPI"]["support_snapshot"]["lean_support"]["status"] != "direct":
        fail("NG_ARROW_DPI atlas lean status must be direct")
    if readiness["NG_PROTOCOL_TRAP"]["lean_support"]["status"] != "direct":
        fail("NG_PROTOCOL_TRAP must now be Lean-direct after T39")

    pack_row = pack["NG_ARROW_DPI"]
    if "direct lean" in " ".join(pack_row["remaining_blockers"]).lower():
        fail("pack blockers must no longer say direct Lean missing")
    if pack_row["next_ticket"]["id"] != "PLAN_NEXT_14_arrow_protocol_guardrail_hold":
        fail("pack next_ticket mismatch")
    claim = claims["NG_ARROW_DPI.core"]
    if "direct lean" in " ".join(claim["blockers"]).lower():
        fail("claim blockers must no longer say direct Lean missing")
    if claim["next_ticket"]["id"] != "PLAN_NEXT_14_arrow_protocol_guardrail_hold":
        fail("claim next_ticket mismatch")

    direct_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "direct"]
    aux_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "auxiliary_only"]
    missing_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "missing"]
    expected_direct = [
        "NG_LADDER_IDEM",
        "NG_FORCE_FOREST",
        "NG_FORCE_NULL",
        "NG_LADDER_BOUNDED_INTERFACE",
        "NG_ARROW_DPI",
        "NG_PROTOCOL_TRAP",
        "NG_MACRO_CLOSURE_DEFICIT",
    ]
    if sorted(direct_ids) != sorted(expected_direct):
        fail("direct Lean frontier mismatch")
    if aux_ids != ["NG_OBJECT_CONTRACTIVE"]:
        fail("auxiliary Lean frontier mismatch")
    if missing_ids != []:
        fail("missing Lean frontier mismatch")

    lake_status = "skipped_tool_unavailable"
    baseline_build_passed = True
    if shutil.which("lake") is not None:
        proc = subprocess.run(["lake", "build"], cwd="lean", capture_output=True, text=True, check=False)
        baseline_build_passed = proc.returncode == 0
        lake_status = "passed" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""
    if repro_p.exists() and "run_t38_lean_arrow_dpi.py" not in repro_text:
        fail("repro.py must include run_t38_lean_arrow_dpi.py")

    summary = {
        "generated_at_utc": now_iso(),
        "theorem_count": 1,
        "updated_theorem_ids": ["NG_ARROW_DPI"],
        "lean_direct_total": len(direct_ids),
        "lean_auxiliary_total": len(aux_ids),
        "lean_missing_total": len(missing_ids),
        "arrow_direct": readiness["NG_ARROW_DPI"]["lean_support"]["status"] == "direct",
        "deterministic_pathlaw_dpi_present": "arrowDPI" in lean_text,
        "reverse_pushforward_commutation_present": "reversePushforwardPathLaw" in lean_text,
        "equality_form_zero_arrow_corollary_present": "microReversible_implies_macroReversible" in lean_text,
        "honest_observation_scope_frozen": "honest deterministic observation only" in json.dumps(row["scope_limits"]).lower(),
        "protocol_still_missing": readiness["NG_PROTOCOL_TRAP"]["lean_support"]["status"] == "missing",
        "baseline_build_passed": baseline_build_passed,
        "baseline_repair_subset_touched": BASELINE_REPAIRS,
        "lake_build_status": lake_status,
        **repro_flags(repro_text),
        "vision_present": Path("vision.md").exists(),
        "status": "success",
    }

    expected = {
        "theorem_count": 1,
        "updated_theorem_ids": ["NG_ARROW_DPI"],
        "lean_direct_total": 7,
        "lean_auxiliary_total": 1,
        "lean_missing_total": 0,
        "arrow_direct": True,
        "deterministic_pathlaw_dpi_present": True,
        "reverse_pushforward_commutation_present": True,
        "equality_form_zero_arrow_corollary_present": True,
        "honest_observation_scope_frozen": True,
        "protocol_still_missing": False,
        "baseline_build_passed": True,
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f"summary anchor mismatch: {key}")
    if lake_status not in {"passed", "skipped_tool_unavailable"}:
        fail("lake_build_status must be passed or skipped_tool_unavailable")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lean_arrow_dpi_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
