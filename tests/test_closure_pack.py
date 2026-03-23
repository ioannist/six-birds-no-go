import json
from pathlib import Path
import subprocess
import sys

import sixbirds_nogo


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _theorem_map(rows: list[dict]) -> dict[str, dict]:
    return {row['theorem_id']: row for row in rows}


def _claim_map(rows: list[dict]) -> dict[str, dict]:
    return {row['claim_id']: row for row in rows}


def test_files_exist_and_parse() -> None:
    assert Path('docs/project/theorem_pack_closure.yaml').exists()
    assert Path('results/T24/closure_pack_summary.json').exists()
    assert Path('results/T24/closure_attribution_resolution.json').exists()
    assert isinstance(_load('docs/project/theorem_pack_closure.yaml'), dict)


def test_theorem_pack_schema() -> None:
    pack = _load('docs/project/theorem_pack_closure.yaml')
    fronts = pack['theorem_fronts']
    assert len(fronts) == 1
    row = fronts[0]
    assert row['theorem_id'] == 'NG_MACRO_CLOSURE_DEFICIT'
    assert row['pack_status'] == 'direct_ready'
    assert row['proof_spine']
    assert row['guardrails']
    assert row['attribution_outcome']
    assert row['evidence_refs']


def test_readiness_atlas_claim_upgrade_anchors() -> None:
    readiness = _theorem_map(_load('docs/project/readiness_checklist.yaml')['theorems'])
    atlas = _theorem_map(_load('docs/project/theorem_atlas.yaml')['theorems'])
    claims = _claim_map(_load('docs/project/claim_audit_freeze.yaml')['claims'])

    assert readiness['NG_MACRO_CLOSURE_DEFICIT']['analytic_support']['status'] == 'present'
    assert atlas['NG_MACRO_CLOSURE_DEFICIT']['support_snapshot']['analytic_support']['status'] == 'present'

    assert claims['NG_MACRO_CLOSURE_DEFICIT.core']['support_grade'] == 'direct'
    assert claims['NG_MACRO_CLOSURE_DEFICIT.guardrail']['support_grade'] == 'direct'
    assert claims['NG_MACRO_CLOSURE_DEFICIT.primitive_attribution_gap']['freeze_status'] != 'blocked'


def test_attribution_isolator_anchors() -> None:
    data = _load('results/T24/closure_attribution_resolution.json')
    assert data['outcome_mode'] == 'resolved_by_local_isolator'

    assert data['base_case']['witness_id'] == 'zero_closure_deficit_lumpable'
    assert data['local_isolator']['variant_id'] == 'zero_closure_deficit_lumpable__rewrite_A1_to_B1'

    pd = data['primitive_delta']
    assert pd['rewrite'] == 'off_to_on'
    for k in ['gating', 'holonomy', 'staging', 'packaging', 'drive']:
        assert pd[k] == 'same_off'

    assert data['base_case']['closure']['kind'] == 'zero'
    assert data['local_isolator']['closure']['kind'] == 'finite_positive'

    assert data['base_case']['cycle_rank'] == 1
    assert data['local_isolator']['cycle_rank'] == 1

    assert data['base_case']['max_cycle_affinity'] == '0/1'
    assert data['local_isolator']['max_cycle_affinity'] == '0/1'

    assert data['base_case']['exactness_flag'] is True
    assert data['local_isolator']['exactness_flag'] is True

    assert data['local_isolator']['best_kernel_rows'] == [['1/6', '5/6'], ['1/2', '1/2']]


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / 't24'
    proc = subprocess.run(
        [sys.executable, 'scripts/run_t24_closure_pack.py', '--output-dir', str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads((out / 'closure_pack_summary.json').read_text(encoding='utf-8'))
    assert (out / 'closure_attribution_resolution.json').exists()

    assert summary['theorem_count'] == 1
    assert summary['analytic_present_total'] == 8
    assert summary['overall_direct_core_count'] == 8
    assert summary['pack_direct_core_count'] == 1
    assert summary['attribution_outcome_mode'] == 'resolved_by_local_isolator'
    assert summary['primitive_attribution_resolved'] is True
    assert summary['local_isolator_rewrite_only'] is True
    assert summary['local_isolator_positive_closure'] is True
    assert summary['local_isolator_preserves_exact_null_force_context'] is True
    assert summary['status'] == 'success'


def test_repro_alignment() -> None:
    text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8')
    assert 'run_t24_closure_pack.py' in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
