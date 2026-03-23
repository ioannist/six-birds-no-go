"""Deterministic graph/cycle-space utilities for finite chains."""

from __future__ import annotations

from collections import deque
from typing import Iterable

from sixbirds_nogo.markov import FiniteMarkovChain

UndirectedEdge = tuple[str, str]
Cycle = tuple[str, ...]


def _order_map(states: Iterable[str], state_order: Iterable[str] | None = None) -> tuple[tuple[str, ...], dict[str, int]]:
    states_tuple = tuple(states)
    if state_order is None:
        ordered = states_tuple
    else:
        ordered = tuple(state_order)
        if set(ordered) != set(states_tuple) or len(ordered) != len(states_tuple):
            raise ValueError("state_order must be a permutation of states")
    return ordered, {s: i for i, s in enumerate(ordered)}


def support_digraph(chain: FiniteMarkovChain, include_self_loops: bool = False) -> dict[str, tuple[str, ...]]:
    """Directed support adjacency in canonical state order."""
    states = chain.states
    out: dict[str, tuple[str, ...]] = {}
    for i, s in enumerate(states):
        nbrs = []
        for j, t in enumerate(states):
            if not include_self_loops and i == j:
                continue
            if chain.matrix[i][j] > 0:
                nbrs.append(t)
        out[s] = tuple(nbrs)
    return out


def support_undirected_edges(chain: FiniteMarkovChain, include_self_loops: bool = False) -> tuple[UndirectedEdge, ...]:
    """Simple undirected support edges in canonical sorted order."""
    states, idx = _order_map(chain.states)
    edges: set[UndirectedEdge] = set()

    for i, u in enumerate(states):
        for j, v in enumerate(states):
            if i == j:
                continue
            if chain.matrix[i][j] > 0 or chain.matrix[j][i] > 0:
                a, b = (u, v) if idx[u] < idx[v] else (v, u)
                edges.add((a, b))

    return tuple(sorted(edges, key=lambda e: (idx[e[0]], idx[e[1]])))


