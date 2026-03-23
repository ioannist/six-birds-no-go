#!/usr/bin/env python3
"""Validate witness registry schema and cross-references."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
from typing import Any

REQUIRED_WITNESS_IDS = {
    "rev_tree_4",
    "rev_cycle_3",
    "biased_cycle_3",
    "hidden_clock_reversible",
    "hidden_clock_driven",
    "zero_closure_deficit_lumpable",
    "positive_closure_deficit",
    "contractive_unique_object",
    "noncontractive_multiobject",
    "fixed_idempotent_no_ladder",
    "lens_extension_escape",
}

ALLOWED_KIND = {"markov_chain", "phase_lift_markov", "packaging_endomap", "extension_witness"}
ALLOWED_THEOREM_ROLE = {"supports", "contrast"}
ALLOWED_AUDIT_REL = {"eq", "gt", "ge", "lt", "le"}
ALLOWED_PACKAGING_FAMILY = {"state_map", "stochastic_operator"}


def parse_rational(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise ValueError("boolean not allowed for rational")
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty rational string")
        if "." in text:
            raise ValueError(f"decimal literal not allowed: {value!r}")
        return Fraction(text)
    raise ValueError(f"unsupported rational type: {type(value).__name__}")


def _load_obj(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON-compatible YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level must be an object")
    return data


def _validate_row_stochastic(
    *,
    matrix: Any,
    row_states: Any,
    states: list[str],
    where: str,
    errors: list[str],
) -> None:
    if not isinstance(row_states, list) or not all(isinstance(s, str) for s in row_states):
        errors.append(f"{where}: row_states must be a list of strings")
        return
    if set(row_states) != set(states):
        errors.append(f"{where}: row_states must match microstate states as a set")
    n = len(row_states)
    if not isinstance(matrix, list) or len(matrix) != n:
        errors.append(f"{where}: matrix must be square with dimension {n}")
        return
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != n:
            errors.append(f"{where}: row {i} must have length {n}")
            continue
        try:
            vals = [parse_rational(x) for x in row]
        except Exception as exc:
            errors.append(f"{where}: row {i} has invalid rational entry: {exc}")
            continue
        if any(v < 0 for v in vals):
            errors.append(f"{where}: row {i} has negative entry")
        if sum(vals, Fraction(0, 1)) != Fraction(1, 1):
            errors.append(f"{where}: row {i} does not sum to 1 exactly")


def validate_all(config_dir: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {
        "witnesses": 0,
        "markov": 0,
        "phase_lift": 0,
        "packaging": 0,
        "extension": 0,
    }

    witnesses_path = config_dir / "witnesses.yaml"
    theorems_path = config_dir / "theorems.yaml"
    for req in (witnesses_path, theorems_path):
        if not req.exists():
            errors.append(f"missing required config: {req}")
    if errors:
        return errors, counts

    try:
        registry = _load_obj(witnesses_path)
        theorems = _load_obj(theorems_path)
    except ValueError as exc:
        return [str(exc)], counts

    for key in ("version", "numeric_encoding", "witnesses"):
        if key not in registry:
            errors.append(f"witnesses.yaml missing key: {key}")
    if registry.get("numeric_encoding") != "rational_string_v1":
        errors.append("witnesses.yaml numeric_encoding must be rational_string_v1")
    for key in ("audit_registry", "theorems"):
        if key not in theorems:
            errors.append(f"theorems.yaml missing key: {key}")

    theorem_ids = set()
    for item in theorems.get("theorems", []):
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            theorem_ids.add(item["id"])
    audit_ids = set()
    for item in theorems.get("audit_registry", []):
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            audit_ids.add(item["id"])

    witnesses = registry.get("witnesses")
    if not isinstance(witnesses, list):
        errors.append("witnesses must be a list")
        return errors, counts

    ids: list[str] = []
    for i, w in enumerate(witnesses):
        if not isinstance(w, dict):
            errors.append(f"witnesses[{i}] must be an object")
            continue
        wid = w.get("id")
        if not isinstance(wid, str) or not wid:
            errors.append(f"witnesses[{i}] missing non-empty id")
            continue
        ids.append(wid)

    id_set = set(ids)
    counts["witnesses"] = len(ids)
    if len(id_set) != len(ids):
        errors.append("duplicate witness ids detected")
    missing = sorted(REQUIRED_WITNESS_IDS - id_set)
    if missing:
        errors.append(f"missing required witness ids: {missing}")

    for w in witnesses:
        if not isinstance(w, dict) or not isinstance(w.get("id"), str):
            continue
        wid = w["id"]
        kind = w.get("kind")
        if kind not in ALLOWED_KIND:
            errors.append(f"witness {wid}: invalid kind {kind}")
            continue
        if kind == "markov_chain":
            counts["markov"] += 1
        elif kind == "phase_lift_markov":
            counts["phase_lift"] += 1
        elif kind == "packaging_endomap":
            counts["packaging"] += 1
        elif kind == "extension_witness":
            counts["extension"] += 1

        space = w.get("microstate_space")
        if not isinstance(space, dict):
            errors.append(f"witness {wid}: microstate_space must be an object")
            continue
        states = space.get("states")
        size = space.get("size")
        if not isinstance(states, list) or not states or not all(isinstance(s, str) and s for s in states):
            errors.append(f"witness {wid}: microstate_space.states must be non-empty list of strings")
            continue
        if len(set(states)) != len(states):
            errors.append(f"witness {wid}: microstate_space.states must be unique")
        if size != len(states):
            errors.append(f"witness {wid}: microstate_space.size must equal len(states)")

        lenses = w.get("lenses")
        lens_ids: set[str] = set()
        if not isinstance(lenses, list) or not lenses:
            errors.append(f"witness {wid}: lenses must be non-empty list")
        else:
            for lens in lenses:
                if not isinstance(lens, dict):
                    errors.append(f"witness {wid}: lens must be object")
                    continue
                lid = lens.get("id")
                mapping = lens.get("mapping")
                if not isinstance(lid, str) or not lid:
                    errors.append(f"witness {wid}: lens missing non-empty id")
                    continue
                lens_ids.add(lid)
                if not isinstance(mapping, dict):
                    errors.append(f"witness {wid}: lens {lid} mapping must be object")
                    continue
                if set(mapping.keys()) != set(states):
                    errors.append(f"witness {wid}: lens {lid} must cover every microstate exactly once")

        dynamics = w.get("dynamics")
        if kind in {"markov_chain", "phase_lift_markov"}:
            if not isinstance(dynamics, dict):
                errors.append(f"witness {wid}: dynamics must be an object for kind {kind}")
            else:
                if dynamics.get("family") != "discrete_markov":
                    errors.append(f"witness {wid}: dynamics.family must be discrete_markov")
                _validate_row_stochastic(
                    matrix=dynamics.get("matrix"),
                    row_states=dynamics.get("row_states"),
                    states=states,
                    where=f"witness {wid} dynamics",
                    errors=errors,
                )
                sd = dynamics.get("stationary_distribution")
                if not isinstance(sd, list) or len(sd) != len(states):
                    errors.append(f"witness {wid}: stationary_distribution length mismatch")
                else:
                    try:
                        vals = [parse_rational(x) for x in sd]
                        if any(v < 0 for v in vals):
                            errors.append(f"witness {wid}: stationary_distribution has negative entry")
                        if sum(vals, Fraction(0, 1)) != Fraction(1, 1):
                            errors.append(f"witness {wid}: stationary_distribution must sum to 1")
                    except Exception as exc:
                        errors.append(f"witness {wid}: invalid stationary_distribution value: {exc}")
        else:
            if dynamics is not None:
                errors.append(f"witness {wid}: dynamics must be null for kind {kind}")

        packaging = w.get("packaging")
        if kind in {"packaging_endomap", "extension_witness"}:
            if not isinstance(packaging, dict):
                errors.append(f"witness {wid}: packaging must be an object for kind {kind}")
            else:
                family = packaging.get("family")
                if family not in ALLOWED_PACKAGING_FAMILY:
                    errors.append(f"witness {wid}: invalid packaging.family {family}")
                if not isinstance(packaging.get("id"), str) or not packaging.get("id"):
                    errors.append(f"witness {wid}: packaging.id must be non-empty string")
                if family == "state_map":
                    mapping = packaging.get("mapping")
                    if not isinstance(mapping, dict):
                        errors.append(f"witness {wid}: state_map packaging requires mapping object")
                    else:
                        if set(mapping.keys()) != set(states):
                            errors.append(f"witness {wid}: state_map keys must match states")
                        bad_vals = [v for v in mapping.values() if v not in set(states)]
                        if bad_vals:
                            errors.append(f"witness {wid}: state_map values must be valid states")
                elif family == "stochastic_operator":
                    if "action" not in packaging:
                        errors.append(f"witness {wid}: stochastic_operator requires action")
                    _validate_row_stochastic(
                        matrix=packaging.get("matrix"),
                        row_states=packaging.get("row_states"),
                        states=states,
                        where=f"witness {wid} packaging",
                        errors=errors,
                    )
        else:
            if packaging is not None:
                errors.append(f"witness {wid}: packaging must be null for pure Markov kinds")

        if kind == "extension_witness":
            if not isinstance(lenses, list) or len(lenses) < 2:
                errors.append(f"witness {wid}: extension_witness requires at least two lenses")
            pairs = w.get("extension_pairs")
            if not isinstance(pairs, list) or not pairs:
                errors.append(f"witness {wid}: extension_witness requires non-empty extension_pairs")
            else:
                for pair in pairs:
                    if not isinstance(pair, dict):
                        errors.append(f"witness {wid}: extension pair must be object")
                        continue
                    b = pair.get("base_lens_id")
                    e = pair.get("extended_lens_id")
                    if b not in lens_ids or e not in lens_ids:
                        errors.append(f"witness {wid}: extension pair references unknown lens id")
                    if b == e:
                        errors.append(f"witness {wid}: extension pair must use distinct lens ids")

        theorem_targets = w.get("theorem_targets")
        if not isinstance(theorem_targets, list) or not theorem_targets:
            errors.append(f"witness {wid}: theorem_targets must be non-empty list")
        else:
            for t in theorem_targets:
                if t not in theorem_ids:
                    errors.append(f"witness {wid}: unknown theorem target {t}")

        sig = w.get("expected_signatures")
        if not isinstance(sig, dict):
            errors.append(f"witness {wid}: expected_signatures must be object")
        else:
            th_sig = sig.get("theorems")
            au_sig = sig.get("audits")
            if not isinstance(th_sig, list):
                errors.append(f"witness {wid}: expected_signatures.theorems must be list")
            else:
                for item in th_sig:
                    if not isinstance(item, dict):
                        errors.append(f"witness {wid}: theorem signature entry must be object")
                        continue
                    tid = item.get("theorem_id")
                    role = item.get("role")
                    if tid not in theorem_ids:
                        errors.append(f"witness {wid}: theorem signature references unknown theorem_id {tid}")
                    if role not in ALLOWED_THEOREM_ROLE:
                        errors.append(f"witness {wid}: invalid theorem role {role}")
            if not isinstance(au_sig, list):
                errors.append(f"witness {wid}: expected_signatures.audits must be list")
            else:
                for item in au_sig:
                    if not isinstance(item, dict):
                        errors.append(f"witness {wid}: audit signature entry must be object")
                        continue
                    aid = item.get("audit_id")
                    rel = item.get("relation")
                    if aid not in audit_ids:
                        errors.append(f"witness {wid}: audit signature references unknown audit_id {aid}")
                    if rel not in ALLOWED_AUDIT_REL:
                        errors.append(f"witness {wid}: invalid audit relation {rel}")
                    if "value" not in item:
                        errors.append(f"witness {wid}: audit signature missing value")
                    else:
                        val = item["value"]
                        if isinstance(val, str):
                            try:
                                parse_rational(val)
                            except Exception:
                                pass

        tags = w.get("tags")
        if not isinstance(tags, list) or not tags or not all(isinstance(t, str) and t for t in tags):
            errors.append(f"witness {wid}: tags must be non-empty list of strings")

    return errors, counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate witness registry")
    parser.add_argument("--summary", action="store_true", help="Print concise PASS/FAIL summary")
    parser.add_argument("--config-dir", default="configs", help="Directory containing witnesses.yaml/theorems.yaml")
    args = parser.parse_args()

    errors, counts = validate_all(Path(args.config_dir))
    if errors:
        if args.summary:
            print(f"FAIL {len(errors)}")
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    if args.summary:
        print(
            "PASS "
            f"witnesses={counts['witnesses']} "
            f"markov={counts['markov']} "
            f"phase_lift={counts['phase_lift']} "
            f"packaging={counts['packaging']} "
            f"extension={counts['extension']}"
        )
    else:
        print("Witness validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
