#!/usr/bin/env python3
"""Validate T26 bounded-interface theorem pack and emit summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path} must parse to object')
    return data


def fail(msg: str) -> None:
    raise ValueError(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run T26 bounded-interface theorem pack validation')
    parser.add_argument('--output-dir', default='results/T26')
    args = parser.parse_args()

    pack_p = Path('docs/project/theorem_pack_bounded_interface.yaml')
    ready_p = Path('docs/project/readiness_checklist.yaml')
    atlas_p = Path('docs/project/theorem_atlas.yaml')
    claims_p = Path('docs/project/claim_audit_freeze.yaml')
    t11_metrics_p = Path('results/T11/definability_metrics.json')
    t11_demos_p = Path('results/T11/no_ladder_demos.json')
    t11_random_p = Path('results/T11/random_checks.json')
    t14_cov_p = Path('results/T14/primitive_coverage.json')
    t14_mat_p = Path('results/T14/primitive_matrix.csv')

    for p in [pack_p, ready_p, atlas_p, claims_p, t11_metrics_p, t11_demos_p, t11_random_p, t14_cov_p, t14_mat_p]:
        if not p.exists():
            fail(f'missing required input: {p}')

    pack = load_json(pack_p)
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    claims = load_json(claims_p)
    t11_metrics = load_json(t11_metrics_p)
    t11_demos = load_json(t11_demos_p)
    _ = load_json(t11_random_p)
    t14_cov = load_json(t14_cov_p)

    for key in ['version', 'generated_at_utc', 'source_context', 'status_enums', 'theorem_fronts']:
        if key not in pack:
            fail(f'theorem pack missing key: {key}')

    fronts = pack['theorem_fronts']
    if not isinstance(fronts, list) or len(fronts) != 1:
        fail('theorem pack must contain exactly one theorem front')
    front = fronts[0]
    if front.get('theorem_id') != 'NG_LADDER_BOUNDED_INTERFACE':
        fail('theorem pack theorem ID must be NG_LADDER_BOUNDED_INTERFACE')
    if front.get('pack_status') != 'direct_ready':
        fail('bounded-interface theorem pack must have pack_status=direct_ready')

    for req in ['theorem_statement', 'theorem_core', 'proof_spine', 'guardrails', 'evidence_refs']:
        if req not in front:
            fail(f'theorem front missing {req}')
    if not str(front['theorem_statement']).strip():
        fail('theorem_statement must be non-empty')
    if not front['proof_spine'] or not front['guardrails'] or not front['evidence_refs']:
        fail('proof_spine/guardrails/evidence_refs must be non-empty')

    theorem_text = [front['theorem_statement']]
    for key in ['antecedent', 'conclusion', 'scope_limits']:
        theorem_text.extend(front['theorem_core'].get(key, []))
    theorem_text.extend(front.get('proof_spine', []))
    joined = ' '.join(str(x) for x in theorem_text).lower()

    if not ('definable' in joined or '2^' in joined):
        fail('theorem core/proof spine must mention definable count or 2^')
    if not ('idempotent' in joined or 'saturat' in joined):
        fail('theorem core/proof spine must mention idempotent or saturation')
    if 'interface' not in joined:
        fail('theorem core/proof spine must mention interface')

    guardrail_text = ' '.join(g.get('guardrail_text', '') for g in front['guardrails']).lower()
    if not all(token in guardrail_text for token in ['fixed']):
        fail('guardrails must mention fixed lens/domain/package')
    if not (('lens' in guardrail_text or 'domain' in guardrail_text) and ('extension' in guardrail_text or 'scope' in guardrail_text)):
        fail('guardrails must mention fixed lens/domain/package and extension/scope')

    ready_map = {t['theorem_id']: t for t in readiness['theorems']}
    atlas_map = {t['theorem_id']: t for t in atlas['theorems']}
    claim_map = {c['claim_id']: c for c in claims['claims']}

    if ready_map['NG_LADDER_BOUNDED_INTERFACE']['analytic_support']['status'] != 'present':
        fail('readiness bounded-interface analytic_support must be present')
    if atlas_map['NG_LADDER_BOUNDED_INTERFACE']['support_snapshot']['analytic_support']['status'] != 'present':
        fail('atlas bounded-interface analytic_support must be present')
    if claim_map['NG_LADDER_BOUNDED_INTERFACE.core']['support_grade'] != 'direct':
        fail('bounded-interface core claim support_grade must be direct')
    if 'NG_LADDER_BOUNDED_INTERFACE.guardrail' not in claim_map:
        fail('bounded-interface guardrail claim missing')
    if claim_map['NG_LADDER_BOUNDED_INTERFACE.guardrail']['support_grade'] != 'direct':
        fail('bounded-interface guardrail claim support_grade must be direct')
    if ready_map['NG_LADDER_BOUNDED_INTERFACE']['proxy_risk']['status'] != 'low':
        fail('bounded-interface proxy_risk must remain low')

    # Data anchors from T11/T14.
    rows = t11_metrics.get('rows', [])
    target_row = next(
        (
            r for r in rows
            if r.get('witness_id') == 'fixed_idempotent_no_ladder'
            and r.get('lens_id') == 'base_binary'
        ),
        None,
    )
    if target_row is None:
        fail('definability metrics missing fixed_idempotent_no_ladder/base_binary row')
    if str(target_row.get('no_ladder_holds', '')).lower() != 'true':
        fail('fixed_idempotent_no_ladder/base_binary must have no_ladder_holds=true')

    demo_base = next((r for r in t11_demos.get('fixed_interface_reports', []) if r.get('lens_id') == 'base_binary'), None)
    if demo_base is None or demo_base.get('no_ladder_holds') is not True:
        fail('T11 no_ladder_demos must show base_binary fixed-interface no-ladder holds')

    if t11_demos.get('extension_escape_report', {}).get('escape_present') is not True:
        fail('T11 extension escape report must have escape_present=true')

    cov_row = next(
        (r for r in t14_cov.get('theorem_targets', []) if r.get('theorem_id') == 'NG_LADDER_BOUNDED_INTERFACE'),
        None,
    )
    if cov_row is None:
        fail('primitive coverage missing NG_LADDER_BOUNDED_INTERFACE entry')
    if cov_row.get('coverage_satisfied') is not True:
        fail('NG_LADDER_BOUNDED_INTERFACE coverage_satisfied must be true')

    repro_text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8') if Path('src/sixbirds_nogo/repro.py').exists() else ''
    includes_t20 = 'run_t20_readiness_checkpoint.py' in repro_text
    includes_t21 = 'run_t21_theorem_atlas.py' in repro_text
    includes_t22 = 'run_t22_dpi_protocol_pack.py' in repro_text
    includes_t23 = 'run_t23_graph_affinity_pack.py' in repro_text
    includes_t24 = 'run_t24_closure_pack.py' in repro_text
    includes_t25 = 'run_t25_objecthood_pack.py' in repro_text
    includes_t26 = 'run_t26_bounded_interface_pack.py' in repro_text
    if not includes_t26:
        fail('repro pipeline missing run_t26_bounded_interface_pack.py step')

    analytic_present_total = sum(1 for t in readiness['theorems'] if t['analytic_support']['status'] == 'present')
    overall_direct_core = sum(
        1 for c in claims['claims'] if c.get('claim_class') == 'core' and c.get('support_grade') == 'direct'
    )

    fixed_interface_frozen = 'fixed interface' in joined or 'interface size is fixed and bounded' in joined
    fixed_domain_frozen = 'fixed domain' in joined
    fixed_package_frozen = 'fixed packaging' in joined or ('packaging is fixed' in joined and 'idempotent' in joined)
    definability_bound_explicit = '2^|im(f)|' in joined or '2^{|im(f)|}' in joined or 'definable predicate count' in joined
    idempotent_saturation_explicit = ('idempotent' in joined) and ('saturat' in joined)
    extension_escape_scoped = ('extension' in joined) and ('outside theorem scope' in joined)
    theorem_guardrails_frozen = claim_map['NG_LADDER_BOUNDED_INTERFACE.guardrail']['freeze_status'] == 'frozen'

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': 1,
        'updated_theorem_ids': ['NG_LADDER_BOUNDED_INTERFACE'],
        'analytic_present_total': analytic_present_total,
        'overall_direct_core_count': overall_direct_core,
        'pack_direct_core_count': 1,
        'fixed_interface_frozen': fixed_interface_frozen,
        'fixed_domain_frozen': fixed_domain_frozen,
        'fixed_package_frozen': fixed_package_frozen,
        'definability_bound_explicit': definability_bound_explicit,
        'idempotent_saturation_explicit': idempotent_saturation_explicit,
        'extension_escape_scoped_outside_theorem': extension_escape_scoped,
        'theorem_guardrails_frozen': theorem_guardrails_frozen,
        'low_proxy_risk_preserved': ready_map['NG_LADDER_BOUNDED_INTERFACE']['proxy_risk']['status'] == 'low',
        'reproduce_includes_t20': includes_t20,
        'reproduce_includes_t21': includes_t21,
        'reproduce_includes_t22': includes_t22,
        'reproduce_includes_t23': includes_t23,
        'reproduce_includes_t24': includes_t24,
        'reproduce_includes_t25': includes_t25,
        'reproduce_includes_t26': includes_t26,
        'vision_present': bool(pack.get('source_context', {}).get('vision_present')),
        'status': 'success',
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'bounded_interface_pack_summary.json'
    out_path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')

    print('PASS: T26 bounded-interface theorem pack validation')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path('results/T26')
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            'generated_at_utc': now_iso(),
            'theorem_count': 0,
            'updated_theorem_ids': [],
            'analytic_present_total': 0,
            'overall_direct_core_count': 0,
            'pack_direct_core_count': 0,
            'fixed_interface_frozen': False,
            'fixed_domain_frozen': False,
            'fixed_package_frozen': False,
            'definability_bound_explicit': False,
            'idempotent_saturation_explicit': False,
            'extension_escape_scoped_outside_theorem': False,
            'theorem_guardrails_frozen': False,
            'low_proxy_risk_preserved': False,
            'reproduce_includes_t20': False,
            'reproduce_includes_t21': False,
            'reproduce_includes_t22': False,
            'reproduce_includes_t23': False,
            'reproduce_includes_t24': False,
            'reproduce_includes_t25': False,
            'reproduce_includes_t26': False,
            'vision_present': Path('vision.md').exists(),
            'status': 'failed',
            'error': str(exc),
        }
        (out_dir / 'bounded_interface_pack_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(f'FAIL: {exc}')
        raise SystemExit(1)
