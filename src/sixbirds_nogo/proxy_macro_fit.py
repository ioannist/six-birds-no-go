"""Proxy first-order macro-Markov fitting utilities.

All functionality in this module is explicitly diagnostic/proxy-level and must
not be used as an honest theorem-level observed-process audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from sixbirds_nogo.coarse import DeterministicLens, enumerate_observed_path_law, pushforward_distribution_through_lens
from sixbirds_nogo.markov import FiniteMarkovChain, is_stationary_distribution, parse_probability_vector
from sixbirds_nogo.pathspace import enumerate_path_law, path_probability


@dataclass(frozen=True)
class ProxyMacroMarkovFit:
    proxy_id: str
    lens_id: str
    macro_chain: FiniteMarkovChain
    initial_distribution: tuple[Fraction, ...]
    notes: str


def _resolve_initial(chain: FiniteMarkovChain, initial_dist: Any) -> tuple[Fraction, ...]:
    if initial_dist is None:
        if chain.stationary_distribution is None:
            raise ValueError("initial_dist is required when chain has no stationary_distribution")
        return chain.stationary_distribution
    parsed = parse_probability_vector(initial_dist)
    if len(parsed) != chain.size:
        raise ValueError("initial_dist dimension mismatch")
    return parsed


def fit_proxy_macro_chain(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    initial_dist: Any = None,
) -> ProxyMacroMarkovFit:
    """Fit a first-order macro Markov proxy from exact one-step coarse pair law."""
    if lens.domain_states != chain.states:
        raise ValueError("lens.domain_states must match chain.states exactly")

    micro_init = _resolve_initial(chain, initial_dist)
    coarse_init = pushforward_distribution_through_lens(micro_init, lens)

    one_step_law = enumerate_observed_path_law(chain, lens, horizon=1, initial_dist=micro_init)
    idx = {s: i for i, s in enumerate(lens.image_states)}

    rows = []
    for a in lens.image_states:
        denom = coarse_init[idx[a]]
        if denom == 0:
            raise ValueError(f"undefined conditional for coarse state {a!r}: zero initial mass")
        row = []
        for b in lens.image_states:
            num = one_step_law.get((a, b), Fraction(0, 1))
            row.append(num / denom)
        rows.append(tuple(row))

    macro_chain = FiniteMarkovChain(states=lens.image_states, matrix=tuple(rows), stationary_distribution=None)
    stationary = coarse_init if is_stationary_distribution(macro_chain, coarse_init) else None
    macro_chain = FiniteMarkovChain(states=lens.image_states, matrix=macro_chain.matrix, stationary_distribution=stationary)

    return ProxyMacroMarkovFit(
        proxy_id="PROXY_MACRO_MARKOV_ARROW",
        lens_id=lens.id,
        macro_chain=macro_chain,
        initial_distribution=coarse_init,
        notes="Diagnostic proxy fit under first-order macro Markov assumption; not an honest theorem-level audit.",
    )


def proxy_path_probability(
    fit: ProxyMacroMarkovFit,
    path: tuple[str, ...] | list[str],
    initial_dist: Any = None,
) -> Fraction:
    """Exact path probability under fitted proxy macro chain."""
    init = fit.initial_distribution if initial_dist is None else parse_probability_vector(initial_dist)
    return path_probability(fit.macro_chain, path, init)


def proxy_path_law(
    fit: ProxyMacroMarkovFit,
    horizon: int,
    initial_dist: Any = None,
) -> dict[tuple[str, ...], Fraction]:
    """Exact finite-horizon path law under fitted proxy macro chain."""
    init = fit.initial_distribution if initial_dist is None else parse_probability_vector(initial_dist)
    return enumerate_path_law(fit.macro_chain, horizon, initial_dist=init)
