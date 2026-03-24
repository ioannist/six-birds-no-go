import csv
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from sixbirds_nogo.closure_deficit import (
    best_macro_gap,
    best_macro_kernel,
    closure_deficit,
    current_macro_distribution,
    grid_search_two_state_macro_kernels,
    packaged_future_laws,
    variational_objective,
)
from sixbirds_nogo.coarse import load_lens_from_witness, strong_lumpable_macro_chain
from sixbirds_nogo.markov import FiniteMarkovChain, load_chain_from_witness


def test_packaged_future_law_anchors() -> None:
    z = load_chain_from_witness("zero_closure_deficit_lumpable")
    z_lens = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    z_laws = packaged_future_laws(z, z_lens, 1)
    assert z_laws == {
        "A0": (Fraction(1, 2), Fraction(1, 2)),
        "A1": (Fraction(1, 2), Fraction(1, 2)),
        "B0": (Fraction(1, 2), Fraction(1, 2)),
        "B1": (Fraction(1, 2), Fraction(1, 2)),
    }

    p = load_chain_from_witness("positive_closure_deficit")
    p_lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    p_laws = packaged_future_laws(p, p_lens, 1)
    assert p_laws["A0"] == (Fraction(1, 2), Fraction(1, 2))
    assert p_laws["A1"] == (Fraction(0, 1), Fraction(1, 1))
    assert p_laws["B0"] == (Fraction(1, 1), Fraction(0, 1))
    assert p_laws["B1"] == (Fraction(1, 1), Fraction(0, 1))

    assert current_macro_distribution(p, p_lens) == (Fraction(3, 5), Fraction(2, 5))


def test_best_macro_kernel_anchors() -> None:
    z = load_chain_from_witness("zero_closure_deficit_lumpable")
    z_lens = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    kz = best_macro_kernel(z, z_lens, 1)
    assert kz.states == ("A", "B")
    assert kz.matrix == (
        (Fraction(1, 2), Fraction(1, 2)),
        (Fraction(1, 2), Fraction(1, 2)),
    )
    assert kz.stationary_distribution == (Fraction(1, 2), Fraction(1, 2))
    assert kz.matrix == strong_lumpable_macro_chain(z, z_lens).matrix

    p = load_chain_from_witness("positive_closure_deficit")
    p_lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    kp = best_macro_kernel(p, p_lens, 1)
    assert kp.states == ("A", "B")
    assert kp.matrix == (
        (Fraction(1, 3), Fraction(2, 3)),
        (Fraction(1, 1), Fraction(0, 1)),
    )
    assert kp.stationary_distribution == (Fraction(3, 5), Fraction(2, 5))


def test_closure_deficit_and_best_gap_anchors() -> None:
    for wid in ("zero_closure_deficit_lumpable", "positive_closure_deficit"):
        c = load_chain_from_witness(wid)
        lens = load_lens_from_witness(wid, "macro_AB")
        cd0 = closure_deficit(c, lens, 0)
        bg0 = best_macro_gap(c, lens, 0)
        assert cd0.kind == "zero"
        assert bg0.kind == "zero"

    z = load_chain_from_witness("zero_closure_deficit_lumpable")
    z_lens = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    cdz = closure_deficit(z, z_lens, 1)
    bgz = best_macro_gap(z, z_lens, 1)
    assert cdz.kind == "zero"
    assert bgz.kind == "zero"
    assert cdz.log_terms == ()
    assert bgz.log_terms == ()

    p = load_chain_from_witness("positive_closure_deficit")
    p_lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    cdp = closure_deficit(p, p_lens, 1)
    bgp = best_macro_gap(p, p_lens, 1)
    assert cdp.kind == "finite_positive"
    assert cdp.log_terms == (
        (Fraction(3, 4), Fraction(1, 5)),
        (Fraction(3, 2), Fraction(2, 5)),
    )
    assert cdp.decimal_value is not None and cdp.decimal_value > 0
    assert cdp.kind == bgp.kind
    assert cdp.support_mismatch_count == bgp.support_mismatch_count
    assert cdp.log_terms == bgp.log_terms


def test_candidate_variational_objective_examples() -> None:
    p = load_chain_from_witness("positive_closure_deficit")
    lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")

    cand1 = FiniteMarkovChain(
        states=("A", "B"),
        matrix=((Fraction(1, 2), Fraction(1, 2)), (Fraction(1, 1), Fraction(0, 1))),
        stationary_distribution=None,
    )
    v1 = variational_objective(p, lens, cand1, 1)
    assert v1.kind == "finite_positive"
    assert v1.log_terms == ((Fraction(2, 1), Fraction(1, 5)),)

    best = best_macro_gap(p, lens, 1)
    assert v1.decimal_value is not None and best.decimal_value is not None
    assert v1.decimal_value > best.decimal_value

    cand2 = FiniteMarkovChain(
        states=("A", "B"),
        matrix=((Fraction(0, 1), Fraction(1, 1)), (Fraction(1, 1), Fraction(0, 1))),
        stationary_distribution=None,
    )
    v2 = variational_objective(p, lens, cand2, 1)
    assert v2.kind == "infinite"
    assert v2.support_mismatch_count == 1


def test_grid_check_validation() -> None:
    z = load_chain_from_witness("zero_closure_deficit_lumpable")
    z_lens = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    gz = grid_search_two_state_macro_kernels(z, z_lens, 1, denominator=12)
    assert gz["analytic_best_in_grid_minima"] is True
    assert gz["grid_best_gap"]["kind"] == "zero"

    p = load_chain_from_witness("positive_closure_deficit")
    p_lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    gp = grid_search_two_state_macro_kernels(p, p_lens, 1, denominator=12)
    assert gp["analytic_best_in_grid_minima"] is True
    assert gp["grid_best_kernels"] == [gp["analytic_best_kernel"]]


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t09"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_t09_closure_suite.py",
            "--output-dir",
            str(out),
            "--precision",
            "80",
            "--grid-denominator",
            "12",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    for name in ("closure_metrics.csv", "closure_metrics.json", "grid_check.json", "case_manifest.json"):
        assert (out / name).exists()

    manifest = json.loads((out / "case_manifest.json").read_text(encoding="utf-8"))
    assert manifest["row_count"] == 4
    assert manifest["grid_check_count"] == 2

    rows = list(csv.DictReader((out / "closure_metrics.csv").open()))
    positive = [r for r in rows if r["witness_id"] == "positive_closure_deficit" and r["tau"] == "1"][0]
    assert positive["closure_kind"] == "finite_positive"

    zero_rows = [r for r in rows if r["witness_id"] == "zero_closure_deficit_lumpable"]
    assert all(r["closure_kind"] == "zero" for r in zero_rows)


def test_exact_type_checks() -> None:
    p = load_chain_from_witness("positive_closure_deficit")
    lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")

    laws = packaged_future_laws(p, lens, 1)
    assert all(isinstance(v, Fraction) for row in laws.values() for v in row)

    k = best_macro_kernel(p, lens, 1)
    assert all(isinstance(v, Fraction) for row in k.matrix for v in row)

    cd = closure_deficit(p, lens, 1)
    assert all(isinstance(r, Fraction) and isinstance(c, Fraction) for r, c in cd.log_terms)
