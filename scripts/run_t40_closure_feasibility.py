#!/usr/bin/env python3
"""Run T40 closure-feasibility validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

REQUIRED_OBLIGATION_IDS = [
    "CL_BASE_FINITE_LAWS",
    "CL_BASE_FINITE_KL",
    "CL_PACKAGED_FUTURE_LAW_FAMILY",
    "CL_FINITE_MACRO_KERNEL",
    "CL_VARIATIONAL_OBJECTIVE",
    "CL_ROWWISE_MINIMIZER_LEMMA",
    "CL_CLOSED_FORM_BEST_KERNEL",
    "CL_CLOSURE_VARIATIONAL_IDENTITY_AND_COROLLARY",
    "CL_ATTRIBUTION_RESOLUTION_OUT_OF_SCOPE",
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


def repro_flags(text: str) -> dict[str, bool]:
    return {f"reproduce_includes_t{i}": f"run_t{i}" in text for i in range(20, 43)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T40 closure-feasibility validation")
    parser.add_argument("--output-dir", default="results/T40")
    args = parser.parse_args()

    yaml_p = Path("docs/project/lean_closure_feasibility.yaml")
    boundary_p = Path("docs/project/lean_closure_formal_boundary.md")
    pack_p = Path("docs/project/theorem_pack_closure.yaml")
    readiness_p = Path("docs/project/readiness_checklist.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    charter_p = Path("docs/project/lean_probability_scope_charter.yaml")
    core_p = Path("docs/project/lean_probability_core.yaml")
    kl_p = Path("docs/project/lean_kl_dpi_core.yaml")
    t09_metrics_p = Path("results/T09/closure_metrics.json")
    t09_grid_p = Path("results/T09/grid_check.json")
    t24_p = Path("results/T24/closure_attribution_resolution.json")
    repro_p = Path("src/sixbirds_nogo/repro.py")

    for path in [yaml_p, boundary_p, pack_p, readiness_p, atlas_p, charter_p, core_p, kl_p, t09_metrics_p, t09_grid_p, t24_p]:
        if not path.exists():
            fail(f"missing required input: {path}")

    data = load_json(yaml_p)
    pack = theorem_map(load_json(pack_p)["theorem_fronts"])
    readiness = theorem_map(load_json(readiness_p)["theorems"])
    atlas = theorem_map(load_json(atlas_p)["theorems"])
    boundary_text = boundary_p.read_text(encoding="utf-8")
    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""

    target = data["theorem_target"]
    if target["theorem_id"] != "NG_MACRO_CLOSURE_DEFICIT":
        fail("theorem target must be NG_MACRO_CLOSURE_DEFICIT")

    snapshot = data["current_frontier_snapshot"]
    if len(snapshot["direct_ids"]) != 7 or len(snapshot["auxiliary_ids"]) != 1 or len(snapshot["missing_ids"]) != 0:
        fail("frontier snapshot counts must now be 7/1/0")
    if snapshot["auxiliary_ids"] != ["NG_OBJECT_CONTRACTIVE"]:
        fail("objecthood must now be the only auxiliary frontier")

    if readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] != "direct":
        fail("closure readiness Lean status must now be direct")
    if atlas["NG_MACRO_CLOSURE_DEFICIT"]["support_snapshot"]["lean_support"]["status"] != "direct":
        fail("closure atlas Lean status must now be direct")

    obligations = data["obligation_matrix"]
    ids = [row["obligation_id"] for row in obligations]
    if ids != REQUIRED_OBLIGATION_IDS:
        fail("obligation matrix IDs/order mismatch")
    obligation_map = {row["obligation_id"]: row for row in obligations}
    if obligation_map["CL_BASE_FINITE_LAWS"]["status"] != "already_formalized":
        fail("CL_BASE_FINITE_LAWS status mismatch")
    if obligation_map["CL_BASE_FINITE_KL"]["status"] != "already_formalized":
        fail("CL_BASE_FINITE_KL status mismatch")
    if obligation_map["CL_ATTRIBUTION_RESOLUTION_OUT_OF_SCOPE"]["status"] != "out_of_scope":
        fail("CL_ATTRIBUTION_RESOLUTION_OUT_OF_SCOPE status mismatch")

    decision = data["decision"]
    decision_mode = decision["decision_mode"]
    if decision_mode not in {"proceed_to_variational_core", "freeze_boundary_now"}:
        fail("invalid decision mode")

    middle_ids = REQUIRED_OBLIGATION_IDS[2:8]
    middle_statuses = [obligation_map[k]["status"] for k in middle_ids]
    if decision_mode == "proceed_to_variational_core":
        if middle_statuses != [
            "already_formalized",
            "already_formalized",
            "already_formalized",
            "already_formalized",
            "already_formalized",
            "already_formalized",
        ]:
            fail("post-T42 proceed branch requires obligations 3-8 to be already_formalized")
        if any(row["status"] == "requires_forbidden_expansion" for row in obligations):
            fail("proceed branch must not require forbidden expansion")
        if decision["next_ticket_id"] is not None:
            fail("post-T42 proceed branch next ticket must be null")
    else:
        if not any(status == "requires_forbidden_expansion" for status in middle_statuses):
            fail("boundary branch requires at least one forbidden expansion obligation")
        if decision["next_ticket_id"] is not None:
            fail("post-T42 boundary branch next ticket must be null")

    if decision_mode not in boundary_text:
        fail("formal boundary markdown must mention the decision mode")
    if decision_mode == "proceed_to_variational_core":
        for needle in [
            "the finite closure variational core and the direct closure theorem wrapper are both now landed",
            "primitive attribution remains analytically resolved and out of scope for lean",
        ]:
            if needle.lower() not in boundary_text.lower():
                fail("formal boundary markdown inconsistent with proceed decision")
    else:
        for needle in [
            "current formal boundary stops before the closure variational theorem",
            "stopping point is due to forbidden broad expansion, not theorem falsity",
            "primitive attribution is already resolved analytically and is not part of the Lean target",
        ]:
            if needle.lower() not in boundary_text.lower():
                fail("formal boundary markdown inconsistent with boundary decision")

    if "out of scope for this lean feasibility spike" not in target["attribution_status"].lower():
        fail("primitive attribution must be explicitly out of scope")
    policy = data["decision_policy"]
    if policy["objecthood_revisit_deferred_until_after_decision"] is not True:
        fail("objecthood must remain deferred")
    if repro_p.exists() and "run_t40_closure_feasibility.py" not in repro_text:
        fail("repro.py must include run_t40_closure_feasibility.py")

    pack_row = pack["NG_MACRO_CLOSURE_DEFICIT"]
    if pack_row["theorem_statement"] != target["theorem_statement"]:
        fail("closure theorem statement must match frozen theorem pack statement")

    counts = {key: 0 for key in ["already_formalized", "needed_narrow", "requires_forbidden_expansion", "out_of_scope"]}
    for row in obligations:
        counts[row["status"]] += 1

    lake_status = "skipped_tool_unavailable"
    if shutil.which("lake") is not None:
        proc = subprocess.run(["lake", "build"], cwd="lean", capture_output=True, text=True, check=False)
        lake_status = "passed" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    summary = {
        "generated_at_utc": now_iso(),
        "theorem_count": 1,
        "direct_front_count": len(snapshot["direct_ids"]),
        "auxiliary_front_count": len(snapshot["auxiliary_ids"]),
        "missing_front_count": len(snapshot["missing_ids"]),
        "current_closure_lean_status": readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"],
        "obligation_count": len(obligations),
        "already_formalized_count": counts["already_formalized"],
        "needed_narrow_count": counts["needed_narrow"],
        "requires_forbidden_expansion_count": counts["requires_forbidden_expansion"],
        "out_of_scope_count": counts["out_of_scope"],
        "decision_mode": decision_mode,
        "narrow_bridge_possible": decision_mode == "proceed_to_variational_core",
        "generic_optimization_required": decision_mode == "freeze_boundary_now",
        "attribution_out_of_scope": obligation_map["CL_ATTRIBUTION_RESOLUTION_OUT_OF_SCOPE"]["status"] == "out_of_scope",
        "objecthood_still_deferred": policy["objecthood_revisit_deferred_until_after_decision"] is True,
        "theorem_status_unchanged": policy["no_status_changes_in_t40"] is True,
        "next_ticket_id": decision["next_ticket_id"],
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
        "current_closure_lean_status": "direct",
        "obligation_count": 9,
        "already_formalized_count": 8,
        "out_of_scope_count": 1,
        "attribution_out_of_scope": True,
        "objecthood_still_deferred": True,
        "theorem_status_unchanged": True,
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f"summary anchor mismatch: {key}")

    if decision_mode == "proceed_to_variational_core":
        branch_expected = {
            "needed_narrow_count": 0,
            "requires_forbidden_expansion_count": 0,
            "narrow_bridge_possible": True,
            "generic_optimization_required": False,
            "next_ticket_id": None,
        }
    else:
        if summary["needed_narrow_count"] > 5:
            fail("boundary branch needed_narrow_count must be <= 5")
        if summary["requires_forbidden_expansion_count"] < 1:
            fail("boundary branch requires_forbidden_expansion_count must be >= 1")
        branch_expected = {
            "narrow_bridge_possible": False,
            "generic_optimization_required": True,
            "next_ticket_id": None,
        }
    for key, value in branch_expected.items():
        if summary[key] != value:
            fail(f"branch summary anchor mismatch: {key}")

    if lake_status not in {"passed", "skipped_tool_unavailable"}:
        fail("lake_build_status must be passed or skipped_tool_unavailable")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lean_closure_feasibility_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
