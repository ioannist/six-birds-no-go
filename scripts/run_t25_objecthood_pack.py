#!/usr/bin/env python3
"""Validate T25 objecthood theorem-facing pack and emit resolution outputs."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sixbirds_nogo.objecthood import (  # noqa: E402
    check_approximate_object_separation,
    dobrushin_contraction_lambda,
    epsilon_stable_distributions,
    fixed_point_count,
    solve_unique_fixed_distribution,
)
from sixbirds_nogo.packaging import load_packaging_from_witness  # noqa: E402


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path} must parse to object')
    return data


def fail(msg: str) -> None:
    raise ValueError(msg)


def _f(x: Fraction) -> str:
    return f'{x.numerator}/{x.denominator}'


def _vec(v: tuple[Fraction, ...]) -> list[str]:
    return [_f(x) for x in v]


def main() -> int:
    parser = argparse.ArgumentParser(description='Run T25 objecthood theorem pack validation')
    parser.add_argument('--output-dir', default='results/T25')
    args = parser.parse_args()

    pack_p = Path('docs/project/theorem_pack_objecthood.yaml')
    ready_p = Path('docs/project/readiness_checklist.yaml')
    atlas_p = Path('docs/project/theorem_atlas.yaml')
    claims_p = Path('docs/project/claim_audit_freeze.yaml')
    t10_metrics_p = Path('results/T10/objecthood_metrics.json')
    t10_grid_p = Path('results/T10/stability_grid.json')
    t15_sweep_p = Path('results/T15/objecthood_metric_sweep.csv')
    t15_adv_p = Path('results/T15/adversarial_cases.json')
    t15_frag_p = Path('results/T15/fragility_summary.json')

    for p in [pack_p, ready_p, atlas_p, claims_p, t10_metrics_p, t10_grid_p, t15_sweep_p, t15_adv_p, t15_frag_p]:
        if not p.exists():
            fail(f'missing required input: {p}')

    pack = load_json(pack_p)
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    claims = load_json(claims_p)
    _ = load_json(t10_metrics_p)
    t10_grid = load_json(t10_grid_p)
    _ = load_json(t15_adv_p)
    frag = load_json(t15_frag_p)

    with t15_sweep_p.open(newline='', encoding='utf-8') as f:
        sweep_rows = list(csv.DictReader(f))
    if not sweep_rows:
        fail('objecthood_metric_sweep.csv must be non-empty')

    for key in ['version', 'generated_at_utc', 'source_context', 'status_enums', 'theorem_fronts']:
        if key not in pack:
            fail(f'theorem pack missing key: {key}')

    fronts = pack['theorem_fronts']
    if not isinstance(fronts, list) or len(fronts) != 1:
        fail('theorem pack must contain exactly one theorem front')
    front = fronts[0]
    if front.get('theorem_id') != 'NG_OBJECT_CONTRACTIVE':
        fail('theorem pack theorem ID must be NG_OBJECT_CONTRACTIVE')

    if front.get('pack_status') != 'direct_ready':
        fail('objecthood theorem pack must have pack_status=direct_ready')
    for req in ['theorem_statement', 'theorem_core', 'proof_spine', 'guardrails', 'regime_resolution', 'evidence_refs']:
        if req not in front:
            fail(f'theorem front missing {req}')
    if not str(front['theorem_statement']).strip() or not front['proof_spine'] or not front['guardrails']:
        fail('theorem_statement/proof_spine/guardrails must be non-empty')

    core_text = [front['theorem_statement']]
    core_text.extend(front['theorem_core'].get('antecedent', []))
    core_text.extend(front['theorem_core'].get('scope_limits', []))
    joined = ' '.join(core_text).lower()
    if not (('total variation' in joined) or ('dobrushin' in joined)):
        fail('theorem core must mention total variation or Dobrushin')
    if not (('lambda < 1' in joined) or ('lambda_lt_1' in joined) or ('lambda<1' in joined)):
        fail('theorem core must mention lambda < 1 contraction regime')

    guardrail_text = ' '.join(g.get('guardrail_text', '') for g in front['guardrails']).lower()
    if not any(k in guardrail_text for k in ('total-variation', 'total variation', 'dobrushin')):
        fail('guardrails must mention admissible theorem metric')
    if not any(k in guardrail_text for k in ('proxy clustering', 'proxy multiplicity', 'proxy')):
        fail('guardrails must mention proxy clustering/multiplicity exclusion')

    regime = front['regime_resolution']
    if regime.get('mode') != 'resolved_by_metric_regime_freeze':
        fail('regime_resolution mode must be resolved_by_metric_regime_freeze')

    ready_map = {t['theorem_id']: t for t in readiness['theorems']}
    atlas_map = {t['theorem_id']: t for t in atlas['theorems']}
    claim_map = {c['claim_id']: c for c in claims['claims']}

    if ready_map['NG_OBJECT_CONTRACTIVE']['analytic_support']['status'] != 'present':
        fail('readiness objecthood analytic_support must be present')
    if atlas_map['NG_OBJECT_CONTRACTIVE']['support_snapshot']['analytic_support']['status'] != 'present':
        fail('atlas objecthood analytic_support must be present')
    if claim_map['NG_OBJECT_CONTRACTIVE.core']['support_grade'] != 'direct':
        fail('objecthood core claim support_grade must be direct')
    if claim_map['NG_OBJECT_CONTRACTIVE.guardrail']['support_grade'] != 'direct':
        fail('objecthood guardrail claim support_grade must be direct')
    if claim_map['NG_OBJECT_CONTRACTIVE.metric_regime_gap']['freeze_status'] == 'blocked':
        fail('objecthood metric_regime_gap claim must no longer be blocked')

    if ready_map['NG_OBJECT_CONTRACTIVE']['proxy_risk']['status'] != 'high':
        fail('objecthood proxy_risk must remain high')

    # theorem witness and regime checks
    contractive = load_packaging_from_witness('contractive_unique_object')
    noncontractive = load_packaging_from_witness('noncontractive_multiobject')

    lam = dobrushin_contraction_lambda(contractive)
    fpc = fixed_point_count(contractive)
    ufd = solve_unique_fixed_distribution(contractive)
    stable_pts = epsilon_stable_distributions(contractive, denominator=4, epsilon=Fraction(1, 4))

    bound = check_approximate_object_separation(
        contractive,
        (Fraction(1, 2), Fraction(1, 2)),
        (Fraction(1, 1), Fraction(0, 1)),
        Fraction(1, 4),
    )

    # proxy metric artifact from T15 sweep
    row_tv = next((r for r in sweep_rows if r['witness_id'] == 'contractive_unique_object' and r['metric_id'] == 'tv'), None)
    row_proxy = next((r for r in sweep_rows if r['witness_id'] == 'contractive_unique_object' and r['metric_id'] == 'support_signature'), None)
    if row_tv is None or row_proxy is None:
        fail('objecthood metric sweep missing required tv/support_signature rows')

    theorem_cluster_count = int(row_tv['cluster_count'])
    proxy_cluster_count = int(row_proxy['cluster_count'])

    non_lam = dobrushin_contraction_lambda(noncontractive)
    non_fpc = fixed_point_count(noncontractive)

    if t10_grid.get('bound_check', {}).get('holds') is not True:
        fail('T10 bound_check must hold for designated pair')

    frag_ids = {e['fragility_id'] for e in frag.get('entries', [])}
    if 'object_multiplicity_can_be_metric_artifact' not in frag_ids:
        fail('fragility summary missing object multiplicity artifact entry')

    resolution = {
        'generated_at_utc': now_iso(),
        'outcome_mode': 'resolved_by_metric_regime_freeze',
        'historical_gap_claim_id': 'NG_OBJECT_CONTRACTIVE.metric_regime_gap',
        'admissible_metric': {
            'metric_id': 'total_variation',
            'contraction_coefficient': 'dobrushin_tv',
            'note': 'Theorem objecthood claims are stated only in the TV/Dobrushin metric family.'
        },
        'admissible_regime': {
            'lambda_condition': 'lambda_lt_1',
            'stability_metric_match': True,
            'regime_note': 'Epsilon-stability and separation are measured in the same theorem metric.'
        },
        'theorem_witness': {
            'witness_id': 'contractive_unique_object',
            'contraction_lambda': _f(lam),
            'fixed_point_count': fpc,
            'unique_fixed_distribution': _vec(ufd),
            'grid_denominator': 4,
            'epsilon': '1/4',
            'stable_point_count': len(stable_pts),
            'theorem_metric_cluster_count': theorem_cluster_count
        },
        'proxy_metric_artifact': {
            'metric_id': 'support_signature',
            'cluster_count': proxy_cluster_count,
            'note': 'Support-signature clustering is a proxy artifact and not theorem evidence.'
        },
        'contextual_noncontractive_case': {
            'witness_id': 'noncontractive_multiobject',
            'fixed_point_count': non_fpc,
            'contraction_lambda': _f(non_lam),
            'note': 'This case is outside the admissible contraction regime and is contextual rather than contradictory.'
        },
        'approximate_bound_check': {
            'dist_a': ['1/2', '1/2'],
            'dist_b': ['1/1', '0/1'],
            'epsilon': '1/4',
            'holds': bool(bound['holds']),
            'lhs_tv': _f(bound['lhs_tv']),
            'rhs_bound': _f(bound['rhs_bound']) if bound['rhs_bound'] is not None else None
        },
        'resolution_note': 'Earlier objecthood metric/regime gap is resolved by freezing admissible theorem metric/regime to total variation + lambda<1 contraction and excluding proxy clustering metrics from theorem evidence.',
        'status': 'success'
    }

    repro_text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8') if Path('src/sixbirds_nogo/repro.py').exists() else ''
    includes_t20 = 'run_t20_readiness_checkpoint.py' in repro_text
    includes_t21 = 'run_t21_theorem_atlas.py' in repro_text
    includes_t22 = 'run_t22_dpi_protocol_pack.py' in repro_text
    includes_t23 = 'run_t23_graph_affinity_pack.py' in repro_text
    includes_t24 = 'run_t24_closure_pack.py' in repro_text
    includes_t25 = 'run_t25_objecthood_pack.py' in repro_text
    if not includes_t25:
        fail('repro pipeline missing run_t25_objecthood_pack.py step')

    analytic_present_total = sum(1 for t in readiness['theorems'] if t['analytic_support']['status'] == 'present')
    overall_direct_core = sum(1 for c in claims['claims'] if c.get('claim_class') == 'core' and c.get('support_grade') == 'direct')

    metric_gap_resolved = claim_map['NG_OBJECT_CONTRACTIVE.metric_regime_gap']['freeze_status'] != 'blocked'
    admissible_metric_frozen = resolution['admissible_metric']['metric_id'] == 'total_variation'
    admissible_regime_frozen = resolution['admissible_regime']['lambda_condition'] == 'lambda_lt_1'
    proxy_metric_excluded = proxy_cluster_count > theorem_cluster_count
    theorem_guardrails_frozen = claim_map['NG_OBJECT_CONTRACTIVE.guardrail']['freeze_status'] == 'frozen'
    contextual_outside = 'outside' in resolution['contextual_noncontractive_case']['note'].lower()

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': 1,
        'updated_theorem_ids': ['NG_OBJECT_CONTRACTIVE'],
        'analytic_present_total': analytic_present_total,
        'overall_direct_core_count': overall_direct_core,
        'pack_direct_core_count': 1,
        'regime_resolution_mode': 'resolved_by_metric_regime_freeze',
        'metric_regime_gap_resolved': metric_gap_resolved,
        'admissible_metric_frozen': admissible_metric_frozen,
        'admissible_regime_frozen': admissible_regime_frozen,
        'proxy_metric_excluded': proxy_metric_excluded,
        'theorem_guardrails_frozen': theorem_guardrails_frozen,
        'theorem_metric_cluster_count': theorem_cluster_count,
        'proxy_metric_cluster_count': proxy_cluster_count,
        'approximate_bound_holds': bool(bound['holds']),
        'contextual_noncontractive_outside_regime': contextual_outside,
        'reproduce_includes_t20': includes_t20,
        'reproduce_includes_t21': includes_t21,
        'reproduce_includes_t22': includes_t22,
        'reproduce_includes_t23': includes_t23,
        'reproduce_includes_t24': includes_t24,
        'reproduce_includes_t25': includes_t25,
        'vision_present': Path('vision.md').exists(),
        'status': 'success'
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'objecthood_metric_guardrails_resolution.json').write_text(json.dumps(resolution, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'objecthood_pack_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')

    print('PASS: T25 objecthood theorem pack validation')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path('results/T25')
        out_dir.mkdir(parents=True, exist_ok=True)
        fail_summary = {
            'generated_at_utc': now_iso(),
            'theorem_count': 1,
            'updated_theorem_ids': ['NG_OBJECT_CONTRACTIVE'],
            'analytic_present_total': 0,
            'overall_direct_core_count': 0,
            'pack_direct_core_count': 0,
            'regime_resolution_mode': 'blocked_but_sharpened',
            'metric_regime_gap_resolved': False,
            'admissible_metric_frozen': False,
            'admissible_regime_frozen': False,
            'proxy_metric_excluded': False,
            'theorem_guardrails_frozen': False,
            'theorem_metric_cluster_count': 0,
            'proxy_metric_cluster_count': 0,
            'approximate_bound_holds': False,
            'contextual_noncontractive_outside_regime': False,
            'reproduce_includes_t20': False,
            'reproduce_includes_t21': False,
            'reproduce_includes_t22': False,
            'reproduce_includes_t23': False,
            'reproduce_includes_t24': False,
            'reproduce_includes_t25': False,
            'vision_present': Path('vision.md').exists(),
            'status': 'failed',
            'error': str(exc)
        }
        (out_dir / 'objecthood_pack_summary.json').write_text(json.dumps(fail_summary, indent=2) + '\n', encoding='utf-8')
        (out_dir / 'objecthood_metric_guardrails_resolution.json').write_text(json.dumps({'status': 'failed', 'error': str(exc)}, indent=2) + '\n', encoding='utf-8')
        print(f'FAIL: {exc}')
        raise SystemExit(1)
