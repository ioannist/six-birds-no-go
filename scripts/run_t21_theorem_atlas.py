#!/usr/bin/env python3
"""Validate theorem atlas / claim-audit freeze and emit T21 summary."""

from __future__ import annotations

import argparse
from collections import Counter
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
    parser = argparse.ArgumentParser(description='Run T21 theorem atlas validation')
    parser.add_argument('--output-dir', default='results/T21')
    args = parser.parse_args()

    atlas_p = Path('docs/project/theorem_atlas.yaml')
    claims_p = Path('docs/project/claim_audit_freeze.yaml')
    theorems_p = Path('configs/theorems.yaml')
    readiness_p = Path('docs/project/readiness_checklist.yaml')
    frag_p = Path('results/T15/fragility_summary.json')
    prim_p = Path('results/T14/primitive_coverage.json')

    for p in [atlas_p, claims_p, theorems_p, readiness_p, frag_p, prim_p]:
        if not p.exists():
            fail(f'missing required input: {p}')

    atlas = load_json(atlas_p)
    claims = load_json(claims_p)
    theorem_cfg = load_json(theorems_p)
    readiness = load_json(readiness_p)
    _ = load_json(frag_p)
    _ = load_json(prim_p)

    # Top-level keys
    for k in ['version', 'generated_at_utc', 'source_context', 'vision_alignment', 'paper_order', 'section_map', 'theorems']:
        if k not in atlas:
            fail(f'theorem_atlas missing key: {k}')
    for k in ['version', 'generated_at_utc', 'source_context', 'claim_status_enums', 'claims']:
        if k not in claims:
            fail(f'claim_audit_freeze missing key: {k}')

    theorem_ids = [t['id'] for t in theorem_cfg['theorems']]
    atlas_ids = [t['theorem_id'] for t in atlas['theorems']]
    if sorted(atlas_ids) != sorted(theorem_ids) or len(atlas_ids) != len(set(atlas_ids)):
        fail('theorem_atlas theorem IDs must match configs/theorems.yaml exactly once')

    claim_theorem_ids = {c['theorem_id'] for c in claims['claims']}
    if not claim_theorem_ids.issubset(set(atlas_ids)):
        fail('claim theorem IDs must be subset of atlas theorem IDs')

    # paper_order and section_map cover all theorem IDs exactly once
    po = atlas['paper_order']
    if sorted(po) != sorted(theorem_ids) or len(po) != len(set(po)):
        fail('paper_order must contain all theorem IDs exactly once')

    sec_ids = []
    for sec, obj in atlas['section_map'].items():
        if not isinstance(obj, dict) or 'theorems' not in obj:
            fail(f'section_map entry invalid: {sec}')
        sec_ids.extend(obj['theorems'])
    if sorted(sec_ids) != sorted(theorem_ids) or len(sec_ids) != len(set(sec_ids)):
        fail('section_map must cover all theorem IDs exactly once')

    # support snapshot must match readiness exactly
    ready_map = {t['theorem_id']: t for t in readiness['theorems']}
    for t in atlas['theorems']:
        tid = t['theorem_id']
        if tid not in ready_map:
            fail(f'theorem missing in readiness: {tid}')
        rs = ready_map[tid]
        for key in ['analytic_support', 'computational_support', 'lean_support', 'witness_coverage', 'proxy_risk']:
            ast = t['support_snapshot'][key]['status']
            rst = rs[key]['status']
            if ast != rst:
                fail(f'support_snapshot mismatch for {tid}:{key} ({ast} != {rst})')

        for req in ['theorem_statement', 'theorem_schema', 'assumption_refs', 'dependency_refs', 'evidence_handles', 'blockers', 'next_ticket']:
            if req not in t:
                fail(f'{tid} missing {req}')

        ts = t['theorem_schema']
        for req in ['antecedent', 'conclusion', 'scope_limits']:
            if req not in ts or not isinstance(ts[req], list):
                fail(f'{tid}.theorem_schema missing list {req}')

        ar = t['assumption_refs']
        for req in ['bundles', 'normalized_atoms']:
            if req not in ar or not isinstance(ar[req], list):
                fail(f'{tid}.assumption_refs missing list {req}')

        eh = t['evidence_handles']
        for req in ['analytic', 'computational', 'lean', 'witness', 'fragility_guardrails']:
            if req not in eh or not isinstance(eh[req], list):
                fail(f'{tid}.evidence_handles missing list {req}')

        if t['support_snapshot']['proxy_risk']['status'] in ('medium', 'high') and len(eh['fragility_guardrails']) == 0:
            fail(f'{tid} has proxy risk medium/high but no fragility_guardrails')

    claim_map = {c['claim_id']: c for c in claims['claims']}

    # every medium/high proxy theorem has guardrail claim
    atlas_proxy = {t['theorem_id']: t['support_snapshot']['proxy_risk']['status'] for t in atlas['theorems']}
    for tid, risk in atlas_proxy.items():
        if risk in ('medium', 'high') and f'{tid}.guardrail' not in claim_map:
            fail(f'missing guardrail claim for medium/high proxy theorem {tid}')

    # claim validation
    for c in claims['claims']:
        for req in ['claim_id', 'theorem_id', 'claim_class', 'claim_text', 'freeze_status', 'support_grade', 'evidence_refs', 'guardrail_refs', 'blockers', 'next_ticket', 'paper_use', 'note']:
            if req not in c:
                fail(f'claim missing key {req}: {c}')
        if c['freeze_status'] == 'frozen' and len(c['evidence_refs']) == 0:
            fail(f'frozen claim missing evidence_refs: {c["claim_id"]}')
        if c['freeze_status'] in ('blocked', 'deferred'):
            if not c['blockers']:
                fail(f'blocked/deferred claim missing blockers: {c["claim_id"]}')
            if c['next_ticket'] is None:
                fail(f'blocked/deferred claim missing next_ticket: {c["claim_id"]}')
        txt = (c['claim_text'] + ' ' + c['note']).lower()
        if any(p in txt for p in ['tbd', 'todo', 'placeholder']):
            fail(f'placeholder text found in claim: {c["claim_id"]}')

    # mandatory historical/active gap claims
    closure_gap = 'NG_MACRO_CLOSURE_DEFICIT.primitive_attribution_gap'
    if closure_gap not in claim_map:
        fail(f'missing mandatory gap claim: {closure_gap}')
    if claim_map[closure_gap]['freeze_status'] == 'blocked':
        pass
    else:
        closure_text = (claim_map[closure_gap].get('claim_text', '') + ' ' + claim_map[closure_gap].get('note', '')).lower()
        if 'resolv' not in closure_text:
            fail('closure historical gap claim is unblocked but does not explicitly record resolution')

    object_gap = 'NG_OBJECT_CONTRACTIVE.metric_regime_gap'
    if object_gap not in claim_map:
        fail(f'missing mandatory gap claim: {object_gap}')
    if claim_map[object_gap]['freeze_status'] == 'blocked':
        pass
    else:
        object_text = (claim_map[object_gap].get('claim_text', '') + ' ' + claim_map[object_gap].get('note', '')).lower()
        if 'resolv' not in object_text:
            fail('objecthood historical gap claim is unblocked but does not explicitly record resolution')

    # vision + snapshot checks
    src = atlas['source_context']
    vision_present = bool(src.get('vision_present'))
    vision_exists = Path('vision.md').exists()
    if vision_present != vision_exists:
        fail('source_context.vision_present does not match runtime vision.md presence')
    if vision_present:
        if src.get('vision_path') != 'vision.md':
            fail('vision_path must be vision.md when vision_present true')
        snap = Path('.package-repo-snapshot.json')
        if snap.exists():
            sobj = load_json(snap)
            allowed_root = sobj.get('allowed_root_files', [])
            if 'vision.md' not in allowed_root:
                fail('snapshot coverage missing vision.md while vision_present is true')

    repro_text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8') if Path('src/sixbirds_nogo/repro.py').exists() else ''
    includes_t20 = 'run_t20_readiness_checkpoint.py' in repro_text
    includes_t21 = 'run_t21_theorem_atlas.py' in repro_text
    if not includes_t20:
        fail('repro pipeline missing run_t20_readiness_checkpoint.py step')
    if not includes_t21:
        fail('repro pipeline missing run_t21_theorem_atlas.py step')

    # summary metrics
    claim_count = len(claims['claims'])
    freeze_counter = Counter(c['freeze_status'] for c in claims['claims'])
    guardrail_count = sum(1 for c in claims['claims'] if c['claim_class'] == 'guardrail')
    direct_core = sum(1 for c in claims['claims'] if c['claim_class'] == 'core' and c['support_grade'] == 'direct')
    evidence_core = sum(1 for c in claims['claims'] if c['claim_class'] == 'core' and c['support_grade'] == 'evidence_only')

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': len(theorem_ids),
        'claim_count': claim_count,
        'frozen_claim_count': freeze_counter.get('frozen', 0),
        'blocked_claim_count': freeze_counter.get('blocked', 0),
        'deferred_claim_count': freeze_counter.get('deferred', 0),
        'guardrail_claim_count': guardrail_count,
        'direct_core_count': direct_core,
        'evidence_only_core_count': evidence_core,
        'vision_present': vision_present,
        'reproduce_includes_t20': includes_t20,
        'reproduce_includes_t21': includes_t21,
        'status': 'success',
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'theorem_atlas_summary.json'
    out_path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')

    print('PASS: theorem atlas validation')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path('results/T21')
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            'generated_at_utc': now_iso(),
            'theorem_count': 0,
            'claim_count': 0,
            'frozen_claim_count': 0,
            'blocked_claim_count': 0,
            'deferred_claim_count': 0,
            'guardrail_claim_count': 0,
            'direct_core_count': 0,
            'evidence_only_core_count': 0,
            'vision_present': Path('vision.md').exists(),
            'reproduce_includes_t20': False,
            'reproduce_includes_t21': False,
            'status': 'failed',
            'error': str(exc),
        }
        (out_dir / 'theorem_atlas_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(f'FAIL: {exc}')
        raise SystemExit(1)
