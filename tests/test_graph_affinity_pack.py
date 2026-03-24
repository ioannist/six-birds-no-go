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
    assert Path('docs/project/theorem_pack_graph_affinity.yaml').exists()
    assert Path('results/T23/graph_affinity_pack_summary.json').exists()
    data = _load('docs/project/theorem_pack_graph_affinity.yaml')
    assert isinstance(data, dict)


def test_pack_schema_coverage() -> None:
    pack = _load('docs/project/theorem_pack_graph_affinity.yaml')
    rows = pack['theorem_fronts']
    assert [r['theorem_id'] for r in rows] == ['NG_FORCE_FOREST', 'NG_FORCE_NULL']
    for row in rows:
        assert row['pack_status'] == 'direct_ready'
        assert row['proof_spine']
        assert row['guardrails']
        assert row['evidence_refs']


def test_readiness_atlas_claim_upgrade_anchors() -> None:
    readiness = _theorem_map(_load('docs/project/readiness_checklist.yaml')['theorems'])
    atlas = _theorem_map(_load('docs/project/theorem_atlas.yaml')['theorems'])
    claims = _claim_map(_load('docs/project/claim_audit_freeze.yaml')['claims'])

    assert readiness['NG_FORCE_FOREST']['analytic_support']['status'] == 'present'
    assert readiness['NG_FORCE_NULL']['analytic_support']['status'] == 'present'

    assert atlas['NG_FORCE_FOREST']['support_snapshot']['analytic_support']['status'] == 'present'
    assert atlas['NG_FORCE_NULL']['support_snapshot']['analytic_support']['status'] == 'present'

    assert claims['NG_FORCE_FOREST.core']['support_grade'] == 'direct'
    assert claims['NG_FORCE_NULL.core']['support_grade'] == 'direct'

    assert readiness['NG_FORCE_FOREST']['lean_support']['status'] == 'direct'
    assert readiness['NG_FORCE_NULL']['lean_support']['status'] == 'direct'
    assert atlas['NG_FORCE_FOREST']['support_snapshot']['lean_support']['status'] == 'direct'
    assert atlas['NG_FORCE_NULL']['support_snapshot']['lean_support']['status'] == 'direct'


def test_theorem_core_anchors() -> None:
    pack = _theorem_map(_load('docs/project/theorem_pack_graph_affinity.yaml')['theorem_fronts'])
    forest = pack['NG_FORCE_FOREST']
    null = pack['NG_FORCE_NULL']

    forest_text = ' '.join([forest['theorem_statement'], *forest['theorem_core']['antecedent'], *forest['proof_spine']]).lower()
    assert ('forest' in forest_text) or ('cycle rank' in forest_text)

    null_text = ' '.join([null['theorem_statement'], *null['theorem_core']['antecedent'], *null['proof_spine']]).lower()
    assert ('exact' in null_text) or ('null' in null_text) or ('bidirected' in null_text)


def test_guardrail_anchors() -> None:
    claims = _claim_map(_load('docs/project/claim_audit_freeze.yaml')['claims'])

    forest_text = claims['NG_FORCE_FOREST.guardrail']['claim_text'].lower()
    assert ('threshold' in forest_text) or ('floor' in forest_text)
    assert ('one-way' in forest_text) or ('support' in forest_text)

    null_text = claims['NG_FORCE_NULL.guardrail']['claim_text'].lower()
    assert ('threshold' in null_text) or ('regularization' in null_text)
    assert ('exact' in null_text) or ('bidirected' in null_text) or ('affinity' in null_text)


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / 't23'
    proc = subprocess.run(
        [sys.executable, 'scripts/run_t23_graph_affinity_pack.py', '--output-dir', str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary_path = out / 'graph_affinity_pack_summary.json'
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding='utf-8'))

    assert summary['theorem_count'] == 2
    assert summary['analytic_present_total'] == 8
    assert summary['pack_direct_core_count'] == 2
    assert summary['overall_direct_core_count'] == 8
    assert summary['forest_pack_uses_cycle_rank'] is True
    assert summary['null_pack_uses_exactness'] is True
    assert summary['threshold_guardrails_frozen'] is True
    assert summary['status'] == 'success'


def test_repro_alignment() -> None:
    text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8')
    assert 'run_t23_graph_affinity_pack.py' in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__


def test_theorem_pack_lean_evidence_refs() -> None:
    pack = _theorem_map(_load('docs/project/theorem_pack_graph_affinity.yaml')['theorem_fronts'])
    forest_lean = pack['NG_FORCE_FOREST']['evidence_refs']['lean']
    null_lean = pack['NG_FORCE_NULL']['evidence_refs']['lean']
    assert 'lean/SixBirdsNoGo/ForestForceBridge.lean' in forest_lean
    assert 'lean/SixBirdsNoGo/NullForceBridge.lean' in null_lean
    assert 'docs/project/lean_bridge_graph_affinity.yaml' in forest_lean
    assert 'docs/project/lean_bridge_graph_affinity.yaml' in null_lean
