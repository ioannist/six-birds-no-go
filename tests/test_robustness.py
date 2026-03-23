import csv
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from sixbirds_nogo.robustness import (
    run_horizon_lens_sweep,
    run_initial_distribution_sweep,
    run_objecthood_metric_sweep,
    run_perturbation_sweep,
    run_t15_suite,
    run_threshold_sweep,
)


def _find(rows, **kwargs):
    for r in rows:
        ok = True
        for k, v in kwargs.items():
            if r.get(k) != v:
                ok = False
                break
        if ok:
            return r
    raise AssertionError(f"missing row: {kwargs}")


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t15"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_t15_robustness_suite.py",
            "--output-dir",
            str(out),
            "--precision",
            "80",
            "--max-horizon",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    required = [
        "horizon_lens_sweep.csv",
        "initial_distribution_sweep.csv",
        "perturbation_sweep.csv",
        "threshold_sweep.csv",
        "objecthood_metric_sweep.csv",
        "adversarial_cases.json",
        "fragility_summary.json",
        "fragility_notes.md",
        "case_manifest.json",
    ]
    for name in required:
        p = out / name
        assert p.exists()
        assert p.stat().st_size > 0

    manifest = json.loads((out / "case_manifest.json").read_text(encoding="utf-8"))
    assert manifest["horizon_row_count"] == 36
    assert manifest["initial_row_count"] == 11
    assert manifest["perturbation_row_count"] == 12
    assert manifest["threshold_row_count"] == 4
    assert manifest["objecthood_row_count"] == 2
    assert manifest["adversarial_case_count"] >= 4
    assert manifest["fragility_count"] >= 5


def test_horizon_lens_sweep_anchors() -> None:
    rows = run_horizon_lens_sweep(max_horizon=5)

    for r in rows:
        if r["witness_id"] == "hidden_clock_reversible":
            assert r["macro_arrow_kl_honest"] == "0"
            assert r["micro_arrow_kl"] == "0"

    h3_id = _find(rows, witness_id="hidden_clock_driven", lens_id="identity", horizon=3)
    h3_x = _find(rows, witness_id="hidden_clock_driven", lens_id="observe_x_binary", horizon=3)
    h3_c = _find(rows, witness_id="hidden_clock_driven", lens_id="observe_clock_3", horizon=3)

    assert h3_id["macro_arrow_kind_honest"] == "finite_positive"
    assert h3_x["macro_arrow_kl_honest"] == "0"
    assert h3_c["macro_arrow_kind_honest"] == "finite_positive"

    for h in (2, 3):
        row = _find(rows, witness_id="hidden_clock_driven", lens_id="observe_clock_3", horizon=h)
        assert row["proxy_diverges_materially"] is True


def test_initial_distribution_anchors() -> None:
    rows = run_initial_distribution_sweep()

    st = _find(rows, witness_id="hidden_clock_reversible", initial_id="stationary", horizon=3)
    assert st["micro_arrow_kl"] == "0"

    for init_id in ("delta_L0", "delta_R0", "delta_R1", "delta_L1"):
        r = _find(rows, witness_id="hidden_clock_reversible", initial_id=init_id, horizon=3)
        assert r["micro_arrow_kl"] == "Infinity"

    adv = _find(
        rows,
        witness_id="hidden_clock_driven",
        lens_id="observe_x_binary",
        initial_id="phase1_balanced",
        horizon=2,
    )
    assert adv["macro_arrow_kl_honest"] == "0"
    assert adv["macro_arrow_kind_proxy"] == "finite_positive"
    assert adv["proxy_diverges_materially"] is True


def test_threshold_sweep_anchors() -> None:
    rows = run_threshold_sweep()
    f0 = _find(rows, floor="0")
    f100 = _find(rows, floor="1/100")

    assert f0["one_way_directed_edge_count"] == 0
    assert f100["one_way_directed_edge_count"] == 2
    assert f100["original_exactness_flag"] is True
    assert f100["original_cycle_rank"] == 1


def test_perturbation_anchors() -> None:
    rows = run_perturbation_sweep()

    h0 = _find(rows, family_id="hidden_clock_mix", alpha=Fraction(0, 1))
    assert h0["micro_arrow_kl"] == "0"
    assert h0["macro_arrow_observe_x_binary"] == "0"
    assert h0["macro_arrow_observe_clock_3"] == "0"

    hs = _find(rows, family_id="hidden_clock_mix", alpha=Fraction(1, 20))
    assert hs["micro_arrow_kind"] == "finite_positive"
    assert hs["macro_arrow_observe_x_binary"] == "0"
    assert hs["macro_arrow_observe_clock_3_kind"] == "finite_positive"

    c0 = _find(rows, family_id="cycle_drive_mix", alpha=Fraction(0, 1))
    assert c0["max_cycle_affinity"] == Fraction(0, 1)
    assert c0["exactness_flag"] is True

    cs = _find(rows, family_id="cycle_drive_mix", alpha=Fraction(1, 20))
    assert cs["max_cycle_affinity"] > 0
    assert cs["exactness_flag"] is False


def test_objecthood_metric_anchors() -> None:
    rows = run_objecthood_metric_sweep()
    tv = _find(rows, metric_id="tv")
    ss = _find(rows, metric_id="support_signature")

    assert tv["stable_point_count"] == 3
    assert tv["cluster_count"] == 1
    assert ss["cluster_count"] == 2


def test_adversarial_case_coverage() -> None:
    manifest = run_t15_suite()
    cases = manifest["adversarial_cases"]["cases"]
    assert len(cases) >= 3

    ids = {c["case_id"] for c in cases}
    assert "proxy_spurious_macro_arrow_nonstationary" in ids
    assert "threshold_creates_spurious_one_way_support" in ids
    assert "poor_metric_splits_unique_object" in ids

    assert any(c["honest_reference"].get("macro_arrow_kl_honest") == "0" and c["proxy_reference"].get("macro_arrow_kind_proxy") == "finite_positive" for c in cases if c["case_id"] == "proxy_spurious_macro_arrow_nonstationary")
    assert any(bool(c.get("material_divergence")) for c in cases)


def test_fragility_summary_coverage() -> None:
    manifest = run_t15_suite()
    frag = manifest["fragility_summary"]
    ids = {e["fragility_id"] for e in frag["entries"]}

    required = {
        "stationary_zero_arrow_is_fragile_to_initial_distribution",
        "macro_arrow_depends_strongly_on_lens_choice",
        "fitted_markov_proxy_can_create_or_distort_macro_arrow",
        "threshold_floors_can_introduce_spurious_one_way_support",
        "object_multiplicity_can_be_metric_artifact",
    }
    assert required.issubset(ids)

    notes = manifest["fragility_notes"]
    assert notes.strip()


def test_exact_type_checks_before_serialization() -> None:
    perturb = run_perturbation_sweep()
    row = _find(perturb, family_id="cycle_drive_mix", alpha=Fraction(1, 20))
    assert isinstance(row["max_cycle_affinity"], Fraction)
