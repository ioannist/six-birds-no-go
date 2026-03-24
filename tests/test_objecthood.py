import csv
import json
import subprocess
import sys
from fractions import Fraction

from sixbirds_nogo.objecthood import (
    check_approximate_object_separation,
    distribution_residual,
    dobrushin_contraction_lambda,
    enumerate_simplex_grid,
    epsilon_stable_distributions,
    fixed_point_count,
    solve_unique_fixed_distribution,
    total_variation_distance,
)
from sixbirds_nogo.packaging import load_packaging_from_witness


def test_tv_and_contraction_anchors() -> None:
    assert total_variation_distance((Fraction(1, 1), Fraction(0, 1)), (Fraction(1, 2), Fraction(1, 2))) == Fraction(1, 2)
    c = load_packaging_from_witness("contractive_unique_object")
    assert dobrushin_contraction_lambda(c) == Fraction(0, 1)


def test_fixed_point_anchors() -> None:
    c = load_packaging_from_witness("contractive_unique_object")
    assert solve_unique_fixed_distribution(c) == (Fraction(3, 4), Fraction(1, 4))
    assert fixed_point_count(c) == 1

    n = load_packaging_from_witness("noncontractive_multiobject")
    f = load_packaging_from_witness("fixed_idempotent_no_ladder")
    assert fixed_point_count(n) == 2
    assert fixed_point_count(f) == 2


def test_residual_and_epsilon_stability_anchors() -> None:
    c = load_packaging_from_witness("contractive_unique_object")
    assert distribution_residual(c, (Fraction(3, 4), Fraction(1, 4))) == Fraction(0, 1)
    assert distribution_residual(c, (Fraction(1, 2), Fraction(1, 2))) == Fraction(1, 4)
    assert distribution_residual(c, (Fraction(1, 1), Fraction(0, 1))) == Fraction(1, 4)

    stable0 = epsilon_stable_distributions(c, denominator=4, epsilon=Fraction(0, 1))
    assert stable0 == ((Fraction(3, 4), Fraction(1, 4)),)

    stableq = epsilon_stable_distributions(c, denominator=4, epsilon=Fraction(1, 4))
    assert stableq == (
        (Fraction(1, 2), Fraction(1, 2)),
        (Fraction(3, 4), Fraction(1, 4)),
        (Fraction(1, 1), Fraction(0, 1)),
    )


def test_approximate_object_separation_bound_anchor() -> None:
    c = load_packaging_from_witness("contractive_unique_object")
    out = check_approximate_object_separation(
        c,
        (Fraction(1, 2), Fraction(1, 2)),
        (Fraction(1, 1), Fraction(0, 1)),
        Fraction(1, 4),
    )
    assert out["lambda_coeff"] == Fraction(0, 1)
    assert out["residual_a"] == Fraction(1, 4)
    assert out["residual_b"] == Fraction(1, 4)
    assert out["premises_hold"] is True
    assert out["lhs_tv"] == Fraction(1, 2)
    assert out["rhs_bound"] == Fraction(1, 2)
    assert out["holds"] is True


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t10"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_t10_objecthood_suite.py",
            "--output-dir",
            str(out),
            "--grid-denominator",
            "4",
            "--epsilon",
            "1/4",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    for name in ("objecthood_metrics.csv", "objecthood_metrics.json", "stability_grid.json", "case_manifest.json"):
        assert (out / name).exists()

    manifest = json.loads((out / "case_manifest.json").read_text(encoding="utf-8"))
    assert manifest["row_count"] == 4

    rows = list(csv.DictReader((out / "objecthood_metrics.csv").open()))
    c = next(r for r in rows if r["witness_id"] == "contractive_unique_object")
    assert c["contraction_lambda"] == "0/1"
    assert c["fixed_point_count"] == "1"
    assert c["eps_stable_count"] == "3"
    assert c["bound_holds"] == "true"

    for wid in ("noncontractive_multiobject", "fixed_idempotent_no_ladder", "lens_extension_escape"):
        r = next(x for x in rows if x["witness_id"] == wid)
        assert r["idempotence_defect"] == "0/1"
        assert r["saturation_max_step"] == "1"


def test_exact_type_checks() -> None:
    c = load_packaging_from_witness("contractive_unique_object")
    pts = enumerate_simplex_grid(c.states, 4)
    assert all(all(isinstance(x, Fraction) for x in p) for p in pts)

    out = check_approximate_object_separation(
        c,
        (Fraction(1, 2), Fraction(1, 2)),
        (Fraction(1, 1), Fraction(0, 1)),
        Fraction(1, 4),
    )
    assert isinstance(out["lambda_coeff"], Fraction)
    assert isinstance(out["residual_a"], Fraction)
    assert isinstance(out["residual_b"], Fraction)
    assert isinstance(out["lhs_tv"], Fraction)
    assert isinstance(out["rhs_bound"], Fraction)
