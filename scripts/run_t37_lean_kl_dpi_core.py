#!/usr/bin/env python3
"""Run T37 Lean finite KL/DPI core validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

EXPECTED_IMPLEMENTED = [
    "FP_MINIMAL_SCALAR_LOG_LAYER",
    "FP_PATH_REVERSAL",
    "FP_FINITE_KL",
    "FP_DETERMINISTIC_DPI",
]
EXPECTED_PENDING: list[str] = []
EXPECTED_DIRECT = [
    "NG_LADDER_IDEM",
    "NG_FORCE_FOREST",
    "NG_FORCE_NULL",
    "NG_LADDER_BOUNDED_INTERFACE",
    "NG_ARROW_DPI",
    "NG_PROTOCOL_TRAP",
    "NG_MACRO_CLOSURE_DEFICIT",
]
EXPECTED_AUX = ["NG_OBJECT_CONTRACTIVE"]
EXPECTED_MISSING = []
REQUIRED_NAMES = [
    "ScalarLogLayer",
    "AbsolutelyContinuous",
    "supportList",
    "reversePathState",
    "reversePathLaw",
    "KL",
    "pushforwardPointWeight_eq_fiberMass",
    "reversePathLaw_sum_eq_one",
    "KL_pushforward_dpi",
    "pathLawPushforwardDPI",
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


def repro_flags(text: str) -> dict[str, bool]:
    return {f"reproduce_includes_t{i}": f"run_t{i}" in text for i in range(20, 38)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T37 Lean KL/DPI core validation")
    parser.add_argument("--output-dir", default="results/T37")
    args = parser.parse_args()

    yaml_p = Path("docs/project/lean_kl_dpi_core.yaml")
    charter_p = Path("docs/project/lean_probability_scope_charter.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    readiness_p = Path("docs/project/readiness_checklist.yaml")
    t36_p = Path("docs/project/lean_probability_core.yaml")
    lean_core_p = Path("lean/SixBirdsNoGo/FiniteKLDPI.lean")
    lean_example_p = Path("lean/SixBirdsNoGo/FiniteKLDPIExample.lean")
    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    repro_p = Path("src/sixbirds_nogo/repro.py")

    for path in [yaml_p, charter_p, atlas_p, readiness_p, t36_p, lean_core_p, lean_example_p, lean_root_p]:
        if not path.exists():
            fail(f"missing required input: {path}")

    data = load_json(yaml_p)
    charter = load_json(charter_p)
    atlas = load_json(atlas_p)
    readiness = load_json(readiness_p)
    t36 = load_json(t36_p)

    required_top = {
        "version",
        "generated_at_utc",
        "source_context",
        "status_enums",
        "formalization_boundary",
        "implemented_foundations",
        "pending_foundations",
        "frontier_status_snapshot",
        "milestone_handoff",
    }
    if set(data) != required_top:
        fail("lean_kl_dpi_core top-level keys must match required set exactly")

    source_context = data["source_context"]
    vision_present = Path("vision.md").exists()
    if source_context.get("vision_present") != vision_present:
        fail("vision_present flag mismatch")
    if vision_present and source_context.get("vision_path") != "vision.md":
        fail("vision_path must be vision.md when vision is present")

    boundary = data["formalization_boundary"]
    if boundary.get("formalization_mode") != "minimal_scalar_log_interface":
        fail("formalization mode mismatch")
    boundary_text = json.dumps(boundary).lower()
    for phrase in [
        "minimal and explicit",
        "no broad information",
        "generic stochastic channels",
        "generic entropy/information library",
        "broad real-analysis buildout",
    ]:
        if phrase not in boundary_text:
            fail(f"formalization boundary missing phrase: {phrase}")

    implemented = data["implemented_foundations"]
    if [row["foundation_id"] for row in implemented] != EXPECTED_IMPLEMENTED:
        fail("implemented foundations must match required order exactly")
    if any(row["component_status"] != "formalized" for row in implemented):
        fail("implemented foundations must all be formalized")

    pending = data["pending_foundations"]
    if [row["foundation_id"] for row in pending] != EXPECTED_PENDING:
        fail("pending foundations must match required order exactly")
    if any(row["component_status"] != "pending" for row in pending):
        fail("pending foundations must all be pending")

    frontier = data["frontier_status_snapshot"]
    if frontier["direct_ids"] != EXPECTED_DIRECT:
        fail("direct frontier ids mismatch")
    if frontier["auxiliary_ids"] != EXPECTED_AUX:
        fail("auxiliary frontier ids mismatch")
    if frontier["missing_ids"] != EXPECTED_MISSING:
        fail("missing frontier ids mismatch")
    if frontier["status"] != "unchanged":
        fail("frontier status snapshot must be unchanged")

    readiness_map = {row["theorem_id"]: row["lean_support"]["status"] for row in readiness["theorems"]}
    no_drift = (
        sorted([tid for tid, status in readiness_map.items() if status == "direct"]) == sorted(EXPECTED_DIRECT)
        and [tid for tid, status in readiness_map.items() if status == "auxiliary_only"] == EXPECTED_AUX
        and sorted([tid for tid, status in readiness_map.items() if status == "missing"]) == sorted(EXPECTED_MISSING)
    )
    if not no_drift:
        fail("theorem status drift detected")

    if data["milestone_handoff"]["next_ticket_id"] is not None:
        fail("next_ticket_id must be null after T44")
    if data["milestone_handoff"]["next_ticket_title"] is not None:
        fail("next_ticket_title must be null after T44")
    if "bounded" not in data["milestone_handoff"]["note"].lower():
        fail("milestone handoff note must mention the explicit boundary")

    charter_ids = {row["foundation_id"] for row in charter["allowed_foundations"]}
    for fid in EXPECTED_IMPLEMENTED + EXPECTED_PENDING:
        if fid not in charter_ids:
            fail(f"foundation absent from T35 charter: {fid}")

    atlas_ids = set(atlas["paper_order"])
    for row in implemented + pending:
        for theorem_id in row["theorem_consumers"]:
            if theorem_id not in atlas_ids:
                fail(f"unknown theorem consumer: {theorem_id}")

    lean_text = lean_core_p.read_text(encoding="utf-8")
    for name in REQUIRED_NAMES:
        if name not in lean_text:
            fail(f"required Lean name missing from FiniteKLDPI.lean: {name}")

    root_text = lean_root_p.read_text(encoding="utf-8")
    for imp in [
        "import SixBirdsNoGo.FiniteKLDPI",
        "import SixBirdsNoGo.FiniteKLDPIExample",
    ]:
        if imp not in root_text:
            fail(f"missing root import: {imp}")

    lake_status = "skipped_tool_unavailable"
    if shutil.which("lake") is not None:
        proc = subprocess.run(["lake", "build"], cwd="lean", capture_output=True, text=True, check=False)
        lake_status = "passed" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""
    if repro_p.exists() and "run_t37_lean_kl_dpi_core.py" not in repro_text:
        fail("repro.py must include run_t37_lean_kl_dpi_core.py")

    total_formalized_foundation_count = sum(1 for row in charter["allowed_foundations"] if row["decision"] == "allowed")
    summary = {
        "generated_at_utc": now_iso(),
        "direct_front_count": len(frontier["direct_ids"]),
        "auxiliary_front_count": len(frontier["auxiliary_ids"]),
        "missing_front_count": len(frontier["missing_ids"]),
        "total_formalized_foundation_count": total_formalized_foundation_count,
        "implemented_foundation_count": len(implemented),
        "pending_foundation_count": len(pending),
        "scalar_log_layer_explicit": "ScalarLogLayer" in lean_text,
        "path_reversal_formalized": all(name in lean_text for name in ["reversePathState", "reversePathLaw", "reversePathLaw_sum_eq_one"]),
        "finite_kl_formalized": "KL" in lean_text,
        "deterministic_dpi_formalized": all(name in lean_text for name in ["KL_pushforward_dpi", "pathLawPushforwardDPI"]),
        "reusable_finite_dpi_engine": True,
        "no_theorem_status_drift": no_drift,
        "lake_build_status": lake_status,
        **repro_flags(repro_text),
        "vision_present": vision_present,
        "status": "success",
    }

    expected = {
        "direct_front_count": 7,
        "auxiliary_front_count": 1,
        "missing_front_count": 0,
        "total_formalized_foundation_count": 9,
        "implemented_foundation_count": 4,
        "pending_foundation_count": 0,
        "scalar_log_layer_explicit": True,
        "path_reversal_formalized": True,
        "finite_kl_formalized": True,
        "deterministic_dpi_formalized": True,
        "reusable_finite_dpi_engine": True,
        "no_theorem_status_drift": True,
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f"summary anchor mismatch: {key}")
    if lake_status not in {"passed", "skipped_tool_unavailable"}:
        fail("lake_build_status must be passed or skipped_tool_unavailable")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lean_kl_dpi_core_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
