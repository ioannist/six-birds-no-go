"""Exact finite-state Markov utilities using Fraction arithmetic."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from sixbirds_nogo.witnesses import load_witness, load_witness_registry


Matrix = tuple[tuple[Fraction, ...], ...]
Vector = tuple[Fraction, ...]


def parse_probability(value: Any) -> Fraction:
    """Parse a probability value as an exact Fraction."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise ValueError("boolean is not a probability")
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty probability string")
        if "." in text:
            raise ValueError(f"decimal literals are not allowed: {value!r}")
        return Fraction(text)
    raise ValueError(f"unsupported probability type: {type(value).__name__}")


def parse_probability_vector(values: Any) -> Vector:
    """Parse a vector of exact probabilities."""
    if not isinstance(values, (list, tuple)):
        raise ValueError("probability vector must be a sequence")
    return tuple(parse_probability(v) for v in values)


def parse_probability_matrix(rows: Any) -> Matrix:
    """Parse a matrix of exact probabilities."""
    if not isinstance(rows, (list, tuple)):
        raise ValueError("probability matrix must be a sequence of rows")
    parsed_rows: list[tuple[Fraction, ...]] = []
    for row in rows:
        if not isinstance(row, (list, tuple)):
            raise ValueError("matrix row must be a sequence")
        parsed_rows.append(tuple(parse_probability(v) for v in row))
    return tuple(parsed_rows)


def validate_distribution(dist: Any) -> None:
    """Validate a distribution as exact nonnegative Fractions summing to 1."""
    if not isinstance(dist, (tuple, list)) or not dist:
        raise ValueError("distribution must be a non-empty sequence")
    if not all(isinstance(x, Fraction) for x in dist):
        raise ValueError("distribution entries must be Fraction values")
    if any(x < 0 for x in dist):
        raise ValueError("distribution entries must be nonnegative")
    if sum(dist, Fraction(0, 1)) != Fraction(1, 1):
        raise ValueError("distribution must sum to exactly 1")


def validate_row_stochastic(matrix: Any) -> None:
    """Validate square row-stochastic matrix over Fractions."""
    if not isinstance(matrix, (tuple, list)) or not matrix:
        raise ValueError("matrix must be a non-empty sequence")
    n = len(matrix)
    for i, row in enumerate(matrix):
        if not isinstance(row, (tuple, list)):
            raise ValueError(f"row {i} must be a sequence")
        if len(row) != n:
            raise ValueError("matrix must be square")
        if not all(isinstance(x, Fraction) for x in row):
            raise ValueError(f"row {i} must contain Fraction entries")
        if any(x < 0 for x in row):
            raise ValueError(f"row {i} has negative entries")
        if sum(row, Fraction(0, 1)) != Fraction(1, 1):
            raise ValueError(f"row {i} does not sum to 1")


def _identity(n: int) -> Matrix:
    return tuple(
        tuple(Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n))
        for i in range(n)
    )


def _matrix_multiply(a: Matrix, b: Matrix) -> Matrix:
    n = len(a)
    out: list[tuple[Fraction, ...]] = []
    for i in range(n):
        row: list[Fraction] = []
        for j in range(n):
            val = Fraction(0, 1)
            for k in range(n):
                val += a[i][k] * b[k][j]
            row.append(val)
        out.append(tuple(row))
    return tuple(out)


def matrix_power(matrix: Matrix, n: int) -> Matrix:
    """Compute exact matrix power with exponentiation by squaring."""
    validate_row_stochastic(matrix)
    if n < 0:
        raise ValueError("n must be nonnegative")
    size = len(matrix)
    result = _identity(size)
    base = matrix
    exp = n
    while exp > 0:
        if exp % 2 == 1:
            result = _matrix_multiply(result, base)
        base = _matrix_multiply(base, base)
        exp //= 2
    return result


def pushforward_distribution(dist: Vector, matrix: Matrix, steps: int = 1) -> Vector:
    """Push a row distribution through a chain for a given number of steps."""
    if steps < 0:
        raise ValueError("steps must be nonnegative")
    validate_distribution(dist)
    validate_row_stochastic(matrix)
    if len(dist) != len(matrix):
        raise ValueError("distribution dimension does not match matrix")

    current = tuple(dist)
    for _ in range(steps):
        next_row: list[Fraction] = []
        for j in range(len(matrix)):
            val = Fraction(0, 1)
            for i in range(len(matrix)):
                val += current[i] * matrix[i][j]
            next_row.append(val)
        current = tuple(next_row)
    return current


def _solve_linear_system(a: list[list[Fraction]], b: list[Fraction]) -> list[Fraction]:
    n = len(a)
    aug = [row[:] + [bval] for row, bval in zip(a, b)]
    pivot_row = 0
    for col in range(n):
        sel = None
        for r in range(pivot_row, n):
            if aug[r][col] != 0:
                sel = r
                break
        if sel is None:
            continue
        if sel != pivot_row:
            aug[pivot_row], aug[sel] = aug[sel], aug[pivot_row]

        pivot = aug[pivot_row][col]
        aug[pivot_row] = [x / pivot for x in aug[pivot_row]]

        for r in range(n):
            if r == pivot_row:
                continue
            factor = aug[r][col]
            if factor == 0:
                continue
            aug[r] = [x - factor * y for x, y in zip(aug[r], aug[pivot_row])]

        pivot_row += 1
        if pivot_row == n:
            break

    for r in range(n):
        if all(aug[r][c] == 0 for c in range(n)) and aug[r][n] != 0:
            raise ValueError("linear system is inconsistent")

    solution = [Fraction(0, 1) for _ in range(n)]
    for r in range(n):
        lead = None
        for c in range(n):
            if aug[r][c] != 0:
                lead = c
                break
        if lead is not None:
            solution[lead] = aug[r][n]

    if any(aug[r][c] != (Fraction(1, 1) if c == r else Fraction(0, 1)) for r in range(n) for c in range(n)):
        # Under-determined or non-unique systems are intentionally unsupported.
        raise ValueError("stationary system is underdetermined or non-unique")

    return solution


