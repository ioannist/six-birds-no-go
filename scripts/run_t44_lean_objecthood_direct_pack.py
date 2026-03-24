#!/usr/bin/env python3
"""Run T44 objecthood direct-pack validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

REQUIRED_DIRECT_NAMES = [
    'LawEquivalent',
    'tvDistance',
    'tvDistance_nonneg',
    'tvDistance_symm',
    'tvDistance_triangle',
    'tvDistance_eq_zero_iff_lawEquivalent',
    'FixedDistribution',
    'epsStable',
    'TVDobrushinLayer',
    'fixedDistribution_unique',
    'epsStable_separation_bound',
    'objecthood_directPack',
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def fail(msg: str) -> None:
    raise ValueError(msg)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        fail(f'{path} must parse to object')
    return data


def theorem_map(rows: list[dict]) -> dict[str, dict]:
    return {row['theorem_id']: row for row in rows}


def repro_flags(text: str) -> dict[str, bool]:
    return {f'reproduce_includes_t{i}': f'run_t{i}' in text for i in range(20, 45)}


def main() -> int:
    parser = argparse.ArgumentParser(description='Run T44 objecthood direct-pack validation')
    parser.add_argument('--output-dir', default='results/T44')
    args = parser.parse_args()

    direct_yaml_p = Path('docs/project/lean_objecthood_direct.yaml')
    tv_feas_p = Path('docs/project/lean_objecthood_tv_feasibility.yaml')
    tv_boundary_p = Path('docs/project/lean_objecthood_tv_formal_boundary.md')
    uniq_p = Path('docs/project/lean_objecthood_uniqueness.yaml')
    uniq_boundary_p = Path('docs/project/lean_objecthood_formal_boundary.md')
    readiness_p = Path('docs/project/readiness_checklist.yaml')
    atlas_p = Path('docs/project/theorem_atlas.yaml')
    pack_p = Path('docs/project/theorem_pack_objecthood.yaml')
    claims_p = Path('docs/project/claim_audit_freeze.yaml')
    repro_p = Path('src/sixbirds_nogo/repro.py')
    lean_root_p = Path('lean/SixBirdsNoGo.lean')
    direct_lean_p = Path('lean/SixBirdsNoGo/ObjecthoodDirectPack.lean')
    direct_example_p = Path('lean/SixBirdsNoGo/ObjecthoodDirectPackExample.lean')

    for path in [direct_yaml_p, tv_feas_p, tv_boundary_p, uniq_p, uniq_boundary_p, readiness_p, atlas_p, pack_p, claims_p]:
        if not path.exists():
            fail(f'missing required input: {path}')

    direct_yaml = load_json(direct_yaml_p)
    tv_feas = load_json(tv_feas_p)
    uniq = load_json(uniq_p)
    readiness = theorem_map(load_json(readiness_p)['theorems'])
    atlas = theorem_map(load_json(atlas_p)['theorems'])
    pack = theorem_map(load_json(pack_p)['theorem_fronts'])
    claim_map = {row['claim_id']: row for row in load_json(claims_p)['claims']}
    repro_text = repro_p.read_text(encoding='utf-8') if repro_p.exists() else ''
    root_text = lean_root_p.read_text(encoding='utf-8') if lean_root_p.exists() else ''

    branch_a = direct_lean_p.exists()
    outcome_mode = direct_yaml['theorem_fronts'][0]['outcome_mode']
    if branch_a and outcome_mode != 'direct_theorem_pack':
        fail('ObjecthoodDirectPack exists but outcome_mode is not direct_theorem_pack')
    if (not branch_a) and outcome_mode != 'permanent_auxiliary_boundary':
        fail('branch B requires permanent_auxiliary_boundary outcome_mode')

    lake_status = 'skipped_tool_unavailable'
    if shutil.which('lake') is not None:
        proc = subprocess.run(['lake', 'build'], cwd='lean', capture_output=True, text=True, check=False)
        lake_status = 'passed' if proc.returncode == 0 else 'failed'
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': 1,
        'outcome_mode': outcome_mode,
        'direct_front_count': sum(1 for row in readiness.values() if row['lean_support']['status'] == 'direct'),
        'auxiliary_front_count': sum(1 for row in readiness.values() if row['lean_support']['status'] == 'auxiliary_only'),
        'missing_front_count': sum(1 for row in readiness.values() if row['lean_support']['status'] == 'missing'),
        'objecthood_direct': readiness['NG_OBJECT_CONTRACTIVE']['lean_support']['status'] == 'direct',
        'direct_pack_present': branch_a,
        'permanent_boundary_note_present': bool(tv_boundary_p.read_text(encoding='utf-8').strip()),
        't43_decision_preserved': tv_feas['decision']['decision_mode'] == 'proceed_to_tv_bridge',
        't30_uniqueness_core_retained': uniq['theorem_fronts'][0]['outcome_mode'] == 'direct_uniqueness_theorem',
        'tv_distance_formalized': False,
        'law_equivalence_explicit': False,
        'dobrushin_layer_present': False,
        'fixed_distribution_unique_present': False,
        'eps_stability_predicate_present': False,
        'separation_bound_present': False,
        'proxy_metrics_out_of_scope': True,
        'noncontractive_context_out_of_scope': True,
        'next_ticket_id': direct_yaml['theorem_fronts'][0]['next_ticket']['id'] if direct_yaml['theorem_fronts'][0]['next_ticket'] else None,
        'lake_build_status': lake_status,
        **repro_flags(repro_text),
        'vision_present': Path('vision.md').exists(),
        'status': 'success',
    }

    if branch_a:
        direct_text = direct_lean_p.read_text(encoding='utf-8')
        example_text = direct_example_p.read_text(encoding='utf-8') if direct_example_p.exists() else ''
        for token in REQUIRED_DIRECT_NAMES:
            if token not in direct_text:
                fail(f'missing direct-pack token: {token}')
        for imp in ['import SixBirdsNoGo.ObjecthoodDirectPack', 'import SixBirdsNoGo.ObjecthoodDirectPackExample']:
            if imp not in root_text:
                fail(f'missing root import: {imp}')
        if readiness['NG_OBJECT_CONTRACTIVE']['lean_support']['status'] != 'direct':
            fail('readiness must mark objecthood direct in branch A')
        if atlas['NG_OBJECT_CONTRACTIVE']['support_snapshot']['lean_support']['status'] != 'direct':
            fail('atlas must mark objecthood direct in branch A')
        if pack['NG_OBJECT_CONTRACTIVE']['next_ticket']['id'] != 'PLAN_NEXT_20_objecthood_scope_guardrail_hold':
            fail('theorem pack next_ticket mismatch in branch A')
        if claim_map['NG_OBJECT_CONTRACTIVE.core']['next_ticket']['id'] != 'PLAN_NEXT_20_objecthood_scope_guardrail_hold':
            fail('claim freeze next_ticket mismatch in branch A')
        summary.update({
            'tv_distance_formalized': True,
            'law_equivalence_explicit': True,
            'dobrushin_layer_present': 'TVDobrushinLayer' in direct_text,
            'fixed_distribution_unique_present': 'fixedDistribution_unique' in direct_text,
            'eps_stability_predicate_present': 'epsStable' in direct_text,
            'separation_bound_present': 'epsStable_separation_bound' in direct_text,
        })
    else:
        if readiness['NG_OBJECT_CONTRACTIVE']['lean_support']['status'] != 'auxiliary_only':
            fail('readiness must keep objecthood auxiliary_only in branch B')
        if atlas['NG_OBJECT_CONTRACTIVE']['support_snapshot']['lean_support']['status'] != 'auxiliary_only':
            fail('atlas must keep objecthood auxiliary_only in branch B')
        if pack['NG_OBJECT_CONTRACTIVE']['remaining_blockers'] != []:
            fail('theorem pack blockers must be empty in branch B')
        if pack['NG_OBJECT_CONTRACTIVE']['next_ticket'] is not None:
            fail('theorem pack next_ticket must be null in branch B')
        if claim_map['NG_OBJECT_CONTRACTIVE.core']['blockers'] != []:
            fail('claim blockers must be empty in branch B')
        if claim_map['NG_OBJECT_CONTRACTIVE.core']['next_ticket'] is not None:
            fail('claim next_ticket must be null in branch B')
        if tv_feas['decision']['decision_mode'] != 'freeze_boundary_now':
            fail('T43 decision must be freeze_boundary_now in branch B post-state')
        statuses = {row['obligation_id']: row['status'] for row in tv_feas['obligation_matrix']}
        if not any(statuses[oid] == 'requires_forbidden_expansion' for oid in [
            'OBJ_TV_DISTANCE_ON_FINITE_LAWS',
            'OBJ_TV_TRIANGLE_AND_ZERO_LEMMAS',
            'OBJ_DOBRUSHIN_CONTRACTION_INTERFACE',
            'OBJ_FIXED_DISTRIBUTION_ON_FINITE_LAWS',
            'OBJ_TV_EPS_STABILITY_PREDICATE',
            'OBJ_APPROXIMATE_OBJECT_SEPARATION_BOUND',
        ]):
            fail('branch B requires at least one forbidden-expansion objecthood obligation')
        if uniq['theorem_fronts'][0]['readiness_delta']['full_tv_bound_bridge_pending'] is not False:
            fail('uniqueness provenance must mark full_tv_bound_bridge_pending false in branch B')
        if uniq['theorem_fronts'][0]['next_ticket'] is not None:
            fail('uniqueness provenance next_ticket must be null in branch B')
        summary['t43_decision_preserved'] = False

    if repro_p.exists() and 'run_t44_lean_objecthood_direct_pack.py' not in repro_text:
        fail('repro.py must include run_t44_lean_objecthood_direct_pack.py')

    expected_common = {
        'theorem_count': 1,
        'permanent_boundary_note_present': True,
        't30_uniqueness_core_retained': True,
        'proxy_metrics_out_of_scope': True,
        'noncontractive_context_out_of_scope': True,
    }
    for key, value in expected_common.items():
        if summary[key] != value:
            fail(f'summary anchor mismatch: {key}')

    if branch_a:
        branch_expected = {
            'outcome_mode': 'direct_theorem_pack',
            'direct_front_count': 8,
            'auxiliary_front_count': 0,
            'missing_front_count': 0,
            'objecthood_direct': True,
            'direct_pack_present': True,
            't43_decision_preserved': True,
            'tv_distance_formalized': True,
            'law_equivalence_explicit': True,
            'dobrushin_layer_present': True,
            'fixed_distribution_unique_present': True,
            'eps_stability_predicate_present': True,
            'separation_bound_present': True,
            'next_ticket_id': 'PLAN_NEXT_20_objecthood_scope_guardrail_hold',
        }
    else:
        branch_expected = {
            'outcome_mode': 'permanent_auxiliary_boundary',
            'direct_front_count': 7,
            'auxiliary_front_count': 1,
            'missing_front_count': 0,
            'objecthood_direct': False,
            'direct_pack_present': False,
            't43_decision_preserved': False,
            'tv_distance_formalized': False,
            'law_equivalence_explicit': False,
            'dobrushin_layer_present': False,
            'fixed_distribution_unique_present': False,
            'eps_stability_predicate_present': False,
            'separation_bound_present': False,
            'next_ticket_id': None,
        }
    for key, value in branch_expected.items():
        if summary[key] != value:
            fail(f'branch summary anchor mismatch: {key}')

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'lean_objecthood_direct_pack_summary.json'
    out_path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(out_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
