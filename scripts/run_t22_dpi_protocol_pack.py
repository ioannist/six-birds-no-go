#!/usr/bin/env python3
"""Validate T22 DPI + protocol theorem pack and emit summary."""

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


def theorem_map(items: list[dict]) -> dict[str, dict]:
    return {item['theorem_id']: item for item in items}


def claim_map(items: list[dict]) -> dict[str, dict]:
    return {item['claim_id']: item for item in items}


def contains_any(texts: list[str], needles: tuple[str, ...]) -> bool:
    merged = ' '.join(texts).lower()
    return any(n in merged for n in needles)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run T22 DPI + protocol pack validation')
    parser.add_argument('--output-dir', default='results/T22')
    args = parser.parse_args()

    pack_p = Path('docs/project/theorem_pack_arrow_protocol.yaml')
    ready_p = Path('docs/project/readiness_checklist.yaml')
    atlas_p = Path('docs/project/theorem_atlas.yaml')
    claims_p = Path('docs/project/claim_audit_freeze.yaml')
    frag_p = Path('results/T15/fragility_summary.json')
    adv_p = Path('results/T15/adversarial_cases.json')
    t21_p = Path('results/T21/theorem_atlas_summary.json')

    for p in [pack_p, ready_p, atlas_p, claims_p, frag_p, adv_p, t21_p]:
        if not p.exists():
            fail(f'missing required input: {p}')

    pack = load_json(pack_p)
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    claims = load_json(claims_p)
    _ = load_json(frag_p)
    _ = load_json(adv_p)
    _ = load_json(t21_p)

    for k in ['version', 'generated_at_utc', 'source_context', 'status_enums', 'theorem_fronts']:
        if k not in pack:
            fail(f'theorem pack missing key: {k}')

    fronts = pack['theorem_fronts']
    if not isinstance(fronts, list):
        fail('theorem_fronts must be a list')

    front_ids = [f.get('theorem_id') for f in fronts]
    expected_ids = ['NG_ARROW_DPI', 'NG_PROTOCOL_TRAP']
    if front_ids != expected_ids:
        fail(f'theorem pack theorem IDs must be exactly {expected_ids} in stable order')

    fmap = theorem_map(fronts)
    for tid in expected_ids:
        row = fmap[tid]
        if row.get('pack_status') != 'direct_ready':
            fail(f'{tid} must have pack_status=direct_ready')
        for req in ['theorem_statement', 'theorem_core', 'proof_spine', 'guardrails', 'evidence_refs']:
            if req not in row:
                fail(f'{tid} missing {req}')
        if not str(row['theorem_statement']).strip():
            fail(f'{tid}.theorem_statement must be non-empty')
        if not isinstance(row['proof_spine'], list) or len(row['proof_spine']) == 0:
            fail(f'{tid}.proof_spine must be non-empty list')
        if not isinstance(row['guardrails'], list) or len(row['guardrails']) == 0:
            fail(f'{tid}.guardrails must be non-empty list')
        if not isinstance(row['evidence_refs'], dict) or len(row['evidence_refs']) == 0:
            fail(f'{tid}.evidence_refs must be non-empty object')

    protocol_scope_text = [fmap['NG_PROTOCOL_TRAP']['theorem_statement']]
    protocol_scope_text.extend(fmap['NG_PROTOCOL_TRAP']['theorem_core'].get('scope_limits', []))
    protocol_scope_has_initial = contains_any(protocol_scope_text, ('stationary', 'initial'))
    if not protocol_scope_has_initial:
        fail('NG_PROTOCOL_TRAP theorem statement/scope must explicitly include stationary or initial-law scope')

    dpi_guardrail_texts = [g.get('guardrail_text', '') for g in fmap['NG_ARROW_DPI']['guardrails']]
    if not contains_any(dpi_guardrail_texts, ('proxy', 'fitted')):
        fail('NG_ARROW_DPI guardrails must mention proxy misuse')
    if not contains_any(dpi_guardrail_texts, ('initial', 'stationary')):
        fail('NG_ARROW_DPI guardrails must mention initial-law dependence')

    pt_guardrail_texts = [g.get('guardrail_text', '') for g in fmap['NG_PROTOCOL_TRAP']['guardrails']]
    if not contains_any(pt_guardrail_texts, ('lifted', 'honest observed')):
        fail('NG_PROTOCOL_TRAP guardrails must mention lifted/honest observed formulation')
    if not contains_any(pt_guardrail_texts, ('stationary', 'initial')):
        fail('NG_PROTOCOL_TRAP guardrails must mention stationary/initial-law scope')
    if not contains_any(pt_guardrail_texts, ('proxy', 'stroboscopic', 'fitted')):
        fail('NG_PROTOCOL_TRAP guardrails must mention proxy/stroboscopic misuse')

    ready = theorem_map(readiness['theorems'])
    atlas_map = theorem_map(atlas['theorems'])
    cmap = claim_map(claims['claims'])

    for tid in expected_ids:
        if ready[tid]['analytic_support']['status'] != 'present':
            fail(f'{tid} readiness analytic_support must be present')
        if atlas_map[tid]['support_snapshot']['analytic_support']['status'] != ready[tid]['analytic_support']['status']:
            fail(f'{tid} atlas support_snapshot analytic status must match readiness')

    if cmap['NG_ARROW_DPI.core']['support_grade'] != 'direct':
        fail('NG_ARROW_DPI.core support_grade must be direct')
    if cmap['NG_PROTOCOL_TRAP.core']['support_grade'] != 'direct':
        fail('NG_PROTOCOL_TRAP.core support_grade must be direct')

    # Proxy risk remains unchanged from T20 anchors.
    expected_proxy = {'NG_ARROW_DPI': 'high', 'NG_PROTOCOL_TRAP': 'medium'}
    for tid, exp in expected_proxy.items():
        if ready[tid]['proxy_risk']['status'] != exp:
            fail(f'{tid} proxy_risk must remain {exp}')

    src = pack['source_context']
    vision_exists = Path('vision.md').exists()
    if bool(src.get('vision_present')) != vision_exists:
        fail('theorem pack source_context.vision_present does not match runtime vision presence')
    if vision_exists and src.get('vision_path') != 'vision.md':
        fail('vision_path must be vision.md when vision_present is true')

    repro_text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8') if Path('src/sixbirds_nogo/repro.py').exists() else ''
    includes_t20 = 'run_t20_readiness_checkpoint.py' in repro_text
    includes_t21 = 'run_t21_theorem_atlas.py' in repro_text
    includes_t22 = 'run_t22_dpi_protocol_pack.py' in repro_text
    if not includes_t22:
        fail('repro pipeline missing run_t22_dpi_protocol_pack.py step')

    core_claims = [c for c in claims['claims'] if c.get('claim_class') == 'core']
    direct_core_total = sum(1 for c in core_claims if c.get('support_grade') == 'direct')
    pack_direct_core_count = sum(1 for cid in ['NG_ARROW_DPI.core', 'NG_PROTOCOL_TRAP.core'] if cmap[cid]['support_grade'] == 'direct')
    guardrail_pack_count = sum(1 for c in claims['claims'] if c.get('claim_id') in ('NG_ARROW_DPI.guardrail', 'NG_PROTOCOL_TRAP.guardrail'))
    analytic_present_total = sum(1 for t in readiness['theorems'] if t['analytic_support']['status'] == 'present')

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': 2,
        'updated_theorem_ids': expected_ids,
        'analytic_present_total': analytic_present_total,
        'overall_direct_core_count': direct_core_total,
        'pack_direct_core_count': pack_direct_core_count,
        'guardrail_claim_count_for_pack': guardrail_pack_count,
        'protocol_scope_has_initial_law': protocol_scope_has_initial,
        'reproduce_includes_t20': includes_t20,
        'reproduce_includes_t21': includes_t21,
        'reproduce_includes_t22': includes_t22,
        'vision_present': vision_exists,
        'status': 'success',
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'dpi_protocol_pack_summary.json'
    out_path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')

    print('PASS: T22 theorem pack validation')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path('results/T22')
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            'generated_at_utc': now_iso(),
            'theorem_count': 2,
            'updated_theorem_ids': ['NG_ARROW_DPI', 'NG_PROTOCOL_TRAP'],
            'analytic_present_total': 0,
            'overall_direct_core_count': 0,
            'pack_direct_core_count': 0,
            'guardrail_claim_count_for_pack': 0,
            'protocol_scope_has_initial_law': False,
            'reproduce_includes_t20': False,
            'reproduce_includes_t21': False,
            'reproduce_includes_t22': False,
            'vision_present': Path('vision.md').exists(),
            'status': 'failed',
            'error': str(exc),
        }
        (out_dir / 'dpi_protocol_pack_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(f'FAIL: {exc}')
        raise SystemExit(1)
