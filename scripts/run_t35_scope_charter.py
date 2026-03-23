#!/usr/bin/env python3
"""Run T35 scope-charter validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


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
EXPECTED_TARGETS: list[str] = []
EXPECTED_ALLOWED_DEFERRED = [
    "FP_MINIMAL_SCALAR_LOG_LAYER",
    "FP_FINITE_DISTRIBUTIONS",
    "FP_DETERMINISTIC_PUSHFORWARD",
    "FP_FIXED_HORIZON_PATH_LAWS",
    "FP_PATH_REVERSAL",
    "FP_FINITE_KL",
    "FP_DETERMINISTIC_DPI",
    "FP_FINITE_MACRO_KERNEL_OBJECTS",
    "FP_FINITE_VARIATIONAL_OBJECTIVES",
    "FP_OBJECTHOOD_METRIC_REVISIT",
]
EXPECTED_FORBIDDEN = [
    "FG_MEASURE_THEORY",
    "FG_PROBABILITY_MONAD",
    "FG_GENERIC_CHANNEL_DPI",
    "FG_GENERIC_INFORMATION_LIBRARY",
    "FG_GENERIC_OPTIMIZATION_LIBRARY",
    "FG_BROAD_METRIC_LIBRARY",
    "FG_UNRELATED_GRAPH_LIBRARY",
    "FG_UNUSED_FOUNDATIONS",
]
EXPECTED_MILESTONES = [f"T{i}" for i in range(36, 45)]
EXPECTED_DEPENDS = {
    "T36": [],
    "T37": ["T36"],
    "T38": ["T37"],
    "T39": ["T38"],
    "T40": ["T39"],
    "T41": ["T40"],
    "T42": ["T41"],
    "T43": ["T42"],
    "T44": ["T43"],
}


def load_optional_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return load_json(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fail(msg: str) -> None:
    raise ValueError(msg)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"{path} must parse to object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T35 scope-charter validation")
    parser.add_argument("--output-dir", default="results/T35")
    args = parser.parse_args()

    charter_p = Path("docs/project/lean_probability_scope_charter.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    claims_p = Path("docs/project/claim_audit_freeze.yaml")
    readiness_p = Path("docs/project/readiness_checklist.yaml")
    repro_p = Path("src/sixbirds_nogo/repro.py")
    t43_p = Path("docs/project/lean_objecthood_tv_feasibility.yaml")

    for path in [charter_p, atlas_p, claims_p, readiness_p]:
        if not path.exists():
            fail(f"missing required input: {path}")

    charter = load_json(charter_p)
    atlas = load_json(atlas_p)
    claims = load_json(claims_p)
    readiness = load_json(readiness_p)
    t43 = load_optional_json(t43_p)

    required_keys = {
        "version",
        "generated_at_utc",
        "source_context",
        "status_enums",
        "current_frontier",
        "allowed_foundations",
        "forbidden_foundations",
        "frontier_targets",
        "milestone_sequence",
        "charter_rules",
    }
    if set(charter) != required_keys:
        fail("charter top-level keys must match required set exactly")

    vision_present = Path("vision.md").exists()
    source_context = charter["source_context"]
    if source_context.get("vision_present") != vision_present:
        fail("vision_present flag mismatch")
    if vision_present and source_context.get("vision_path") != "vision.md":
        fail("vision_path must be vision.md when vision is present")

    status_enums = charter["status_enums"]
    if status_enums["scope_status"] != ["fixed"]:
        fail("scope_status enum mismatch")

    current = charter["current_frontier"]
    if current["lean_direct_ids"] != EXPECTED_DIRECT:
        fail("lean_direct_ids mismatch")
    if current["lean_auxiliary_ids"] != EXPECTED_AUX:
        fail("lean_auxiliary_ids mismatch")
    if current["lean_missing_ids"] != EXPECTED_MISSING:
        fail("lean_missing_ids mismatch")
    note = current["note"].lower()
    if "bounded" not in note or "objecthood" not in note:
        fail("current_frontier note must mention the explicit objecthood boundary")

    readiness_map = {row["theorem_id"]: row["lean_support"]["status"] for row in readiness["theorems"]}
    direct_ids = [tid for tid, status in readiness_map.items() if status == "direct"]
    aux_ids = [tid for tid, status in readiness_map.items() if status == "auxiliary_only"]
    missing_ids = [tid for tid, status in readiness_map.items() if status == "missing"]
    if sorted(direct_ids) != sorted(EXPECTED_DIRECT):
        fail("readiness direct frontier no longer matches charter")
    if aux_ids != EXPECTED_AUX:
        fail("readiness auxiliary frontier no longer matches charter")
    if sorted(missing_ids) != sorted(EXPECTED_MISSING):
        fail("readiness missing frontier no longer matches charter")

    theorem_ids = set(atlas["paper_order"])
    claim_theorem_ids = {row["theorem_id"] for row in claims["claims"]}

    allowed_rows = charter["allowed_foundations"]
    if [row["foundation_id"] for row in allowed_rows] != EXPECTED_ALLOWED_DEFERRED:
        fail("allowed/deferred foundations must appear in required order")
    allowed_map = {row["foundation_id"]: row for row in allowed_rows}
    allowed_count = sum(1 for row in allowed_rows if row["decision"] == "allowed")
    deferred_count = sum(1 for row in allowed_rows if row["decision"] == "deferred")
    if allowed_count != 9 or deferred_count != 1:
        fail("allowed/deferred foundation counts mismatch")
    for fid, row in allowed_map.items():
        if row["decision"] not in {"allowed", "deferred"}:
            fail(f"invalid foundation decision for {fid}")
        if not row["theorem_consumers"]:
            fail(f"every allowed/deferred foundation must have theorem consumer: {fid}")
        for tid in row["theorem_consumers"]:
            if tid not in theorem_ids:
                fail(f"unknown theorem consumer on foundation {fid}: {tid}")

    forbidden_rows = charter["forbidden_foundations"]
    forbidden_map = {row["foundation_id"]: row for row in forbidden_rows}
    for fid in EXPECTED_FORBIDDEN:
        if fid not in forbidden_map:
            fail(f"missing forbidden foundation: {fid}")
        if forbidden_map[fid]["decision"] != "forbidden":
            fail(f"forbidden foundation mis-marked: {fid}")
    if len(forbidden_rows) < 8:
        fail("must include at least 8 forbidden foundations")
    forbidden_text = json.dumps(forbidden_rows).lower()
    for phrase in [
        "sigma-algebra",
        "probability monad",
        "generic stochastic-channel dpi",
        "entropy/information library",
        "convex/variational optimization",
        "metric-space buildout",
        "graph-library expansion",
        "near-term theorem consumer",
    ]:
        if phrase not in forbidden_text:
            fail(f"required non-goal missing from forbidden foundations: {phrase}")

    frontier_rows = charter["frontier_targets"]
    if [row["theorem_id"] for row in frontier_rows] != EXPECTED_TARGETS:
        fail("frontier target theorem ids must match required order exactly")
    frontier_map = {row["theorem_id"]: row for row in frontier_rows}
    for tid, row in frontier_map.items():
        if tid not in theorem_ids or tid not in claim_theorem_ids:
            fail(f"frontier target theorem id not found in frozen theorem sources: {tid}")
        for fid in row["required_foundation_ids"]:
            if fid not in allowed_map:
                fail(f"frontier target references non allowed/deferred foundation: {tid} -> {fid}")
    if frontier_rows:
        fail("post-T44 frontier_targets must be empty")

    milestones = charter["milestone_sequence"]
    if [row["ticket_id"] for row in milestones] != EXPECTED_MILESTONES:
        fail("milestone sequence must be T36..T44 in exact order")
    milestone_map = {row["ticket_id"]: row for row in milestones}
    for tid, deps in EXPECTED_DEPENDS.items():
        if milestone_map[tid]["depends_on"] != deps:
            fail(f"milestone dependency mismatch for {tid}")
        if milestone_map[tid]["status"] != "planned":
            fail(f"milestone status mismatch for {tid}")
        for fid in milestone_map[tid]["allowed_foundation_ids"]:
            if fid not in allowed_map:
                fail(f"milestone {tid} references unknown foundation id {fid}")
    title_checks = {
        "T36": "Lean finite distribution / pushforward core",
        "T37": "Lean finite KL + deterministic DPI core",
        "T38": "Lean NG_ARROW_DPI direct pack",
        "T39": "Lean NG_PROTOCOL_TRAP direct bridge",
        "T40": "Closure variational feasibility spike",
        "T41": "Lean finite macro-kernel variational core",
        "T42": "Lean NG_MACRO_CLOSURE_DEFICIT direct pack or formal-boundary freeze",
        "T43": "Objecthood TV/Dobrushin bridge spike",
        "T44": "Lean NG_OBJECT_CONTRACTIVE direct pack or permanent auxiliary boundary",
    }
    for tid, title in title_checks.items():
        if milestone_map[tid]["title"] != title:
            fail(f"milestone title mismatch for {tid}")

    rules_text = json.dumps(charter["charter_rules"]).lower()
    for phrase in [
        "near-term theorem consumer",
        "deterministic",
        "fixed-horizon",
        "finite-support",
        "no broad abstraction project",
        "closure decision gates the fuller objecthood bridge",
        "theorem statuses must not change in t35",
        "charter is fixed unless later explicitly revised",
    ]:
        if phrase not in rules_text:
            fail(f"missing charter rule phrase: {phrase}")

    repro_text = repro_p.read_text(encoding="utf-8") if repro_p.exists() else ""
    includes = {
        "reproduce_includes_t20": "run_t20_readiness_checkpoint.py" in repro_text,
        "reproduce_includes_t21": "run_t21_theorem_atlas.py" in repro_text,
        "reproduce_includes_t22": "run_t22_dpi_protocol_pack.py" in repro_text,
        "reproduce_includes_t23": "run_t23_graph_affinity_pack.py" in repro_text,
        "reproduce_includes_t24": "run_t24_closure_pack.py" in repro_text,
        "reproduce_includes_t25": "run_t25_objecthood_pack.py" in repro_text,
        "reproduce_includes_t26": "run_t26_bounded_interface_pack.py" in repro_text,
        "reproduce_includes_t27": "run_t27_lean_graph_bridge.py" in repro_text,
        "reproduce_includes_t28": "run_t28_lean_finite_lens_count.py" in repro_text,
        "reproduce_includes_t29": "run_t29_lean_bounded_interface_corollary.py" in repro_text,
        "reproduce_includes_t30": "run_t30_lean_objecthood_uniqueness.py" in repro_text,
        "reproduce_includes_t31": "run_t31_paper_skeleton.py" in repro_text,
        "reproduce_includes_t32": "run_t32_asset_freeze.py" in repro_text,
        "reproduce_includes_t33": "run_t33_draft_v1.py" in repro_text,
        "reproduce_includes_t34": "run_t34_red_team_review.py" in repro_text,
        "reproduce_includes_t35": "run_t35_scope_charter.py" in repro_text,
    }
    if not includes["reproduce_includes_t35"]:
        fail("repro pipeline missing run_t35_scope_charter.py step")

    summary = {
        "generated_at_utc": now_iso(),
        "direct_front_count": len(current["lean_direct_ids"]),
        "auxiliary_front_count": len(current["lean_auxiliary_ids"]),
        "missing_front_count": len(current["lean_missing_ids"]),
        "frontier_target_count": len(frontier_rows),
        "allowed_foundation_count": allowed_count,
        "deferred_foundation_count": deferred_count,
        "forbidden_foundation_count": len(forbidden_rows),
        "milestone_count": len(milestones),
        "dpi_before_protocol": EXPECTED_MILESTONES.index("T38") < EXPECTED_MILESTONES.index("T39") and milestone_map["T39"]["depends_on"] == ["T38"],
        "closure_before_objecthood": EXPECTED_MILESTONES.index("T42") < EXPECTED_MILESTONES.index("T43") and milestone_map["T43"]["depends_on"] == ["T42"],
        "charter_fixed": True,
        **includes,
        "vision_present": vision_present,
        "status": "success",
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lean_probability_scope_charter_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("PASS: T35 scope charter validation")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path("results/T35")
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "generated_at_utc": now_iso(),
            "direct_front_count": 0,
            "auxiliary_front_count": 0,
            "missing_front_count": 0,
            "frontier_target_count": 0,
            "allowed_foundation_count": 0,
            "deferred_foundation_count": 0,
            "forbidden_foundation_count": 0,
            "milestone_count": 0,
            "dpi_before_protocol": False,
            "closure_before_objecthood": False,
            "charter_fixed": False,
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
            "reproduce_includes_t30": False,
            "reproduce_includes_t31": False,
            "reproduce_includes_t32": False,
            "reproduce_includes_t33": False,
            "reproduce_includes_t34": False,
            "reproduce_includes_t35": False,
            "vision_present": Path("vision.md").exists(),
            "status": "failed",
            "error": str(exc),
        }
        (out_dir / "lean_probability_scope_charter_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"FAIL: {exc}")
        raise
