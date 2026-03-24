from fractions import Fraction

from sixbirds_nogo.markov import FiniteMarkovChain, list_chain_witness_ids, load_chain_from_witness
from sixbirds_nogo.pathspace import (
    enumerate_path_law,
    joint_law_from_path_law,
    marginal_from_path_law,
    path_law_total_mass,
    path_probability,
    pair_law_from_path_law,
)


def test_path_law_total_mass_for_chain_witnesses_horizons_0_1_2() -> None:
    ids = list_chain_witness_ids()
    for witness_id in ids:
        chain = load_chain_from_witness(witness_id)
        assert chain.stationary_distribution is not None
        for horizon in (0, 1, 2):
            law = enumerate_path_law(chain, horizon, initial_dist=chain.stationary_distribution)
            assert path_law_total_mass(law) == Fraction(1, 1)


def test_specific_exact_path_probability() -> None:
    chain = load_chain_from_witness("rev_cycle_3")
    prob = path_probability(chain, ("0", "1", "0"), chain.stationary_distribution)
    assert prob == Fraction(1, 12)


def test_marginal_and_joint_utilities() -> None:
    chain = load_chain_from_witness("rev_cycle_3")
    init = chain.stationary_distribution
    law = enumerate_path_law(chain, 2, initial_dist=init)

    t0 = marginal_from_path_law(law, 0)
    expected_t0 = {state: init[i] for i, state in enumerate(chain.states)}
    assert t0 == expected_t0

    joint_02 = pair_law_from_path_law(law, 0, 2)
    assert sum(joint_02.values(), Fraction(0, 1)) == Fraction(1, 1)

    t1 = marginal_from_path_law(law, 1)
    expected_t1 = {state: chain.stationary_distribution[i] for i, state in enumerate(chain.states)}
    assert t1 == expected_t1

    generic_joint = joint_law_from_path_law(law, (1,))
    assert sum(generic_joint.values(), Fraction(0, 1)) == Fraction(1, 1)


def test_default_initial_distribution_behavior() -> None:
    chain = load_chain_from_witness("rev_cycle_3")
    law = enumerate_path_law(chain, 1, initial_dist=None)
    assert path_law_total_mass(law) == Fraction(1, 1)

    no_pi = FiniteMarkovChain(
        states=("x", "y"),
        matrix=((Fraction(1, 2), Fraction(1, 2)), (Fraction(1, 2), Fraction(1, 2))),
        stationary_distribution=None,
    )
    try:
        enumerate_path_law(no_pi, 1, initial_dist=None)
    except ValueError as exc:
        assert "initial_dist" in str(exc)
    else:
        raise AssertionError("expected ValueError when no initial distribution is available")
