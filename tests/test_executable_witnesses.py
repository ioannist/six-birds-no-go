import csv
import json
import subprocess
import sys
from fractions import Fraction

from sixbirds_nogo.executable_witnesses import (
    build_all_executable_witnesses,
    build_executable_witness,
    run_all_witnesses,
    run_expected_audits,
)
from sixbirds_nogo.witnesses import list_witness_ids


def _find_audit(row: dict, audit_id: str, lens_id: str | None = None, horizon: int | None = None, tau: int | None = None):
    for a in row["audit_results"]:
        if a["audit_id"] != audit_id:
            continue
        ctx = a.get("context") or {}
        if lens_id is not None and ctx.get("lens_id") != lens_id:
            continue
        if horizon is not None and int(ctx.get("horizon")) != horizon:
            continue
        if tau is not None and int(ctx.get("tau")) != tau:
            continue
        return a
    raise AssertionError(f"audit not found: {audit_id} lens={lens_id} horizon={horizon} tau={tau}")


def test_construction_coverage() -> None:
    built = build_all_executable_witnesses()
    built_ids = [w.id for w in built]
    reg_ids = list_witness_ids()
    assert set(built_ids) == set(reg_ids)

    rev = build_executable_witness("rev_cycle_3")
    assert rev.chain is not None
    assert rev.lenses
    assert rev.packaging is None

    h = build_executable_witness("hidden_clock_driven")
    assert h.chain is not None
    assert len(h.lenses) >= 2
    assert h.packaging is None

    c = build_executable_witness("contractive_unique_object")
    assert c.chain is None
    assert "identity" in c.lenses
    assert c.packaging is not None

    e = build_executable_witness("lens_extension_escape")
    assert e.chain is None
    assert len(e.lenses) >= 2
    assert e.packaging is not None


def test_required_audit_execution_coverage() -> None:
    for w in build_all_executable_witnesses():
        r = run_expected_audits(w)
        assert r["executed_audit_count"] == r["required_audit_count"]
        assert r["error_count"] == 0
        assert r["execution_status"] == "success"


def test_expected_signature_anchor_checks() -> None:
    manifest = run_all_witnesses()
    rows = {r["witness_id"]: r for r in manifest["witnesses"]}

    # rev_tree_4
    rt = rows["rev_tree_4"]
    assert _find_audit(rt, "AUDIT_CYCLE_RANK")["comparable_value"] == 0
    assert _find_audit(rt, "AUDIT_MAX_CYCLE_AFFINITY")["comparable_value"] == "0/1"
    assert _find_audit(rt, "AUDIT_ONEFORM_EXACTNESS")["comparable_value"] is True

    # hidden_clock_reversible
    hr = rows["hidden_clock_reversible"]
    assert _find_audit(hr, "AUDIT_PATH_KL_MICRO", horizon=3)["actual"]["kind"] == "zero"
    assert _find_audit(hr, "AUDIT_PATH_KL_MACRO_HONEST", lens_id="observe_x_binary", horizon=3)["actual"]["kind"] == "zero"
    assert _find_audit(hr, "AUDIT_PATH_KL_MACRO_HONEST", lens_id="observe_clock_3", horizon=3)["actual"]["kind"] == "zero"
    assert _find_audit(hr, "AUDIT_PHASE_LIFT_REVERSIBILITY")["comparable_value"] is True

    # hidden_clock_driven
    hd = rows["hidden_clock_driven"]
    assert _find_audit(hd, "AUDIT_PATH_KL_MICRO", horizon=3)["actual"]["kind"] == "finite_positive"
    assert _find_audit(hd, "AUDIT_PATH_KL_MACRO_HONEST", lens_id="observe_x_binary", horizon=3)["actual"]["kind"] == "zero"
    assert _find_audit(hd, "AUDIT_PATH_KL_MACRO_HONEST", lens_id="observe_clock_3", horizon=3)["actual"]["kind"] == "finite_positive"
    assert _find_audit(hd, "AUDIT_PHASE_LIFT_REVERSIBILITY")["comparable_value"] is False

    # positive_closure_deficit
    pc = rows["positive_closure_deficit"]
    assert _find_audit(pc, "AUDIT_CLOSURE_DEFICIT", lens_id="macro_AB", tau=1)["actual"]["kind"] == "finite_positive"
    assert _find_audit(pc, "AUDIT_BEST_MACRO_GAP", lens_id="macro_AB", tau=1)["actual"]["kind"] == "finite_positive"

    # contractive_unique_object
    co = rows["contractive_unique_object"]
    assert _find_audit(co, "AUDIT_CONTRACTION_LAMBDA")["comparable_value"] == "0/1"
    assert _find_audit(co, "AUDIT_FIXED_POINT_COUNT")["comparable_value"] == 1

    # fixed_idempotent_no_ladder
    fn = rows["fixed_idempotent_no_ladder"]
    assert _find_audit(fn, "AUDIT_IDEMPOTENCE_DEFECT")["comparable_value"] == "0/1"
    assert _find_audit(fn, "AUDIT_INTERFACE_SIZE", lens_id="base_binary")["comparable_value"] == 2
    assert _find_audit(fn, "AUDIT_DEFINABLE_PREDICATE_COUNT", lens_id="base_binary")["comparable_value"] == 4

    # lens_extension_escape
    le = rows["lens_extension_escape"]
    assert _find_audit(le, "AUDIT_IDEMPOTENCE_DEFECT")["comparable_value"] == "0/1"
    assert _find_audit(le, "AUDIT_INTERFACE_SIZE", lens_id="extended_ternary")["comparable_value"] == 3
    assert _find_audit(le, "AUDIT_DEFINABLE_PREDICATE_COUNT", lens_id="extended_ternary")["comparable_value"] == 8


def test_expectation_satisfaction_coverage() -> None:
    manifest = run_all_witnesses()
    total_required = sum(r["required_audit_count"] for r in manifest["witnesses"])
    total_executed = sum(r["executed_audit_count"] for r in manifest["witnesses"])
    total_fail = sum(r["expectation_fail_count"] for r in manifest["witnesses"])

    assert total_required > 0
    assert total_executed == total_required
    assert total_fail == 0


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t12"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t12_witness_manifest.py", "--output-dir", str(out), "--precision", "80"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    assert (out / "witness_manifest.json").exists()
    assert (out / "witness_summary.csv").exists()

    manifest = json.loads((out / "witness_manifest.json").read_text(encoding="utf-8"))
    assert manifest["witness_count"] == 11
    assert manifest["success_count"] == 11
    assert manifest["partial_count"] == 0
    assert manifest["failed_count"] == 0
    assert manifest["expectation_fail_count"] == 0


def test_exact_type_checks() -> None:
    ew = build_executable_witness("contractive_unique_object")
    r = run_expected_audits(ew)
    a = _find_audit(r, "AUDIT_CONTRACTION_LAMBDA")
    assert a["actual"] == "0/1"
