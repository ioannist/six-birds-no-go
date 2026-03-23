"""Registry-driven executable witness layer for honest theorem-level audits."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

from sixbirds_nogo.affinity import is_exact_oneform, max_cycle_affinity
from sixbirds_nogo.arrow import honest_observed_path_reversal_kl, micro_path_reversal_kl
from sixbirds_nogo.closure_deficit import GroupedKLValue, best_macro_gap, closure_deficit
from sixbirds_nogo.coarse import DeterministicLens, make_lens
from sixbirds_nogo.definability import definable_predicate_count
from sixbirds_nogo.graph_cycle import cycle_rank
from sixbirds_nogo.markov import FiniteMarkovChain, load_chain_from_witness
from sixbirds_nogo.objecthood import dobrushin_contraction_lambda, epsilon_stable_distributions, fixed_point_count
from sixbirds_nogo.packaging import PackagingOperator, idempotence_defect, load_packaging_from_witness
from sixbirds_nogo.witnesses import load_witness, load_witness_registry, list_witness_ids


@dataclass(frozen=True)
class ExecutableWitness:
    id: str
    kind: str
    states: tuple[str, ...]
    raw_witness: dict[str, Any]
    chain: FiniteMarkovChain | None
    lenses: dict[str, DeterministicLens]
    packaging: PackagingOperator | None
    theorem_targets: tuple[str, ...]
    expected_audits: tuple[dict[str, Any], ...]
    expected_theorem_roles: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class AuditExecutionResult:
    audit_id: str
    context: dict[str, Any] | None
    status: str
    actual: Any
    comparable_value: Any
    expected_relation: str | None
    expected_value: Any
    expectation_satisfied: bool | None
    error: str | None


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_numeric_string(s: str) -> Any:
    t = s.strip()
    if t.lower() == "true":
        return True
    if t.lower() == "false":
        return False
    if "/" in t:
        a, b = t.split("/", 1)
        return Fraction(int(a), int(b))
    if t.lstrip("-").isdigit():
        return Fraction(int(t), 1)
    return t


def _fraction_to_decimal(fr: Fraction, precision: int = 80) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = precision
        return Decimal(fr.numerator) / Decimal(fr.denominator)


def _serialize_fraction(fr: Fraction) -> str:
    return f"{fr.numerator}/{fr.denominator}"


def _serialize_any(value: Any) -> Any:
    if isinstance(value, Fraction):
        return _serialize_fraction(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [_serialize_any(v) for v in value]
    if isinstance(value, list):
        return [_serialize_any(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize_any(v) for k, v in value.items()}
    if isinstance(value, PathKLDivergence):
        return {
            "kind": value.kind,
            "support_mismatch_count": value.support_mismatch_count,
            "log_terms": [
                {"ratio": _serialize_fraction(r), "coeff": _serialize_fraction(c)} for r, c in value.log_terms
            ],
            "decimal_value": None if value.decimal_value is None else str(value.decimal_value),
            "precision": value.precision,
        }
    if isinstance(value, GroupedKLValue):
        return {
            "kind": value.kind,
            "support_mismatch_count": value.support_mismatch_count,
            "log_terms": [
                {"ratio": _serialize_fraction(r), "coeff": _serialize_fraction(c)} for r, c in value.log_terms
            ],
            "decimal_value": None if value.decimal_value is None else str(value.decimal_value),
            "precision": value.precision,
        }
    return value


# Deferred import to avoid circular type check issues.
from sixbirds_nogo.arrow import PathKLDivergence  # noqa: E402


def _comparable_from_actual(actual: Any) -> Any:
    if isinstance(actual, Fraction):
        return actual
    if isinstance(actual, bool):
        return actual
    if isinstance(actual, int):
        return actual
    if isinstance(actual, PathKLDivergence):
        if actual.kind == "zero":
            return Fraction(0, 1)
        if actual.kind == "infinite":
            return Decimal("Infinity")
        return actual.decimal_value
    if isinstance(actual, GroupedKLValue):
        if actual.kind == "zero":
            return Fraction(0, 1)
        if actual.kind == "infinite":
            return Decimal("Infinity")
        return actual.decimal_value
    return actual


def _parse_expected_value(v: Any) -> Any:
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return Fraction(v, 1)
    if isinstance(v, str):
        return _parse_numeric_string(v)
    return v


def _compare_relation(actual: Any, expected: Any, relation: str, precision: int = 80) -> bool:
    if relation not in {"eq", "gt", "ge", "lt", "le"}:
        return False

    if isinstance(actual, bool) or isinstance(expected, bool):
        if relation != "eq":
            return False
        return bool(actual) is bool(expected)

    if isinstance(actual, Decimal) or isinstance(expected, Decimal):
        with localcontext() as ctx:
            ctx.prec = precision
            a = actual if isinstance(actual, Decimal) else _fraction_to_decimal(actual if isinstance(actual, Fraction) else Fraction(actual, 1), precision)
            e = expected if isinstance(expected, Decimal) else _fraction_to_decimal(expected if isinstance(expected, Fraction) else Fraction(expected, 1), precision)
    else:
        a = actual if isinstance(actual, Fraction) else Fraction(actual, 1)
        e = expected if isinstance(expected, Fraction) else Fraction(expected, 1)

    if relation == "eq":
        return a == e
    if relation == "gt":
        return a > e
    if relation == "ge":
        return a >= e
    if relation == "lt":
        return a < e
    return a <= e


def build_executable_witness(witness_id: str, config_path: str = "configs/witnesses.yaml") -> ExecutableWitness:
    w = load_witness(witness_id, config_path=config_path).raw
    kind = w.get("kind")

    space = w.get("microstate_space")
    if not isinstance(space, dict) or not isinstance(space.get("states"), list):
        raise ValueError(f"witness {witness_id!r} has invalid microstate_space")
    states = tuple(space["states"])

    chain = None
    if kind in {"markov_chain", "phase_lift_markov"}:
        chain = load_chain_from_witness(witness_id, config_path=config_path)

    lenses: dict[str, DeterministicLens] = {}
    raw_lenses = w.get("lenses")
    if isinstance(raw_lenses, list):
        for entry in raw_lenses:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                lid = entry["id"]
                lenses[lid] = make_lens(states, entry.get("mapping"), lens_id=lid)

    packaging = None
    if w.get("packaging") is not None:
        packaging = load_packaging_from_witness(witness_id, config_path=config_path)

    sig = w.get("expected_signatures") if isinstance(w.get("expected_signatures"), dict) else {}
    exp_audits = tuple(sig.get("audits", [])) if isinstance(sig.get("audits"), list) else ()
    exp_theorems = tuple(sig.get("theorems", [])) if isinstance(sig.get("theorems"), list) else ()

    return ExecutableWitness(
        id=witness_id,
        kind=str(kind),
        states=states,
        raw_witness=w,
        chain=chain,
        lenses=lenses,
        packaging=packaging,
        theorem_targets=tuple(w.get("theorem_targets", [])) if isinstance(w.get("theorem_targets"), list) else (),
        expected_audits=exp_audits,
        expected_theorem_roles=exp_theorems,
    )


def build_all_executable_witnesses(config_path: str = "configs/witnesses.yaml") -> tuple[ExecutableWitness, ...]:
    ids = list_witness_ids(config_path=config_path)
    return tuple(build_executable_witness(wid, config_path=config_path) for wid in ids)


def relevant_honest_audit_requests(executable_witness: ExecutableWitness) -> tuple[dict[str, Any], ...]:
    return tuple(a for a in executable_witness.expected_audits if isinstance(a, dict) and isinstance(a.get("audit_id"), str))


def _require_chain(w: ExecutableWitness, audit_id: str) -> FiniteMarkovChain:
    if w.chain is None:
        raise ValueError(f"{audit_id} requires a chain component")
    return w.chain


def _require_packaging(w: ExecutableWitness, audit_id: str, context: dict[str, Any] | None) -> PackagingOperator:
    if w.packaging is None:
        raise ValueError(f"{audit_id} requires a packaging component")
    if context and "package_id" in context and context["package_id"] != w.packaging.id:
        raise ValueError(f"{audit_id} requested package_id={context['package_id']!r} but witness package is {w.packaging.id!r}")
    return w.packaging


def _require_lens(w: ExecutableWitness, audit_id: str, context: dict[str, Any] | None) -> DeterministicLens:
    if context is None or "lens_id" not in context:
        raise ValueError(f"{audit_id} requires context['lens_id']")
    lens_id = context["lens_id"]
    if lens_id not in w.lenses:
        raise ValueError(f"{audit_id} references unknown lens_id={lens_id!r}")
    return w.lenses[lens_id]


def _ctx_int(context: dict[str, Any] | None, key: str, audit_id: str) -> int:
    if context is None or key not in context:
        raise ValueError(f"{audit_id} requires context[{key!r}]")
    v = context[key]
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.lstrip("-").isdigit():
        return int(v)
    raise ValueError(f"{audit_id} invalid integer context[{key!r}]={v!r}")


def _ctx_fraction(context: dict[str, Any] | None, key: str, audit_id: str) -> Fraction:
    if context is None or key not in context:
        raise ValueError(f"{audit_id} requires context[{key!r}]")
    v = context[key]
    parsed = _parse_expected_value(v)
    if isinstance(parsed, Fraction):
        return parsed
    if isinstance(parsed, int):
        return Fraction(parsed, 1)
    raise ValueError(f"{audit_id} invalid fraction context[{key!r}]={v!r}")


def run_honest_audit(
    executable_witness: ExecutableWitness,
    audit_id: str,
    context: dict[str, Any] | None = None,
    precision: int = 80,
) -> AuditExecutionResult:
    try:
        w = executable_witness
        if audit_id == "AUDIT_CYCLE_RANK":
            actual = cycle_rank(_require_chain(w, audit_id))
        elif audit_id == "AUDIT_MAX_CYCLE_AFFINITY":
            actual = max_cycle_affinity(_require_chain(w, audit_id))
        elif audit_id == "AUDIT_ONEFORM_EXACTNESS":
            actual = is_exact_oneform(_require_chain(w, audit_id))
        elif audit_id == "AUDIT_PATH_KL_MICRO":
            h = _ctx_int(context, "horizon", audit_id)
            actual = micro_path_reversal_kl(_require_chain(w, audit_id), h, precision=precision)
        elif audit_id == "AUDIT_PATH_KL_MACRO_HONEST":
            h = _ctx_int(context, "horizon", audit_id)
            lens = _require_lens(w, audit_id, context)
            actual = honest_observed_path_reversal_kl(_require_chain(w, audit_id), lens, h, precision=precision)
        elif audit_id == "AUDIT_PHASE_LIFT_REVERSIBILITY":
            actual = is_exact_oneform(_require_chain(w, audit_id))
        elif audit_id == "AUDIT_CLOSURE_DEFICIT":
            tau = _ctx_int(context, "tau", audit_id)
            lens = _require_lens(w, audit_id, context)
            actual = closure_deficit(_require_chain(w, audit_id), lens, tau, precision=precision)
        elif audit_id == "AUDIT_BEST_MACRO_GAP":
            tau = _ctx_int(context, "tau", audit_id)
            lens = _require_lens(w, audit_id, context)
            actual = best_macro_gap(_require_chain(w, audit_id), lens, tau, precision=precision)
        elif audit_id == "AUDIT_IDEMPOTENCE_DEFECT":
            actual = idempotence_defect(_require_packaging(w, audit_id, context))
        elif audit_id == "AUDIT_CONTRACTION_LAMBDA":
            actual = dobrushin_contraction_lambda(_require_packaging(w, audit_id, context))
        elif audit_id == "AUDIT_FIXED_POINT_COUNT":
            actual = fixed_point_count(_require_packaging(w, audit_id, context))
        elif audit_id == "AUDIT_DEFINABLE_PREDICATE_COUNT":
            actual = definable_predicate_count(_require_lens(w, audit_id, context))
        elif audit_id == "AUDIT_INTERFACE_SIZE":
            actual = len(_require_lens(w, audit_id, context).image_states)
        elif audit_id == "AUDIT_DPI_GAP":
            # Optional audit: derive micro-minus-macro arrow at context horizon/lens.
            h = _ctx_int(context, "horizon", audit_id)
            lens = _require_lens(w, audit_id, context)
            m = micro_path_reversal_kl(_require_chain(w, audit_id), h, precision=precision)
            g = honest_observed_path_reversal_kl(_require_chain(w, audit_id), lens, h, precision=precision)
            m_cmp = _comparable_from_actual(m)
            g_cmp = _comparable_from_actual(g)
            if isinstance(m_cmp, Decimal) and isinstance(g_cmp, Decimal):
                actual = m_cmp - g_cmp
            elif isinstance(m_cmp, Fraction) and isinstance(g_cmp, Fraction):
                actual = m_cmp - g_cmp
            elif isinstance(m_cmp, Decimal) and isinstance(g_cmp, Fraction):
                actual = m_cmp - _fraction_to_decimal(g_cmp, precision)
            elif isinstance(m_cmp, Fraction) and isinstance(g_cmp, Decimal):
                actual = _fraction_to_decimal(m_cmp, precision) - g_cmp
            else:
                actual = Decimal("Infinity") if m_cmp == Decimal("Infinity") and g_cmp != Decimal("Infinity") else Decimal(0)
        elif audit_id == "AUDIT_EPS_STABLE_COUNT":
            pkg = _require_packaging(w, audit_id, context)
            denom = _ctx_int(context, "denominator", audit_id)
            eps = _ctx_fraction(context, "epsilon", audit_id)
            actual = len(epsilon_stable_distributions(pkg, denominator=denom, epsilon=eps))
        else:
            raise ValueError(f"unsupported audit_id: {audit_id}")

        return AuditExecutionResult(
            audit_id=audit_id,
            context=context,
            status="success",
            actual=actual,
            comparable_value=_comparable_from_actual(actual),
            expected_relation=None,
            expected_value=None,
            expectation_satisfied=None,
            error=None,
        )
    except Exception as exc:
        return AuditExecutionResult(
            audit_id=audit_id,
            context=context,
            status="failed",
            actual=None,
            comparable_value=None,
            expected_relation=None,
            expected_value=None,
            expectation_satisfied=False,
            error=str(exc),
        )


def run_expected_audits(executable_witness: ExecutableWitness, precision: int = 80) -> dict[str, Any]:
    reqs = relevant_honest_audit_requests(executable_witness)
    results: list[AuditExecutionResult] = []
    errors: list[str] = []

    pass_count = 0
    fail_count = 0
    executed = 0

    for req in reqs:
        audit_id = req["audit_id"]
        context = req.get("context") if isinstance(req.get("context"), dict) else None
        relation = req.get("relation") if isinstance(req.get("relation"), str) else None
        expected_raw = req.get("value")

        res = run_honest_audit(executable_witness, audit_id, context=context, precision=precision)

        if res.status == "success":
            executed += 1
            expected = _parse_expected_value(expected_raw)
            comp = res.comparable_value
            satisfied = None
            if relation is not None:
                try:
                    satisfied = _compare_relation(comp, expected, relation, precision=precision)
                except Exception:
                    satisfied = False
            if satisfied is True:
                pass_count += 1
            else:
                fail_count += 1

            res = AuditExecutionResult(
                audit_id=res.audit_id,
                context=res.context,
                status=res.status,
                actual=res.actual,
                comparable_value=res.comparable_value,
                expected_relation=relation,
                expected_value=expected,
                expectation_satisfied=satisfied,
                error=res.error,
            )
        else:
            fail_count += 1
            errors.append(f"{audit_id}: {res.error}")
            res = AuditExecutionResult(
                audit_id=res.audit_id,
                context=res.context,
                status=res.status,
                actual=res.actual,
                comparable_value=res.comparable_value,
                expected_relation=relation,
                expected_value=_parse_expected_value(expected_raw),
                expectation_satisfied=False,
                error=res.error,
            )

        results.append(res)

    required = len(reqs)
    error_count = sum(1 for r in results if r.status != "success")

    if required == 0:
        status = "success"
    elif executed == required and error_count == 0 and fail_count == 0:
        status = "success"
    elif executed == 0:
        status = "failed"
    else:
        status = "partial"

    return {
        "witness_id": executable_witness.id,
        "kind": executable_witness.kind,
        "theorem_targets": list(executable_witness.theorem_targets),
        "lens_ids": list(executable_witness.lenses.keys()),
        "package_id": None if executable_witness.packaging is None else executable_witness.packaging.id,
        "required_audit_count": required,
        "executed_audit_count": executed,
        "expectation_pass_count": pass_count,
        "expectation_fail_count": fail_count,
        "error_count": error_count,
        "execution_status": status,
        "audit_results": [
            {
                "audit_id": r.audit_id,
                "context": r.context,
                "status": r.status,
                "actual": _serialize_any(r.actual),
                "comparable_value": _serialize_any(r.comparable_value),
                "expected_relation": r.expected_relation,
                "expected_value": _serialize_any(r.expected_value),
                "expectation_satisfied": r.expectation_satisfied,
                "error": r.error,
            }
            for r in results
        ],
        "errors": errors,
    }


def run_all_witnesses(config_path: str = "configs/witnesses.yaml", precision: int = 80) -> dict[str, Any]:
    ids = list_witness_ids(config_path=config_path)

    witness_rows = []
    success = partial = failed = expectation_fails = 0

    for wid in ids:
        try:
            ew = build_executable_witness(wid, config_path=config_path)
            row = run_expected_audits(ew, precision=precision)
        except Exception as exc:
            row = {
                "witness_id": wid,
                "kind": "unknown",
                "theorem_targets": [],
                "lens_ids": [],
                "package_id": None,
                "required_audit_count": 0,
                "executed_audit_count": 0,
                "expectation_pass_count": 0,
                "expectation_fail_count": 0,
                "error_count": 1,
                "execution_status": "failed",
                "audit_results": [],
                "errors": [str(exc)],
            }

        status = row["execution_status"]
        if status == "success":
            success += 1
        elif status == "partial":
            partial += 1
        else:
            failed += 1
        expectation_fails += row["expectation_fail_count"]
        witness_rows.append(row)

    return {
        "generation_timestamp_utc": _now_utc(),
        "witness_count": len(ids),
        "success_count": success,
        "partial_count": partial,
        "failed_count": failed,
        "expectation_fail_count": expectation_fails,
        "witnesses": witness_rows,
    }


def serialize_execution_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    # manifest is already serialization-safe; deep-normalize to ensure determinism.
    return _serialize_any(manifest)