def connected_components(
    states: Iterable[str],
    undirected_edges: Iterable[UndirectedEdge],
    state_order: Iterable[str] | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Connected components including isolated vertices, deterministic ordering."""
    ordered, idx = _order_map(states, state_order)
    adjacency: dict[str, set[str]] = {s: set() for s in ordered}
    for u, v in undirected_edges:
        if u == v:
            continue
        if u not in adjacency or v not in adjacency:
            raise ValueError("edge references unknown state")
        adjacency[u].add(v)
        adjacency[v].add(u)

    seen: set[str] = set()
    comps: list[tuple[str, ...]] = []
    for root in ordered:
        if root in seen:
            continue
        q = deque([root])
        seen.add(root)
        comp: list[str] = []
        while q:
            u = q.popleft()
            comp.append(u)
            for v in sorted(adjacency[u], key=lambda s: idx[s]):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        comps.append(tuple(sorted(comp, key=lambda s: idx[s])))
    return tuple(comps)


def cycle_rank_from_edges(states: Iterable[str], undirected_edges: Iterable[UndirectedEdge]) -> int:
    """Cycle-space rank m - n + c on simple undirected support graph."""
    states_tuple = tuple(states)
    edge_set = {(u, v) for (u, v) in undirected_edges if u != v}
    m = len(edge_set)
    n = len(states_tuple)
    c = len(connected_components(states_tuple, edge_set))
    return m - n + c


def cycle_rank(chain: FiniteMarkovChain, include_self_loops: bool = False) -> int:
    edges = support_undirected_edges(chain, include_self_loops=include_self_loops)
    return cycle_rank_from_edges(chain.states, edges)


def is_forest_from_edges(states: Iterable[str], undirected_edges: Iterable[UndirectedEdge]) -> bool:
    return cycle_rank_from_edges(states, undirected_edges) == 0


def is_forest(chain: FiniteMarkovChain, include_self_loops: bool = False) -> bool:
    return cycle_rank(chain, include_self_loops=include_self_loops) == 0


def cycle_to_edges(cycle: Cycle) -> tuple[tuple[str, str], ...]:
    """Convert closed cycle state sequence to directed edge sequence."""
    if len(cycle) < 4 or cycle[0] != cycle[-1]:
        raise ValueError("cycle must be closed and contain at least 3 distinct vertices")
    return tuple((cycle[i], cycle[i + 1]) for i in range(len(cycle) - 1))


def _normalize_cycle(cycle: list[str], idx: dict[str, int]) -> Cycle:
    # cycle is simple (non-closed) vertex list
    if len(cycle) < 3:
        raise ValueError("cycle must contain at least 3 vertices")

    candidates: list[Cycle] = []
    n = len(cycle)
    for oriented in (cycle, list(reversed(cycle))):
        for k in range(n):
            rot = oriented[k:] + oriented[:k]
            candidates.append(tuple(rot + [rot[0]]))

    return min(candidates, key=lambda c: (tuple(idx[s] for s in c), c))


def _tree_path(parent: dict[str, str | None], a: str, b: str) -> list[str]:
    anc: dict[str, int] = {}
    cur = a
    depth = 0
    while cur is not None:
        anc[cur] = depth
        cur = parent[cur]
        depth += 1

    cur = b
    path_b: list[str] = []
    while cur not in anc:
        path_b.append(cur)
        par = parent[cur]
        if par is None:
            raise ValueError("nodes are not connected in spanning forest")
        cur = par
    lca = cur

    path_a: list[str] = []
    cur = a
    while cur != lca:
        path_a.append(cur)
        par = parent[cur]
        if par is None:
            raise ValueError("nodes are not connected in spanning forest")
        cur = par
    path_a.append(lca)

    return path_a + list(reversed(path_b))


def fundamental_cycle_basis_from_edges(
    states: Iterable[str],
    undirected_edges: Iterable[UndirectedEdge],
    state_order: Iterable[str] | None = None,
) -> tuple[Cycle, ...]:
    """Deterministic fundamental cycle basis from a spanning forest."""
    ordered, idx = _order_map(states, state_order)
    edge_list = []
    for u, v in undirected_edges:
        if u == v:
            continue
        if u not in idx or v not in idx:
            raise ValueError("edge references unknown state")
        a, b = (u, v) if idx[u] < idx[v] else (v, u)
        edge_list.append((a, b))
    edge_list = sorted(set(edge_list), key=lambda e: (idx[e[0]], idx[e[1]]))

    parent_uf = {s: s for s in ordered}

    def find(x: str) -> str:
        while parent_uf[x] != x:
            parent_uf[x] = parent_uf[parent_uf[x]]
            x = parent_uf[x]
        return x

    def union(a: str, b: str) -> bool:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent_uf[rb] = ra
        return True

    tree_edges: list[UndirectedEdge] = []
    non_tree_edges: list[UndirectedEdge] = []
    for e in edge_list:
        if union(*e):
            tree_edges.append(e)
        else:
            non_tree_edges.append(e)

    tree_adj: dict[str, list[str]] = {s: [] for s in ordered}
    for u, v in tree_edges:
        tree_adj[u].append(v)
        tree_adj[v].append(u)
    for s in ordered:
        tree_adj[s].sort(key=lambda x: idx[x])

    parent: dict[str, str | None] = {}
    seen: set[str] = set()
    for root in ordered:
        if root in seen:
            continue
        seen.add(root)
        parent[root] = None
        stack = [root]
        while stack:
            u = stack.pop()
            for v in reversed(tree_adj[u]):
                if v in seen:
                    continue
                seen.add(v)
                parent[v] = u
                stack.append(v)

    basis: list[Cycle] = []
    for u, v in non_tree_edges:
        simple = _tree_path(parent, u, v)
        cyc = _normalize_cycle(simple, idx)
        basis.append(cyc)

    return tuple(basis)


def fundamental_cycle_basis(chain: FiniteMarkovChain, include_self_loops: bool = False) -> tuple[Cycle, ...]:
    edges = support_undirected_edges(chain, include_self_loops=include_self_loops)
    return fundamental_cycle_basis_from_edges(chain.states, edges)
