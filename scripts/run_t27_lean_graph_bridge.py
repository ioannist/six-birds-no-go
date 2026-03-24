#!/usr/bin/env python3
"""Validate T27 Lean graph/forest direct bridge and emit summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import shutil


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path} must parse to object')
    return data


def fail(msg: str) -> None:
    raise ValueError(msg)


def _has_nonempty_list(obj: dict, key: str) -> bool:
    return isinstance(obj.get(key), list) and len(obj.get(key)) > 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Run T27 Lean graph bridge validation')
    parser.add_argument('--output-dir', default='results/T27')
    args = parser.parse_args()

    bridge_p = Path('docs/project/lean_bridge_graph_affinity.yaml')
    ready_p = Path('docs/project/readiness_checklist.yaml')
    atlas_p = Path('docs/project/theorem_atlas.yaml')
    pack_p = Path('docs/project/theorem_pack_graph_affinity.yaml')
    claims_p = Path('docs/project/claim_audit_freeze.yaml')
    lean_root_p = Path('lean/SixBirdsNoGo.lean')

    forest_p = Path('lean/SixBirdsNoGo/ForestForceBridge.lean')
    forest_ex_p = Path('lean/SixBirdsNoGo/ForestForceBridgeExample.lean')
    null_p = Path('lean/SixBirdsNoGo/NullForceBridge.lean')
    null_ex_p = Path('lean/SixBirdsNoGo/NullForceBridgeExample.lean')

    required = [
        bridge_p,
        ready_p,
        atlas_p,
        pack_p,
        claims_p,
        lean_root_p,
        forest_p,
        forest_ex_p,
        null_p,
        null_ex_p,
    ]
    for p in required:
        if not p.exists():
            fail(f'missing required input: {p}')

    bridge = load_json(bridge_p)
    readiness = load_json(ready_p)
    atlas = load_json(atlas_p)
    pack = load_json(pack_p)
    claims = load_json(claims_p)

    for k in ['version', 'generated_at_utc', 'source_context', 'status_enums', 'theorem_fronts']:
        if k not in bridge:
            fail(f'lean bridge file missing key: {k}')

    fronts = bridge['theorem_fronts']
    ids = [r.get('theorem_id') for r in fronts]
    if ids != ['NG_FORCE_FOREST', 'NG_FORCE_NULL']:
        fail('theorem-front IDs must be exactly [NG_FORCE_FOREST, NG_FORCE_NULL]')

    for row in fronts:
        if row.get('bridge_status') != 'direct_ready':
            fail(f'{row.get("theorem_id")} bridge_status must be direct_ready')
        if not str(row.get('bridge_statement', '')).strip():
            fail(f'{row.get("theorem_id")} bridge_statement must be non-empty')
        for key in ['prerequisites', 'direct_corollaries', 'scope_limits', 'lean_artifacts']:
            if not _has_nonempty_list(row, key):
                fail(f'{row.get("theorem_id")} must have non-empty {key}')

    forest_text = forest_p.read_text(encoding='utf-8')
    null_text = null_p.read_text(encoding='utf-8')
    lean_root_text = lean_root_p.read_text(encoding='utf-8')

    forest_uses_tree_exactness = 'TreeExactness' in forest_text
    forest_uses_closed_walk_exactness = 'ClosedWalkExactness' in forest_text
    forest_has_zero_closed_walk_corollary = 'forest_closedWalkSum_eq_zero' in forest_text
    null_uses_closed_walk_exactness = 'ClosedWalkExactness' in null_text

    if not (forest_uses_tree_exactness and forest_uses_closed_walk_exactness):
        fail('ForestForceBridge.lean must explicitly use TreeExactness and ClosedWalkExactness')
    if not null_uses_closed_walk_exactness:
        fail('NullForceBridge.lean must explicitly use ClosedWalkExactness')

    for imp in [
        'import SixBirdsNoGo.ForestForceBridge',
        'import SixBirdsNoGo.ForestForceBridgeExample',
        'import SixBirdsNoGo.NullForceBridge',
        'import SixBirdsNoGo.NullForceBridgeExample',
    ]:
        if imp not in lean_root_text:
            fail(f'lean/SixBirdsNoGo.lean missing import: {imp}')

    ready_map = {t['theorem_id']: t for t in readiness['theorems']}
    atlas_map = {t['theorem_id']: t for t in atlas['theorems']}
    claim_map = {c['claim_id']: c for c in claims['claims']}
    pack_map = {t['theorem_id']: t for t in pack['theorem_fronts']}

    if ready_map['NG_FORCE_FOREST']['lean_support']['status'] != 'direct':
        fail('readiness NG_FORCE_FOREST lean_support.status must be direct')
    if ready_map['NG_FORCE_NULL']['lean_support']['status'] != 'direct':
        fail('readiness NG_FORCE_NULL lean_support.status must be direct')

    if atlas_map['NG_FORCE_FOREST']['support_snapshot']['lean_support']['status'] != 'direct':
        fail('atlas NG_FORCE_FOREST lean_support.status must be direct')
    if atlas_map['NG_FORCE_NULL']['support_snapshot']['lean_support']['status'] != 'direct':
        fail('atlas NG_FORCE_NULL lean_support.status must be direct')

    for tid in ['NG_FORCE_FOREST', 'NG_FORCE_NULL']:
        lean_refs = pack_map[tid].get('evidence_refs', {}).get('lean', [])
        if 'docs/project/lean_bridge_graph_affinity.yaml' not in lean_refs:
            fail(f'{tid} theorem pack lean evidence missing bridge yaml ref')

    for cid in ['NG_FORCE_FOREST.core', 'NG_FORCE_NULL.core']:
        bl = ' '.join(claim_map[cid].get('blockers', [])).lower()
        if 'direct lean theorem' in bl or 'lean theorem missing' in bl:
            fail(f'{cid} still carries direct Lean-missing blocker language')

    lake_available = shutil.which('lake') is not None
    if lake_available:
        lake = subprocess.run('cd lean && lake build', shell=True, capture_output=True, text=True, check=False)
        lake_build_passed = lake.returncode == 0
        if not lake_build_passed:
            fail('cd lean && lake build failed')
        lake_build_status = 'passed'
    else:
        lake_build_passed = False
        lake_build_status = 'skipped_tool_unavailable'

    repro_text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8') if Path('src/sixbirds_nogo/repro.py').exists() else ''
    includes_t20 = 'run_t20_readiness_checkpoint.py' in repro_text
    includes_t21 = 'run_t21_theorem_atlas.py' in repro_text
    includes_t22 = 'run_t22_dpi_protocol_pack.py' in repro_text
    includes_t23 = 'run_t23_graph_affinity_pack.py' in repro_text
    includes_t24 = 'run_t24_closure_pack.py' in repro_text
    includes_t25 = 'run_t25_objecthood_pack.py' in repro_text
    includes_t26 = 'run_t26_bounded_interface_pack.py' in repro_text
    includes_t27 = 'run_t27_lean_graph_bridge.py' in repro_text
    if not includes_t27:
        fail('repro pipeline missing run_t27_lean_graph_bridge.py step')

    lean_direct_total = sum(1 for t in readiness['theorems'] if t['lean_support']['status'] == 'direct')
    lean_aux_total = sum(1 for t in readiness['theorems'] if t['lean_support']['status'] == 'auxiliary_only')
    lean_missing_total = sum(1 for t in readiness['theorems'] if t['lean_support']['status'] == 'missing')

    summary = {
        'generated_at_utc': now_iso(),
        'theorem_count': 2,
        'updated_theorem_ids': ['NG_FORCE_FOREST', 'NG_FORCE_NULL'],
        'lean_direct_total': lean_direct_total,
        'lean_auxiliary_total': lean_aux_total,
        'lean_missing_total': lean_missing_total,
        'forest_direct': ready_map['NG_FORCE_FOREST']['lean_support']['status'] == 'direct',
        'null_direct': ready_map['NG_FORCE_NULL']['lean_support']['status'] == 'direct',
        'forest_bridge_uses_tree_exactness': forest_uses_tree_exactness,
        'forest_bridge_has_zero_closed_walk_corollary': forest_has_zero_closed_walk_corollary,
        'null_bridge_uses_closed_walk_exactness': null_uses_closed_walk_exactness,
        'lake_build_passed': lake_build_passed,
        'lake_build_status': lake_build_status,
        'reproduce_includes_t20': includes_t20,
        'reproduce_includes_t21': includes_t21,
        'reproduce_includes_t22': includes_t22,
        'reproduce_includes_t23': includes_t23,
        'reproduce_includes_t24': includes_t24,
        'reproduce_includes_t25': includes_t25,
        'reproduce_includes_t26': includes_t26,
        'reproduce_includes_t27': includes_t27,
        'vision_present': bool(bridge.get('source_context', {}).get('vision_present')),
        'status': 'success',
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'lean_graph_bridge_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')

    print('PASS: T27 lean graph bridge validation')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        out_dir = Path('results/T27')
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            'generated_at_utc': now_iso(),
            'theorem_count': 0,
            'updated_theorem_ids': [],
            'lean_direct_total': 0,
            'lean_auxiliary_total': 0,
            'lean_missing_total': 0,
            'forest_direct': False,
            'null_direct': False,
            'forest_bridge_uses_tree_exactness': False,
            'forest_bridge_has_zero_closed_walk_corollary': False,
            'null_bridge_uses_closed_walk_exactness': False,
            'lake_build_passed': False,
            'lake_build_status': 'failed',
            'reproduce_includes_t20': False,
            'reproduce_includes_t21': False,
            'reproduce_includes_t22': False,
            'reproduce_includes_t23': False,
            'reproduce_includes_t24': False,
            'reproduce_includes_t25': False,
            'reproduce_includes_t26': False,
            'reproduce_includes_t27': False,
            'vision_present': Path('vision.md').exists(),
            'status': 'failed',
            'error': str(exc),
        }
        (out_dir / 'lean_graph_bridge_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(f'FAIL: {exc}')
        raise SystemExit(1)
