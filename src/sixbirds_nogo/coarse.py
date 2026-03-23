"""Deterministic coarse-graining and honest observed-process utilities."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Any

from sixbirds_nogo.markov import FiniteMarkovChain, parse_probability_vector
from sixbirds_nogo.pathspace import enumerate_path_law
from sixbirds_nogo.witnesses import load_witness


@dataclass(frozen=True)
class DeterministicLens:
    id: str
    domain_states: tuple[str, ...]
    mapping: dict[str, str]
    image_states: tuple[str, ...]
    image_to_index: dict[str, int]


def make_lens(domain_states: Any, mapping: Any, lens_id: str = "") -> DeterministicLens:
    """Create and validate a deterministic lens with canonical image order."""
    if not isinstance(domain_states, (tuple, list)) or not domain_states:
        raise ValueError("domain_states must be a non-empty sequence")
    domain = tuple(domain_states)
    if len(set(domain)) != len(domain):
        raise ValueError("domain_states must be unique")
    if not isinstance(mapping, dict):
        raise ValueError("mapping must be a dict")

    keys = set(mapping.keys())
    dom_set = set(domain)
    if keys != dom_set:
        missing = sorted(dom_set - keys)
        extra = sorted(keys - dom_set)
        raise ValueError(f"mapping keys must match domain_states exactly; missing={missing}, extra={extra}")

    image_order: list[str] = []
    seen: set[str] = set()
    for s in domain:
        val = mapping[s]
        if not isinstance(val, str) or not val:
            raise ValueError(f"mapping for state {s!r} must be a non-empty string")
        if val not in seen:
            seen.add(val)
            image_order.append(val)

    image_states = tuple(image_order)
    image_to_index = {s: i for i, s in enumerate(image_states)}

    return DeterministicLens(
        id=lens_id,
        domain_states=domain,
        mapping={k: mapping[k] for k in domain},
        image_states=image_states,
        image_to_index=image_to_index,
    )


def load_lens_from_witness(witness_id: str, lens_id: str, config_path: str = "configs/witnesses.yaml") -> DeterministicLens:
    """Load deterministic lens from witness registry preserving microstate order."""
    witness = load_witness(witness_id, config_path=config_path).raw
    space = witness.get("microstate_space")
    if not isinstance(space, dict) or not isinstance(space.get("states"), list):
        raise ValueError(f"witness {witness_id!r} has invalid microstate_space")
    states = tuple(space["states"])

    lenses = witness.get("lenses")
    if not isinstance(lenses, list):
        raise ValueError(f"witness {witness_id!r} has invalid lenses")
    for lens in lenses:
        if isinstance(lens, dict) and lens.get("id") == lens_id:
            return make_lens(states, lens.get("mapping"), lens_id=lens_id)
    raise KeyError(f"witness {witness_id!r} has no lens with id {lens_id!r}")


def _ensure_compatible(chain: FiniteMarkovChain, lens: DeterministicLens) -> None:
    if lens.domain_states != chain.states:
        raise ValueError("lens.domain_states must match chain.states exactly")


def pushforward_distribution_through_lens(dist: Any, lens: DeterministicLens) -> tuple[Fraction, ...]:
    """Push a micro distribution through a deterministic lens."""
    parsed = parse_probability_vector(dist)
    if len(parsed) != len(lens.domain_states):
        raise ValueError("distribution dimension does not match lens domain")

    out = [Fraction(0, 1) for _ in lens.image_states]
    for i, s in enumerate(lens.domain_states):
        out[lens.image_to_index[lens.mapping[s]]] += parsed[i]
    return tuple(out)


def pushforward_path(path: tuple[str, ...] | list[str], lens: DeterministicLens) -> tuple[str, ...]:
    """Push a micro path to a coarse path."""
    if not isinstance(path, (tuple, list)) or not path:
        raise ValueError("path must be a non-empty sequence")
    out: list[str] = []
    for s in path:
        if s not in lens.mapping:
            raise ValueError(f"state {s!r} not in lens domain")
        out.append(lens.mapping[s])
    return tuple(out)


def pushforward_path_law(path_law: dict[tuple[str, ...], Fraction], lens: DeterministicLens) -> dict[tuple[str, ...], Fraction]:
    """Push a micro path law through a deterministic lens exactly."""
    out: dict[tuple[str, ...], Fraction] = {}
    for path, mass in path_law.items():
        coarse = pushforward_path(path, lens)
        out[coarse] = out.get(coarse, Fraction(0, 1)) + mass
    return out


def enumerate_observed_path_law(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    horizon: int,
    initial_dist: Any = None,
) -> dict[tuple[str, ...], Fraction]:
    """Honest observed path law via exact micro path-law pushforward."""
    _ensure_compatible(chain, lens)
    micro = enumerate_path_law(chain, horizon, initial_dist=initial_dist)
    return pushforward_path_law(micro, lens)


def observed_path_probability_bruteforce(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    observed_path: tuple[str, ...] | list[str],
    initial_dist: Any = None,
) -> Fraction:
    """Exact brute-force observed path probability via micro preimages."""
    _ensure_compatible(chain, lens)
    if not isinstance(observed_path, (tuple, list)) or not observed_path:
        raise ValueError("observed_path must be a non-empty sequence")
    obs = tuple(observed_path)

    if initial_dist is None:
        if chain.stationary_distribution is None:
            raise ValueError("initial_dist is required when chain has no stationary_distribution")
        init = chain.stationary_distribution
    else:
        init = parse_probability_vector(initial_dist)
    if len(init) != chain.size:
        raise ValueError("initial_dist dimension mismatch")

    preimage: dict[str, tuple[str, ...]] = {}
    for c in lens.image_states:
        pre = tuple(s for s in chain.states if lens.mapping[s] == c)
        preimage[c] = pre

    for c in obs:
        if c not in preimage or not preimage[c]:
            return Fraction(0, 1)

    state_idx = {s: i for i, s in enumerate(chain.states)}
    total = Fraction(0, 1)
    for micro_path in product(*(preimage[c] for c in obs)):
        p = init[state_idx[micro_path[0]]]
        if p == 0:
            continue
        ok = True
        for t in range(len(micro_path) - 1):
            step = chain.matrix[state_idx[micro_path[t]]][state_idx[micro_path[t + 1]]]
            if step == 0:
                ok = False
                break
            p *= step
        if ok:
            total += p
    return total


def enumerate_observed_path_law_bruteforce(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    horizon: int,
    initial_dist: Any = None,
) -> dict[tuple[str, ...], Fraction]:
    """Exact brute-force observed path law over all coarse paths."""
    _ensure_compatible(chain, lens)
    if horizon < 0:
        raise ValueError("horizon must be nonnegative")

    out: dict[tuple[str, ...], Fraction] = {}
    for coarse_path in product(lens.image_states, repeat=horizon + 1):
        p = observed_path_probability_bruteforce(chain, lens, coarse_path, initial_dist=initial_dist)
        if p != 0:
            out[tuple(coarse_path)] = p
    return out


def block_transition_rows(chain: FiniteMarkovChain, lens: DeterministicLens) -> dict[str, tuple[Fraction, ...]]:
    """Per-microstate transition mass into each coarse block."""
    _ensure_compatible(chain, lens)
    rows: dict[str, tuple[Fraction, ...]] = {}
    block_members = {
        b: tuple(s for s in chain.states if lens.mapping[s] == b)
        for b in lens.image_states
    }
    idx = {s: i for i, s in enumerate(chain.states)}
    for x in chain.states:
        i = idx[x]
        row: list[Fraction] = []
        for b in lens.image_states:
            mass = Fraction(0, 1)
            for y in block_members[b]:
                mass += chain.matrix[i][idx[y]]
            row.append(mass)
        rows[x] = tuple(row)
    return rows


def is_strongly_lumpable(chain: FiniteMarkovChain, lens: DeterministicLens) -> bool:
    """Exact strong lumpability test on deterministic blocks."""
    _ensure_compatible(chain, lens)
    rows = block_transition_rows(chain, lens)
    blocks: dict[str, list[str]] = {b: [] for b in lens.image_states}
    for s in chain.states:
        blocks[lens.mapping[s]].append(s)

    for members in blocks.values():
        if len(members) <= 1:
            continue
        ref = rows[members[0]]
        for s in members[1:]:
            if rows[s] != ref:
                return False
    return True


def strong_lumpable_macro_chain(chain: FiniteMarkovChain, lens: DeterministicLens) -> FiniteMarkovChain:
    """Construct exact honest macro chain when strong lumpability holds."""
    _ensure_compatible(chain, lens)
    if not is_strongly_lumpable(chain, lens):
        raise ValueError("lens is not strongly lumpable for the given chain")

    rows = block_transition_rows(chain, lens)
    reps: list[str] = []
    for b in lens.image_states:
        rep = next((s for s in chain.states if lens.mapping[s] == b), None)
        if rep is None:
            raise ValueError(f"coarse block {b!r} has no domain states")
        reps.append(rep)

    macro_matrix = tuple(rows[rep] for rep in reps)
    macro_stationary = None
    if chain.stationary_distribution is not None:
        macro_stationary = pushforward_distribution_through_lens(chain.stationary_distribution, lens)

    return FiniteMarkovChain(
        states=lens.image_states,
        matrix=macro_matrix,
        stationary_distribution=macro_stationary,
    )
