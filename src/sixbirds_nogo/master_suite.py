"""Deterministic master aggregation over executable witness audits."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
import csv
import json
from pathlib import Path
from typing import Any

from sixbirds_nogo.affinity import is_exact_oneform, max_cycle_affinity
from sixbirds_nogo.definability import definable_predicate_count
from sixbirds_nogo.executable_witnesses import (
    ExecutableWitness,
    build_all_executable_witnesses,
    run_expected_audits,
)
from sixbirds_nogo.graph_cycle import cycle_rank
from sixbirds_nogo.objecthood import dobrushin_contraction_lambda, epsilon_stable_distributions, fixed_point_count


REQUIRED_METRICS = (
    "micro_arrow_kl",
    "macro_arrow_kl",
    "cycle_rank",
    "max_cycle_affinity",
    "exactness_flag",
    "closure_deficit",
    "best_macro_gap",
    "contraction_lambda",
    "fixed_point_count",
    "eps_stable_count",
    "definable_predicate_count",
    "interface_size",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def serialize_fraction(frac: Fraction) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def serialize_decimal(value: Decimal) -> str:
    return str(value)


def _parse_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, Fraction, Decimal)):
        return value
    if isinstance(value, str):
        if value == "Infinity":
            return Decimal("Infinity")
        if "/" in value:
            a, b = value.split("/", 1)
            return Fraction(int(a), int(b))
        if value.lstrip("-").isdigit():
            return int(value)
        try:
            return Decimal(value)
        except Exception:
            return value
    return value


def scalarize_kl_like(value: Any) -> tuple[str | None, str]:
    if value is None:
        return None, "unavailable"
    if not isinstance(value, dict):
        return None, "unavailable"
    kind = value.get("kind", "unavailable")
    if kind == "zero":
        return "0", "zero"
    if kind == "infinite":
        return "Infinity", "infinite"
    if kind == "finite_positive":
        dec = value.get("decimal_value")
        return (None if dec is None else str(dec)), "finite_positive"
    return None, str(kind)


def preferred_lens_ids(executable_witness: ExecutableWitness) -> tuple[str, ...]:
    ids = tuple(executable_witness.lenses.keys())
    if not ids:
        return ()
    non_id = tuple(i for i in ids if i != "identity")
    return non_id if non_id else ids


def select_representative_lens(executable_witness: ExecutableWitness) -> str | None:
    cands = preferred_lens_ids(executable_witness)
    if not cands:
        return None
    lenses = executable_witness.lenses
    return sorted(cands, key=lambda lid: (-len(lenses[lid].image_states), lid))[0]


def _metric(status: str, value: Any, kind: str | None = None, context: dict[str, Any] | None = None, explanation: str = "") -> dict[str, Any]:
    return {
        "status": status,
        "value": value,
        "kind": kind,
        "context": context,
        "explanation": explanation,
    }


def _pick_max_by_comparable(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None

    def key(rec: dict[str, Any]) -> tuple[int, Any]:
        c = _parse_scalar(rec.get("comparable_value"))
        if c == Decimal("Infinity"):
            return (3, Decimal("Infinity"))
        if isinstance(c, Decimal):
            return (2, c)
        if isinstance(c, Fraction):
            return (1, c)
        if isinstance(c, int):
            return (1, Fraction(c, 1))
        if isinstance(c, bool):
            return (1, Fraction(int(c), 1))
        return (0, Fraction(0, 1))

    best = records[0]
    for rec in records[1:]:
        if key(rec) > key(best):
            best = rec
    return best


def _record_context_string(rec: dict[str, Any]) -> str:
    ctx = rec.get("context")
    if not isinstance(ctx, dict) or not ctx:
        return ""
    return json.dumps(ctx, sort_keys=True, separators=(",", ":"))


def _derive_strongest_signal(row: dict[str, Any]) -> str:
    m = row["metrics"]

    ext = row.get("kind") == "extension_witness" and m["interface_size"]["value"] == 3 and m["definable_predicate_count"]["value"] == 8
    if ext:
        return "lens extension raises interface and definable capacity"

    if m["max_cycle_affinity"]["status"] == "computed" and m["max_cycle_affinity"]["value"] not in ("0", "0/1", 0, Fraction(0, 1)):
        return "nonzero cycle affinity on support"

    if m["micro_arrow_kl"]["status"] == "computed" and m["macro_arrow_kl"]["status"] == "computed":
        micro = m["micro_arrow_kl"]["kind"]
        macro = m["macro_arrow_kl"]["kind"]
        if micro == "finite_positive" and macro == "zero":
            return "positive micro arrow erased under coarse lens"
        if micro == "finite_positive" and macro == "finite_positive":
            return "positive micro arrow retained under coarse lens"

    if m["closure_deficit"]["status"] == "computed" and m["closure_deficit"]["kind"] == "finite_positive":
        return "positive closure deficit / best-gap obstruction"

    if m["contraction_lambda"]["status"] == "computed" and m["contraction_lambda"]["value"] in ("0", "0/1", 0, Fraction(0, 1)):
        if m["fixed_point_count"]["value"] == 1:
            return "strict contraction with unique fixed distribution"

    if m["interface_size"]["status"] == "computed" and m["definable_predicate_count"]["status"] == "computed":
        if m["interface_size"]["value"] in ("2", 2) and m["definable_predicate_count"]["value"] in ("4", 4):
            return "idempotent bounded-interface saturation"

    if m["cycle_rank"]["status"] == "computed":
        if m["cycle_rank"]["value"] in (0, "0"):
            return "forest / no-cycle support"
        if m["exactness_flag"]["status"] == "computed" and m["exactness_flag"]["value"] is True:
            return "cyclic support with exact one-form"

    return "baseline executable witness with satisfied audits"


def summarize_witness(
    executable_witness: ExecutableWitness,
    precision: int = 80,
    eps_denominator: int = 4,
    eps_epsilon: Fraction = Fraction(1, 4),
) -> dict[str, Any]:
    audit_exec = run_expected_audits(executable_witness, precision=precision)
    audits = audit_exec["audit_results"]
    chain = executable_witness.chain
    pkg = executable_witness.packaging

    metrics: dict[str, dict[str, Any]] = {}

    # direct chain metrics
    if chain is None:
        for key in ("cycle_rank", "max_cycle_affinity", "exactness_flag"):
            metrics[key] = _metric("not_applicable", None, explanation="not_applicable:no_chain")
    else:
        metrics["cycle_rank"] = _metric("computed", cycle_rank(chain))
        metrics["max_cycle_affinity"] = _metric("computed", max_cycle_affinity(chain))
        metrics["exactness_flag"] = _metric("computed", is_exact_oneform(chain))

    # arrow summaries from expected audits
    micro_recs = [a for a in audits if a["audit_id"] == "AUDIT_PATH_KL_MICRO" and a["status"] == "success"]
    if micro_recs:
        micro_recs = sorted(micro_recs, key=lambda a: (_parse_scalar(a["comparable_value"]), int((a.get("context") or {}).get("horizon", 0)), _record_context_string(a)))
        pick = micro_recs[-1]
        scalar, kind = scalarize_kl_like(pick["actual"])
        metrics["micro_arrow_kl"] = _metric("computed", scalar, kind=kind, context=pick.get("context"), explanation="")
    else:
        metrics["micro_arrow_kl"] = _metric("not_requested", None, explanation="not_requested:no_registered_micro_arrow_context")

    macro_recs = [a for a in audits if a["audit_id"] == "AUDIT_PATH_KL_MACRO_HONEST" and a["status"] == "success"]
    if macro_recs:
        non_identity = [a for a in macro_recs if (a.get("context") or {}).get("lens_id") != "identity"]
        pool = non_identity if non_identity else macro_recs

        def mkey(a: dict[str, Any]) -> tuple[Any, int, int, str]:
            lens_id = (a.get("context") or {}).get("lens_id", "")
            iface = len(executable_witness.lenses[lens_id].image_states) if lens_id in executable_witness.lenses else 0
            return (
                _parse_scalar(a["comparable_value"]),
                iface,
                int((a.get("context") or {}).get("horizon", 0)),
                lens_id,
            )

        pick = sorted(pool, key=mkey)[-1]
        scalar, kind = scalarize_kl_like(pick["actual"])
        metrics["macro_arrow_kl"] = _metric("computed", scalar, kind=kind, context=pick.get("context"), explanation="")
    else:
        metrics["macro_arrow_kl"] = _metric("not_requested", None, explanation="not_requested:no_registered_macro_arrow_context")

    # closure / best gap from expected contexts
    for col, aid, miss in [
        ("closure_deficit", "AUDIT_CLOSURE_DEFICIT", "not_requested:no_registered_closure_context"),
        ("best_macro_gap", "AUDIT_BEST_MACRO_GAP", "not_requested:no_registered_best_gap_context"),
    ]:
        recs = [a for a in audits if a["audit_id"] == aid and a["status"] == "success"]
        if recs:
            recs = sorted(
                recs,
                key=lambda a: (
                    _parse_scalar(a["comparable_value"]),
                    int((a.get("context") or {}).get("tau", 0)),
                    str((a.get("context") or {}).get("lens_id", "")),
                ),
            )
            pick = recs[-1]
            scalar, kind = scalarize_kl_like(pick["actual"])
            metrics[col] = _metric("computed", scalar, kind=kind, context=pick.get("context"), explanation="")
        else:
            metrics[col] = _metric("not_requested", None, explanation=miss)

    # packaging metrics
    if pkg is None:
        for key in ("contraction_lambda", "fixed_point_count", "eps_stable_count"):
            metrics[key] = _metric("not_applicable", None, explanation="not_applicable:no_packaging")
    else:
        metrics["contraction_lambda"] = _metric("computed", dobrushin_contraction_lambda(pkg))
        metrics["fixed_point_count"] = _metric("computed", fixed_point_count(pkg))
        metrics["eps_stable_count"] = _metric(
            "computed",
            len(epsilon_stable_distributions(pkg, denominator=eps_denominator, epsilon=eps_epsilon)),
            context={"denominator": eps_denominator, "epsilon": eps_epsilon},
        )

    # representative-lens metrics
    rep_lens_id = select_representative_lens(executable_witness)
    if rep_lens_id is None:
        metrics["definable_predicate_count"] = _metric("error", None, explanation="error:no_lens_available")
        metrics["interface_size"] = _metric("error", None, explanation="error:no_lens_available")
    else:
        lens = executable_witness.lenses[rep_lens_id]
        metrics["definable_predicate_count"] = _metric("computed", definable_predicate_count(lens), context={"lens_id": rep_lens_id})
        metrics["interface_size"] = _metric("computed", len(lens.image_states), context={"lens_id": rep_lens_id})

    row = {
        "witness_id": executable_witness.id,
        "kind": executable_witness.kind,
        "theorem_targets": list(executable_witness.theorem_targets),
        "execution_status": audit_exec["execution_status"],
        "lens_ids": list(executable_witness.lenses.keys()),
        "package_id": None if executable_witness.packaging is None else executable_witness.packaging.id,
        "representative_lens_id": rep_lens_id,
        "required_audit_count": audit_exec["required_audit_count"],
        "executed_audit_count": audit_exec["executed_audit_count"],
        "expectation_fail_count": audit_exec["expectation_fail_count"],
        "error_count": audit_exec["error_count"],
        "metrics": metrics,
        "strongest_signal": "",
    }
    row["strongest_signal"] = _derive_strongest_signal(row)
    return row


def run_master_suite(
    config_path: str = "configs/witnesses.yaml",
    precision: int = 80,
    eps_denominator: int = 4,
    eps_epsilon: Fraction = Fraction(1, 4),
) -> dict[str, Any]:
    witnesses = build_all_executable_witnesses(config_path=config_path)
    rows = [
        summarize_witness(w, precision=precision, eps_denominator=eps_denominator, eps_epsilon=eps_epsilon)
        for w in witnesses
    ]

    success = sum(1 for r in rows if r["execution_status"] == "success")
    partial = sum(1 for r in rows if r["execution_status"] == "partial")
    failed = sum(1 for r in rows if r["execution_status"] == "failed")

    unexplained_missing = 0
    for r in rows:
        for m in REQUIRED_METRICS:
            ent = r["metrics"][m]
            value = ent["value"]
            explanation = ent.get("explanation", "")
            blank = value is None or value == ""
            if blank and (not explanation):
                unexplained_missing += 1

    return {
        "generation_timestamp_utc": _now_utc(),
        "precision": precision,
        "eps_grid_denominator": eps_denominator,
        "eps_epsilon": eps_epsilon,
        "witness_count": len(rows),
        "success_count": success,
        "partial_count": partial,
        "failed_count": failed,
        "unexplained_missing_count": unexplained_missing,
        "rows": rows,
    }


def _csv_cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, Fraction):
        return serialize_fraction(v)
    if isinstance(v, Decimal):
        return serialize_decimal(v)
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(_json_cell(v), sort_keys=True, separators=(",", ":"))
    return str(v)


def _json_cell(value: Any) -> Any:
    if isinstance(value, Fraction):
        return serialize_fraction(value)
    if isinstance(value, Decimal):
        return serialize_decimal(value)
    if isinstance(value, dict):
        return {str(k): _json_cell(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_cell(v) for v in value]
    return value


def write_master_suite_outputs(manifest: dict[str, Any], output_dir: str = "results/master") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "witness_manifest.json"
    csv_path = out / "witness_metrics.csv"

    json_path.write_text(json.dumps(_json_cell(manifest), indent=2) + "\n", encoding="utf-8")

    metric_cols = list(REQUIRED_METRICS)
    fields = ["witness_id"] + metric_cols + [f"{c}_explanation" for c in metric_cols] + [
        "kind",
        "execution_status",
        "representative_lens_id",
        "micro_arrow_context",
        "macro_arrow_context",
        "closure_context",
        "best_macro_gap_context",
        "eps_grid_denominator",
        "eps_epsilon",
        "strongest_signal",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in manifest["rows"]:
            rec: dict[str, Any] = {
                "witness_id": row["witness_id"],
                "kind": row["kind"],
                "execution_status": row["execution_status"],
                "representative_lens_id": row["representative_lens_id"],
                "eps_grid_denominator": manifest["eps_grid_denominator"],
                "eps_epsilon": _csv_cell(manifest["eps_epsilon"]),
                "strongest_signal": row["strongest_signal"],
                "micro_arrow_context": _csv_cell(row["metrics"]["micro_arrow_kl"].get("context")),
                "macro_arrow_context": _csv_cell(row["metrics"]["macro_arrow_kl"].get("context")),
                "closure_context": _csv_cell(row["metrics"]["closure_deficit"].get("context")),
                "best_macro_gap_context": _csv_cell(row["metrics"]["best_macro_gap"].get("context")),
            }
            for c in metric_cols:
                rec[c] = _csv_cell(row["metrics"][c].get("value"))
                rec[f"{c}_explanation"] = row["metrics"][c].get("explanation", "")
            w.writerow(rec)
