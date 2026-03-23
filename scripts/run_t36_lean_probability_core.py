#!/usr/bin/env python3
"""Run T36 Lean finite probability core validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

EXPECTED_IMPLEMENTED = [
    "FP_FINITE_DISTRIBUTIONS",
    "FP_DETERMINISTIC_PUSHFORWARD",
    "FP_FIXED_HORIZON_PATH_LAWS",
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
    "FinLaw",
    "FiniteKernel",
    "PathState",
    "pushforward",
    "pushforwardPathLaw",
    "firstMarginal",
    "secondMarginal",
    "timeMarginal",
    "twoTimeMarginal",
    "pathLaw",
    "pushforward_sum_eq_one",
    "firstMarginal_sum_eq_one",
    "secondMarginal_sum_eq_one",
    "timeMarginal_sum_eq_one",
    "pathLaw_sum_eq_one",
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
    return {f"reproduce_includes_t{i}": f"run_t{i}" in text for i in range(20, 37)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T36 Lean probability core validation")
    parser.add_argument("--output-dir", default="results/T36")
    args = parser.parse_args()

    charter_p = Path("docs/project/lean_probability_scope_charter.yaml")
    core_p = Path("docs/project/lean_probability_core.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    readiness_p = Path("docs/project/readiness_checklist.yaml")
    lean_core_p = Path("lean/SixBirdsNoGo/FiniteProbabilityCore.lean")
    lean_example_p = Path("lean/SixBirdsNoGo/FiniteProbabilityCoreExample.lean")
    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    repro_p = Path("src/sixbirds_nogo/repro.py")

    for path in [charter_p, core_p, atlas_p, readiness_p, lean_core_p, lean_example_p, lean_root_p]:
        if not path.exists():
            fail(f"missing required input: {path}")

    charter = load_json(charter_p)
    core = load_json(core_p)
    atlas = load_json(atlas_p)
    readiness = load_json(readiness_p)

    required_top = {
        "version",
        "generated_at_utc",
        "source_context",
        "status_enums",
        "implemented_foundations",
        "pending_foundations",
        "frontier_status_snapshot",
        "milestone_handoff",
    }
    if set(core) != required_top:
        fail("lean_probability_core top-level keys must match required set exactly")

    source_context = core["source_context"]
    vision_present = Path("vision.md").exists()
    if source_context.get("vision_present") != vision_present:
        fail("vision_present flag mismatch")
    if vision_present and source_context.get("vision_path") != "vision.md":
        fail("vision_path must be vision.md when vision is present")

    implemented = core["implemented_foundations"]
    if [row["foundation_id"] for row in implemented] != EXPECTED_IMPLEMENTED:
        fail("implemented_foundations must match required order exactly")
    if any(row["component_status"] != "formalized" for row in implemented):
        fail("implemented foundations must all be formalized")
    if not any("marginal" in row["note"].lower() for row in implemented):
        fail("implemented foundations must mention exact marginals")

    pending = core["pending_foundations"]
    pending_ids = [row["foundation_id"] for row in pending]
    for fid in EXPECTED_PENDING:
        if fid not in pending_ids:
            fail(f"missing pending foundation {fid}")
        row = next(r for r in pending if r["foundation_id"] == fid)
        if row["component_status"] != "pending":
            fail(f"pending foundation mis-marked: {fid}")

    frontier = core["frontier_status_snapshot"]
    if frontier["direct_ids"] != EXPECTED_DIRECT:
        fail("direct frontier ids mismatch")
    if frontier["auxiliary_ids"] != EXPECTED_AUX:
        fail("auxiliary frontier ids mismatch")
    if frontier["missing_ids"] != EXPECTED_MISSING:
        fail("missing frontier ids mismatch")
    if frontier["status"] != "unchanged":
        fail("frontier status snapshot must be unchanged")

    readiness_map = {row["theorem_id"]: row["lean_support"]["status"] for row in readiness["theorems"]}
    direct_ids = [tid for tid, status in readiness_map.items() if status == "direct"]
    aux_ids = [tid for tid, status in readiness_map.items() if status == "auxiliary_only"]
    missing_ids = [tid for tid, status in readiness_map.items() if status == "missing"]
    no_drift = sorted(direct_ids) == sorted(EXPECTED_DIRECT) and aux_ids == EXPECTED_AUX and sorted(missing_ids) == sorted(EXPECTED_MISSING)
    if not no_drift:
        fail("theorem status drift detected")

    if core["milestone_handoff"]["next_ticket_id"] is not None:
        fail("next_ticket_id must be null after T44")
    if core["milestone_handoff"]["next_ticket_title"] is not None:
        fail("next_ticket_title must be null after T44")
    if "bounded" not in core["milestone_handoff"]["note"].lower():
        fail("milestone handoff note must mention the explicit boundary")

    charter_ids = {row["foundation_id"] for row in charter["allowed_foundations"]}
    for fid in EXPECTED_IMPLEMENTED + EXPECTED_PENDING:
        if fid not in charter_ids:
            fail(f"core references foundation absent from T35 charter: {fid}")

    atlas_ids = set(atlas["paper_order"])
    for row in implemented + pending:
        for theorem_id in row["theorem_consumers"]:
            if theorem_id not in atlas_ids:
                fail(f"unknown theorem consumer {theorem_id} in core metadata")

    lean_core_text = lean_core_p.read_text(encoding="utf-8")
    for name in REQUIRED_NAMES:
        if name not in lean_core_text:
            fail(f"required Lean name missing from core file: {name}")

    root_text = lean_root_p.read_text(encoding="utf-8")
    for imp in [
        "import SixBirdsNoGo.FiniteProbabilityCore",
        "import SixBirdsNoGo.FiniteProbabilityCoreExample",
    ]:
        if imp not in root_text:
            fail(f"missing root import: {imp}")

    lake_status = "skipped_tool_unavailable"
    if shutil.which("lake") is not None:
        proc = subprocess.run(
            ["lake", "build"],
            cwd="lean",
            capture_output=True,
            text=True,
            check=False,
        )
        lake_status = "passed" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""
    if repro_p.exists() and "run_t36_lean_probability_core.py" not in repro_text:
        fail("repro.py must include run_t36_lean_probability_core.py")

    summary = {
        "generated_at_utc": now_iso(),
        "direct_front_count": len(frontier["direct_ids"]),
        "auxiliary_front_count": len(frontier["auxiliary_ids"]),
        "missing_front_count": len(frontier["missing_ids"]),
        "implemented_foundation_count": len(implemented),
        "pending_foundation_count": len(pending),
        "finite_distributions_formalized": "FP_FINITE_DISTRIBUTIONS" in [row["foundation_id"] for row in implemented],
        "deterministic_pushforward_formalized": "FP_DETERMINISTIC_PUSHFORWARD" in [row["foundation_id"] for row in implemented],
        "marginals_formalized": all(name in lean_core_text for name in ["firstMarginal", "secondMarginal", "timeMarginal", "twoTimeMarginal"]),
        "fixed_horizon_path_laws_formalized": "FP_FIXED_HORIZON_PATH_LAWS" in [row["foundation_id"] for row in implemented],
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
        "implemented_foundation_count": 3,
        "pending_foundation_count": 0,
        "finite_distributions_formalized": True,
        "deterministic_pushforward_formalized": True,
        "marginals_formalized": True,
        "fixed_horizon_path_laws_formalized": True,
        "no_theorem_status_drift": True,
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f"summary anchor mismatch: {key}")
    if lake_status not in {"passed", "skipped_tool_unavailable"}:
        fail("lake_build_status must be passed or skipped_tool_unavailable")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lean_probability_core_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
