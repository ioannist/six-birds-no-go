"""Regression cases for theorem domains and support-sensitive identities."""

from fractions import Fraction as F

import pytest

from sixbirds_nogo.affinity import is_exact_oneform
from sixbirds_nogo.arrow import path_kl_divergence
from sixbirds_nogo.closure_deficit import best_macro_gap, closure_deficit, variational_objective
from sixbirds_nogo.coarse import make_lens, pushforward_distribution_through_lens
from sixbirds_nogo.markov import FiniteMarkovChain, is_stationary_reversible
from sixbirds_nogo.objecthood import (
    ergodic_class_count, fixed_distribution_count, fixed_point_count,
    solve_unique_fixed_distribution,
)
from sixbirds_nogo.packaging import make_state_map_package, make_stochastic_operator_package


def test_zero_mass_rows_do_not_contribute_infinite_kl():
    chain = FiniteMarkovChain(("a", "b"), ((F(1), F(0)), (F(0), F(1))))
    lens = make_lens(chain.states, {"a": "A", "b": "B"})
    candidate = FiniteMarkovChain(("A", "B"), ((F(1), F(0)), (F(1), F(0))))
    initial = (F(1), F(0))
    # The unused b row has infinite KL, but the expectation omits zero weights.
    for value in (closure_deficit(chain, lens, 1, initial),
                  best_macro_gap(chain, lens, 1, initial),
                  variational_objective(chain, lens, candidate, 1, initial)):
        assert value.kind == "zero"
        assert value.support_mismatch_count == 0


def test_zero_mass_state_in_a_positive_fiber_is_ignored():
    chain = FiniteMarkovChain(("a", "b", "c"),
                             ((F(1), F(0), F(0)),
                              (F(0), F(0), F(1)),
                              (F(0), F(0), F(1))))
    lens = make_lens(chain.states, {"a": "A", "b": "A", "c": "B"})
    assert closure_deficit(chain, lens, 1, (F(1), F(0), F(0))).kind == "zero"
    assert closure_deficit(chain, lens, 1, (F(1, 2), F(1, 2), F(0))).kind == "finite_positive"


def test_stationary_label_requires_stationarity():
    with pytest.raises(ValueError, match="pi P = pi"):
        FiniteMarkovChain(("a", "b"), ((F(0), F(1)), (F(1), F(0))), (F(1), F(0)))


def test_one_way_edges_are_not_a_reversibility_certificate():
    chain = FiniteMarkovChain(("a", "b", "c"),
                             ((F(0), F(1), F(0)),
                              (F(0), F(0), F(1)),
                              (F(1), F(0), F(0))), (F(1, 3),) * 3)
    assert is_exact_oneform(chain)  # Its bidirected support is empty.
    assert not is_stationary_reversible(chain)


def test_fixed_state_plus_disjoint_cycle_is_not_unique_invariant_law():
    pkg = make_state_map_package(("a", "b", "c"), {"a": "a", "b": "c", "c": "b"})
    assert fixed_point_count(pkg) == 1  # The audit is on states.
    assert ergodic_class_count(pkg) == 2
    assert fixed_distribution_count(pkg) == "infinite"
    with pytest.raises(ValueError, match="non-unique"):
        solve_unique_fixed_distribution(pkg)


def test_noncontractive_cycle_has_one_invariant_law():
    pkg = make_state_map_package(("a", "b"), {"a": "b", "b": "a"})
    assert fixed_point_count(pkg) == 0
    assert fixed_distribution_count(pkg) == 1
    assert solve_unique_fixed_distribution(pkg) == (F(1, 2), F(1, 2))
    stochastic = make_stochastic_operator_package(pkg.states, ((F(0), F(1)), (F(1), F(0))))
    assert fixed_point_count(stochastic) == 1


def test_identity_operator_has_infinitely_many_invariant_laws():
    pkg = make_stochastic_operator_package(("a", "b"), ((F(1), F(0)), (F(0), F(1))))
    assert ergodic_class_count(pkg) == 2
    assert fixed_point_count(pkg) == "infinite"


@pytest.mark.parametrize("invalid", [(F(-1), F(2)), (F(1), F(1))])
def test_probability_entry_points_reject_invalid_laws(invalid):
    lens = make_lens(("a", "b"), {"a": "A", "b": "B"})
    with pytest.raises(ValueError):
        pushforward_distribution_through_lens(invalid, lens)
    with pytest.raises(ValueError):
        path_kl_divergence({("a",): invalid[0], ("b",): invalid[1]}, {("a",): F(1)})
