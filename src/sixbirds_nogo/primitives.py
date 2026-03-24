"""Primitive-toggle matrix and theorem-coverage pre-check utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import csv
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from sixbirds_nogo.affinity import is_exact_oneform, max_cycle_affinity
from sixbirds_nogo.coarse import make_lens
from sixbirds_nogo.definability import definable_predicate_count
from sixbirds_nogo.executable_witnesses import build_all_executable_witnesses, run_honest_audit
from sixbirds_nogo.graph_cycle import cycle_rank
from sixbirds_nogo.markov import FiniteMarkovChain, parse_probability_matrix
from sixbirds_nogo.master_suite import run_master_suite
from sixbirds_nogo.witnesses import list_witness_ids


PRIMITIVE_IDS = ("rewrite", "gating", "holonomy", "staging", "packaging", "drive")


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _serialize_fraction(frac: Fraction) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def _serialize_decimal(value: Decimal) -> str:
    return str(value)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Fraction):
        return _serialize_fraction(value)
    if isinstance(value, Decimal):
        return _serialize_decimal(value)
    if hasattr(value, "kind") and hasattr(value, "support_mismatch_count") and hasattr(value, "log_terms"):
        return {
            "kind": getattr(value, "kind"),
            "support_mismatch_count": getattr(value, "support_mismatch_count"),
            "log_terms": [
                {"ratio": _serialize_fraction(r), "coeff": _serialize_fraction(c)} for r, c in getattr(value, "log_terms")
            ],
            "decimal_value": None if getattr(value, "decimal_value", None) is None else str(getattr(value, "decimal_value")),
            "precision": getattr(value, "precision", None),
        }
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    return value


def _parse_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, Fraction, Decimal)):
        return value
    if isinstance(value, str):
        t = value.strip()
        if t == "":
            return None
        if t == "Infinity":
            return Decimal("Infinity")
        if t.lower() == "true":
            return True
        if t.lower() == "false":
            return False
        if "/" in t:
            a, b = t.split("/", 1)
            return Fraction(int(a), int(b))
        if t.lstrip("-").isdigit():
            return int(t)
        try:
            return Decimal(t)
        except Exception:
            return t
    if isinstance(value, dict) and "kind" in value:
        kind = value.get("kind")
        if kind == "zero":
            return Fraction(0, 1)
        if kind == "infinite":
            return Decimal("Infinity")
        if kind == "finite_positive":
            dec = value.get("decimal_value")
            return None if dec is None else Decimal(str(dec))
    return value


def _compare(lhs: Any, rhs: Any, relation: str) -> bool:
    if relation == "off_to_on":
        return lhs == "off" and rhs == "on"
    if relation == "on_to_off":
        return lhs == "on" and rhs == "off"

    a = _parse_scalar(lhs)
    b = _parse_scalar(rhs)

    if relation == "eq":
        return a == b
    if relation == "ne":
        return a != b
    if relation == "lt":
        return a < b
    if relation == "gt":
        return a > b
    if relation == "le":
        return a <= b
    if relation == "ge":
        return a >= b
    raise ValueError(f"unsupported relation: {relation}")


def _row_metric_value(master_row: dict[str, Any], key: str) -> Any:
    return master_row["metrics"][key]["value"]


def load_primitives_config(config_path: str = "configs/primitives.yaml") -> dict:
    data = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("primitives config must be an object")
    return data


def _master_row_map(precision: int = 80) -> dict[str, dict[str, Any]]:
    manifest = run_master_suite(precision=precision)
    return {row["witness_id"]: row for row in manifest["rows"]}


def build_registered_primitive_rows(config_path: str = "configs/primitives.yaml", precision: int = 80) -> tuple[dict, ...]:
    cfg = load_primitives_config(config_path)
    assignments = cfg.get("witness_assignments")
    if not isinstance(assignments, list):
        raise ValueError("witness_assignments must be a list")

    assignment_map: dict[str, dict[str, Any]] = {}
    for item in assignments:
        if not isinstance(item, dict) or not isinstance(item.get("witness_id"), str):
            raise ValueError("invalid witness assignment entry")
        wid = item["witness_id"]
        if wid in assignment_map:
            raise ValueError(f"duplicate witness assignment: {wid}")
        assignment_map[wid] = item

    master_map = _master_row_map(precision=precision)
    rows: list[dict[str, Any]] = []
    for wid in list_witness_ids():
        if wid not in assignment_map:
            raise ValueError(f"missing primitive assignment for witness: {wid}")
        if wid not in master_map:
            raise ValueError(f"missing master row for witness: {wid}")

        assn = assignment_map[wid]
        toggles = assn.get("toggles")
        if not isinstance(toggles, dict):
            raise ValueError(f"assignment {wid} missing toggles")
        for pid in PRIMITIVE_IDS:
            if pid not in toggles:
                raise ValueError(f"assignment {wid} missing toggle: {pid}")

        master_row = master_map[wid]
        row = {
            "row_id": wid,
            "row_kind": "registered",
            "parent_witness_id": "",
            "witness_id": wid,
            "kind": master_row["kind"],
            "theorem_targets": tuple(master_row.get("theorem_targets", [])),
            "rewrite": toggles["rewrite"],
            "gating": toggles["gating"],
            "holonomy": toggles["holonomy"],
            "staging": toggles["staging"],
            "packaging": toggles["packaging"],
            "drive": toggles["drive"],
            "ambiguous_assignment": any(toggles[p] == "ambiguous" for p in PRIMITIVE_IDS),
            "assignment_note": assn.get("assignment_notes", ""),
            "ambiguity_note": assn.get("ambiguity_notes", ""),
            "cycle_rank": _row_metric_value(master_row, "cycle_rank"),
            "max_cycle_affinity": _row_metric_value(master_row, "max_cycle_affinity"),
            "exactness_flag": _row_metric_value(master_row, "exactness_flag"),
            "micro_arrow_kl": _row_metric_value(master_row, "micro_arrow_kl"),
            "macro_arrow_kl": _row_metric_value(master_row, "macro_arrow_kl"),
            "closure_deficit": _row_metric_value(master_row, "closure_deficit"),
            "best_macro_gap": _row_metric_value(master_row, "best_macro_gap"),
            "contraction_lambda": _row_metric_value(master_row, "contraction_lambda"),
            "fixed_point_count": _row_metric_value(master_row, "fixed_point_count"),
            "definable_predicate_count": _row_metric_value(master_row, "definable_predicate_count"),
            "interface_size": _row_metric_value(master_row, "interface_size"),
            "representative_lens_id": master_row.get("representative_lens_id", ""),
        }
        rows.append(row)
    return tuple(rows)


def _build_derived_chain(variant: dict[str, Any]) -> FiniteMarkovChain:
    states = tuple(variant.get("states", []))
    if not states or not all(isinstance(s, str) for s in states):
        raise ValueError(f"derived variant {variant.get('id')} has invalid states")
    matrix = parse_probability_matrix(variant.get("matrix"))
    return FiniteMarkovChain(states=states, matrix=matrix)


def build_derived_variant_rows(config_path: str = "configs/primitives.yaml", precision: int = 80) -> tuple[dict, ...]:
    del precision
    cfg = load_primitives_config(config_path)
    variants = cfg.get("derived_variants")
    if not isinstance(variants, list):
        raise ValueError("derived_variants must be a list")

    rows: list[dict[str, Any]] = []
    for variant in variants:
        if not isinstance(variant, dict) or not isinstance(variant.get("id"), str):
            raise ValueError("invalid derived variant entry")

        chain = _build_derived_chain(variant)
        lenses = variant.get("lenses")
        if not isinstance(lenses, list) or not lenses:
            raise ValueError(f"derived variant {variant['id']} must provide lenses")
        first_lens = lenses[0]
        if not isinstance(first_lens, dict) or first_lens.get("id") != "identity":
            raise ValueError(f"derived variant {variant['id']} requires identity lens as first lens")

        lens = make_lens(chain.states, first_lens.get("mapping"), lens_id="identity")
        toggles = variant.get("toggles")
        if not isinstance(toggles, dict):
            raise ValueError(f"derived variant {variant['id']} missing toggles")

        row = {
            "row_id": variant["id"],
            "row_kind": "derived_variant",
            "parent_witness_id": variant.get("parent_witness_id", ""),
            "witness_id": "",
            "kind": variant.get("kind", "derived_markov_variant"),
            "theorem_targets": tuple(),
            "rewrite": toggles["rewrite"],
            "gating": toggles["gating"],
            "holonomy": toggles["holonomy"],
            "staging": toggles["staging"],
            "packaging": toggles["packaging"],
            "drive": toggles["drive"],
            "ambiguous_assignment": any(toggles[p] == "ambiguous" for p in PRIMITIVE_IDS),
            "assignment_note": variant.get("assignment_notes", ""),
            "ambiguity_note": variant.get("ambiguity_notes", ""),
            "cycle_rank": cycle_rank(chain),
            "max_cycle_affinity": max_cycle_affinity(chain),
            "exactness_flag": is_exact_oneform(chain),
            "micro_arrow_kl": None,
            "macro_arrow_kl": None,
            "closure_deficit": None,
            "best_macro_gap": None,
            "contraction_lambda": None,
            "fixed_point_count": None,
            "definable_predicate_count": definable_predicate_count(lens),
            "interface_size": len(lens.image_states),
            "representative_lens_id": "identity",
        }
        rows.append(row)

    return tuple(rows)


def build_primitive_matrix(config_path: str = "configs/primitives.yaml", precision: int = 80) -> tuple[dict, ...]:
    reg = build_registered_primitive_rows(config_path=config_path, precision=precision)
    drv = build_derived_variant_rows(config_path=config_path, precision=precision)
    return tuple(list(reg) + list(drv))


def _resolve_row_reference(row_map: dict[str, dict[str, Any]], ref: dict[str, Any]) -> dict[str, Any]:
    rid = ref.get("row_id")
    if not isinstance(rid, str) or rid not in row_map:
        raise ValueError(f"unresolvable row reference: {ref!r}")
    return row_map[rid]


def _resolve_audit_reference(
    executable_map: dict[str, Any],
    ref: dict[str, Any],
    precision: int,
) -> dict[str, Any]:
    wid = ref.get("witness_id")
    audit_id = ref.get("audit_id")
    context = ref.get("context")
    if not isinstance(wid, str) or wid not in executable_map:
        raise ValueError(f"unresolvable audit witness_id: {wid!r}")
    if not isinstance(audit_id, str):
        raise ValueError(f"invalid audit_id in reference: {ref!r}")
    result = run_honest_audit(executable_map[wid], audit_id=audit_id, context=context, precision=precision)
    if result.status != "success":
        raise ValueError(f"audit reference failed: witness={wid} audit={audit_id} error={result.error}")
    return {
        "witness_id": wid,
        "audit_id": audit_id,
        "context": context,
        "actual": result.actual,
        "comparable_value": result.comparable_value,
    }


def _check_from_rows(lhs_row: dict[str, Any], rhs_row: dict[str, Any], check: dict[str, Any]) -> dict[str, Any]:
    lhs_field = check.get("lhs_field")
    rhs_field = check.get("rhs_field")
    relation = check.get("relation")
    if not isinstance(lhs_field, str) or not isinstance(rhs_field, str) or not isinstance(relation, str):
        raise ValueError(f"invalid witness_pair check: {check!r}")

    lhs_val = lhs_row.get(lhs_field)
    rhs_val = rhs_row.get(rhs_field)
    passed = _compare(lhs_val, rhs_val, relation)
    return {
        "lhs_field": lhs_field,
        "rhs_field": rhs_field,
        "relation": relation,
        "lhs_value": _serialize_value(lhs_val),
        "rhs_value": _serialize_value(rhs_val),
        "passed": passed,
    }


def _check_from_audit(lhs_ref: dict[str, Any], rhs_ref: dict[str, Any], check: dict[str, Any]) -> dict[str, Any]:
    relation = check.get("relation")
    if not isinstance(relation, str):
        raise ValueError(f"invalid audit_context_pair check: {check!r}")

    side = check.get("side")
    if side is None:
        lhs_val = lhs_ref["comparable_value"]
        rhs_val = rhs_ref["comparable_value"]
        passed = _compare(lhs_val, rhs_val, relation)
        return {
            "relation": relation,
            "lhs_value": _serialize_value(lhs_val),
            "rhs_value": _serialize_value(rhs_val),
            "passed": passed,
        }

    if side not in {"lhs", "rhs"}:
        raise ValueError(f"invalid side in audit check: {check!r}")
    expected = check.get("value")
    actual = lhs_ref["comparable_value"] if side == "lhs" else rhs_ref["comparable_value"]
    passed = _compare(actual, expected, relation)
    return {
        "side": side,
        "relation": relation,
        "actual_value": _serialize_value(actual),
        "expected_value": _serialize_value(expected),
        "passed": passed,
    }


def evaluate_theorem_coverage(config_path: str = "configs/primitives.yaml", precision: int = 80) -> dict:
    cfg = load_primitives_config(config_path)
    coverage = cfg.get("theorem_coverage")
    if not isinstance(coverage, list):
        raise ValueError("theorem_coverage must be a list")

    theorem_cfg = json.loads(Path("configs/theorems.yaml").read_text(encoding="utf-8"))
    theorem_items = theorem_cfg.get("theorems")
    if not isinstance(theorem_items, list):
        raise ValueError("configs/theorems.yaml invalid: theorems must be list")
    theorem_ids = [t.get("id") for t in theorem_items if isinstance(t, dict) and isinstance(t.get("id"), str)]

    cov_ids = [t.get("theorem_id") for t in coverage if isinstance(t, dict)]
    if sorted(cov_ids) != sorted(theorem_ids) or len(cov_ids) != len(set(cov_ids)):
        raise ValueError("theorem_coverage must contain all theorem IDs exactly once")

    matrix_rows = build_primitive_matrix(config_path=config_path, precision=precision)
    row_map = {r["row_id"]: r for r in matrix_rows}
    executable_map = {w.id: w for w in build_all_executable_witnesses()}

    out_targets: list[dict[str, Any]] = []
    supporting_pair_count = 0
    gap_note_count = 0
    coverage_satisfied_count = 0

    for item in coverage:
        theorem_id = item.get("theorem_id")
        mode = item.get("coverage_mode")
        pairs = item.get("pairs", [])
        gap_note = item.get("gap_note", "")
        if not isinstance(theorem_id, str) or mode not in {"supporting_pair", "gap_note", "mixed"}:
            raise ValueError(f"invalid theorem coverage entry: {item!r}")
        if not isinstance(pairs, list):
            raise ValueError(f"theorem coverage pairs must be list for {theorem_id}")

        pair_results: list[dict[str, Any]] = []
        satisfied_pair_count = 0
        for pair in pairs:
            pair_id = pair.get("pair_id")
            pair_type = pair.get("pair_type")
            checks = pair.get("checks", [])
            note = pair.get("note", "")
            if not isinstance(pair_id, str) or pair_type not in {"witness_pair", "audit_context_pair"}:
                raise ValueError(f"invalid pair entry in {theorem_id}: {pair!r}")
            if not isinstance(checks, list):
                raise ValueError(f"checks must be list in {pair_id}")

            check_results: list[dict[str, Any]] = []
            lhs_serialized: Any
            rhs_serialized: Any
            if pair_type == "witness_pair":
                lhs_row = _resolve_row_reference(row_map, pair.get("lhs", {}))
                rhs_row = _resolve_row_reference(row_map, pair.get("rhs", {}))
                for check in checks:
                    check_results.append(_check_from_rows(lhs_row, rhs_row, check))
                lhs_serialized = {"row_id": lhs_row["row_id"]}
                rhs_serialized = {"row_id": rhs_row["row_id"]}
            else:
                lhs_ref = _resolve_audit_reference(executable_map, pair.get("lhs", {}), precision)
                rhs_ref = _resolve_audit_reference(executable_map, pair.get("rhs", {}), precision)
                for check in checks:
                    check_results.append(_check_from_audit(lhs_ref, rhs_ref, check))
                lhs_serialized = _serialize_value(lhs_ref)
                rhs_serialized = _serialize_value(rhs_ref)

            checks_passed = all(c["passed"] for c in check_results)
            if checks_passed:
                satisfied_pair_count += 1
                supporting_pair_count += 1

            pair_results.append(
                {
                    "pair_id": pair_id,
                    "pair_type": pair_type,
                    "lhs": lhs_serialized,
                    "rhs": rhs_serialized,
                    "checks": check_results,
                    "checks_passed": checks_passed,
                    "note": note,
                }
            )

        nonempty_gap = isinstance(gap_note, str) and gap_note.strip() != ""
        if nonempty_gap:
            gap_note_count += 1

        if mode == "supporting_pair":
            satisfied = satisfied_pair_count > 0
        elif mode == "gap_note":
            satisfied = nonempty_gap
        else:
            satisfied = satisfied_pair_count > 0 or nonempty_gap

        if satisfied:
            coverage_satisfied_count += 1

        out_targets.append(
            {
                "theorem_id": theorem_id,
                "coverage_mode": mode,
                "coverage_satisfied": satisfied,
                "pair_count": len(pair_results),
                "satisfied_pair_count": satisfied_pair_count,
                "gap_note": gap_note,
                "pairs": pair_results,
            }
        )

    return {
        "generation_timestamp_utc": _now_utc(),
        "theorem_target_count": len(out_targets),
        "supporting_pair_count": supporting_pair_count,
        "gap_note_count": gap_note_count,
        "coverage_satisfied_count": coverage_satisfied_count,
        "theorem_targets": out_targets,
    }


def run_primitive_matrix(config_path: str = "configs/primitives.yaml", precision: int = 80) -> dict:
    rows = build_primitive_matrix(config_path=config_path, precision=precision)
    coverage = evaluate_theorem_coverage(config_path=config_path, precision=precision)
    registered_count = sum(1 for r in rows if r["row_kind"] == "registered")
    derived_count = sum(1 for r in rows if r["row_kind"] == "derived_variant")
    return {
        "generation_timestamp_utc": _now_utc(),
        "registered_witness_count": registered_count,
        "derived_variant_count": derived_count,
        "row_count": len(rows),
        "theorem_target_count": coverage["theorem_target_count"],
        "rows": rows,
        "coverage": coverage,
    }


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Fraction):
        return _serialize_fraction(value)
    if isinstance(value, Decimal):
        return _serialize_decimal(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (list, tuple)):
        return ";".join(str(v) for v in value)
    return str(value)


def write_primitive_outputs(manifest: dict, output_dir: str = "results/T14") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    matrix_path = out / "primitive_matrix.csv"
    coverage_path = out / "primitive_coverage.json"

    coverage_path.write_text(json.dumps(_serialize_value(manifest["coverage"]), indent=2) + "\n", encoding="utf-8")

    fields = [
        "row_id",
        "row_kind",
        "parent_witness_id",
        "witness_id",
        "kind",
        "rewrite",
        "gating",
        "holonomy",
        "staging",
        "packaging",
        "drive",
        "ambiguous_assignment",
        "assignment_note",
        "ambiguity_note",
        "theorem_targets",
        "cycle_rank",
        "max_cycle_affinity",
        "exactness_flag",
        "micro_arrow_kl",
        "macro_arrow_kl",
        "closure_deficit",
        "best_macro_gap",
        "contraction_lambda",
        "fixed_point_count",
        "definable_predicate_count",
        "interface_size",
        "representative_lens_id",
    ]

    with matrix_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in manifest["rows"]:
            rec = {k: _csv_cell(row.get(k)) for k in fields}
            w.writerow(rec)
