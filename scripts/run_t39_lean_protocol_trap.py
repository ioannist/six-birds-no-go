#!/usr/bin/env python3
"""Run T39 Lean protocol-trap validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

REQUIRED_NAMES = [
    "AutonomousLiftedSystem",
    "liftedPathLaw",
    "stationaryInitializedMicroReversible",
    "honestObservedLiftedPathLaw",
    "stationaryLiftedArrowDPI",
    "stationaryLiftedMicroReversible_implies_macroReversible",
    "protocolTrap_noHonestArrow",
]
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
    return {f"reproduce_includes_t{i}": f"run_t{i}" in text for i in range(20, 40)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T39 Lean protocol-trap validation")
    parser.add_argument("--output-dir", default="results/T39")
    args = parser.parse_args()

    yaml_p = Path("docs/project/lean_protocol_trap.yaml")
    arrow_yaml_p = Path("docs/project/lean_arrow_dpi.yaml")
    readiness_p = Path("docs/project/readiness_checklist.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    pack_p = Path("docs/project/theorem_pack_arrow_protocol.yaml")
    claims_p = Path("docs/project/claim_audit_freeze.yaml")
    lean_p = Path("lean/SixBirdsNoGo/ProtocolTrap.lean")
    lean_example_p = Path("lean/SixBirdsNoGo/ProtocolTrapExample.lean")
    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    repro_p = Path("src/sixbirds_nogo/repro.py")

    for path in [yaml_p, arrow_yaml_p, readiness_p, atlas_p, pack_p, claims_p, lean_p, lean_example_p, lean_root_p]:
        if not path.exists():
            fail(f"missing required input: {path}")

    data = load_json(yaml_p)
    arrow_data = load_json(arrow_yaml_p)
    readiness = theorem_map(load_json(readiness_p)["theorems"])
    atlas = theorem_map(load_json(atlas_p)["theorems"])
    pack = theorem_map(load_json(pack_p)["theorem_fronts"])
    claims = claim_map(load_json(claims_p)["claims"])

    if len(data["theorem_fronts"]) != 1 or data["theorem_fronts"][0]["theorem_id"] != "NG_PROTOCOL_TRAP":
        fail("lean_protocol_trap must contain exactly NG_PROTOCOL_TRAP")
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
    if "ArrowDPI" not in lean_text:
        fail("ProtocolTrap.lean must use ArrowDPI")

    root_text = lean_root_p.read_text(encoding="utf-8")
    for imp in ["import SixBirdsNoGo.ProtocolTrap", "import SixBirdsNoGo.ProtocolTrapExample"]:
        if imp not in root_text:
            fail(f"missing root import: {imp}")

    if readiness["NG_PROTOCOL_TRAP"]["lean_support"]["status"] != "direct":
        fail("NG_PROTOCOL_TRAP readiness lean status must be direct")
    if readiness["NG_ARROW_DPI"]["lean_support"]["status"] != "direct":
        fail("NG_ARROW_DPI readiness lean status must remain direct")
    if atlas["NG_PROTOCOL_TRAP"]["support_snapshot"]["lean_support"]["status"] != "direct":
        fail("NG_PROTOCOL_TRAP atlas lean status must be direct")
    if readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] != "direct":
        fail("NG_MACRO_CLOSURE_DEFICIT must now be Lean-direct")

    pack_row = pack["NG_PROTOCOL_TRAP"]
    if not all(ref in pack_row["evidence_refs"]["lean"] for ref in [
        "lean/SixBirdsNoGo/ArrowDPI.lean",
        "lean/SixBirdsNoGo/ArrowDPIExample.lean",
        "lean/SixBirdsNoGo/ProtocolTrap.lean",
        "lean/SixBirdsNoGo/ProtocolTrapExample.lean",
        "docs/project/lean_arrow_dpi.yaml",
        "docs/project/lean_protocol_trap.yaml",
        "results/T38/lean_arrow_dpi_summary.json",
        "results/T39/lean_protocol_trap_summary.json",
    ]):
        fail("protocol pack Lean evidence refs incomplete")
    if "direct lean" in " ".join(pack_row["remaining_blockers"]).lower():
        fail("protocol pack blockers must no longer say direct Lean missing")
    if pack_row["next_ticket"]["id"] != "PLAN_NEXT_14_arrow_protocol_guardrail_hold":
        fail("protocol pack next_ticket mismatch")

    claim = claims["NG_PROTOCOL_TRAP.core"]
    if "direct lean" in " ".join(claim["blockers"]).lower():
        fail("protocol claim blockers must no longer say direct Lean missing")
    if claim["next_ticket"]["id"] != "PLAN_NEXT_14_arrow_protocol_guardrail_hold":
        fail("protocol claim next_ticket mismatch")

    arrow_row = arrow_data["theorem_fronts"][0]
    arrow_followup_rebased = arrow_row["next_ticket"]["id"] == "PLAN_NEXT_14_arrow_protocol_guardrail_hold"
    if not arrow_followup_rebased:
        fail("ArrowDPI follow-up must be rebased to PLAN_NEXT_14")

    direct_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "direct"]
    aux_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "auxiliary_only"]
    missing_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "missing"]
    if sorted(direct_ids) != sorted(EXPECTED_DIRECT):
        fail("direct Lean frontier mismatch")
    if aux_ids != EXPECTED_AUX:
        fail("auxiliary Lean frontier mismatch")
    if sorted(missing_ids) != sorted(EXPECTED_MISSING):
        fail("missing Lean frontier mismatch")

    lake_status = "skipped_tool_unavailable"
    if shutil.which("lake") is not None:
        proc = subprocess.run(["lake", "build"], cwd="lean", capture_output=True, text=True, check=False)
        lake_status = "passed" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""
    if repro_p.exists() and "run_t39_lean_protocol_trap.py" not in repro_text:
        fail("repro.py must include run_t39_lean_protocol_trap.py")

    summary = {
        "generated_at_utc": now_iso(),
        "theorem_count": 1,
        "updated_theorem_ids": ["NG_PROTOCOL_TRAP"],
        "lean_direct_total": len(direct_ids),
        "lean_auxiliary_total": len(aux_ids),
        "lean_missing_total": len(missing_ids),
        "protocol_direct": readiness["NG_PROTOCOL_TRAP"]["lean_support"]["status"] == "direct",
        "autonomous_lifted_wrapper_present": "AutonomousLiftedSystem" in lean_text,
        "stationary_initial_scope_explicit": "stationary or reversal-compatible initialization only" in json.dumps(row["scope_limits"]).lower(),
        "stationary_lifted_arrow_dpi_present": "stationaryLiftedArrowDPI" in lean_text,
        "stationary_macro_reversibility_corollary_present": "stationaryLiftedMicroReversible_implies_macroReversible" in lean_text,
        "protocol_no_honest_arrow_wrapper_present": "protocolTrap_noHonestArrow" in lean_text,
        "arrow_dependency_used": "ArrowDPI" in lean_text,
        "arrow_followup_rebased": arrow_followup_rebased,
        "closure_still_missing": readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] == "missing",
        "lake_build_status": lake_status,
        **repro_flags(repro_text),
        "vision_present": Path("vision.md").exists(),
        "status": "success",
    }

    expected = {
        "theorem_count": 1,
        "updated_theorem_ids": ["NG_PROTOCOL_TRAP"],
        "lean_direct_total": 7,
        "lean_auxiliary_total": 1,
        "lean_missing_total": 0,
        "protocol_direct": True,
        "autonomous_lifted_wrapper_present": True,
        "stationary_initial_scope_explicit": True,
        "stationary_lifted_arrow_dpi_present": True,
        "stationary_macro_reversibility_corollary_present": True,
        "protocol_no_honest_arrow_wrapper_present": True,
        "arrow_dependency_used": True,
        "arrow_followup_rebased": True,
        "closure_still_missing": False,
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f"summary anchor mismatch: {key}")
    if lake_status not in {"passed", "skipped_tool_unavailable"}:
        fail("lake_build_status must be passed or skipped_tool_unavailable")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lean_protocol_trap_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
