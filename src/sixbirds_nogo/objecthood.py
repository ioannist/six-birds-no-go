"""Exact objecthood/contraction/stability utilities."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from sixbirds_nogo.markov import (
    FiniteMarkovChain,
    parse_probability_vector,
    solve_stationary_distribution,
    validate_distribution,
)
from sixbirds_nogo.packaging import (
    PackagingOperator,
    apply_packaging_to_distribution,
    induced_operator_matrix,
    state_fixed_points,
)


def total_variation_distance(p: Any, q: Any) -> Fraction:
    pp = parse_probability_vector(p)
    qq = parse_probability_vector(q)
    if len(pp) != len(qq):
        raise ValueError("dimension mismatch")
    validate_distribution(pp)
    validate_distribution(qq)
    return sum((abs(a - b) for a, b in zip(pp, qq)), Fraction(0, 1)) / 2


def distribution_residual(pkg: PackagingOperator, dist: Any) -> Fraction:
    d = parse_probability_vector(dist)
    validate_distribution(d)
    nxt = apply_packaging_to_distribution(pkg, d, steps=1)
    return total_variation_distance(nxt, d)


def dobrushin_contraction_lambda(pkg: PackagingOperator) -> Fraction:
    mat = induced_operator_matrix(pkg)
    n = len(mat)
    mx = Fraction(0, 1)
    for i in range(n):
        for j in range(n):
            l1 = sum((abs(a - b) for a, b in zip(mat[i], mat[j])), Fraction(0, 1))
            val = l1 / 2
            if val > mx:
                mx = val
    return mx


def solve_unique_fixed_distribution(pkg: PackagingOperator) -> tuple[Fraction, ...]:
    if pkg.family == "state_map":
        fps = state_fixed_points(pkg)
        if len(fps) != 1:
            raise ValueError("unique fixed distribution is unsupported for non-unique state_map fixed points")
        target = fps[0]
        return tuple(Fraction(1, 1) if s == target else Fraction(0, 1) for s in pkg.states)

    lam = dobrushin_contraction_lambda(pkg)
    if lam >= 1:
        raise ValueError("unique fixed distribution not guaranteed when contraction lambda >= 1")
    chain = FiniteMarkovChain(states=pkg.states, matrix=induced_operator_matrix(pkg), stationary_distribution=None)
    return solve_stationary_distribution(chain)


def fixed_point_count(pkg: PackagingOperator) -> int:
    if pkg.family == "state_map":
        return len(state_fixed_points(pkg))
    return 1 if dobrushin_contraction_lambda(pkg) < 1 else 0


def enumerate_simplex_grid(states: tuple[str, ...], denominator: int) -> tuple[tuple[Fraction, ...], ...]:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    if not states:
        raise ValueError("states must be non-empty")

    n = len(states)
    out: list[tuple[Fraction, ...]] = []

    def rec(prefix: list[int], remaining: int, k: int) -> None:
        if k == n - 1:
            counts = prefix + [remaining]
            out.append(tuple(Fraction(c, denominator) for c in counts))
            return
        for c in range(remaining + 1):
            rec(prefix + [c], remaining - c, k + 1)

    rec([], denominator, 0)
    return tuple(out)


def epsilon_stable_distributions(
    pkg: PackagingOperator,
    denominator: int,
    epsilon: Fraction,
) -> tuple[tuple[Fraction, ...], ...]:
    grid = enumerate_simplex_grid(pkg.states, denominator)
    return tuple(mu for mu in grid if distribution_residual(pkg, mu) <= epsilon)


def approximate_object_separation_bound(lambda_coeff: Fraction, epsilon: Fraction) -> Fraction | None:
    if lambda_coeff >= 1:
        return None
    return (2 * epsilon) / (Fraction(1, 1) - lambda_coeff)


def check_approximate_object_separation(
    pkg: PackagingOperator,
    dist_a: Any,
    dist_b: Any,
    epsilon: Fraction,
) -> dict[str, Any]:
    lambda_coeff = dobrushin_contraction_lambda(pkg)
    residual_a = distribution_residual(pkg, dist_a)
    residual_b = distribution_residual(pkg, dist_b)
    premises_hold = residual_a <= epsilon and residual_b <= epsilon and lambda_coeff < 1

    lhs_tv = total_variation_distance(dist_a, dist_b)
    rhs = approximate_object_separation_bound(lambda_coeff, epsilon)
    if rhs is None:
        holds = None
    else:
        holds = lhs_tv <= rhs

    return {
        "lambda_coeff": lambda_coeff,
        "epsilon": epsilon,
        "residual_a": residual_a,
        "residual_b": residual_b,
        "premises_hold": premises_hold,
        "lhs_tv": lhs_tv,
        "rhs_bound": rhs,
        "holds": holds,
    }
