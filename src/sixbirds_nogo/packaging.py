"""Exact finite packaging operators and idempotence/saturation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from sixbirds_nogo.markov import (
    parse_probability_matrix,
    parse_probability_vector,
    pushforward_distribution,
    validate_distribution,
    validate_row_stochastic,
)
from sixbirds_nogo.witnesses import load_witness


@dataclass(frozen=True)
class PackagingOperator:
    id: str
    family: str
    states: tuple[str, ...]
    mapping: dict[str, str] | None
    matrix: tuple[tuple[Fraction, ...], ...] | None
    action: str | None


def make_state_map_package(states: Any, mapping: Any, package_id: str = "") -> PackagingOperator:
    if not isinstance(states, (tuple, list)) or not states:
        raise ValueError("states must be a non-empty sequence")
    st = tuple(states)
    if len(set(st)) != len(st):
        raise ValueError("states must be unique")
    if not isinstance(mapping, dict):
        raise ValueError("mapping must be a dict")
    keys = set(mapping.keys())
    st_set = set(st)
    if keys != st_set:
        raise ValueError("state_map keys must match states exactly")
    if any(v not in st_set for v in mapping.values()):
        raise ValueError("state_map values must be valid states")
    return PackagingOperator(
        id=package_id,
        family="state_map",
        states=st,
        mapping={s: mapping[s] for s in st},
        matrix=None,
        action=None,
    )


def make_stochastic_operator_package(
    states: Any,
    matrix: Any,
    package_id: str = "",
    action: str = "row_distribution_left_multiply",
) -> PackagingOperator:
    if not isinstance(states, (tuple, list)) or not states:
        raise ValueError("states must be a non-empty sequence")
    st = tuple(states)
    if len(set(st)) != len(st):
        raise ValueError("states must be unique")
    mat = parse_probability_matrix(matrix)
    if len(mat) != len(st) or any(len(r) != len(st) for r in mat):
        raise ValueError("stochastic_operator matrix dimension mismatch")
    validate_row_stochastic(mat)
    return PackagingOperator(
        id=package_id,
        family="stochastic_operator",
        states=st,
        mapping=None,
        matrix=mat,
        action=action,
    )


def load_packaging_from_witness(witness_id: str, config_path: str = "configs/witnesses.yaml") -> PackagingOperator:
    witness = load_witness(witness_id, config_path=config_path).raw
    kind = witness.get("kind")
    if kind not in {"packaging_endomap", "extension_witness"}:
        raise ValueError(f"witness {witness_id!r} does not support packaging load (kind={kind!r})")

    space = witness.get("microstate_space")
    if not isinstance(space, dict) or not isinstance(space.get("states"), list):
        raise ValueError(f"witness {witness_id!r} missing/invalid microstate_space")
    states = tuple(space["states"])

    pkg = witness.get("packaging")
    if not isinstance(pkg, dict):
        raise ValueError(f"witness {witness_id!r} has no packaging")

    pkg_id = pkg.get("id")
    family = pkg.get("family")
    if not isinstance(pkg_id, str) or not pkg_id:
        raise ValueError("packaging.id must be a non-empty string")

    if family == "state_map":
        return make_state_map_package(states, pkg.get("mapping"), package_id=pkg_id)
    if family == "stochastic_operator":
        row_states = pkg.get("row_states")
        if not isinstance(row_states, list) or set(row_states) != set(states):
            raise ValueError("stochastic_operator row_states must match witness states")
        idx = {s: i for i, s in enumerate(row_states)}
        raw = parse_probability_matrix(pkg.get("matrix"))
        if len(raw) != len(states) or any(len(r) != len(states) for r in raw):
            raise ValueError("stochastic_operator matrix dimension mismatch")
        # Reorder into witness canonical order.
        mat = tuple(tuple(raw[idx[s_i]][idx[s_j]] for s_j in states) for s_i in states)
        return make_stochastic_operator_package(
            states,
            mat,
            package_id=pkg_id,
            action=str(pkg.get("action") or "row_distribution_left_multiply"),
        )

    raise ValueError(f"unsupported packaging family: {family!r}")


def basis_distribution(states: tuple[str, ...], state: str) -> tuple[Fraction, ...]:
    if state not in states:
        raise KeyError(f"unknown state: {state}")
    return tuple(Fraction(1, 1) if s == state else Fraction(0, 1) for s in states)


def induced_operator_matrix(pkg: PackagingOperator) -> tuple[tuple[Fraction, ...], ...]:
    if pkg.family == "stochastic_operator":
        assert pkg.matrix is not None
        return pkg.matrix
    if pkg.family == "state_map":
        assert pkg.mapping is not None
        idx = {s: i for i, s in enumerate(pkg.states)}
        rows = []
        for s in pkg.states:
            target = pkg.mapping[s]
            rows.append(tuple(Fraction(1, 1) if j == idx[target] else Fraction(0, 1) for j in range(len(pkg.states))))
        return tuple(rows)
    raise ValueError(f"unsupported packaging family: {pkg.family!r}")


def apply_packaging_to_state(pkg: PackagingOperator, state: str, steps: int = 1) -> str:
    if pkg.family != "state_map":
        raise ValueError("apply_packaging_to_state is only valid for state_map packaging")
    if steps < 0:
        raise ValueError("steps must be nonnegative")
    if state not in pkg.states:
        raise KeyError(f"unknown state: {state}")
    assert pkg.mapping is not None
    cur = state
    for _ in range(steps):
        cur = pkg.mapping[cur]
    return cur


def apply_packaging_to_distribution(pkg: PackagingOperator, dist: Any, steps: int = 1) -> tuple[Fraction, ...]:
    if steps < 0:
        raise ValueError("steps must be nonnegative")
    parsed = parse_probability_vector(dist)
    if len(parsed) != len(pkg.states):
        raise ValueError("distribution dimension mismatch")
    validate_distribution(parsed)
    mat = induced_operator_matrix(pkg)
    return pushforward_distribution(parsed, mat, steps=steps)


def distribution_trajectory(pkg: PackagingOperator, initial_dist: Any, steps: int) -> tuple[tuple[Fraction, ...], ...]:
    if steps < 0:
        raise ValueError("steps must be nonnegative")
    cur = parse_probability_vector(initial_dist)
    if len(cur) != len(pkg.states):
        raise ValueError("distribution dimension mismatch")
    validate_distribution(cur)
    out = [tuple(cur)]
    for _ in range(steps):
        cur = apply_packaging_to_distribution(pkg, cur, steps=1)
        out.append(tuple(cur))
    return tuple(out)


def state_trajectory(pkg: PackagingOperator, initial_state: str, steps: int) -> tuple[str, ...]:
    if pkg.family != "state_map":
        raise ValueError("state_trajectory is only valid for state_map packaging")
    if steps < 0:
        raise ValueError("steps must be nonnegative")
    out = [initial_state]
    cur = initial_state
    for _ in range(steps):
        cur = apply_packaging_to_state(pkg, cur, 1)
        out.append(cur)
    return tuple(out)


def _tv(p: tuple[Fraction, ...], q: tuple[Fraction, ...]) -> Fraction:
    if len(p) != len(q):
        raise ValueError("dimension mismatch")
    return sum((abs(a - b) for a, b in zip(p, q)), Fraction(0, 1)) / 2


def idempotence_defect(pkg: PackagingOperator) -> Fraction:
    mat = induced_operator_matrix(pkg)
    out = Fraction(0, 1)
    for s in pkg.states:
        delta = basis_distribution(pkg.states, s)
        e1 = pushforward_distribution(delta, mat, 1)
        e2 = pushforward_distribution(delta, mat, 2)
        d = _tv(e2, e1)
        if d > out:
            out = d
    return out


def is_idempotent(pkg: PackagingOperator) -> bool:
    return idempotence_defect(pkg) == Fraction(0, 1)


def state_fixed_points(pkg: PackagingOperator) -> tuple[str, ...]:
    if pkg.family != "state_map":
        raise ValueError("state_fixed_points is only valid for state_map packaging")
    assert pkg.mapping is not None
    return tuple(s for s in pkg.states if pkg.mapping[s] == s)


def state_saturation_steps(pkg: PackagingOperator) -> dict[str, int]:
    if pkg.family != "state_map":
        raise ValueError("state_saturation_steps is only valid for state_map packaging")
    assert pkg.mapping is not None
    out: dict[str, int] = {}
    n = len(pkg.states)
    for s in pkg.states:
        cur = s
        for step in range(n + 1):
            nxt = pkg.mapping[cur]
            if nxt == cur:
                out[s] = step
                break
            cur = nxt
        else:
            raise ValueError(f"state {s!r} does not saturate to a fixed point")
    return out


def max_state_saturation_step(pkg: PackagingOperator) -> int:
    steps = state_saturation_steps(pkg)
    return max(steps.values()) if steps else 0
