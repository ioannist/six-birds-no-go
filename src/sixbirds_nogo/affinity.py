"""Exact cycle-ratio and one-form exactness utilities on bidirected support."""

from __future__ import annotations

from collections import deque
from fractions import Fraction

from sixbirds_nogo.graph_cycle import (
    Cycle,
    connected_components,
    fundamental_cycle_basis_from_edges,
)
from sixbirds_nogo.markov import FiniteMarkovChain


def bidirected_support_digraph(chain: FiniteMarkovChain, include_self_loops: bool = False) -> dict[str, tuple[str, ...]]:
    """Directed support restricted to bidirected positive edges."""
    states = chain.states
    out: dict[str, tuple[str, ...]] = {}
    for i, u in enumerate(states):
        nbrs = []
        for j, v in enumerate(states):
            if not include_self_loops and i == j:
                continue
            if chain.matrix[i][j] > 0 and chain.matrix[j][i] > 0:
                nbrs.append(v)
        out[u] = tuple(nbrs)
    return out


def bidirected_support_undirected_edges(chain: FiniteMarkovChain, include_self_loops: bool = False) -> tuple[tuple[str, str], ...]:
    """Simple undirected edges from bidirected support."""
    idx = {s: i for i, s in enumerate(chain.states)}
    edges = set()
    for i, u in enumerate(chain.states):
        for j, v in enumerate(chain.states):
            if i == j:
                continue
            if chain.matrix[i][j] > 0 and chain.matrix[j][i] > 0:
                a, b = (u, v) if idx[u] < idx[v] else (v, u)
                edges.add((a, b))
    return tuple(sorted(edges, key=lambda e: (idx[e[0]], idx[e[1]])))


def log_ratio_ratio_form(chain: FiniteMarkovChain, include_self_loops: bool = False) -> dict[tuple[str, str], Fraction]:
    """Exact multiplicative representative of the log-ratio 1-form."""
    out: dict[tuple[str, str], Fraction] = {}
    for i, u in enumerate(chain.states):
        for j, v in enumerate(chain.states):
            if not include_self_loops and i == j:
                continue
            pij = chain.matrix[i][j]
            pji = chain.matrix[j][i]
            if pij > 0 and pji > 0:
                out[(u, v)] = pij / pji
    return out


def cycle_ratio(cycle: Cycle, ratio_form: dict[tuple[str, str], Fraction]) -> Fraction:
    """Multiply exact edge ratios along a directed closed cycle."""
    if len(cycle) < 4 or cycle[0] != cycle[-1]:
        raise ValueError("cycle must be a closed sequence with >= 3 distinct vertices")
    r = Fraction(1, 1)
    for i in range(len(cycle) - 1):
        e = (cycle[i], cycle[i + 1])
        if e not in ratio_form:
            raise ValueError(f"missing ratio-form edge: {e}")
        r *= ratio_form[e]
    return r


def cycle_affinity_surrogate(cycle_ratio_value: Fraction) -> Fraction:
    """Exact nonnegative surrogate: max(r, 1/r) - 1."""
    if cycle_ratio_value <= 0:
        raise ValueError("cycle ratio must be positive")
    inv = Fraction(1, 1) / cycle_ratio_value
    return (cycle_ratio_value if cycle_ratio_value >= inv else inv) - Fraction(1, 1)


def cycle_affinities(
    chain: FiniteMarkovChain,
    cycle_basis: tuple[Cycle, ...] | None = None,
) -> dict[Cycle, Fraction]:
    """Cycle surrogates over undirected bidirected-support basis."""
    ratio = log_ratio_ratio_form(chain)
    if cycle_basis is None:
        bi_edges = bidirected_support_undirected_edges(chain)
        cycle_basis = fundamental_cycle_basis_from_edges(chain.states, bi_edges)
    return {cyc: cycle_affinity_surrogate(cycle_ratio(cyc, ratio)) for cyc in cycle_basis}


def max_cycle_affinity(chain: FiniteMarkovChain, cycle_basis: tuple[Cycle, ...] | None = None) -> Fraction:
    """Maximum exact cycle surrogate across chosen cycle basis."""
    vals = list(cycle_affinities(chain, cycle_basis=cycle_basis).values())
    if not vals:
        return Fraction(0, 1)
    return max(vals)


def reconstruct_exact_potential(chain: FiniteMarkovChain) -> dict[str, Fraction] | None:
    """Reconstruct exact rational potential phi with r_ij = phi[j]/phi[i]."""
    states = chain.states
    ratio = log_ratio_ratio_form(chain)
    edges = bidirected_support_undirected_edges(chain)
    comps = connected_components(states, edges)

    adj: dict[str, list[str]] = {s: [] for s in states}
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    idx = {s: i for i, s in enumerate(states)}
    for s in states:
        adj[s].sort(key=lambda x: idx[x])

    phi: dict[str, Fraction] = {}
    for comp in comps:
        if not comp:
            continue
        root = comp[0]
        if root not in phi:
            phi[root] = Fraction(1, 1)
        q = deque([root])
        seen = {root}
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in seen:
                    r_uv = ratio[(u, v)]
                    phi[v] = phi[u] * r_uv
                    seen.add(v)
                    q.append(v)
                else:
                    r_uv = ratio[(u, v)]
                    if phi[v] != phi[u] * r_uv:
                        return None

    for (u, v), r_uv in ratio.items():
        if phi.get(u) is None or phi.get(v) is None:
            return None
        if phi[v] != phi[u] * r_uv:
            return None

    for s in states:
        phi.setdefault(s, Fraction(1, 1))
    return phi


def is_exact_oneform(chain: FiniteMarkovChain) -> bool:
    """Exactness predicate based on potential reconstruction."""
    return reconstruct_exact_potential(chain) is not None
