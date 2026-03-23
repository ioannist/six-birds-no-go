"""Exact finite-horizon path-space utilities."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from sixbirds_nogo.markov import FiniteMarkovChain, parse_probability_vector, validate_distribution


def _resolve_initial_distribution(chain: FiniteMarkovChain, initial_dist: Any) -> tuple[Fraction, ...]:
    if initial_dist is None:
        if chain.stationary_distribution is None:
            raise ValueError("initial_dist is required when chain has no stationary_distribution")
        dist = chain.stationary_distribution
    else:
        dist = parse_probability_vector(initial_dist)
    validate_distribution(dist)
    if len(dist) != chain.size:
        raise ValueError("initial_dist dimension does not match chain")
    return dist


def path_probability(
    chain: FiniteMarkovChain,
    path: tuple[str, ...] | list[str],
    initial_dist: Any,
) -> Fraction:
    """Compute exact probability of a concrete state path."""
    if not isinstance(path, (tuple, list)) or not path:
        raise ValueError("path must be a non-empty sequence of state labels")

    dist = _resolve_initial_distribution(chain, initial_dist)
    labels = tuple(path)
    try:
        indices = [chain.index_of(s) for s in labels]
    except KeyError as exc:
        raise ValueError(str(exc)) from exc

    prob = dist[indices[0]]
    for i in range(len(indices) - 1):
        step = chain.matrix[indices[i]][indices[i + 1]]
        if step == 0:
            return Fraction(0, 1)
        prob *= step
    return prob


def enumerate_path_law(
    chain: FiniteMarkovChain,
    horizon: int,
    initial_dist: Any = None,
) -> dict[tuple[str, ...], Fraction]:
    """Enumerate exact finite-horizon path law over state labels."""
    if horizon < 0:
        raise ValueError("horizon must be nonnegative")

    dist = _resolve_initial_distribution(chain, initial_dist)
    law: dict[tuple[str, ...], Fraction] = {}

    def rec(prefix: tuple[str, ...], prob: Fraction, steps_done: int) -> None:
        if steps_done == horizon:
            if prob != 0:
                law[prefix] = prob
            return
        last_idx = chain.index_of(prefix[-1])
        for nxt in chain.states:
            p = chain.matrix[last_idx][chain.index_of(nxt)]
            if p == 0:
                continue
            rec(prefix + (nxt,), prob * p, steps_done + 1)

    for idx, state in enumerate(chain.states):
        p0 = dist[idx]
        if p0 == 0:
            continue
        rec((state,), p0, 0)

    return law


def path_law_total_mass(path_law: dict[tuple[str, ...], Fraction]) -> Fraction:
    """Sum all path masses exactly."""
    return sum(path_law.values(), Fraction(0, 1))


def joint_law_from_path_law(
    path_law: dict[tuple[str, ...], Fraction],
    time_indices: tuple[int, ...] | list[int],
) -> dict[tuple[str, ...], Fraction]:
    """Aggregate a path law into a joint law on selected time coordinates."""
    if not isinstance(time_indices, (tuple, list)) or not time_indices:
        raise ValueError("time_indices must be a non-empty sequence")
    if any((not isinstance(t, int) or t < 0) for t in time_indices):
        raise ValueError("time_indices must contain nonnegative integers")

    t_idx = tuple(time_indices)
    joint: dict[tuple[str, ...], Fraction] = {}
    for path, mass in path_law.items():
        if max(t_idx) >= len(path):
            raise ValueError("time index out of range for path length")
        key = tuple(path[t] for t in t_idx)
        joint[key] = joint.get(key, Fraction(0, 1)) + mass
    return joint


def marginal_from_path_law(path_law: dict[tuple[str, ...], Fraction], time_index: int) -> dict[str, Fraction]:
    """Extract one-time marginal from a path law."""
    joint = joint_law_from_path_law(path_law, (time_index,))
    return {k[0]: v for k, v in joint.items()}


def pair_law_from_path_law(
    path_law: dict[tuple[str, ...], Fraction],
    i: int,
    j: int,
) -> dict[tuple[str, str], Fraction]:
    """Convenience two-time joint law extractor."""
    out = joint_law_from_path_law(path_law, (i, j))
    return {(a, b): mass for (a, b), mass in out.items()}
