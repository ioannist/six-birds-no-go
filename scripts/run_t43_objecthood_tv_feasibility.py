#!/usr/bin/env python3
"""Run T43 objecthood TV-feasibility validation and emit a summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

REQUIRED_OBLIGATION_IDS = [
    'OBJ_BASE_FINITE_LAWS',
    'OBJ_STRICT_CONTRACTION_UNIQUENESS_CORE',
    'OBJ_TV_DISTANCE_ON_FINITE_LAWS',
    'OBJ_TV_TRIANGLE_AND_ZERO_LEMMAS',
    'OBJ_DOBRUSHIN_CONTRACTION_INTERFACE',
    'OBJ_FIXED_DISTRIBUTION_ON_FINITE_LAWS',
    'OBJ_TV_EPS_STABILITY_PREDICATE',
    'OBJ_APPROXIMATE_OBJECT_SEPARATION_BOUND',
    'OBJ_PROXY_AND_NONCONTRACTIVE_CONTEXT_OUT_OF_SCOPE',
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
    return {f'reproduce_includes_t{i}': f'run_t{i}' in text for i in range(20, 44)}


def main() -> int:
    parser = argparse.ArgumentParser(description='Run T43 objecthood TV-feasibility validation')
    parser.add_argument('--output-dir', default='results/T43')
    args = parser.parse_args()

    yaml_p = Path('docs/project/lean_objecthood_tv_feasibility.yaml')
    boundary_p = Path('docs/project/lean_objecthood_tv_formal_boundary.md')
    pack_p = Path('docs/project/theorem_pack_objecthood.yaml')
    readiness_p = Path('docs/project/readiness_checklist.yaml')
    atlas_p = Path('docs/project/theorem_atlas.yaml')
    uniq_p = Path('docs/project/lean_objecthood_uniqueness.yaml')
    charter_p = Path('docs/project/lean_probability_scope_charter.yaml')
    t10_metrics_p = Path('results/T10/objecthood_metrics.json')
    t10_grid_p = Path('results/T10/stability_grid.json')
    t15_sweep_p = Path('results/T15/objecthood_metric_sweep.csv')
    t15_adv_p = Path('results/T15/adversarial_cases.json')
    repro_p = Path('src/sixbirds_nogo/repro.py')

    for path in [yaml_p, boundary_p, pack_p, readiness_p, atlas_p, uniq_p, charter_p, t10_metrics_p, t10_grid_p, t15_sweep_p, t15_adv_p]:
        if not path.exists():
            fail(f'missing required input: {path}')

    data = load_json(yaml_p)
    pack = theorem_map(load_json(pack_p)['theorem_fronts'])
    readiness = theorem_map(load_json(readiness_p)['theorems'])
    atlas = theorem_map(load_json(atlas_p)['theorems'])
    uniq = load_json(uniq_p)
    boundary_text = boundary_p.read_text(encoding='utf-8')
    repro_text = repro_p.read_text(encoding='utf-8') if repro_p.exists() else ''

    target = data['theorem_target']
    if target['theorem_id'] != 'NG_OBJECT_CONTRACTIVE':
        fail('theorem target must be NG_OBJECT_CONTRACTIVE')

    snapshot = data['current_frontier_snapshot']
    if len(snapshot['direct_ids']) != 7 or len(snapshot['auxiliary_ids']) != 1 or len(snapshot['missing_ids']) != 0:
        fail('frontier snapshot counts must remain 7/1/0')
    if snapshot['auxiliary_ids'] != ['NG_OBJECT_CONTRACTIVE']:
        fail('objecthood must remain the only auxiliary frontier')

    if readiness['NG_OBJECT_CONTRACTIVE']['lean_support']['status'] != 'auxiliary_only':
        fail('objecthood readiness Lean status must remain auxiliary_only')
    if atlas['NG_OBJECT_CONTRACTIVE']['support_snapshot']['lean_support']['status'] != 'auxiliary_only':
        fail('objecthood atlas Lean status must remain auxiliary_only')

    obligations = data['obligation_matrix']
    ids = [row['obligation_id'] for row in obligations]
    if ids != REQUIRED_OBLIGATION_IDS:
        fail('obligation matrix IDs/order mismatch')
    obligation_map = {row['obligation_id']: row for row in obligations}
    if obligation_map['OBJ_BASE_FINITE_LAWS']['status'] != 'already_formalized':
        fail('OBJ_BASE_FINITE_LAWS status mismatch')
    if obligation_map['OBJ_STRICT_CONTRACTION_UNIQUENESS_CORE']['status'] != 'already_formalized':
        fail('OBJ_STRICT_CONTRACTION_UNIQUENESS_CORE status mismatch')
    if obligation_map['OBJ_PROXY_AND_NONCONTRACTIVE_CONTEXT_OUT_OF_SCOPE']['status'] != 'out_of_scope':
        fail('OBJ_PROXY_AND_NONCONTRACTIVE_CONTEXT_OUT_OF_SCOPE status mismatch')

    decision = data['decision']
    decision_mode = decision['decision_mode']
    if decision_mode not in {'proceed_to_tv_bridge', 'freeze_boundary_now'}:
        fail('invalid decision mode')

    middle_ids = REQUIRED_OBLIGATION_IDS[2:8]
    middle_statuses = [obligation_map[k]['status'] for k in middle_ids]
    if decision_mode == 'proceed_to_tv_bridge':
        if middle_statuses != ['needed_narrow'] * 6 and middle_statuses != ['already_formalized'] * 6:
            fail('proceed branch requires obligations 3-8 to be needed_narrow before T44 or already_formalized after completion')
        if any(row['status'] == 'requires_forbidden_expansion' for row in obligations):
            fail('proceed branch must not require forbidden expansion')
        expected_next = 'T44' if target['current_lean_status'] == 'auxiliary_only' else None
        if decision['next_ticket_id'] != expected_next:
            fail('proceed branch next ticket mismatch')
        expected_branch = 'attempt_direct_pack' if target['current_lean_status'] == 'auxiliary_only' else 'attempt_direct_pack_completed'
        if decision['t44_branch'] != expected_branch:
            fail('proceed branch t44_branch mismatch')
    else:
        if not any(status == 'requires_forbidden_expansion' for status in middle_statuses):
            fail('boundary branch requires at least one forbidden expansion obligation')
        if decision['next_ticket_id'] is not None:
            fail('post-T44 boundary branch next ticket must be null')
        if decision['t44_branch'] != 'freeze_permanent_auxiliary_boundary':
            fail('boundary branch t44_branch mismatch')

    if decision_mode not in boundary_text:
        fail('formal boundary markdown must mention the decision mode')
    if decision_mode == 'proceed_to_tv_bridge':
        for needle in [
            'narrow enough for a finite tv/dobrushin bridge',
            'boundary remains before any broad metric or analysis library',
            'uniqueness core is already formalized',
            'proxy clustering and noncontractive contextual cases remain out of scope',
        ]:
            if needle not in boundary_text.lower():
                fail('formal boundary markdown inconsistent with proceed decision')
    else:
        for needle in [
            'current formal boundary stops at the uniqueness core',
            'stopping point is due to forbidden broad expansion, not theorem falsity',
            'proxy clustering and noncontractive contextual cases remain out of scope',
        ]:
            if needle not in boundary_text.lower():
                fail('formal boundary markdown inconsistent with boundary decision')

    if 'proxy clustering metrics are not part of the lean target' not in json.dumps(data['non_goals']).lower():
        fail('proxy metrics must be explicitly out of scope')
    if 'noncontractive contextual cases are not part of the lean target' not in json.dumps(data['non_goals']).lower():
        fail('noncontractive contextual cases must be explicitly out of scope')

    uniq_row = uniq['theorem_fronts'][0]
    if uniq_row['theorem_id'] != 'NG_OBJECT_CONTRACTIVE':
        fail('uniqueness provenance theorem_id mismatch')
    if decision_mode == 'proceed_to_tv_bridge':
        if target['current_lean_status'] == 'auxiliary_only':
            if uniq_row['readiness_delta']['full_tv_bound_bridge_pending'] is not True:
                fail('pre-T44 proceed branch requires full_tv_bound_bridge_pending true')
            if uniq_row['next_ticket']['id'] != 'T44':
                fail('pre-T44 proceed branch next ticket must be T44')
        else:
            if uniq_row['readiness_delta']['full_tv_bound_bridge_pending'] is not False:
                fail('post-T44 proceed branch requires full_tv_bound_bridge_pending false')
            if uniq_row['next_ticket'] is not None:
                fail('post-T44 proceed branch next ticket must be null')
    else:
        if uniq_row['readiness_delta']['full_tv_bound_bridge_pending'] is not False:
            fail('boundary branch requires full_tv_bound_bridge_pending false')
        if uniq_row['next_ticket'] is not None:
            fail('boundary branch next ticket must be null')

    if repro_p.exists() and 'run_t43_objecthood_tv_feasibility.py' not in repro_text:
        fail('repro.py must include run_t43_objecthood_tv_feasibility.py')

    pack_row = pack['NG_OBJECT_CONTRACTIVE']
    if pack_row['theorem_statement'] != target['theorem_statement']:
        fail('objecthood theorem statement must match frozen theorem pack statement')

    counts = {key: 0 for key in ['already_formalized', 'needed_narrow', 'requires_forbidden_expansion', 'out_of_scope']}
    for row in obligations:
        counts[row['status']] += 1

    lake_status = 'skipped_tool_unavailable'
    if shutil.which('lake') is not None:
        proc = subprocess.run(['lake', 'build'], cwd='lean', capture_output=True, text=True, check=False)
        lake_status = 'passed' if proc.returncode == 0 else 'failed'
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': 1,
        'direct_front_count': len(snapshot['direct_ids']),
        'auxiliary_front_count': len(snapshot['auxiliary_ids']),
        'missing_front_count': len(snapshot['missing_ids']),
        'current_objecthood_lean_status': readiness['NG_OBJECT_CONTRACTIVE']['lean_support']['status'],
        'obligation_count': len(obligations),
        'already_formalized_count': counts['already_formalized'],
        'needed_narrow_count': counts['needed_narrow'],
        'requires_forbidden_expansion_count': counts['requires_forbidden_expansion'],
        'out_of_scope_count': counts['out_of_scope'],
        'decision_mode': decision_mode,
        'narrow_bridge_possible': decision_mode == 'proceed_to_tv_bridge',
        'generic_metric_or_analysis_required': decision_mode == 'freeze_boundary_now',
        'uniqueness_core_retained': True,
        'proxy_metrics_out_of_scope': obligation_map['OBJ_PROXY_AND_NONCONTRACTIVE_CONTEXT_OUT_OF_SCOPE']['status'] == 'out_of_scope',
        'noncontractive_context_out_of_scope': obligation_map['OBJ_PROXY_AND_NONCONTRACTIVE_CONTEXT_OUT_OF_SCOPE']['status'] == 'out_of_scope',
        'theorem_status_unchanged': data['decision_policy']['no_status_changes_in_t43'] is True,
        'next_ticket_id': decision['next_ticket_id'],
        't44_branch': decision['t44_branch'],
        'lake_build_status': lake_status,
        **repro_flags(repro_text),
        'vision_present': Path('vision.md').exists(),
        'status': 'success',
    }

    expected = {
        'theorem_count': 1,
        'direct_front_count': 7,
        'auxiliary_front_count': 1,
        'missing_front_count': 0,
        'current_objecthood_lean_status': 'auxiliary_only',
        'obligation_count': 9,
        'out_of_scope_count': 1,
        'uniqueness_core_retained': True,
        'proxy_metrics_out_of_scope': True,
        'noncontractive_context_out_of_scope': True,
        'theorem_status_unchanged': True,
        'next_ticket_id': None if decision_mode == 'freeze_boundary_now' else ('T44' if target['current_lean_status'] == 'auxiliary_only' else None),
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f'summary anchor mismatch: {key}')

    if decision_mode == 'proceed_to_tv_bridge':
        expected_already_formalized = 2 if target['current_lean_status'] == 'auxiliary_only' else 8
        if summary['already_formalized_count'] != expected_already_formalized:
            fail('proceed branch already_formalized_count mismatch')
        branch_expected = {
            'requires_forbidden_expansion_count': 0,
            'narrow_bridge_possible': True,
            'generic_metric_or_analysis_required': False,
        }
        if target['current_lean_status'] == 'auxiliary_only':
            branch_expected['needed_narrow_count'] = 6
            branch_expected['t44_branch'] = 'attempt_direct_pack'
        else:
            branch_expected['needed_narrow_count'] = 0
            branch_expected['t44_branch'] = 'attempt_direct_pack_completed'
    else:
        if summary['already_formalized_count'] < 2:
            fail('boundary branch already_formalized_count must be >= 2')
        if summary['needed_narrow_count'] > 5:
            fail('boundary branch needed_narrow_count must be <= 5')
        if summary['requires_forbidden_expansion_count'] < 1:
            fail('boundary branch requires_forbidden_expansion_count >= 1')
        branch_expected = {
            'narrow_bridge_possible': False,
            'generic_metric_or_analysis_required': True,
            't44_branch': 'freeze_permanent_auxiliary_boundary',
            'next_ticket_id': None,
        }
    for key, value in branch_expected.items():
        if summary[key] != value:
            fail(f'branch summary anchor mismatch: {key}')

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'lean_objecthood_tv_feasibility_summary.json'
    out_path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(out_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
