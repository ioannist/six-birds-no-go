#!/usr/bin/env python3
"""Validate T23 graph/affinity theorem pack and emit summary."""

from __future__ import annotations

import argparse
import csv
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


def theorem_map(rows: list[dict]) -> dict[str, dict]:
    return {r['theorem_id']: r for r in rows}


def claim_map(rows: list[dict]) -> dict[str, dict]:
    return {r['claim_id']: r for r in rows}


def contains_any(texts: list[str], needles: tuple[str, ...]) -> bool:
    merged = ' '.join(texts).lower()
    return any(n in merged for n in needles)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run T23 graph/affinity pack validation')
    parser.add_argument('--output-dir', default='results/T23')
    args = parser.parse_args()

    pack_p = Path('docs/project/theorem_pack_graph_affinity.yaml')
    ready_p = Path('docs/project/readiness_checklist.yaml')
    atlas_p = Path('docs/project/theorem_atlas.yaml')
    claims_p = Path('docs/project/claim_audit_freeze.yaml')
    prim_p = Path('results/T14/primitive_coverage.json')
    frag_p = Path('results/T15/fragility_summary.json')
    thresh_p = Path('results/T15/threshold_sweep.csv')
    t22_p = Path('results/T22/dpi_protocol_pack_summary.json')

    for p in [pack_p, ready_p, atlas_p, claims_p, prim_p, frag_p, thresh_p, t22_p]:
        if not p.exists():
            fail(f'missing required input: {p}')

    pack = load_json(pack_p)
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    claims = load_json(claims_p)
    prim = load_json(prim_p)
    frag = load_json(frag_p)
    _ = load_json(t22_p)

    # parse threshold csv (malformed check)
    with thresh_p.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
        if not rows:
            fail('threshold_sweep.csv must be non-empty')

    for k in ['version', 'generated_at_utc', 'source_context', 'status_enums', 'theorem_fronts']:
        if k not in pack:
            fail(f'theorem pack missing key: {k}')

    fronts = pack['theorem_fronts']
    if not isinstance(fronts, list):
        fail('theorem_fronts must be a list')
    ids = [r.get('theorem_id') for r in fronts]
    expected = ['NG_FORCE_FOREST', 'NG_FORCE_NULL']
    if ids != expected:
        fail(f'theorem pack theorem IDs must be exactly {expected} in stable order')

    fmap = theorem_map(fronts)
    for tid in expected:
        row = fmap[tid]
        if row.get('pack_status') != 'direct_ready':
            fail(f'{tid} must have pack_status=direct_ready')
        for req in ['theorem_statement', 'theorem_core', 'proof_spine', 'guardrails', 'evidence_refs']:
            if req not in row:
                fail(f'{tid} missing {req}')
        if not str(row['theorem_statement']).strip():
            fail(f'{tid}.theorem_statement must be non-empty')
        if not isinstance(row['proof_spine'], list) or not row['proof_spine']:
            fail(f'{tid}.proof_spine must be non-empty list')
        if not isinstance(row['guardrails'], list) or not row['guardrails']:
            fail(f'{tid}.guardrails must be non-empty list')
        if not isinstance(row['evidence_refs'], dict) or not row['evidence_refs']:
            fail(f'{tid}.evidence_refs must be non-empty object')

    forest_text = [fmap['NG_FORCE_FOREST']['theorem_statement']]
    forest_text.extend(fmap['NG_FORCE_FOREST']['theorem_core'].get('antecedent', []))
    forest_text.extend(fmap['NG_FORCE_FOREST']['proof_spine'])
    forest_uses_cycle = contains_any(forest_text, ('forest', 'cycle rank'))
    if not forest_uses_cycle:
        fail('NG_FORCE_FOREST must explicitly mention forest or cycle rank')

    null_text = [fmap['NG_FORCE_NULL']['theorem_statement']]
    null_text.extend(fmap['NG_FORCE_NULL']['theorem_core'].get('antecedent', []))
    null_text.extend(fmap['NG_FORCE_NULL']['proof_spine'])
    null_uses_exactness = contains_any(null_text, ('exact', 'null-affinity', 'bidirected', 'null affinity'))
    if not null_uses_exactness:
        fail('NG_FORCE_NULL must explicitly mention exact/null-affinity/bidirected scope')

    # threshold/regularization mentions in guardrails
    guardrails_forest = [g.get('guardrail_text', '') for g in fmap['NG_FORCE_FOREST']['guardrails']]
    guardrails_null = [g.get('guardrail_text', '') for g in fmap['NG_FORCE_NULL']['guardrails']]
    forest_guardrail_ok = contains_any(guardrails_forest, ('threshold', 'regularization', 'floor'))
    null_guardrail_ok = contains_any(guardrails_null, ('threshold', 'regularization', 'floor'))
    threshold_guardrails_frozen = forest_guardrail_ok and null_guardrail_ok
    if not threshold_guardrails_frozen:
        fail('Both theorem fronts must include explicit threshold/regularization guardrails')

    ready = theorem_map(readiness['theorems'])
    atlas_map = theorem_map(atlas['theorems'])
    cmap = claim_map(claims['claims'])

    for tid in expected:
        if ready[tid]['analytic_support']['status'] != 'present':
            fail(f'{tid} readiness analytic_support must be present')
        if atlas_map[tid]['support_snapshot']['analytic_support']['status'] != ready[tid]['analytic_support']['status']:
            fail(f'{tid} atlas analytic status must match readiness')

    if cmap['NG_FORCE_FOREST.core']['support_grade'] != 'direct':
        fail('NG_FORCE_FOREST.core support_grade must be direct')
    if cmap['NG_FORCE_NULL.core']['support_grade'] != 'direct':
        fail('NG_FORCE_NULL.core support_grade must be direct')

    # proxy risk unchanged anchors
    if ready['NG_FORCE_FOREST']['proxy_risk']['status'] != 'high':
        fail('NG_FORCE_FOREST proxy_risk must remain high')
    if ready['NG_FORCE_NULL']['proxy_risk']['status'] != 'high':
        fail('NG_FORCE_NULL proxy_risk must remain high')

    # primitive coverage satisfied
    tmap = theorem_map(prim['theorem_targets'])
    if not tmap['NG_FORCE_FOREST']['coverage_satisfied']:
        fail('primitive coverage for NG_FORCE_FOREST must be satisfied')
    if not tmap['NG_FORCE_NULL']['coverage_satisfied']:
        fail('primitive coverage for NG_FORCE_NULL must be satisfied')

    frag_ids = {e['fragility_id'] for e in frag.get('entries', [])}
    if 'threshold_floors_can_introduce_spurious_one_way_support' not in frag_ids:
        fail('fragility summary missing threshold fragility entry')

    src = pack['source_context']
    vision_exists = Path('vision.md').exists()
    if bool(src.get('vision_present')) != vision_exists:
        fail('theorem pack source_context.vision_present does not match runtime state')
    if vision_exists and src.get('vision_path') != 'vision.md':
        fail('vision_path must be vision.md when vision_present is true')

    repro_text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8') if Path('src/sixbirds_nogo/repro.py').exists() else ''
    includes_t20 = 'run_t20_readiness_checkpoint.py' in repro_text
    includes_t21 = 'run_t21_theorem_atlas.py' in repro_text
    includes_t22 = 'run_t22_dpi_protocol_pack.py' in repro_text
    includes_t23 = 'run_t23_graph_affinity_pack.py' in repro_text
    if not includes_t23:
        fail('repro pipeline missing run_t23_graph_affinity_pack.py step')

    direct_core_total = sum(1 for c in claims['claims'] if c.get('claim_class') == 'core' and c.get('support_grade') == 'direct')
    pack_direct_core = sum(1 for cid in ['NG_FORCE_FOREST.core', 'NG_FORCE_NULL.core'] if cmap[cid]['support_grade'] == 'direct')
    analytic_present_total = sum(1 for t in readiness['theorems'] if t['analytic_support']['status'] == 'present')
    guardrail_pack_count = sum(1 for c in claims['claims'] if c.get('claim_id') in ('NG_FORCE_FOREST.guardrail', 'NG_FORCE_NULL.guardrail'))

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': 2,
        'updated_theorem_ids': expected,
        'analytic_present_total': analytic_present_total,
        'overall_direct_core_count': direct_core_total,
        'pack_direct_core_count': pack_direct_core,
        'guardrail_claim_count_for_pack': guardrail_pack_count,
        'forest_pack_uses_cycle_rank': forest_uses_cycle,
        'null_pack_uses_exactness': null_uses_exactness,
        'threshold_guardrails_frozen': threshold_guardrails_frozen,
        'reproduce_includes_t20': includes_t20,
        'reproduce_includes_t21': includes_t21,
        'reproduce_includes_t22': includes_t22,
        'reproduce_includes_t23': includes_t23,
        'vision_present': vision_exists,
        'status': 'success',
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'graph_affinity_pack_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')

    print('PASS: T23 graph/affinity theorem pack validation')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path('results/T23')
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            'generated_at_utc': now_iso(),
            'theorem_count': 2,
            'updated_theorem_ids': ['NG_FORCE_FOREST', 'NG_FORCE_NULL'],
            'analytic_present_total': 0,
            'overall_direct_core_count': 0,
            'pack_direct_core_count': 0,
            'guardrail_claim_count_for_pack': 0,
            'forest_pack_uses_cycle_rank': False,
            'null_pack_uses_exactness': False,
            'threshold_guardrails_frozen': False,
            'reproduce_includes_t20': False,
            'reproduce_includes_t21': False,
            'reproduce_includes_t22': False,
            'reproduce_includes_t23': False,
            'vision_present': Path('vision.md').exists(),
            'status': 'failed',
            'error': str(exc),
        }
        (out_dir / 'graph_affinity_pack_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(f'FAIL: {exc}')
        raise SystemExit(1)
