"""Exact definability, bounded-interface, and no-ladder utilities."""

from __future__ import annotations

from fractions import Fraction
from itertools import product
import random
from typing import Any

from sixbirds_nogo.coarse import DeterministicLens
from sixbirds_nogo.packaging import (
    PackagingOperator,
    apply_packaging_to_state,
    idempotence_defect,
    is_idempotent,
)


def predicate_from_true_states(states: tuple[str, ...] | list[str], true_states: set[str] | tuple[str, ...] | list[str]) -> tuple[bool, ...]:
    st = tuple(states)
    ts = set(true_states)
    if not ts.issubset(set(st)):
        raise ValueError("true_states must be a subset of states")
    return tuple(s in ts for s in st)


def predicate_to_true_states(predicate: tuple[bool, ...] | list[bool], states: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    pred = tuple(predicate)
    st = tuple(states)
    if len(pred) != len(st):
        raise ValueError("predicate length must match states length")
    if not all(isinstance(v, bool) for v in pred):
        raise ValueError("predicate must contain bool entries")
    return tuple(s for s, v in zip(st, pred) if v)


def enumerate_all_predicates(states: tuple[str, ...] | list[str]) -> tuple[tuple[bool, ...], ...]:
    st = tuple(states)
    return tuple(tuple(bits) for bits in product((False, True), repeat=len(st)))


def is_predicate_definable_from_lens(predicate: tuple[bool, ...] | list[bool], lens: DeterministicLens) -> bool:
    pred = tuple(predicate)
    if len(pred) != len(lens.domain_states):
        raise ValueError("predicate length must match lens.domain_states")
    if not all(isinstance(v, bool) for v in pred):
        raise ValueError("predicate must contain bool entries")

    fibers: dict[str, bool] = {}
    for i, state in enumerate(lens.domain_states):
        y = lens.mapping[state]
        v = pred[i]
        if y in fibers and fibers[y] != v:
            return False
        fibers[y] = v
    return True


def enumerate_definable_predicates(lens: DeterministicLens) -> tuple[tuple[bool, ...], ...]:
    all_preds = enumerate_all_predicates(lens.domain_states)
    return tuple(p for p in all_preds if is_predicate_definable_from_lens(p, lens))


def definable_predicate_count(lens: DeterministicLens) -> int:
    return len(enumerate_definable_predicates(lens))


def formula_definable_predicate_count(lens: DeterministicLens) -> int:
    return 2 ** len(lens.image_states)


def formula_definability_probability(lens: DeterministicLens) -> Fraction:
    n = len(lens.domain_states)
    k = len(lens.image_states)
    return Fraction(2**k, 2**n)


def sample_random_predicates(
    states: tuple[str, ...] | list[str],
    sample_count: int,
    seed: int = 0,
    replace: bool = True,
) -> tuple[tuple[bool, ...], ...]:
    st = tuple(states)
    n = len(st)
    if sample_count < 0:
        raise ValueError("sample_count must be nonnegative")

    rng = random.Random(seed)
    total = 2**n

    if replace:
        out = []
        for _ in range(sample_count):
            out.append(tuple(bool(rng.getrandbits(1)) for _ in range(n)))
        return tuple(out)

    if sample_count > total:
        raise ValueError("sample_count cannot exceed full predicate space when replace=False")

    all_preds = list(enumerate_all_predicates(st))
    rng.shuffle(all_preds)
    return tuple(all_preds[:sample_count])


def empirical_definability_rate(lens: DeterministicLens, sample_count: int, seed: int = 0, replace: bool = True) -> Fraction:
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    samples = sample_random_predicates(lens.domain_states, sample_count, seed=seed, replace=replace)
    hits = sum(1 for p in samples if is_predicate_definable_from_lens(p, lens))
    return Fraction(hits, sample_count)


def lens_refinement_factor(base_lens: DeterministicLens, refined_lens: DeterministicLens) -> dict[str, str] | None:
    if base_lens.domain_states != refined_lens.domain_states:
        raise ValueError("lenses must share identical domain_states")

    factor: dict[str, str] = {}
    for s in refined_lens.domain_states:
        r = refined_lens.mapping[s]
        b = base_lens.mapping[s]
        if r in factor and factor[r] != b:
            return None
        factor[r] = b
    return factor


def predicates_gained_under_extension(base_lens: DeterministicLens, extended_lens: DeterministicLens) -> tuple[tuple[bool, ...], ...]:
    if base_lens.domain_states != extended_lens.domain_states:
        raise ValueError("lenses must share identical domain_states")

    base = set(enumerate_definable_predicates(base_lens))
    ext = enumerate_definable_predicates(extended_lens)
    return tuple(p for p in ext if p not in base)


def observed_packaging_signature(pkg: PackagingOperator, lens: DeterministicLens, steps: int) -> tuple[str, ...]:
    if pkg.family != "state_map":
        raise ValueError("observed_packaging_signature requires state_map packaging")
    if pkg.states != lens.domain_states:
        raise ValueError("pkg.states must match lens.domain_states exactly")
    if steps < 0:
        raise ValueError("steps must be nonnegative")

    out = []
    for s in pkg.states:
        s_n = apply_packaging_to_state(pkg, s, steps=steps)
        out.append(lens.mapping[s_n])
    return tuple(out)


def observed_signature_sequence(pkg: PackagingOperator, lens: DeterministicLens, max_steps: int) -> tuple[tuple[str, ...], ...]:
    if max_steps < 0:
        raise ValueError("max_steps must be nonnegative")
    return tuple(observed_packaging_signature(pkg, lens, n) for n in range(max_steps + 1))


def signature_stabilization_step(sequence: tuple[tuple[str, ...], ...] | list[tuple[str, ...]]) -> int | None:
    seq = tuple(sequence)
    for i in range(len(seq)):
        if all(seq[j] == seq[i] for j in range(i, len(seq))):
            return i
    return None


def fixed_interface_no_ladder_report(pkg: PackagingOperator, lens: DeterministicLens, max_steps: int = 3) -> dict[str, Any]:
    if pkg.family != "state_map":
        raise ValueError("fixed_interface_no_ladder_report requires state_map packaging")
    if pkg.states != lens.domain_states:
        raise ValueError("pkg.states must match lens.domain_states exactly")

    seq = observed_signature_sequence(pkg, lens, max_steps)
    stab = signature_stabilization_step(seq)

    no_new_after_step1 = True if len(seq) <= 1 else all(sig == seq[1] for sig in seq[1:])

    idemp_def = idempotence_defect(pkg)
    no_ladder_holds = (idemp_def == Fraction(0, 1)) and no_new_after_step1

    return {
        "package_id": pkg.id,
        "lens_id": lens.id,
        "state_count": len(lens.domain_states),
        "interface_size": len(lens.image_states),
        "definable_predicate_count": definable_predicate_count(lens),
        "formula_definable_predicate_count": formula_definable_predicate_count(lens),
        "idempotence_defect": idemp_def,
        "signature_sequence": seq,
        "stabilization_step": stab,
        "no_new_signatures_after_step1": no_new_after_step1,
        "no_ladder_holds": no_ladder_holds,
    }


def lens_extension_escape_report(base_lens: DeterministicLens, extended_lens: DeterministicLens) -> dict[str, Any]:
    if base_lens.domain_states != extended_lens.domain_states:
        raise ValueError("lenses must share identical domain_states")

    factor = lens_refinement_factor(base_lens, extended_lens)
    strict = factor is not None and len(extended_lens.image_states) > len(base_lens.image_states)

    gained = predicates_gained_under_extension(base_lens, extended_lens)

    return {
        "base_lens_id": base_lens.id,
        "extended_lens_id": extended_lens.id,
        "strict_refinement": strict,
        "factor_map": factor,
        "base_interface_size": len(base_lens.image_states),
        "extended_interface_size": len(extended_lens.image_states),
        "base_definable_count": definable_predicate_count(base_lens),
        "extended_definable_count": definable_predicate_count(extended_lens),
        "gained_predicate_count": len(gained),
        "gained_predicates": gained,
        "escape_present": strict and len(gained) > 0,
    }
