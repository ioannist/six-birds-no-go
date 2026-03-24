"""Exact closure-deficit and best macro-law utilities."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

from sixbirds_nogo.coarse import (
    DeterministicLens,
    pushforward_distribution_through_lens,
)
from sixbirds_nogo.markov import (
    FiniteMarkovChain,
    parse_probability_vector,
    pushforward_distribution,
)


@dataclass(frozen=True)
class GroupedKLValue:
    kind: str
    support_mismatch_count: int
    log_terms: tuple[tuple[Fraction, Fraction], ...]
    decimal_value: Decimal | None
    precision: int


def _fraction_to_decimal(frac: Fraction, precision: int) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = precision
        return Decimal(frac.numerator) / Decimal(frac.denominator)


def _evaluate_log_terms(log_terms: tuple[tuple[Fraction, Fraction], ...], precision: int) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = precision
        out = Decimal(0)
        for ratio, coeff in log_terms:
            out += _fraction_to_decimal(coeff, precision) * _fraction_to_decimal(ratio, precision).ln()
        return +out


def _build_grouped_kl(grouped: dict[Fraction, Fraction], mismatches: int, precision: int) -> GroupedKLValue:
    if mismatches > 0:
        return GroupedKLValue(
            kind="infinite",
            support_mismatch_count=mismatches,
            log_terms=(),
            decimal_value=None,
            precision=precision,
        )
    terms = tuple(sorted(((r, c) for r, c in grouped.items() if r != 1 and c != 0), key=lambda x: (x[0], x[1])))
    if not terms:
        return GroupedKLValue(
            kind="zero",
            support_mismatch_count=0,
            log_terms=(),
            decimal_value=Decimal(0),
            precision=precision,
        )
    return GroupedKLValue(
        kind="finite_positive",
        support_mismatch_count=0,
        log_terms=terms,
        decimal_value=_evaluate_log_terms(terms, precision=precision),
        precision=precision,
    )


def grouped_kl_equal(a: GroupedKLValue, b: GroupedKLValue) -> bool:
    return (
        a.kind == b.kind
        and a.support_mismatch_count == b.support_mismatch_count
        and a.log_terms == b.log_terms
    )


def _resolve_initial(chain: FiniteMarkovChain, initial_dist: Any) -> tuple[Fraction, ...]:
    if initial_dist is None:
        if chain.stationary_distribution is None:
            raise ValueError("initial_dist is required when chain has no stationary_distribution")
        return chain.stationary_distribution
    parsed = parse_probability_vector(initial_dist)
    if len(parsed) != chain.size:
        raise ValueError("initial_dist dimension mismatch")
    return parsed


def _delta(n: int, i: int) -> tuple[Fraction, ...]:
    return tuple(Fraction(1, 1) if j == i else Fraction(0, 1) for j in range(n))


def packaged_future_distribution(chain: FiniteMarkovChain, lens: DeterministicLens, state: str, tau: int) -> tuple[Fraction, ...]:
    """Compute p_x^(tau) = Pr(Y_{t+tau} | X_t = x)."""
    if tau < 0:
        raise ValueError("tau must be nonnegative")
    if lens.domain_states != chain.states:
        raise ValueError("lens.domain_states must match chain.states exactly")
    i = chain.index_of(state)
    mu0 = _delta(chain.size, i)
    mu_tau = pushforward_distribution(mu0, chain.matrix, steps=tau)
    return pushforward_distribution_through_lens(mu_tau, lens)


def packaged_future_laws(chain: FiniteMarkovChain, lens: DeterministicLens, tau: int) -> dict[str, tuple[Fraction, ...]]:
    """Compute packaged future laws for every microstate."""
    return {x: packaged_future_distribution(chain, lens, x, tau) for x in chain.states}


def current_macro_distribution(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    initial_dist: Any = None,
) -> tuple[Fraction, ...]:
    """Compute mu_Y at current time."""
    mu = _resolve_initial(chain, initial_dist)
    return pushforward_distribution_through_lens(mu, lens)


def macro_pair_joint_law(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    tau: int,
    initial_dist: Any = None,
) -> dict[tuple[str, str], Fraction]:
    """Exact joint law Pr(Y_t, Y_{t+tau})."""
    mu = _resolve_initial(chain, initial_dist)
    p_laws = packaged_future_laws(chain, lens, tau)

    out: dict[tuple[str, str], Fraction] = {}
    for i, x in enumerate(chain.states):
        y = lens.mapping[x]
        for j, yp in enumerate(lens.image_states):
            contrib = mu[i] * p_laws[x][j]
            key = (y, yp)
            out[key] = out.get(key, Fraction(0, 1)) + contrib
    return out


def best_macro_kernel(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    tau: int,
    initial_dist: Any = None,
) -> FiniteMarkovChain:
    """Compute closed-form K* from current macro distribution and pair joint law."""
    mu_y = current_macro_distribution(chain, lens, initial_dist=initial_dist)
    joint = macro_pair_joint_law(chain, lens, tau, initial_dist=initial_dist)

    rows: list[tuple[Fraction, ...]] = []
    for i, y in enumerate(lens.image_states):
        denom = mu_y[i]
        if denom == 0:
            row = tuple(Fraction(1, 1) if j == i else Fraction(0, 1) for j in range(len(lens.image_states)))
        else:
            row_vals = [joint.get((y, yp), Fraction(0, 1)) / denom for yp in lens.image_states]
            row = tuple(row_vals)
        rows.append(row)

    kernel = FiniteMarkovChain(states=lens.image_states, matrix=tuple(rows), stationary_distribution=None)
    stationary = mu_y if all(pushforward_distribution(mu_y, kernel.matrix, 1)[i] == mu_y[i] for i in range(len(mu_y))) else None
    return FiniteMarkovChain(states=lens.image_states, matrix=kernel.matrix, stationary_distribution=stationary)


def _validate_candidate(candidate_macro_chain: FiniteMarkovChain, lens: DeterministicLens) -> None:
    if candidate_macro_chain.states != lens.image_states:
        raise ValueError("candidate macro chain states must match lens.image_states exactly")


def variational_objective(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    candidate_macro_chain: FiniteMarkovChain,
    tau: int,
    initial_dist: Any = None,
    precision: int = 80,
) -> GroupedKLValue:
    """Compute V_tau(K) = sum_x mu(x) KL(p_x^(tau) || K_{Pi(x)})."""
    if lens.domain_states != chain.states:
        raise ValueError("lens.domain_states must match chain.states exactly")
    _validate_candidate(candidate_macro_chain, lens)

    mu = _resolve_initial(chain, initial_dist)
    p_laws = packaged_future_laws(chain, lens, tau)
    row_idx = lens.image_to_index

    grouped: dict[Fraction, Fraction] = {}
    mismatches = 0

    for i, x in enumerate(chain.states):
        row = candidate_macro_chain.matrix[row_idx[lens.mapping[x]]]
        p_x = p_laws[x]
        for j, p in enumerate(p_x):
            if p == 0:
                continue
            q = row[j]
            if q == 0:
                mismatches += 1
                continue
            ratio = p / q
            coeff = mu[i] * p
            grouped[ratio] = grouped.get(ratio, Fraction(0, 1)) + coeff

    return _build_grouped_kl(grouped, mismatches, precision)


def closure_deficit(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    tau: int,
    initial_dist: Any = None,
    precision: int = 80,
) -> GroupedKLValue:
    """Compute CD_tau(Pi) = I(X_t ; Y_{t+tau} | Y_t) via conditional-information route."""
    if lens.domain_states != chain.states:
        raise ValueError("lens.domain_states must match chain.states exactly")

    mu = _resolve_initial(chain, initial_dist)
    p_laws = packaged_future_laws(chain, lens, tau)
    mu_y = current_macro_distribution(chain, lens, initial_dist=initial_dist)

    cond: dict[tuple[str, str], Fraction] = {}
    joint = macro_pair_joint_law(chain, lens, tau, initial_dist=initial_dist)
    for i, y in enumerate(lens.image_states):
        denom = mu_y[i]
        for yp in lens.image_states:
            if denom == 0:
                cond[(y, yp)] = Fraction(1, 1) if yp == y else Fraction(0, 1)
            else:
                cond[(y, yp)] = joint.get((y, yp), Fraction(0, 1)) / denom

    grouped: dict[Fraction, Fraction] = {}
    mismatches = 0

    for i, x in enumerate(chain.states):
        y = lens.mapping[x]
        p_x = p_laws[x]
        for j, yp in enumerate(lens.image_states):
            p = p_x[j]
            if p == 0:
                continue
            q = cond[(y, yp)]
            if q == 0:
                mismatches += 1
                continue
            ratio = p / q
            coeff = mu[i] * p
            grouped[ratio] = grouped.get(ratio, Fraction(0, 1)) + coeff

    return _build_grouped_kl(grouped, mismatches, precision)


def best_macro_gap(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    tau: int,
    initial_dist: Any = None,
    precision: int = 80,
) -> GroupedKLValue:
    """Variational minimum objective at analytic best macro kernel K*."""
    k_star = best_macro_kernel(chain, lens, tau, initial_dist=initial_dist)
    return variational_objective(chain, lens, k_star, tau, initial_dist=initial_dist, precision=precision)


def _row_to_strings(row: tuple[Fraction, ...]) -> list[str]:
    return [f"{x.numerator}/{x.denominator}" for x in row]


def _kernel_to_strings(kernel: FiniteMarkovChain) -> list[list[str]]:
    return [_row_to_strings(row) for row in kernel.matrix]


def _grouped_to_serializable(v: GroupedKLValue) -> dict[str, Any]:
    return {
        "kind": v.kind,
        "support_mismatch_count": v.support_mismatch_count,
        "log_terms": [
            {
                "ratio": f"{ratio.numerator}/{ratio.denominator}",
                "coeff": f"{coeff.numerator}/{coeff.denominator}",
            }
            for ratio, coeff in v.log_terms
        ],
        "decimal_value": None if v.decimal_value is None else str(v.decimal_value),
        "precision": v.precision,
    }


def grid_search_two_state_macro_kernels(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    tau: int,
    denominator: int = 12,
    initial_dist: Any = None,
    precision: int = 80,
) -> dict[str, Any]:
    """Brute-force denominator grid search over 2-state macro kernels."""
    if len(lens.image_states) != 2:
        raise ValueError("grid search currently supports only 2-state macro spaces")
    if denominator <= 0:
        raise ValueError("denominator must be positive")

    analytic_k = best_macro_kernel(chain, lens, tau, initial_dist=initial_dist)
    analytic_gap = variational_objective(chain, lens, analytic_k, tau, initial_dist=initial_dist, precision=precision)

    total = (denominator + 1) ** 2
    finite_count = 0
    infinite_count = 0

    best_terms: GroupedKLValue | None = None
    best_kernels: list[FiniteMarkovChain] = []
    tol = Decimal(1) / (Decimal(10) ** max(10, precision // 2))

    def rank(v: GroupedKLValue) -> int:
        if v.kind == "zero":
            return 0
        if v.kind == "finite_positive":
            return 1
        return 2

    def is_strictly_better(a: GroupedKLValue, b: GroupedKLValue) -> bool:
        ra, rb = rank(a), rank(b)
        if ra != rb:
            return ra < rb
        if ra == 0:
            return False
        if ra == 2:
            return False
        assert a.decimal_value is not None and b.decimal_value is not None
        with localcontext() as ctx:
            ctx.prec = max(precision, 80) + 20
            return a.decimal_value + tol < b.decimal_value

    def is_tie(a: GroupedKLValue, b: GroupedKLValue) -> bool:
        if rank(a) != rank(b):
            return False
        if rank(a) in (0, 2):
            return True
        assert a.decimal_value is not None and b.decimal_value is not None
        with localcontext() as ctx:
            ctx.prec = max(precision, 80) + 20
            return abs(a.decimal_value - b.decimal_value) <= tol

    for a in range(denominator + 1):
        r0 = (Fraction(a, denominator), Fraction(denominator - a, denominator))
        for b in range(denominator + 1):
            r1 = (Fraction(b, denominator), Fraction(denominator - b, denominator))
            cand = FiniteMarkovChain(states=lens.image_states, matrix=(r0, r1), stationary_distribution=None)
            val = variational_objective(chain, lens, cand, tau, initial_dist=initial_dist, precision=precision)
            if val.kind == "infinite":
                infinite_count += 1
                continue
            finite_count += 1
            if best_terms is None:
                best_terms = val
                best_kernels = [cand]
                continue

            if is_strictly_better(val, best_terms):
                best_terms = val
                best_kernels = [cand]
            elif is_tie(val, best_terms):
                best_kernels.append(cand)

    if best_terms is None:
        best_terms = GroupedKLValue("infinite", support_mismatch_count=1, log_terms=(), decimal_value=None, precision=precision)
        best_kernels = []

    analytic_in_minima = any(k.matrix == analytic_k.matrix for k in best_kernels)

    return {
        "denominator": denominator,
        "total_candidate_count": total,
        "finite_candidate_count": finite_count,
        "infinite_candidate_count": infinite_count,
        "analytic_best_kernel": _kernel_to_strings(analytic_k),
        "analytic_best_gap": _grouped_to_serializable(analytic_gap),
        "grid_best_kernels": [_kernel_to_strings(k) for k in best_kernels],
        "grid_best_gap": _grouped_to_serializable(best_terms),
        "analytic_best_in_grid_minima": analytic_in_minima,
    }
