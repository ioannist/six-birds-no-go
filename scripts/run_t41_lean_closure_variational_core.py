#!/usr/bin/env python3
"""Run T41 Lean closure variational-core validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

REQUIRED_NAMES = [
    "MacroKernel",
    "deltaLaw",
    "packagedFutureLaw",
    "packagedFutureLawFamily",
    "macroCurrentLaw",
    "macroPairLaw",
    "conditionalMacroFutureRow",
    "ClosureVariationalLayer",
    "rowwiseObjective",
    "variationalObjective",
    "bestMacroKernel",
    "bestMacroKernel_row_formula",
    "bestMacroKernel_minimizesObjective",
    "bestMacroGap",
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
    return {f"reproduce_includes_t{i}": f"run_t{i}" in text for i in range(20, 43)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T41 Lean closure variational-core validation")
    parser.add_argument("--output-dir", default="results/T41")
    args = parser.parse_args()

    yaml_p = Path("docs/project/lean_closure_variational_core.yaml")
    feas_p = Path("docs/project/lean_closure_feasibility.yaml")
    readiness_p = Path("docs/project/readiness_checklist.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    pack_p = Path("docs/project/theorem_pack_closure.yaml")
    claims_p = Path("docs/project/claim_audit_freeze.yaml")
    lean_p = Path("lean/SixBirdsNoGo/ClosureVariationalCore.lean")
    lean_example_p = Path("lean/SixBirdsNoGo/ClosureVariationalCoreExample.lean")
    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    repro_p = Path("src/sixbirds_nogo/repro.py")

    for path in [yaml_p, feas_p, readiness_p, atlas_p, pack_p, claims_p, lean_p, lean_example_p, lean_root_p]:
        if not path.exists():
            fail(f"missing required input: {path}")

    data = load_json(yaml_p)
    feas = load_json(feas_p)
    readiness = theorem_map(load_json(readiness_p)["theorems"])
    atlas = theorem_map(load_json(atlas_p)["theorems"])
    pack = theorem_map(load_json(pack_p)["theorem_fronts"])
    claims = claim_map(load_json(claims_p)["claims"])

    if len(data["theorem_fronts"]) != 1 or data["theorem_fronts"][0]["theorem_id"] != "NG_MACRO_CLOSURE_DEFICIT":
        fail("lean_closure_variational_core must contain exactly NG_MACRO_CLOSURE_DEFICIT")
    row = data["theorem_fronts"][0]
    if row["bridge_status"] != "core_ready":
        fail("bridge_status must be core_ready")
    for key in ["bridge_statement", "prerequisites", "direct_corollaries", "scope_limits", "lean_artifacts"]:
        if not row.get(key):
            fail(f"missing nonempty field: {key}")

    lean_text = lean_p.read_text(encoding="utf-8")
    for name in REQUIRED_NAMES:
        if name not in lean_text:
            fail(f"missing required Lean name: {name}")
    for dep in ["FiniteProbabilityCore", "FiniteKLDPI"]:
        if dep not in lean_text:
            fail(f"ClosureVariationalCore.lean must use {dep}")

    root_text = lean_root_p.read_text(encoding="utf-8")
    for imp in ["import SixBirdsNoGo.ClosureVariationalCore", "import SixBirdsNoGo.ClosureVariationalCoreExample"]:
        if imp not in root_text:
            fail(f"missing root import: {imp}")

    if readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] != "direct":
        fail("NG_MACRO_CLOSURE_DEFICIT readiness Lean status must be direct")
    if atlas["NG_MACRO_CLOSURE_DEFICIT"]["support_snapshot"]["lean_support"]["status"] != "direct":
        fail("NG_MACRO_CLOSURE_DEFICIT atlas Lean status must be direct")

    pack_row = pack["NG_MACRO_CLOSURE_DEFICIT"]
    for ref in [
        "lean/SixBirdsNoGo/ClosureVariationalCore.lean",
        "lean/SixBirdsNoGo/ClosureVariationalCoreExample.lean",
        "docs/project/lean_closure_feasibility.yaml",
        "docs/project/lean_closure_variational_core.yaml",
        "results/T40/lean_closure_feasibility_summary.json",
        "results/T41/lean_closure_variational_core_summary.json",
        "results/T42/lean_closure_direct_pack_summary.json",
    ]:
        if ref not in pack_row["evidence_refs"]["lean"]:
            fail(f"missing theorem_pack_closure Lean evidence ref: {ref}")
    if "direct lean" in " ".join(pack_row["remaining_blockers"]).lower():
        fail("theorem_pack_closure blockers must no longer say direct Lean missing")
    if pack_row["next_ticket"]["id"] != "PLAN_NEXT_18_closure_scope_guardrail_hold":
        fail("theorem_pack_closure next_ticket mismatch")

    claim = claims["NG_MACRO_CLOSURE_DEFICIT.core"]
    if "direct lean" in " ".join(claim["blockers"]).lower():
        fail("claim blockers must no longer say direct Lean missing")
    if claim["next_ticket"]["id"] != "PLAN_NEXT_18_closure_scope_guardrail_hold":
        fail("claim next_ticket mismatch")

    if feas["decision"]["decision_mode"] != "proceed_to_variational_core":
        fail("T40 decision mode must remain proceed_to_variational_core")
    if feas["theorem_target"]["current_lean_status"] != "direct":
        fail("T40 artifact must now record closure as direct")
    obligation_map = {row["obligation_id"]: row for row in feas["obligation_matrix"]}
    for oid in [
        "CL_PACKAGED_FUTURE_LAW_FAMILY",
        "CL_FINITE_MACRO_KERNEL",
        "CL_VARIATIONAL_OBJECTIVE",
        "CL_ROWWISE_MINIMIZER_LEMMA",
        "CL_CLOSED_FORM_BEST_KERNEL",
    ]:
        if obligation_map[oid]["status"] != "already_formalized":
            fail(f"{oid} must now be already_formalized")
    if obligation_map["CL_CLOSURE_VARIATIONAL_IDENTITY_AND_COROLLARY"]["status"] != "already_formalized":
        fail("CL_CLOSURE_VARIATIONAL_IDENTITY_AND_COROLLARY must now be already_formalized")

    direct_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "direct"]
    aux_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "auxiliary_only"]
    missing_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "missing"]

    if sorted(direct_ids) != sorted([
        "NG_LADDER_IDEM",
        "NG_FORCE_FOREST",
        "NG_FORCE_NULL",
        "NG_LADDER_BOUNDED_INTERFACE",
        "NG_ARROW_DPI",
        "NG_PROTOCOL_TRAP",
        "NG_MACRO_CLOSURE_DEFICIT",
    ]):
        fail("direct frontier mismatch")
    if sorted(aux_ids) != sorted(["NG_OBJECT_CONTRACTIVE"]):
        fail("auxiliary frontier mismatch")
    if missing_ids != []:
        fail("missing frontier must be empty after T41")

    lake_status = "skipped_tool_unavailable"
    if shutil.which("lake") is not None:
        proc = subprocess.run(["lake", "build"], cwd="lean", capture_output=True, text=True, check=False)
        lake_status = "passed" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""
    if repro_p.exists() and "run_t41_lean_closure_variational_core.py" not in repro_text:
        fail("repro.py must include run_t41_lean_closure_variational_core.py")

    summary = {
        "generated_at_utc": now_iso(),
        "theorem_count": 1,
        "direct_front_count": len(direct_ids),
        "auxiliary_front_count": len(aux_ids),
        "missing_front_count": len(missing_ids),
        "closure_auxiliary": readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] == "auxiliary_only",
        "packaged_future_laws_formalized": "packagedFutureLaw" in lean_text and "packagedFutureLawFamily" in lean_text,
        "macro_kernel_objects_formalized": all(name in lean_text for name in ["MacroKernel", "conditionalMacroFutureRow", "bestMacroKernel"]),
        "variational_objective_formalized": all(name in lean_text for name in ["rowwiseObjective", "variationalObjective"]),
        "rowwise_minimizer_present": "bestMacroKernel_minimizesObjective" in lean_text and "ClosureVariationalLayer" in lean_text,
        "best_macro_kernel_formula_present": "bestMacroKernel_row_formula" in lean_text,
        "best_macro_gap_present": "bestMacroGap" in lean_text,
        "t40_decision_preserved": feas["decision"]["decision_mode"] == "proceed_to_variational_core",
        "full_closure_theorem_pending": obligation_map["CL_CLOSURE_VARIATIONAL_IDENTITY_AND_COROLLARY"]["status"] != "already_formalized",
        "attribution_out_of_scope": obligation_map["CL_ATTRIBUTION_RESOLUTION_OUT_OF_SCOPE"]["status"] == "out_of_scope",
        "next_ticket_id": feas["decision"]["next_ticket_id"],
        "lake_build_status": lake_status,
        **repro_flags(repro_text),
        "vision_present": Path("vision.md").exists(),
        "status": "success",
    }

    expected = {
        "theorem_count": 1,
        "direct_front_count": 7,
        "auxiliary_front_count": 1,
        "missing_front_count": 0,
        "closure_auxiliary": False,
        "packaged_future_laws_formalized": True,
        "macro_kernel_objects_formalized": True,
        "variational_objective_formalized": True,
        "rowwise_minimizer_present": True,
        "best_macro_kernel_formula_present": True,
        "best_macro_gap_present": True,
        "t40_decision_preserved": True,
        "full_closure_theorem_pending": False,
        "attribution_out_of_scope": True,
        "next_ticket_id": None,
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f"summary anchor mismatch: {key}")
    if lake_status not in {"passed", "skipped_tool_unavailable"}:
        fail("lake_build_status must be passed or skipped_tool_unavailable")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lean_closure_variational_core_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
