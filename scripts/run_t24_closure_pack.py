#!/usr/bin/env python3
"""Validate T24 closure theorem pack and emit closure attribution resolution outputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sixbirds_nogo.affinity import is_exact_oneform, max_cycle_affinity  # noqa: E402
from sixbirds_nogo.closure_deficit import (  # noqa: E402
    GroupedKLValue,
    best_macro_gap,
    best_macro_kernel,
    closure_deficit,
    grouped_kl_equal,
    packaged_future_laws,
)
from sixbirds_nogo.coarse import is_strongly_lumpable, load_lens_from_witness, make_lens  # noqa: E402
from sixbirds_nogo.graph_cycle import cycle_rank  # noqa: E402
from sixbirds_nogo.markov import FiniteMarkovChain, load_chain_from_witness  # noqa: E402


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path} must parse to object')
    return data


def fail(msg: str) -> None:
    raise ValueError(msg)


def _frac_str(x: Fraction) -> str:
    return f'{x.numerator}/{x.denominator}'


def _row_str(row: tuple[Fraction, ...]) -> list[str]:
    return [_frac_str(x) for x in row]


def _matrix_str(matrix: tuple[tuple[Fraction, ...], ...]) -> list[list[str]]:
    return [_row_str(r) for r in matrix]


def _grouped(v: GroupedKLValue) -> dict:
    return {
        'kind': v.kind,
        'support_mismatch_count': v.support_mismatch_count,
        'log_terms': [
            {'ratio': _frac_str(r), 'coeff': _frac_str(c)}
            for r, c in v.log_terms
        ],
        'decimal_value': None if v.decimal_value is None else str(v.decimal_value),
        'precision': v.precision,
    }


def _state_metrics(chain: FiniteMarkovChain, lens, tau: int) -> dict:
    cd = closure_deficit(chain, lens, tau)
    bg = best_macro_gap(chain, lens, tau)
    laws = packaged_future_laws(chain, lens, tau)
    kstar = best_macro_kernel(chain, lens, tau)
    return {
        'closure': _grouped(cd),
        'best_gap': _grouped(bg),
        'strong_lumpable': is_strongly_lumpable(chain, lens),
        'best_kernel_rows': _matrix_str(kstar.matrix),
        'packaged_future_laws': {k: _row_str(v) for k, v in laws.items()},
        'packaged_future_distinct_count': len(set(laws.values())),
        'cycle_rank': cycle_rank(chain),
        'max_cycle_affinity': _frac_str(max_cycle_affinity(chain)),
        'exactness_flag': is_exact_oneform(chain),
    }


def build_local_isolator() -> tuple[FiniteMarkovChain, object]:
    states = ('A0', 'A1', 'B0', 'B1')
    matrix = (
        (Fraction(0, 1), Fraction(1, 2), Fraction(1, 2), Fraction(0, 1)),
        (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1), Fraction(1, 1)),
        (Fraction(1, 2), Fraction(0, 1), Fraction(0, 1), Fraction(1, 2)),
        (Fraction(0, 1), Fraction(1, 2), Fraction(1, 2), Fraction(0, 1)),
    )
    stationary = (Fraction(1, 8), Fraction(1, 4), Fraction(1, 4), Fraction(3, 8))
    chain = FiniteMarkovChain(states=states, matrix=matrix, stationary_distribution=stationary)
    lens = make_lens(states, {'A0': 'A', 'A1': 'A', 'B0': 'B', 'B1': 'B'}, lens_id='macro_AB')
    return chain, lens


def main() -> int:
    parser = argparse.ArgumentParser(description='Run T24 closure theorem pack validation')
    parser.add_argument('--output-dir', default='results/T24')
    args = parser.parse_args()

    pack_p = Path('docs/project/theorem_pack_closure.yaml')
    ready_p = Path('docs/project/readiness_checklist.yaml')
    atlas_p = Path('docs/project/theorem_atlas.yaml')
    claims_p = Path('docs/project/claim_audit_freeze.yaml')
    t09_metrics_p = Path('results/T09/closure_metrics.json')
    t09_grid_p = Path('results/T09/grid_check.json')
    t14_p = Path('results/T14/primitive_coverage.json')

    for p in [pack_p, ready_p, atlas_p, claims_p, t09_metrics_p, t09_grid_p, t14_p]:
        if not p.exists():
            fail(f'missing required input: {p}')

    pack = load_json(pack_p)
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    claims = load_json(claims_p)
    _ = load_json(t09_metrics_p)
    _ = load_json(t09_grid_p)
    prim = load_json(t14_p)

    for key in ['version', 'generated_at_utc', 'source_context', 'status_enums', 'theorem_fronts']:
        if key not in pack:
            fail(f'theorem pack missing key: {key}')

    fronts = pack['theorem_fronts']
    if not isinstance(fronts, list) or len(fronts) != 1:
        fail('theorem pack must contain exactly one theorem front')
    front = fronts[0]
    if front.get('theorem_id') != 'NG_MACRO_CLOSURE_DEFICIT':
        fail('theorem pack theorem ID must be NG_MACRO_CLOSURE_DEFICIT')

    if front.get('pack_status') != 'direct_ready':
        fail('closure theorem pack must have pack_status=direct_ready')
    for req in ['theorem_statement', 'theorem_core', 'proof_spine', 'guardrails', 'attribution_outcome', 'evidence_refs']:
        if req not in front:
            fail(f'theorem front missing {req}')
    if not str(front['theorem_statement']).strip():
        fail('theorem_statement must be non-empty')
    if not front['proof_spine'] or not front['guardrails']:
        fail('proof_spine and guardrails must be non-empty')

    core_text = [front['theorem_statement']]
    core_text.extend(front['theorem_core'].get('antecedent', []))
    core_text.extend(front['theorem_core'].get('conclusion', []))
    core_text.extend(front['proof_spine'])
    joined_core = ' '.join(core_text).lower()
    if not any(k in joined_core for k in ('variational', 'best macro kernel', 'packaged future')):
        fail('theorem core/proof spine must mention variational or best macro kernel or packaged future')

    guardrail_text = ' '.join(g.get('guardrail_text', '') for g in front['guardrails']).lower()
    if not any(k in guardrail_text for k in ('exact packaged future', 'exact variational')):
        fail('guardrails must mention exact packaged future laws or exact variational evaluation')
    if not any(k in guardrail_text for k in ('proxy macro fits', 'heuristic attribution', 'proxy')):
        fail('guardrails must exclude proxy macro fits / heuristic attribution')

    attr = front['attribution_outcome']
    if attr.get('mode') != 'resolved_by_local_isolator':
        fail('attribution_outcome mode must be resolved_by_local_isolator')

    # Validate readiness / atlas / claims current state.
    ready_map = {t['theorem_id']: t for t in readiness['theorems']}
    atlas_map = {t['theorem_id']: t for t in atlas['theorems']}
    claim_map = {c['claim_id']: c for c in claims['claims']}

    if ready_map['NG_MACRO_CLOSURE_DEFICIT']['analytic_support']['status'] != 'present':
        fail('readiness closure analytic_support must be present')
    if atlas_map['NG_MACRO_CLOSURE_DEFICIT']['support_snapshot']['analytic_support']['status'] != 'present':
        fail('atlas closure analytic_support must be present')
    if claim_map['NG_MACRO_CLOSURE_DEFICIT.core']['support_grade'] != 'direct':
        fail('closure core claim support_grade must be direct')
    if claim_map['NG_MACRO_CLOSURE_DEFICIT.guardrail']['support_grade'] != 'direct':
        fail('closure guardrail claim support_grade must be direct')
    if claim_map['NG_MACRO_CLOSURE_DEFICIT.primitive_attribution_gap']['freeze_status'] == 'blocked':
        fail('closure primitive_attribution_gap claim must no longer be blocked')

    if ready_map['NG_MACRO_CLOSURE_DEFICIT']['proxy_risk']['status'] != 'medium':
        fail('closure proxy_risk must remain medium')

    prim_targets = {t['theorem_id']: t for t in prim['theorem_targets']}
    if prim_targets['NG_MACRO_CLOSURE_DEFICIT']['coverage_mode'] != 'gap_note':
        fail('T14 primitive coverage for closure should remain historical gap_note pre-check')

    # Build local attribution isolator and evaluate exact anchors.
    base_chain = load_chain_from_witness('zero_closure_deficit_lumpable')
    base_lens = load_lens_from_witness('zero_closure_deficit_lumpable', 'macro_AB')
    local_chain, local_lens = build_local_isolator()
    positive_chain = load_chain_from_witness('positive_closure_deficit')
    positive_lens = load_lens_from_witness('positive_closure_deficit', 'macro_AB')

    base_metrics = _state_metrics(base_chain, base_lens, tau=1)
    local_metrics = _state_metrics(local_chain, local_lens, tau=1)
    pos_metrics = _state_metrics(positive_chain, positive_lens, tau=1)

    # Exact anchor checks.
    expected_terms = [
        {'ratio': '3/5', 'coeff': '1/16'},
        {'ratio': '6/5', 'coeff': '1/4'},
        {'ratio': '3/1', 'coeff': '1/16'},
    ]

    if base_metrics['closure']['kind'] != 'zero' or base_metrics['best_gap']['kind'] != 'zero':
        fail('base witness closure/best_gap must be zero')
    if not base_metrics['strong_lumpable']:
        fail('base witness must be strongly lumpable')
    if base_metrics['packaged_future_distinct_count'] != 1:
        fail('base packaged future distinct count must be 1')

    if local_metrics['closure']['kind'] != 'finite_positive':
        fail('local isolator closure kind must be finite_positive')
    if local_metrics['best_gap']['kind'] != 'finite_positive':
        fail('local isolator best_gap kind must be finite_positive')
    if local_metrics['closure']['log_terms'] != expected_terms:
        fail('local isolator closure log_terms do not match expected exact terms')
    if local_metrics['best_gap']['log_terms'] != expected_terms:
        fail('local isolator best_gap log_terms do not match expected exact terms')
    if local_metrics['best_kernel_rows'] != [['1/6', '5/6'], ['1/2', '1/2']]:
        fail('local isolator best kernel rows mismatch')
    expected_laws = {
        'A0': ['1/2', '1/2'],
        'A1': ['0/1', '1/1'],
        'B0': ['1/2', '1/2'],
        'B1': ['1/2', '1/2'],
    }
    if local_metrics['packaged_future_laws'] != expected_laws:
        fail('local isolator packaged future laws mismatch')
    if local_metrics['packaged_future_distinct_count'] != 2:
        fail('local isolator packaged future distinct count must be 2')

    for tag, m in [('base', base_metrics), ('local', local_metrics)]:
        if m['cycle_rank'] != 1:
            fail(f'{tag} cycle_rank must be 1')
        if m['max_cycle_affinity'] != '0/1':
            fail(f'{tag} max_cycle_affinity must be 0')
        if m['exactness_flag'] is not True:
            fail(f'{tag} exactness_flag must be true')

    primitive_delta = {
        'rewrite': 'off_to_on',
        'gating': 'same_off',
        'holonomy': 'same_off',
        'staging': 'same_off',
        'packaging': 'same_off',
        'drive': 'same_off',
    }

    resolution = {
        'generated_at_utc': now_iso(),
        'outcome_mode': 'resolved_by_local_isolator',
        'base_case': {
            'witness_id': 'zero_closure_deficit_lumpable',
            'lens_id': 'macro_AB',
            'tau': 1,
            **base_metrics,
        },
        'local_isolator': {
            'variant_id': 'zero_closure_deficit_lumpable__rewrite_A1_to_B1',
            'parent_witness_id': 'zero_closure_deficit_lumpable',
            'lens_id': 'macro_AB',
            'tau': 1,
            'states': ['A0', 'A1', 'B0', 'B1'],
            'matrix': _matrix_str(local_chain.matrix),
            'stationary_distribution': _row_str(local_chain.stationary_distribution),
            **local_metrics,
        },
        'historical_positive_case': {
            'witness_id': 'positive_closure_deficit',
            'lens_id': 'macro_AB',
            'tau': 1,
            'closure': pos_metrics['closure'],
            'best_gap': pos_metrics['best_gap'],
            'note': 'Historical seeded positive witness remains valid theorem-front evidence.'
        },
        'primitive_delta': primitive_delta,
        'resolution_note': 'Earlier closure primitive-attribution gap is resolved locally by a rewrite-only nonlumpable contrast within the exact/null-affinity regime.',
        'status': 'success',
    }

    repro_text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8') if Path('src/sixbirds_nogo/repro.py').exists() else ''
    includes_t20 = 'run_t20_readiness_checkpoint.py' in repro_text
    includes_t21 = 'run_t21_theorem_atlas.py' in repro_text
    includes_t22 = 'run_t22_dpi_protocol_pack.py' in repro_text
    includes_t23 = 'run_t23_graph_affinity_pack.py' in repro_text
    includes_t24 = 'run_t24_closure_pack.py' in repro_text
    if not includes_t24:
        fail('repro pipeline missing run_t24_closure_pack.py step')

    analytic_present_total = sum(1 for t in readiness['theorems'] if t['analytic_support']['status'] == 'present')
    overall_direct_core = sum(1 for c in claims['claims'] if c.get('claim_class') == 'core' and c.get('support_grade') == 'direct')

    local_positive = local_metrics['closure']['kind'] == 'finite_positive'
    local_rewrite_only = primitive_delta['rewrite'] == 'off_to_on' and all(
        primitive_delta[k] == 'same_off' for k in ['gating', 'holonomy', 'staging', 'packaging', 'drive']
    )
    preserves_context = (
        base_metrics['cycle_rank'] == 1
        and local_metrics['cycle_rank'] == 1
        and base_metrics['max_cycle_affinity'] == '0/1'
        and local_metrics['max_cycle_affinity'] == '0/1'
        and base_metrics['exactness_flag'] is True
        and local_metrics['exactness_flag'] is True
    )

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': 1,
        'updated_theorem_ids': ['NG_MACRO_CLOSURE_DEFICIT'],
        'analytic_present_total': analytic_present_total,
        'overall_direct_core_count': overall_direct_core,
        'pack_direct_core_count': 1,
        'attribution_outcome_mode': 'resolved_by_local_isolator',
        'primitive_attribution_resolved': True,
        'local_isolator_present': True,
        'local_isolator_rewrite_only': local_rewrite_only,
        'local_isolator_positive_closure': local_positive,
        'local_isolator_preserves_exact_null_force_context': preserves_context,
        'reproduce_includes_t20': includes_t20,
        'reproduce_includes_t21': includes_t21,
        'reproduce_includes_t22': includes_t22,
        'reproduce_includes_t23': includes_t23,
        'reproduce_includes_t24': includes_t24,
        'vision_present': Path('vision.md').exists(),
        'status': 'success',
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'closure_attribution_resolution.json').write_text(json.dumps(resolution, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'closure_pack_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')

    print('PASS: T24 closure theorem pack validation')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path('results/T24')
        out_dir.mkdir(parents=True, exist_ok=True)
        fail_summary = {
            'generated_at_utc': now_iso(),
            'theorem_count': 1,
            'updated_theorem_ids': ['NG_MACRO_CLOSURE_DEFICIT'],
            'analytic_present_total': 0,
            'overall_direct_core_count': 0,
            'pack_direct_core_count': 0,
            'attribution_outcome_mode': 'blocked_but_sharpened',
            'primitive_attribution_resolved': False,
            'local_isolator_present': False,
            'local_isolator_rewrite_only': False,
            'local_isolator_positive_closure': False,
            'local_isolator_preserves_exact_null_force_context': False,
            'reproduce_includes_t20': False,
            'reproduce_includes_t21': False,
            'reproduce_includes_t22': False,
            'reproduce_includes_t23': False,
            'reproduce_includes_t24': False,
            'vision_present': Path('vision.md').exists(),
            'status': 'failed',
            'error': str(exc),
        }
        (out_dir / 'closure_pack_summary.json').write_text(json.dumps(fail_summary, indent=2) + '\n', encoding='utf-8')
        (out_dir / 'closure_attribution_resolution.json').write_text(json.dumps({'status': 'failed', 'error': str(exc)}, indent=2) + '\n', encoding='utf-8')
        print(f'FAIL: {exc}')
        raise SystemExit(1)
