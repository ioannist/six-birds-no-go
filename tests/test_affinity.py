from fractions import Fraction

from sixbirds_nogo.affinity import (
    bidirected_support_digraph,
    cycle_affinities,
    cycle_affinity_surrogate,
    cycle_ratio,
    is_exact_oneform,
    log_ratio_ratio_form,
    max_cycle_affinity,
    reconstruct_exact_potential,
)
from sixbirds_nogo.graph_cycle import fundamental_cycle_basis
from sixbirds_nogo.markov import load_chain_from_witness


def test_bidirected_support_and_ratio_form() -> None:
    rev = load_chain_from_witness("rev_cycle_3")
    ratios_rev = log_ratio_ratio_form(rev)
    assert ratios_rev
    assert all(isinstance(v, Fraction) for v in ratios_rev.values())
    assert all(v == Fraction(1, 1) for v in ratios_rev.values())

    biased = load_chain_from_witness("biased_cycle_3")
    ratios_b = log_ratio_ratio_form(biased)
    assert ratios_b[("0", "1")] == Fraction(2, 1)
    assert ratios_b[("1", "0")] == Fraction(1, 2)

    pos = load_chain_from_witness("positive_closure_deficit")
    bi_dg = bidirected_support_digraph(pos)
    assert "B1" not in bi_dg["A1"]


def test_exactness_and_null_affinity_fixtures() -> None:
    tree = load_chain_from_witness("rev_tree_4")
    assert max_cycle_affinity(tree) == Fraction(0, 1)
    assert is_exact_oneform(tree) is True
    assert reconstruct_exact_potential(tree) is not None

    rev = load_chain_from_witness("rev_cycle_3")
    cycle = ("0", "1", "2", "0")
    assert cycle_ratio(cycle, log_ratio_ratio_form(rev)) == Fraction(1, 1)
    assert max_cycle_affinity(rev) == Fraction(0, 1)
    assert is_exact_oneform(rev) is True

    biased = load_chain_from_witness("biased_cycle_3")
    c = ("0", "1", "2", "0")
    r = cycle_ratio(c, log_ratio_ratio_form(biased))
    assert r == Fraction(8, 1)
    assert cycle_affinity_surrogate(Fraction(8, 1)) == Fraction(7, 1)
    assert max_cycle_affinity(biased) > Fraction(0, 1)
    assert is_exact_oneform(biased) is False
    assert reconstruct_exact_potential(biased) is None


def test_exact_type_checks_and_basis_integration() -> None:
    chain = load_chain_from_witness("biased_cycle_3")
    basis = fundamental_cycle_basis(chain)
    affinities = cycle_affinities(chain, cycle_basis=basis)
    assert affinities
    assert all(isinstance(v, Fraction) for v in affinities.values())
    assert isinstance(max_cycle_affinity(chain, cycle_basis=basis), Fraction)
