#!/usr/bin/env python3
"""Run T42 Lean closure direct-pack validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess


REQUIRED_T41 = [
    "lean/SixBirdsNoGo/ClosureVariationalCore.lean",
    "lean/SixBirdsNoGo/ClosureVariationalCoreExample.lean",
    "docs/project/lean_closure_variational_core.yaml",
    "scripts/run_t41_lean_closure_variational_core.py",
    "tests/test_lean_closure_variational_core.py",
    "docs/research-log/T41.md",
    "results/T41/lean_closure_variational_core_summary.json",
]

REQUIRED_NAMES = [
    "closureDeficitValue",
    "ExactClosedMacroLaw",
    "closureDeficit_attainedBy_bestMacroKernel",
    "closureDeficit_le_allKernels",
    "closureDeficit_is_variationalMinimum",
    "positiveClosureDeficit_forbidsExactClosure",
    "closureTheorem_directPack",
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
    parser = argparse.ArgumentParser(description="Run T42 Lean closure direct-pack validation")
    parser.add_argument("--output-dir", default="results/T42")
    args = parser.parse_args()

    direct_yaml_p = Path("docs/project/lean_closure_direct.yaml")
    feas_p = Path("docs/project/lean_closure_feasibility.yaml")
    boundary_p = Path("docs/project/lean_closure_formal_boundary.md")
    core_yaml_p = Path("docs/project/lean_closure_variational_core.yaml")
    readiness_p = Path("docs/project/readiness_checklist.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    pack_p = Path("docs/project/theorem_pack_closure.yaml")
    claims_p = Path("docs/project/claim_audit_freeze.yaml")
    direct_lean_p = Path("lean/SixBirdsNoGo/ClosureDirectPack.lean")
    direct_example_p = Path("lean/SixBirdsNoGo/ClosureDirectPackExample.lean")
    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    repro_p = Path("src/sixbirds_nogo/repro.py")

    for path in [direct_yaml_p, feas_p, boundary_p, core_yaml_p, readiness_p, atlas_p, pack_p, claims_p]:
        if not path.exists():
            fail(f"missing required input: {path}")

    missing_t41 = [rel for rel in REQUIRED_T41 if not Path(rel).exists()]
    if missing_t41:
        fail(f"T41 fold-forward missing artifacts: {missing_t41}")

    direct_yaml = load_json(direct_yaml_p)
    feas = load_json(feas_p)
    core_yaml = load_json(core_yaml_p)
    readiness = theorem_map(load_json(readiness_p)["theorems"])
    atlas = theorem_map(load_json(atlas_p)["theorems"])
    pack = theorem_map(load_json(pack_p)["theorem_fronts"])
    claims = claim_map(load_json(claims_p)["claims"])
    boundary_text = boundary_p.read_text(encoding="utf-8")
    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""

    if len(direct_yaml["theorem_fronts"]) != 1 or direct_yaml["theorem_fronts"][0]["theorem_id"] != "NG_MACRO_CLOSURE_DEFICIT":
        fail("lean_closure_direct must contain exactly NG_MACRO_CLOSURE_DEFICIT")
    row = direct_yaml["theorem_fronts"][0]

    if not direct_lean_p.exists():
        fail("ClosureDirectPack.lean is required for the direct theorem-pack branch")
    if not direct_example_p.exists():
        fail("ClosureDirectPackExample.lean is required for the direct theorem-pack branch")

    if row["outcome_mode"] != "direct_theorem_pack" or row["bridge_status"] != "direct_ready":
        fail("T42 artifact must record the direct theorem-pack outcome")
    for key in ["bridge_statement", "prerequisites", "direct_corollaries", "scope_limits", "lean_artifacts"]:
        if not row.get(key):
            fail(f"missing nonempty field: {key}")

    lean_text = direct_lean_p.read_text(encoding="utf-8")
    for name in REQUIRED_NAMES:
        if name not in lean_text:
            fail(f"missing required Lean name: {name}")

    root_text = lean_root_p.read_text(encoding="utf-8")
    for imp in [
        "import SixBirdsNoGo.ClosureDirectPack",
        "import SixBirdsNoGo.ClosureDirectPackExample",
    ]:
        if imp not in root_text:
            fail(f"missing root import: {imp}")

    if readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] != "direct":
        fail("readiness must mark closure as direct")
    if atlas["NG_MACRO_CLOSURE_DEFICIT"]["support_snapshot"]["lean_support"]["status"] != "direct":
        fail("atlas must mark closure as direct")

    pack_row = pack["NG_MACRO_CLOSURE_DEFICIT"]
    for ref in [
        "lean/SixBirdsNoGo/ClosureVariationalCore.lean",
        "lean/SixBirdsNoGo/ClosureVariationalCoreExample.lean",
        "lean/SixBirdsNoGo/ClosureDirectPack.lean",
        "lean/SixBirdsNoGo/ClosureDirectPackExample.lean",
        "docs/project/lean_closure_feasibility.yaml",
        "docs/project/lean_closure_variational_core.yaml",
        "docs/project/lean_closure_direct.yaml",
        "results/T40/lean_closure_feasibility_summary.json",
        "results/T41/lean_closure_variational_core_summary.json",
        "results/T42/lean_closure_direct_pack_summary.json",
    ]:
        if ref not in pack_row["evidence_refs"]["lean"]:
            fail(f"missing theorem_pack_closure Lean evidence ref: {ref}")
    if any("pending" in blocker.lower() for blocker in pack_row["remaining_blockers"]):
        fail("theorem_pack_closure blockers must no longer say theorem wrapper pending")
    if pack_row["next_ticket"]["id"] != "PLAN_NEXT_18_closure_scope_guardrail_hold":
        fail("theorem_pack_closure next_ticket mismatch")

    claim = claims["NG_MACRO_CLOSURE_DEFICIT.core"]
    if any("pending" in blocker.lower() for blocker in claim["blockers"]):
        fail("claim blockers must no longer say theorem wrapper pending")
    if claim["next_ticket"]["id"] != "PLAN_NEXT_18_closure_scope_guardrail_hold":
        fail("claim next_ticket mismatch")

    obligation_map = {entry["obligation_id"]: entry for entry in feas["obligation_matrix"]}
    if obligation_map["CL_CLOSURE_VARIATIONAL_IDENTITY_AND_COROLLARY"]["status"] != "already_formalized":
        fail("obligation 8 must now be already_formalized")
    if feas["decision"]["decision_mode"] != "proceed_to_variational_core":
        fail("T40 decision mode must remain proceed_to_variational_core")
    if feas["theorem_target"]["current_lean_status"] != "direct":
        fail("T40 artifact must now record closure as direct")

    core_row = core_yaml["theorem_fronts"][0]
    if core_row["readiness_delta"]["full_theorem_wrapper_pending"] is not False:
        fail("T41 provenance artifact must mark the full wrapper as no longer pending")

    lake_status = "skipped_tool_unavailable"
    if shutil.which("lake") is not None:
        proc = subprocess.run(["lake", "build"], cwd="lean", capture_output=True, text=True, check=False)
        lake_status = "passed" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    if repro_p.exists() and "run_t42_lean_closure_direct_pack.py" not in repro_text:
        fail("repro.py must include run_t42_lean_closure_direct_pack.py")

    direct_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "direct"]
    aux_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "auxiliary_only"]
    missing_ids = [tid for tid, t in readiness.items() if t["lean_support"]["status"] == "missing"]

    summary = {
        "generated_at_utc": now_iso(),
        "theorem_count": 1,
        "outcome_mode": "direct_theorem_pack",
        "direct_front_count": len(direct_ids),
        "auxiliary_front_count": len(aux_ids),
        "missing_front_count": len(missing_ids),
        "closure_direct": readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] == "direct",
        "direct_pack_present": direct_lean_p.exists() and direct_example_p.exists(),
        "formal_boundary_note_present": bool(boundary_text.strip()),
        "t41_foldforward_present": all(Path(rel).exists() for rel in REQUIRED_T41),
        "t41_core_retained": Path("lean/SixBirdsNoGo/ClosureVariationalCore.lean").exists(),
        "variational_identity_present": "closureDeficit_is_variationalMinimum" in lean_text,
        "positive_deficit_corollary_present": "positiveClosureDeficit_forbidsExactClosure" in lean_text,
        "exact_closed_macro_law_predicate_present": "ExactClosedMacroLaw" in lean_text,
        "attribution_out_of_scope": "primitive attribution out of scope" in json.dumps(row["scope_limits"]).lower(),
        "next_ticket_id": pack_row["next_ticket"]["id"],
        "lake_build_status": lake_status,
        **repro_flags(repro_text),
        "vision_present": Path("vision.md").exists(),
        "status": "success",
    }

    expected = {
        "theorem_count": 1,
        "outcome_mode": "direct_theorem_pack",
        "direct_front_count": 7,
        "auxiliary_front_count": 1,
        "missing_front_count": 0,
        "closure_direct": True,
        "direct_pack_present": True,
        "formal_boundary_note_present": True,
        "t41_foldforward_present": True,
        "t41_core_retained": True,
        "variational_identity_present": True,
        "positive_deficit_corollary_present": True,
        "exact_closed_macro_law_predicate_present": True,
        "attribution_out_of_scope": True,
        "next_ticket_id": "PLAN_NEXT_18_closure_scope_guardrail_hold",
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f"summary anchor mismatch: {key}")
    if lake_status not in {"passed", "skipped_tool_unavailable"}:
        fail("lake_build_status must be passed or skipped_tool_unavailable")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lean_closure_direct_pack_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
