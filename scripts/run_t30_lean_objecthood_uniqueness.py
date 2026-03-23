#!/usr/bin/env python3
"""Validate T30 objecthood Lean uniqueness spike and emit summary."""

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


def _require(path: Path) -> None:
    if not path.exists():
        fail(f"missing required input: {path}")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T30 objecthood Lean uniqueness validation")
    parser.add_argument("--output-dir", default="results/T30")
    args = parser.parse_args()

    uniq_p = Path("docs/project/lean_objecthood_uniqueness.yaml")
    boundary_p = Path("docs/project/lean_objecthood_formal_boundary.md")
    ready_p = Path("docs/project/readiness_checklist.yaml")
    atlas_p = Path("docs/project/theorem_atlas.yaml")
    pack_p = Path("docs/project/theorem_pack_objecthood.yaml")
    claims_p = Path("docs/project/claim_audit_freeze.yaml")
    tv_feas_p = Path("docs/project/lean_objecthood_tv_feasibility.yaml")
    tv_summary_p = Path("results/T43/lean_objecthood_tv_feasibility_summary.json")
    t44_summary_p = Path("results/T44/lean_objecthood_direct_pack_summary.json")
    t29_log_p = Path("docs/research-log/T29.md")
    lean_root_p = Path("lean/SixBirdsNoGo.lean")
    uniq_lean_p = Path("lean/SixBirdsNoGo/ContractionUniqueness.lean")
    uniq_ex_p = Path("lean/SixBirdsNoGo/ContractionUniquenessExample.lean")

    for p in [uniq_p, boundary_p, ready_p, atlas_p, pack_p, claims_p, t29_log_p, lean_root_p]:
        _require(p)

    uniq = load_json(uniq_p)
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    pack = load_json(pack_p)
    claims = load_json(claims_p)
    tv_feas = load_json(tv_feas_p) if tv_feas_p.exists() else None
    tv_summary = load_json(tv_summary_p) if tv_summary_p.exists() else None
    t44_summary = load_json(t44_summary_p) if t44_summary_p.exists() else None
    t44_direct_p = Path("docs/project/lean_objecthood_direct.yaml")
    t44_direct = load_json(t44_direct_p) if t44_direct_p.exists() else None

    if not t29_log_p.read_text(encoding="utf-8").strip():
        fail("docs/research-log/T29.md must be nonempty")
    if not boundary_p.read_text(encoding="utf-8").strip():
        fail("docs/project/lean_objecthood_formal_boundary.md must be nonempty")

    for k in ["version", "generated_at_utc", "source_context", "status_enums", "theorem_fronts"]:
        if k not in uniq:
            fail(f"lean objecthood file missing key: {k}")
    fronts = uniq["theorem_fronts"]
    if not isinstance(fronts, list) or len(fronts) != 1:
        fail("lean objecthood file must contain exactly one theorem front")
    row = fronts[0]
    if row.get("theorem_id") != "NG_OBJECT_CONTRACTIVE":
        fail("theorem-front ID must be NG_OBJECT_CONTRACTIVE")
    if row.get("outcome_mode") not in {"direct_uniqueness_theorem", "formal_boundary_note"}:
        fail("invalid outcome_mode in lean objecthood file")
    if row.get("bridge_status") not in {"uniqueness_core_ready", "boundary_frozen"}:
        fail("invalid bridge_status in lean objecthood file")

    ready_map = {t["theorem_id"]: t for t in readiness["theorems"]}
    atlas_map = {t["theorem_id"]: t for t in atlas["theorems"]}
    claim_map = {c["claim_id"]: c for c in claims["claims"]}

    boundary_text = _text(boundary_p)

    branch_a = uniq_lean_p.exists()
    lean_root_text = _text(lean_root_p)
    uniq_text = _text(uniq_lean_p) if branch_a else ""
    uniq_ex_text = _text(uniq_ex_p) if branch_a and uniq_ex_p.exists() else ""
    if branch_a and row.get("outcome_mode") != "direct_uniqueness_theorem":
        fail("lean objecthood file must use direct_uniqueness_theorem when Lean theorem exists")
    if (not branch_a) and row.get("outcome_mode") != "formal_boundary_note":
        fail("lean objecthood file must use formal_boundary_note when Lean theorem is absent")

    if branch_a:
        _require(uniq_lean_p)
        _require(uniq_ex_p)
        for token in [
            "FixedPoint",
            "StrictlyContractiveOnNe",
            "fixed_eq_of_strictContraction",
            "atMostOneFixedPoint_of_strictContraction",
        ]:
            if token not in uniq_text:
                fail(f"ContractionUniqueness.lean missing token: {token}")
        for imp in [
            "import SixBirdsNoGo.ContractionUniqueness",
            "import SixBirdsNoGo.ContractionUniquenessExample",
        ]:
            if imp not in lean_root_text:
                fail(f"lean/SixBirdsNoGo.lean missing import: {imp}")
        if "ContractionUniqueness" not in uniq_ex_text:
            fail("ContractionUniquenessExample.lean must import the uniqueness module")
        if ready_map["NG_OBJECT_CONTRACTIVE"]["lean_support"]["status"] != "auxiliary_only":
            fail("readiness objecthood lean_support must be auxiliary_only")
        if atlas_map["NG_OBJECT_CONTRACTIVE"]["support_snapshot"]["lean_support"]["status"] != "auxiliary_only":
            fail("atlas objecthood lean_support must be auxiliary_only")
        if "lean/SixBirdsNoGo/ContractionUniqueness.lean" not in row.get("lean_artifacts", []):
            fail("lean objecthood file missing uniqueness Lean artifact")

    else:
        if ready_map["NG_OBJECT_CONTRACTIVE"]["lean_support"]["status"] != "missing":
            fail("readiness objecthood lean_support must be missing")
        if atlas_map["NG_OBJECT_CONTRACTIVE"]["support_snapshot"]["lean_support"]["status"] != "missing":
            fail("atlas objecthood lean_support must be missing")

    if claim_map["NG_OBJECT_CONTRACTIVE.core"].get("support_grade") != "direct":
        fail("objecthood core claim must remain direct")
    if claim_map["NG_OBJECT_CONTRACTIVE.guardrail"].get("support_grade") != "direct":
        fail("objecthood guardrail claim must remain direct")
    if claim_map["NG_OBJECT_CONTRACTIVE.metric_regime_gap"].get("freeze_status") == "blocked":
        fail("objecthood metric regime gap must not be blocked")

    lean_direct_total = sum(1 for t in readiness["theorems"] if t["lean_support"]["status"] == "direct")
    lean_aux_total = sum(1 for t in readiness["theorems"] if t["lean_support"]["status"] == "auxiliary_only")
    lean_missing_total = sum(1 for t in readiness["theorems"] if t["lean_support"]["status"] == "missing")
    expected_counts = (7, 1, 0)
    expected_status = "auxiliary_only"
    if t44_summary is not None and t44_summary.get("outcome_mode") == "direct_theorem_pack":
        expected_counts = (8, 0, 0)
        expected_status = "direct"
    if (lean_direct_total, lean_aux_total, lean_missing_total) != expected_counts:
        fail("global Lean frontier counts mismatch after T44")
    if ready_map["NG_OBJECT_CONTRACTIVE"]["lean_support"]["status"] != expected_status:
        fail("current objecthood Lean status mismatch after T44")

    t43_branch = None
    if tv_feas is not None:
        t43_decision = tv_feas["decision"]
        t43_branch = t43_decision["decision_mode"]
        if t43_branch not in {"proceed_to_tv_bridge", "freeze_boundary_now"}:
            fail("invalid T43 decision mode")
        t44_finalized = t44_summary is not None or (
            t44_direct is not None and t44_direct.get("theorem_fronts")
        )
        if not t44_finalized:
            next_ticket = row.get("next_ticket")
            if not isinstance(next_ticket, dict) or next_ticket.get("id") != "T44":
                fail("lean objecthood uniqueness next_ticket must be T44 after T43")
            if next_ticket.get("id") == "PLAN_NEXT_12_objecthood_tv_bound_lean_bridge":
                fail("stale PLAN_NEXT_12 next_ticket id remains in lean objecthood uniqueness artifact")
            pending = row["readiness_delta"]["full_tv_bound_bridge_pending"]
            if t43_branch == "proceed_to_tv_bridge":
                if pending is not True:
                    fail("Branch A requires full_tv_bound_bridge_pending == true")
            else:
                if pending is not False:
                    fail("Branch B requires full_tv_bound_bridge_pending == false")
        if tv_summary is not None:
            if tv_summary.get("theorem_count") != 1:
                fail("T43 summary theorem_count mismatch")
    if t44_summary is not None:
        if row["readiness_delta"]["full_tv_bound_bridge_pending"] is not False:
            fail("post-T44 uniqueness provenance must mark full_tv_bound_bridge_pending false")
        if row["next_ticket"] is not None:
            fail("post-T44 uniqueness provenance next_ticket must be null")

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
    includes_t30 = "run_t30_lean_objecthood_uniqueness.py" in repro_text
    if not includes_t30:
        fail("repro pipeline missing run_t30_lean_objecthood_uniqueness.py step")

    outcome_mode = row.get("outcome_mode")
    summary = {
        "generated_at_utc": now_iso(),
        "theorem_count": 1,
        "updated_theorem_ids": ["NG_OBJECT_CONTRACTIVE"],
        "outcome_mode": outcome_mode,
        "lean_direct_total": lean_direct_total,
        "lean_auxiliary_total": lean_aux_total,
        "lean_missing_total": lean_missing_total,
        "direct_uniqueness_theorem_present": branch_a and "FixedPoint" in uniq_text and "atMostOneFixedPoint_of_strictContraction" in uniq_text,
        "formal_boundary_note_present": bool(boundary_text.strip()),
        "objecthood_lean_status_after": ready_map["NG_OBJECT_CONTRACTIVE"]["lean_support"]["status"],
        "strict_contraction_on_ne_explicit": branch_a and "StrictlyContractiveOnNe" in uniq_text,
        "at_most_one_fixed_point_formalized": branch_a and "atMostOneFixedPoint_of_strictContraction" in uniq_text,
        "discrete_model_example_present": branch_a and uniq_ex_p.exists(),
        "formal_boundary_frozen": True,
        "full_tv_bound_bridge_pending": row["readiness_delta"]["full_tv_bound_bridge_pending"],
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
        "reproduce_includes_t30": includes_t30,
        "vision_present": bool(uniq.get("source_context", {}).get("vision_present")),
        "status": "success",
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lean_objecthood_uniqueness_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("PASS: T30 objecthood uniqueness validation")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path("results/T30")
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "generated_at_utc": now_iso(),
            "theorem_count": 0,
            "updated_theorem_ids": [],
            "outcome_mode": "formal_boundary_note",
            "lean_direct_total": 0,
            "lean_auxiliary_total": 0,
            "lean_missing_total": 0,
            "direct_uniqueness_theorem_present": False,
            "formal_boundary_note_present": True,
            "objecthood_lean_status_after": "missing",
            "strict_contraction_on_ne_explicit": False,
            "at_most_one_fixed_point_formalized": False,
            "discrete_model_example_present": False,
            "formal_boundary_frozen": True,
            "full_tv_bound_bridge_pending": False,
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
            "reproduce_includes_t30": False,
            "vision_present": Path("vision.md").exists(),
            "status": "failed",
            "error": str(exc),
        }
        (out_dir / "lean_objecthood_uniqueness_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        print(f"FAIL: {exc}")
        raise SystemExit(1)
