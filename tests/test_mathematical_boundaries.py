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


@pytest.mark.parametrize("count", [0.5, F(1, 2), True, -1])
def test_iteration_counts_are_natural_numbers(count):
    from sixbirds_nogo.markov import matrix_power, pushforward_distribution
    from sixbirds_nogo.pathspace import enumerate_path_law
    from sixbirds_nogo.closure_deficit import packaged_future_distribution
    chain = FiniteMarkovChain(("a", "b"), ((F(0), F(1)), (F(1), F(0))))
    lens = make_lens(chain.states, {"a": "A", "b": "B"})
    for operation in (lambda: matrix_power(chain.matrix, count),
                      lambda: pushforward_distribution((F(1), F(0)), chain.matrix, count),
                      lambda: enumerate_path_law(chain, count, (F(1), F(0))),
                      lambda: packaged_future_distribution(chain, lens, "a", count)):
        with pytest.raises(ValueError, match="nonnegative integer"):
            operation()


def test_closure_uses_the_current_law_at_the_chosen_time():
    from sixbirds_nogo.markov import pushforward_distribution
    chain = FiniteMarkovChain(("a", "b", "c"),
        ((F(1), F(0), F(0)), (F(0), F(0), F(1)), (F(0), F(0), F(1))))
    lens = make_lens(chain.states, {"a": "A", "b": "A", "c": "B"})
    initial = (F(1, 2), F(1, 2), F(0))
    current = pushforward_distribution(initial, chain.matrix)
    assert closure_deficit(chain, lens, 1, initial).kind == "finite_positive"
    assert closure_deficit(chain, lens, 1, current).kind == "zero"


def test_dobrushin_estimate_on_all_small_stochastic_rows():
    from itertools import product
    from sixbirds_nogo.objecthood import dobrushin_contraction_lambda, total_variation_distance
    from sixbirds_nogo.packaging import apply_packaging_to_distribution
    laws = ((F(0), F(1)), (F(1, 2), F(1, 2)), (F(1), F(0)))
    for rows in product(laws, repeat=2):
        pkg = make_stochastic_operator_package(("a", "b"), rows)
        rho = dobrushin_contraction_lambda(pkg)
        for p, q in product(laws, repeat=2):
            assert total_variation_distance(apply_packaging_to_distribution(pkg, p),
                apply_packaging_to_distribution(pkg, q)) <= rho * total_variation_distance(p, q)


def test_unsupported_stochastic_action_is_rejected():
    with pytest.raises(ValueError, match="row_distribution_left_multiply"):
        make_stochastic_operator_package(("a", "b"), ((F(0), F(1)), (F(1), F(0))),
            action="column_distribution_right_multiply")


def test_undirected_edges_are_counted_once_for_cycle_rank():
    from sixbirds_nogo.graph_cycle import cycle_rank_from_edges, is_forest_from_edges
    edges = (("a", "b"), ("b", "a"), ("a", "b"))
    assert cycle_rank_from_edges(("a", "b"), edges) == 0
    assert is_forest_from_edges(("a", "b"), edges)
    with pytest.raises(ValueError, match="unique"):
        cycle_rank_from_edges(("a", "a"), ())


def test_bruteforce_observation_rejects_invalid_initial_law():
    from sixbirds_nogo.coarse import observed_path_probability_bruteforce
    chain = FiniteMarkovChain(("a", "b"), ((F(0), F(1)), (F(1), F(0))))
    lens = make_lens(chain.states, {"a": "A", "b": "B"})
    with pytest.raises(ValueError, match="nonnegative"):
        observed_path_probability_bruteforce(chain, lens, ("A",), (F(-1), F(2)))


def test_two_infinite_divergences_have_no_subtractive_dpi_gap():
    from sixbirds_nogo.executable_witnesses import ExecutableWitness, run_honest_audit
    chain = FiniteMarkovChain(("a", "b", "c"),
        ((F(0), F(1), F(0)), (F(0), F(0), F(1)), (F(1), F(0), F(0))), (F(1, 3),) * 3)
    lens = make_lens(chain.states, {s: s for s in chain.states})
    witness = ExecutableWitness("cycle", "markov_chain", chain.states, {}, chain,
        {"identity": lens}, None, (), (), ())
    result = run_honest_audit(witness, "AUDIT_DPI_GAP", {"horizon": 1, "lens_id": "identity"})
    assert result.status == "failed"
    assert "both divergences are infinite" in result.error


def test_direct_constructors_enforce_their_mathematical_domains():
    from sixbirds_nogo.coarse import DeterministicLens
    from sixbirds_nogo.packaging import PackagingOperator
    with pytest.raises(ValueError, match="negative"):
        PackagingOperator("invalid", "stochastic_operator", ("a", "b"), None,
            ((F(-1), F(2)), (F(0), F(1))), "row_distribution_left_multiply")
    with pytest.raises(ValueError, match="canonical mapping image"):
        DeterministicLens("invalid", ("a", "b"), {"a": "A", "b": "A"},
            ("A", "B"), {"A": 0, "B": 1})


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