@dataclass(frozen=True)
class FiniteMarkovChain:
    """Finite-state Markov chain with exact transition probabilities."""

    states: tuple[str, ...]
    matrix: Matrix
    stationary_distribution: Vector | None = None
    state_to_index: dict[str, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.states or len(set(self.states)) != len(self.states):
            raise ValueError("states must be non-empty and unique")
        validate_row_stochastic(self.matrix)
        if len(self.matrix) != len(self.states):
            raise ValueError("matrix dimension must match number of states")

        mapping = {s: i for i, s in enumerate(self.states)}
        object.__setattr__(self, "state_to_index", mapping)

        if self.stationary_distribution is not None:
            validate_distribution(self.stationary_distribution)
            if len(self.stationary_distribution) != len(self.states):
                raise ValueError("stationary distribution dimension mismatch")

    @property
    def size(self) -> int:
        return len(self.states)

    def index_of(self, state: str) -> int:
        try:
            return self.state_to_index[state]
        except KeyError as exc:
            raise KeyError(f"unknown state: {state}") from exc


def solve_stationary_distribution(chain: FiniteMarkovChain) -> Vector:
    """Solve pi P = pi with sum(pi)=1 via exact Gaussian elimination."""
    n = chain.size
    p = chain.matrix

    a: list[list[Fraction]] = []
    b: list[Fraction] = []
    for i in range(n - 1):
        row = []
        for j in range(n):
            coeff = p[j][i] - (Fraction(1, 1) if i == j else Fraction(0, 1))
            row.append(coeff)
        a.append(row)
        b.append(Fraction(0, 1))

    a.append([Fraction(1, 1) for _ in range(n)])
    b.append(Fraction(1, 1))

    sol = tuple(_solve_linear_system(a, b))
    validate_distribution(sol)
    return sol


def is_stationary_distribution(chain: FiniteMarkovChain, dist: Any) -> bool:
    """Check exact stationarity under one-step pushforward."""
    parsed = parse_probability_vector(dist)
    validate_distribution(parsed)
    if len(parsed) != chain.size:
        return False
    return pushforward_distribution(parsed, chain.matrix, steps=1) == parsed


def list_chain_witness_ids(config_path: str = "configs/witnesses.yaml") -> list[str]:
    """List witness IDs that define Markov dynamics."""
    data = load_witness_registry(config_path)
    witnesses = data.get("witnesses")
    if not isinstance(witnesses, list):
        raise ValueError("witnesses must be a list")

    out: list[str] = []
    for item in witnesses:
        if not isinstance(item, dict):
            continue
        wid = item.get("id")
        kind = item.get("kind")
        if isinstance(wid, str) and kind in {"markov_chain", "phase_lift_markov"}:
            out.append(wid)
    return out


def load_chain_from_witness(witness_id: str, config_path: str = "configs/witnesses.yaml") -> FiniteMarkovChain:
    """Load a chain witness into a validated FiniteMarkovChain."""
    witness = load_witness(witness_id, config_path=config_path).raw
    kind = witness.get("kind")
    if kind not in {"markov_chain", "phase_lift_markov"}:
        raise ValueError(f"witness {witness_id!r} has unsupported kind: {kind!r}")

    space = witness.get("microstate_space")
    if not isinstance(space, dict):
        raise ValueError(f"witness {witness_id!r} missing microstate_space")
    states = space.get("states")
    if not isinstance(states, list) or not states or not all(isinstance(s, str) for s in states):
        raise ValueError(f"witness {witness_id!r} has invalid states list")
    if len(set(states)) != len(states):
        raise ValueError(f"witness {witness_id!r} states must be unique")

    dynamics = witness.get("dynamics")
    if not isinstance(dynamics, dict):
        raise ValueError(f"witness {witness_id!r} missing dynamics")
    if dynamics.get("family") != "discrete_markov":
        raise ValueError(f"witness {witness_id!r} dynamics.family must be discrete_markov")

    row_states = dynamics.get("row_states")
    if not isinstance(row_states, list) or not all(isinstance(s, str) for s in row_states):
        raise ValueError(f"witness {witness_id!r} has invalid row_states")
    if set(row_states) != set(states):
        raise ValueError(f"witness {witness_id!r} row_states must match states")

    raw_matrix = parse_probability_matrix(dynamics.get("matrix"))
    if len(raw_matrix) != len(row_states) or any(len(r) != len(row_states) for r in raw_matrix):
        raise ValueError(f"witness {witness_id!r} has invalid transition matrix shape")

    row_idx = {s: i for i, s in enumerate(row_states)}
    matrix_rows: list[tuple[Fraction, ...]] = []
    for s_i in states:
        src_row = raw_matrix[row_idx[s_i]]
        reordered = tuple(src_row[row_idx[s_j]] for s_j in states)
        matrix_rows.append(reordered)
    matrix = tuple(matrix_rows)
    validate_row_stochastic(matrix)

    stationary_raw = dynamics.get("stationary_distribution")
    stationary: Vector | None = None
    if stationary_raw is not None:
        parsed = parse_probability_vector(stationary_raw)
        if len(parsed) != len(row_states):
            raise ValueError(f"witness {witness_id!r} stationary_distribution size mismatch")
        stationary = tuple(parsed[row_idx[s]] for s in states)
        validate_distribution(stationary)

    return FiniteMarkovChain(states=tuple(states), matrix=matrix, stationary_distribution=stationary)
