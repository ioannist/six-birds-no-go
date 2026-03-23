#!/usr/bin/env python3
"""Validate assumptions/theorems/proxies configuration registries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REQUIRED_ASSUMPTION_ATOMS = {
    "A_FIN",
    "A_AUT",
    "A_LENS_HONEST",
    "A_PHASE_INTERNAL",
    "A_PHASE_REV",
    "A_SHARED_STATIONARY",
    "A_REV_SUPPORT",
    "A_NULL_AFFINITY",
    "A_SUPPORT_FOREST",
    "A_STAGING_FIXED",
    "A_PACKAGE_DEFINED",
    "A_PACKAGE_FIXED",
    "A_PACKAGE_IDEM",
    "A_PACKAGE_CONTRACTIVE",
    "A_METRIC_TV",
    "A_INTERFACE_FIXED",
    "A_INTERFACE_BOUNDED",
    "A_DOMAIN_FIXED",
}

REQUIRED_BUNDLES = {
    "B_PATHSPACE_HONEST",
    "B_PROTOCOL_TRAP",
    "B_FORCE_FOREST",
    "B_FORCE_NULL",
    "B_MACRO_CLOSURE",
    "B_OBJECT_CONTRACTIVE",
    "B_LADDER_IDEM",
    "B_LADDER_BOUNDED_INTERFACE",
}

REQUIRED_THEOREMS = {
    "NG_ARROW_DPI",
    "NG_PROTOCOL_TRAP",
    "NG_FORCE_FOREST",
    "NG_FORCE_NULL",
    "NG_MACRO_CLOSURE_DEFICIT",
    "NG_OBJECT_CONTRACTIVE",
    "NG_LADDER_IDEM",
    "NG_LADDER_BOUNDED_INTERFACE",
}

REQUIRED_SOURCE_BASIS = {
    "CLASSICAL_DATA_PROCESSING",
    "CLASSICAL_CYCLE_AFFINITY",
    "SIX_BIRDS_FOUNDATIONS",
    "MINIMAL_SUBSTRATE_SEMANTICS",
    "OBJECTHOOD_TRACK",
    "TIME_TRACK",
}

REQUIRED_THEOREM_AUDITS = {
    "AUDIT_PATH_KL_MICRO",
    "AUDIT_PATH_KL_MACRO_HONEST",
    "AUDIT_DPI_GAP",
    "AUDIT_PHASE_LIFT_REVERSIBILITY",
    "AUDIT_CYCLE_RANK",
    "AUDIT_MAX_CYCLE_AFFINITY",
    "AUDIT_ONEFORM_EXACTNESS",
    "AUDIT_CLOSURE_DEFICIT",
    "AUDIT_BEST_MACRO_GAP",
    "AUDIT_IDEMPOTENCE_DEFECT",
    "AUDIT_CONTRACTION_LAMBDA",
    "AUDIT_FIXED_POINT_COUNT",
    "AUDIT_EPS_STABLE_COUNT",
    "AUDIT_DEFINABLE_PREDICATE_COUNT",
    "AUDIT_INTERFACE_SIZE",
}

REQUIRED_PROXIES = {
    "PROXY_MACRO_MARKOV_ARROW",
    "PROXY_THRESHOLD_SUPPORT_GRAPH",
    "PROXY_REGULARIZED_AFFINITY",
    "PROXY_MC_CLOSURE_DEFICIT",
    "PROXY_CLUSTERED_OBJECT_COUNT",
}

ALLOWED_ORIGIN = {"existing", "new"}
ALLOWED_EVIDENCE = {"analytic", "lean", "experiment"}
ALLOWED_CLAIM_TYPES = {
    "monotonicity_impossibility",
    "obstruction",
    "variational_obstruction",
    "uniqueness_under_contraction",
    "saturation",
    "finite_capacity_obstruction",
}


def _load_json_yaml(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON-compatible YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level must be an object")
    return data


def _ids(items: Any, kind: str, errors: list[str]) -> list[str]:
    if not isinstance(items, list):
        errors.append(f"{kind}: expected list")
        return []
    out: list[str] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{kind}[{idx}]: expected object")
            continue
        val = item.get("id")
        if not isinstance(val, str) or not val:
            errors.append(f"{kind}[{idx}]: missing non-empty id")
            continue
        out.append(val)
    return out


def validate_all(config_dir: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts: dict[str, int] = {
        "assumption_atoms": 0,
        "assumption_bundles": 0,
        "theorems": 0,
        "theorem_audits": 0,
        "proxy_audits": 0,
    }

    assumptions_path = config_dir / "assumptions.yaml"
    theorems_path = config_dir / "theorems.yaml"
    proxies_path = config_dir / "proxies.yaml"

    for req in (assumptions_path, theorems_path, proxies_path):
        if not req.exists():
            errors.append(f"missing required config: {req}")

    if errors:
        return errors, counts

    try:
        assumptions = _load_json_yaml(assumptions_path)
        theorems = _load_json_yaml(theorems_path)
        proxies = _load_json_yaml(proxies_path)
    except ValueError as exc:
        return [str(exc)], counts

    for key in ("version", "atoms", "bundles"):
        if key not in assumptions:
            errors.append(f"assumptions.yaml missing key: {key}")
    for key in ("version", "source_basis_registry", "audit_registry", "theorems"):
        if key not in theorems:
            errors.append(f"theorems.yaml missing key: {key}")
    for key in ("version", "proxy_audits"):
        if key not in proxies:
            errors.append(f"proxies.yaml missing key: {key}")

    atom_ids = _ids(assumptions.get("atoms"), "atoms", errors)
    bundle_ids = _ids(assumptions.get("bundles"), "bundles", errors)
    source_ids = _ids(theorems.get("source_basis_registry"), "source_basis_registry", errors)
    theorem_audit_ids = _ids(theorems.get("audit_registry"), "audit_registry", errors)
    theorem_ids = _ids(theorems.get("theorems"), "theorems", errors)
    proxy_ids = _ids(proxies.get("proxy_audits"), "proxy_audits", errors)

    counts["assumption_atoms"] = len(atom_ids)
    counts["assumption_bundles"] = len(bundle_ids)
    counts["theorems"] = len(theorem_ids)
    counts["theorem_audits"] = len(theorem_audit_ids)
    counts["proxy_audits"] = len(proxy_ids)

    atom_set = set(atom_ids)
    bundle_set = set(bundle_ids)
    source_set = set(source_ids)
    theorem_audit_set = set(theorem_audit_ids)
    proxy_set = set(proxy_ids)
    theorem_id_set = set(theorem_ids)

    if len(atom_ids) != len(atom_set):
        errors.append("atoms: duplicate ids detected")
    if len(bundle_ids) != len(bundle_set):
        errors.append("bundles: duplicate ids detected")
    if len(theorem_ids) != len(theorem_id_set):
        errors.append("theorems: duplicate ids detected")
    if len(theorem_audit_ids) != len(theorem_audit_set):
        errors.append("audit_registry: duplicate ids detected")
    if len(proxy_ids) != len(proxy_set):
        errors.append("proxy_audits: duplicate ids detected")

    missing_atoms = sorted(REQUIRED_ASSUMPTION_ATOMS - atom_set)
    missing_bundles = sorted(REQUIRED_BUNDLES - bundle_set)
    missing_theorems = sorted(REQUIRED_THEOREMS - theorem_id_set)
    missing_sources = sorted(REQUIRED_SOURCE_BASIS - source_set)
    missing_theorem_audits = sorted(REQUIRED_THEOREM_AUDITS - theorem_audit_set)
    missing_proxy = sorted(REQUIRED_PROXIES - proxy_set)

    if missing_atoms:
        errors.append(f"missing required atom ids: {missing_atoms}")
    if missing_bundles:
        errors.append(f"missing required bundle ids: {missing_bundles}")
    if missing_theorems:
        errors.append(f"missing required theorem ids: {missing_theorems}")
    if missing_sources:
        errors.append(f"missing required source basis ids: {missing_sources}")
    if missing_theorem_audits:
        errors.append(f"missing required theorem audit ids: {missing_theorem_audits}")
    if missing_proxy:
        errors.append(f"missing required proxy ids: {missing_proxy}")

    cross_ids = sorted(theorem_audit_set & proxy_set)
    if cross_ids:
        errors.append(f"theorem/proxy audit ids are not disjoint: {cross_ids}")

    bundle_map: dict[str, list[str]] = {}
    bundles = assumptions.get("bundles", [])
    if isinstance(bundles, list):
        for b in bundles:
            if not isinstance(b, dict):
                continue
            bid = b.get("id")
            ass = b.get("assumptions")
            if isinstance(bid, str) and isinstance(ass, list):
                bundle_map[bid] = [x for x in ass if isinstance(x, str)]
                for atom in bundle_map[bid]:
                    if atom not in atom_set:
                        errors.append(f"bundle {bid} references unknown atom: {atom}")

    theorems_list = theorems.get("theorems", [])
    if isinstance(theorems_list, list):
        for th in theorems_list:
            if not isinstance(th, dict):
                continue
            tid = th.get("id", "<unknown>")
            for field in (
                "id",
                "short_name",
                "claim_type",
                "assumptions",
                "conclusion",
                "origin",
                "evidence_required",
                "source_basis_refs",
                "required_witnesses",
                "required_audits",
            ):
                if field not in th:
                    errors.append(f"theorem {tid} missing field: {field}")

            claim_type = th.get("claim_type")
            if claim_type not in ALLOWED_CLAIM_TYPES:
                errors.append(f"theorem {tid} invalid claim_type: {claim_type}")

            origin = th.get("origin")
            if origin not in ALLOWED_ORIGIN:
                errors.append(f"theorem {tid} invalid origin: {origin}")

            evidence = th.get("evidence_required")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"theorem {tid} evidence_required must be non-empty list")
            else:
                bad = [e for e in evidence if e not in ALLOWED_EVIDENCE]
                if bad:
                    errors.append(f"theorem {tid} invalid evidence_required entries: {bad}")

            refs = th.get("source_basis_refs")
            if isinstance(refs, list):
                for ref in refs:
                    if ref not in source_set:
                        errors.append(f"theorem {tid} references unknown source_basis_ref: {ref}")
            else:
                errors.append(f"theorem {tid} source_basis_refs must be a list")

            audits = th.get("required_audits")
            if isinstance(audits, list):
                for aid in audits:
                    if aid not in theorem_audit_set:
                        errors.append(f"theorem {tid} references unknown theorem audit: {aid}")
                    if aid in proxy_set:
                        errors.append(f"theorem {tid} uses proxy audit id in required_audits: {aid}")
            else:
                errors.append(f"theorem {tid} required_audits must be a list")

            aobj = th.get("assumptions")
            if not isinstance(aobj, dict):
                errors.append(f"theorem {tid} assumptions must be an object")
                continue
            for k in ("bundles", "atoms", "normalized_atoms"):
                if k not in aobj:
                    errors.append(f"theorem {tid} assumptions missing key: {k}")
            brefs = aobj.get("bundles") if isinstance(aobj.get("bundles"), list) else None
            arefs = aobj.get("atoms") if isinstance(aobj.get("atoms"), list) else None
            norm = aobj.get("normalized_atoms") if isinstance(aobj.get("normalized_atoms"), list) else None
            if brefs is None or arefs is None or norm is None:
                errors.append(f"theorem {tid} assumptions bundles/atoms/normalized_atoms must be lists")
                continue

            expanded: set[str] = set()
            for bid in brefs:
                if bid not in bundle_set:
                    errors.append(f"theorem {tid} references unknown bundle: {bid}")
                    continue
                expanded.update(bundle_map.get(bid, []))
            for aid in arefs:
                if aid not in atom_set:
                    errors.append(f"theorem {tid} references unknown atom: {aid}")
                    continue
                expanded.add(aid)

            normalized_expected = sorted(expanded)
            normalized_given = norm
            if normalized_given != sorted(set(normalized_given)):
                errors.append(f"theorem {tid} normalized_atoms must be sorted unique")
            if normalized_given != normalized_expected:
                errors.append(
                    f"theorem {tid} normalized_atoms mismatch: expected {normalized_expected} got {normalized_given}"
                )

    return errors, counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate project config registries.")
    parser.add_argument("--summary", action="store_true", help="Print concise summary output")
    parser.add_argument(
        "--config-dir",
        default="configs",
        help="Directory containing assumptions.yaml, theorems.yaml, proxies.yaml",
    )
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
            f"atoms={counts['assumption_atoms']} "
            f"bundles={counts['assumption_bundles']} "
            f"theorems={counts['theorems']} "
            f"theorem_audits={counts['theorem_audits']} "
            f"proxy_audits={counts['proxy_audits']}"
        )
    else:
        print("Config validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
