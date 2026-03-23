import csv
import json
import subprocess
import sys
from fractions import Fraction

from sixbirds_nogo.coarse import load_lens_from_witness
from sixbirds_nogo.definability import (
    definable_predicate_count,
    empirical_definability_rate,
    fixed_interface_no_ladder_report,
    formula_definability_probability,
    formula_definable_predicate_count,
    is_predicate_definable_from_lens,
    lens_extension_escape_report,
    predicate_from_true_states,
    predicate_to_true_states,
)
from sixbirds_nogo.packaging import load_packaging_from_witness


def test_exact_count_formula_anchors() -> None:
    f = load_lens_from_witness("fixed_idempotent_no_ladder", "base_binary")
    assert definable_predicate_count(f) == 4
    assert formula_definable_predicate_count(f) == 4
    assert formula_definability_probability(f) == Fraction(1, 2)

    e = load_lens_from_witness("lens_extension_escape", "extended_ternary")
    assert definable_predicate_count(e) == 8
    assert formula_definable_predicate_count(e) == 8
    assert formula_definability_probability(e) == Fraction(1, 1)

    x = load_lens_from_witness("hidden_clock_reversible", "observe_x_binary")
    assert definable_predicate_count(x) == 4
    assert formula_definability_probability(x) == Fraction(1, 4)

    c3 = load_lens_from_witness("hidden_clock_reversible", "observe_clock_3")
    assert definable_predicate_count(c3) == 8
    assert formula_definability_probability(c3) == Fraction(1, 2)

    m = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    assert definable_predicate_count(m) == 4
    assert formula_definability_probability(m) == Fraction(1, 4)


def test_specific_definability_decisions() -> None:
    lens = load_lens_from_witness("fixed_idempotent_no_ladder", "base_binary")
    states = lens.domain_states

    p_x = predicate_from_true_states(states, {"x"})
    p_y = predicate_from_true_states(states, {"y"})
    p_z = predicate_from_true_states(states, {"z"})
    p_yz = predicate_from_true_states(states, {"y", "z"})

    assert is_predicate_definable_from_lens(p_x, lens) is True
    assert is_predicate_definable_from_lens(p_y, lens) is False
    assert is_predicate_definable_from_lens(p_z, lens) is False
    assert is_predicate_definable_from_lens(p_yz, lens) is True

    ext = load_lens_from_witness("lens_extension_escape", "extended_ternary")
    for st in ext.domain_states:
        p = predicate_from_true_states(ext.domain_states, {st})
        assert is_predicate_definable_from_lens(p, ext) is True


def test_deterministic_empirical_checks_fullspace() -> None:
    a = load_lens_from_witness("fixed_idempotent_no_ladder", "base_binary")
    assert empirical_definability_rate(a, 8, seed=7, replace=False) == Fraction(1, 2)

    b = load_lens_from_witness("lens_extension_escape", "extended_ternary")
    assert empirical_definability_rate(b, 8, seed=7, replace=False) == Fraction(1, 1)

    c = load_lens_from_witness("hidden_clock_reversible", "observe_x_binary")
    assert empirical_definability_rate(c, 16, seed=7, replace=False) == Fraction(1, 4)


def test_no_ladder_anchors() -> None:
    lens = load_lens_from_witness("fixed_idempotent_no_ladder", "base_binary")
    pkg = load_packaging_from_witness("fixed_idempotent_no_ladder")
    r = fixed_interface_no_ladder_report(pkg, lens, max_steps=3)

    assert r["idempotence_defect"] == Fraction(0, 1)
    assert r["interface_size"] == 2
    assert r["definable_predicate_count"] == 4
    assert r["signature_sequence"] == (
        ("0", "1", "1"),
        ("0", "1", "1"),
        ("0", "1", "1"),
        ("0", "1", "1"),
    )
    assert r["stabilization_step"] == 0
    assert r["no_new_signatures_after_step1"] is True
    assert r["no_ladder_holds"] is True

    lens2 = load_lens_from_witness("lens_extension_escape", "extended_ternary")
    pkg2 = load_packaging_from_witness("lens_extension_escape")
    r2 = fixed_interface_no_ladder_report(pkg2, lens2, max_steps=3)
    assert r2["signature_sequence"] == (
        ("0", "1", "2"),
        ("0", "1", "1"),
        ("0", "1", "1"),
        ("0", "1", "1"),
    )
    assert r2["stabilization_step"] == 1
    assert r2["no_ladder_holds"] is True


def test_extension_escape_anchors() -> None:
    base = load_lens_from_witness("lens_extension_escape", "base_binary")
    ext = load_lens_from_witness("lens_extension_escape", "extended_ternary")
    rep = lens_extension_escape_report(base, ext)

    assert rep["strict_refinement"] is True
    assert rep["escape_present"] is True
    assert rep["base_interface_size"] == 2
    assert rep["extended_interface_size"] == 3
    assert rep["base_definable_count"] == 4
    assert rep["extended_definable_count"] == 8
    assert rep["gained_predicate_count"] == 4
    gained = {
        predicate_to_true_states(p, base.domain_states)
        for p in rep["gained_predicates"]
    }
    assert gained == {("y",), ("z",), ("x", "y"), ("x", "z")}
    assert rep["factor_map"] == {"0": "0", "1": "1", "2": "1"}


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t11"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_t11_definability_suite.py",
            "--output-dir",
            str(out),
            "--seed",
            "7",
            "--max-steps",
            "3",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    for name in (
        "definability_metrics.csv",
        "definability_metrics.json",
        "random_checks.json",
        "no_ladder_demos.json",
        "case_manifest.json",
    ):
        assert (out / name).exists()

    manifest = json.loads((out / "case_manifest.json").read_text(encoding="utf-8"))
    assert manifest["row_count"] == 6
    assert manifest["random_check_count"] == 3
    assert manifest["no_ladder_demo_count"] == 3

    rows = list(csv.DictReader((out / "definability_metrics.csv").open()))
    base_rows = [r for r in rows if r["lens_id"] == "base_binary"]
    assert all(r["exact_definable_count"] == "4" for r in base_rows)
    ext_row = next(r for r in rows if r["lens_id"] == "extended_ternary")
    assert ext_row["exact_definable_count"] == "8"

    demos = json.loads((out / "no_ladder_demos.json").read_text(encoding="utf-8"))
    assert demos["extension_escape_report"]["extended_definable_count"] > demos["extension_escape_report"]["base_definable_count"]


def test_exact_type_checks() -> None:
    lens = load_lens_from_witness("fixed_idempotent_no_ladder", "base_binary")
    assert isinstance(formula_definability_probability(lens), Fraction)
    assert isinstance(empirical_definability_rate(lens, 8, seed=7, replace=False), Fraction)
