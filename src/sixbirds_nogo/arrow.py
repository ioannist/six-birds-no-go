"""Exact path-space arrow and DPI utilities.

Path-law construction and classification are exact over Fractions.
Finite KL numeric values are evaluated with high-precision Decimal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

from sixbirds_nogo.coarse import DeterministicLens, enumerate_observed_path_law
from sixbirds_nogo.markov import FiniteMarkovChain, load_chain_from_witness
from sixbirds_nogo.pathspace import enumerate_path_law


@dataclass(frozen=True)
class PathKLDivergence:
    kind: str
    exact_equal: bool
    support_mismatch_count: int
    log_terms: tuple[tuple[Fraction, Fraction], ...]
    decimal_value: Decimal | None
    precision: int


def reverse_path(path: tuple[Any, ...] | list[Any]) -> tuple[Any, ...]:
    """Return reversed path tuple."""
    return tuple(reversed(tuple(path)))


def _normalize_path_law(path_law: dict[tuple[Any, ...], Fraction]) -> dict[tuple[Any, ...], Fraction]:
    out: dict[tuple[Any, ...], Fraction] = {}
    for path, mass in path_law.items():
        if mass == 0:
            continue
        if not isinstance(mass, Fraction):
            raise ValueError("path-law masses must be Fraction")
        out[path] = out.get(path, Fraction(0, 1)) + mass
    return {k: v for k, v in out.items() if v != 0}


def reverse_path_law(path_law: dict[tuple[Any, ...], Fraction]) -> dict[tuple[Any, ...], Fraction]:
    """Reverse a path law by pushing mass to reversed paths."""
    norm = _normalize_path_law(path_law)
    out: dict[tuple[Any, ...], Fraction] = {}
    for path, mass in norm.items():
        rp = reverse_path(path)
        out[rp] = out.get(rp, Fraction(0, 1)) + mass
    return out


def fraction_to_decimal(frac: Fraction, precision: int) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = precision
        return Decimal(frac.numerator) / Decimal(frac.denominator)


def evaluate_log_terms(log_terms: tuple[tuple[Fraction, Fraction], ...], precision: int = 80) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = precision
        total = Decimal(0)
        for ratio, coeff in log_terms:
            ratio_d = fraction_to_decimal(ratio, precision)
            coeff_d = fraction_to_decimal(coeff, precision)
            total += coeff_d * ratio_d.ln()
        return +total


def path_kl_divergence(
    path_law_p: dict[tuple[Any, ...], Fraction],
    path_law_q: dict[tuple[Any, ...], Fraction],
    precision: int = 80,
) -> PathKLDivergence:
    """Compute KL(P||Q) regime exactly and evaluate finite case with Decimal."""
    p = _normalize_path_law(path_law_p)
    q = _normalize_path_law(path_law_q)

    if p == q:
        return PathKLDivergence(
            kind="zero",
            exact_equal=True,
            support_mismatch_count=0,
            log_terms=(),
            decimal_value=Decimal(0),
            precision=precision,
        )

    mismatch = 0
    for path, mass in p.items():
        if mass > 0 and q.get(path, Fraction(0, 1)) == 0:
            mismatch += 1

    if mismatch > 0:
        return PathKLDivergence(
            kind="infinite",
            exact_equal=False,
            support_mismatch_count=mismatch,
            log_terms=(),
            decimal_value=None,
            precision=precision,
        )

    grouped: dict[Fraction, Fraction] = {}
    for path, p_mass in p.items():
        q_mass = q.get(path, Fraction(0, 1))
        ratio = p_mass / q_mass
        if ratio == 1:
            continue
        grouped[ratio] = grouped.get(ratio, Fraction(0, 1)) + p_mass

    log_terms = tuple(sorted(grouped.items(), key=lambda x: (x[0], x[1])))

    dec = evaluate_log_terms(log_terms, precision=precision) if log_terms else Decimal(0)
    kind = "zero" if log_terms == () else "finite_positive"

    return PathKLDivergence(
        kind=kind,
        exact_equal=False if kind != "zero" else True,
        support_mismatch_count=0,
        log_terms=log_terms,
        decimal_value=dec,
        precision=precision,
    )


def path_reversal_kl_from_law(path_law: dict[tuple[Any, ...], Fraction], precision: int = 80) -> PathKLDivergence:
    """Compute KL(path_law || reversed(path_law))."""
    rev = reverse_path_law(path_law)
    return path_kl_divergence(path_law, rev, precision=precision)


def micro_path_reversal_kl(
    chain: FiniteMarkovChain,
    horizon: int,
    initial_dist: Any = None,
    precision: int = 80,
) -> PathKLDivergence:
    """Micro path reversal KL at given horizon."""
    law = enumerate_path_law(chain, horizon, initial_dist=initial_dist)
    return path_reversal_kl_from_law(law, precision=precision)


def honest_observed_path_reversal_kl(
    chain: FiniteMarkovChain,
    lens: DeterministicLens,
    horizon: int,
    initial_dist: Any = None,
    precision: int = 80,
) -> PathKLDivergence:
    """Honest observed path reversal KL via exact observed path law."""
    law = enumerate_observed_path_law(chain, lens, horizon, initial_dist=initial_dist)
    return path_reversal_kl_from_law(law, precision=precision)


def dpi_status(micro_kl: PathKLDivergence, macro_kl: PathKLDivergence, precision: int = 80) -> dict[str, Any]:
    """Determine DPI hold/equality/strict-loss status from KL summaries."""
    with localcontext() as ctx:
        ctx.prec = max(precision, 80) + 20
        tol = Decimal(1) / (Decimal(10) ** max(10, precision // 2))

        if micro_kl.kind == "infinite":
            holds = True
            equal_value = macro_kl.kind == "infinite"
            strict_loss = macro_kl.kind != "infinite"
        elif macro_kl.kind == "infinite":
            holds = False
            equal_value = False
            strict_loss = False
        else:
            m = micro_kl.decimal_value if micro_kl.decimal_value is not None else Decimal(0)
            g = macro_kl.decimal_value if macro_kl.decimal_value is not None else Decimal(0)
            holds = g <= m + tol
            equal_value = abs(m - g) <= tol
            strict_loss = holds and (g + tol < m)

    return {
        "holds": holds,
        "equal_value": equal_value,
        "strict_loss": strict_loss,
        "micro_kind": micro_kl.kind,
        "macro_kind": macro_kl.kind,
    }


def _serialize_kl(kl: PathKLDivergence) -> dict[str, Any]:
    return {
        "kind": kl.kind,
        "exact_equal": kl.exact_equal,
        "support_mismatch_count": kl.support_mismatch_count,
        "log_terms": [
            {"ratio": f"{ratio.numerator}/{ratio.denominator}", "coeff": f"{coeff.numerator}/{coeff.denominator}"}
            for ratio, coeff in kl.log_terms
        ],
        "decimal_value": None if kl.decimal_value is None else str(kl.decimal_value),
        "precision": kl.precision,
    }


def horizon_sweep_arrow(case_specs: list[dict[str, Any]], precision: int = 80) -> list[dict[str, Any]]:
    """Deterministic sweep over (witness,lens,horizon) case specs."""
    rows: list[dict[str, Any]] = []
    for case in case_specs:
        witness_id = case["witness_id"]
        lens_id = case["lens_id"]
        horizons = tuple(case.get("horizons", (0, 1, 2, 3)))
        initial_mode = case.get("initial_mode", "stationary_if_available")

        chain = load_chain_from_witness(witness_id)
        from sixbirds_nogo.coarse import load_lens_from_witness  # local import to keep module dependencies minimal

        lens = load_lens_from_witness(witness_id, lens_id)

        if initial_mode == "stationary_if_available" and chain.stationary_distribution is not None:
            init = chain.stationary_distribution
            resolved_init_mode = "stationary"
        else:
            init = case.get("initial_dist")
            resolved_init_mode = "explicit"

        for horizon in horizons:
            micro = micro_path_reversal_kl(chain, horizon, initial_dist=init, precision=precision)
            macro = honest_observed_path_reversal_kl(chain, lens, horizon, initial_dist=init, precision=precision)
            dpi = dpi_status(micro, macro, precision=precision)

            rows.append(
                {
                    "witness_id": witness_id,
                    "lens_id": lens_id,
                    "horizon": int(horizon),
                    "initial_mode": resolved_init_mode,
                    "micro": _serialize_kl(micro),
                    "macro": _serialize_kl(macro),
                    "dpi": dpi,
                    "precision": precision,
                }
            )

    rows.sort(key=lambda r: (r["witness_id"], r["lens_id"], r["horizon"]))
    return rows


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
