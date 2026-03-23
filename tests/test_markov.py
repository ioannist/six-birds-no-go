from fractions import Fraction

from sixbirds_nogo.markov import (
    FiniteMarkovChain,
    is_stationary_distribution,
    list_chain_witness_ids,
    load_chain_from_witness,
    matrix_power,
    pushforward_distribution,
    solve_stationary_distribution,
    validate_row_stochastic,
)


REQUIRED_CHAIN_IDS = {
    "rev_tree_4",
    "rev_cycle_3",
    "biased_cycle_3",
    "hidden_clock_reversible",
    "hidden_clock_driven",
    "zero_closure_deficit_lumpable",
    "positive_closure_deficit",
}


def _identity(n: int) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(
        tuple(Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n))
        for i in range(n)
    )


def test_chain_loading_and_validation() -> None:
    ids = set(list_chain_witness_ids())
    assert REQUIRED_CHAIN_IDS.issubset(ids)
    for witness_id in ids:
        chain = load_chain_from_witness(witness_id)
        validate_row_stochastic(chain.matrix)


def test_stationary_solver_reversible_and_nonreversible() -> None:
    for witness_id in ("rev_cycle_3", "hidden_clock_driven"):
        chain = load_chain_from_witness(witness_id)
        assert chain.stationary_distribution is not None

        solved = solve_stationary_distribution(chain)
        assert solved == chain.stationary_distribution
        assert is_stationary_distribution(chain, solved)
        assert pushforward_distribution(solved, chain.matrix) == solved


def test_exact_fraction_types_and_matrix_power_pushforward() -> None:
    chain = load_chain_from_witness("rev_cycle_3")
    assert isinstance(chain.matrix[0][1], Fraction)

    solved = solve_stationary_distribution(chain)
    assert all(isinstance(x, Fraction) for x in solved)

    assert matrix_power(chain.matrix, 0) == _identity(chain.size)

    one_step = pushforward_distribution(chain.stationary_distribution, chain.matrix, steps=1)
    two_step_a = pushforward_distribution(chain.stationary_distribution, chain.matrix, steps=2)
    two_step_b = pushforward_distribution(one_step, chain.matrix, steps=1)
    assert two_step_a == two_step_b


def test_load_chain_from_witness_rejects_non_chain_kind() -> None:
    try:
        load_chain_from_witness("contractive_unique_object")
    except ValueError as exc:
        assert "unsupported kind" in str(exc)
    else:
        raise AssertionError("expected ValueError for non-chain witness")


def test_finite_chain_rejects_invalid_stationary_dimension() -> None:
    try:
        FiniteMarkovChain(
            states=("x", "y"),
            matrix=((Fraction(1, 2), Fraction(1, 2)), (Fraction(1, 2), Fraction(1, 2))),
            stationary_distribution=(Fraction(1, 1),),
        )
    except ValueError as exc:
        assert "dimension" in str(exc)
    else:
        raise AssertionError("expected dimension validation error")
