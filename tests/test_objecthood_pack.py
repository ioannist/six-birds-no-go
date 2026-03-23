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


def _t44_outcome() -> str | None:
    p = Path('results/T44/lean_objecthood_direct_pack_summary.json')
    if not p.exists():
        return None
    return _load(str(p))['outcome_mode']


def test_files_exist_and_parse() -> None:
    assert Path('docs/project/theorem_pack_objecthood.yaml').exists()
    assert Path('results/T25/objecthood_pack_summary.json').exists()
    assert Path('results/T25/objecthood_metric_guardrails_resolution.json').exists()
    assert Path('docs/project/lean_objecthood_uniqueness.yaml').exists()
    assert Path('docs/project/lean_objecthood_formal_boundary.md').exists()
    assert Path('results/T30/lean_objecthood_uniqueness_summary.json').exists()
    assert isinstance(_load('docs/project/theorem_pack_objecthood.yaml'), dict)


def test_theorem_pack_schema() -> None:
    pack = _load('docs/project/theorem_pack_objecthood.yaml')
    fronts = pack['theorem_fronts']
    assert len(fronts) == 1
    row = fronts[0]
    assert row['theorem_id'] == 'NG_OBJECT_CONTRACTIVE'
    assert row['pack_status'] == 'direct_ready'
    assert row['proof_spine']
    assert row['guardrails']
    assert row['regime_resolution']
    assert row['evidence_refs']
    lean_refs = row['evidence_refs']['lean']
    assert 'lean/SixBirdsNoGo/ContractionUniqueness.lean' in lean_refs
    assert 'lean/SixBirdsNoGo/ContractionUniquenessExample.lean' in lean_refs
    assert 'docs/project/lean_objecthood_uniqueness.yaml' in lean_refs
    assert 'docs/project/lean_objecthood_formal_boundary.md' in lean_refs
    assert 'results/T30/lean_objecthood_uniqueness_summary.json' in lean_refs
    if _t44_outcome() == 'direct_theorem_pack':
        assert row['next_ticket']['id'] == 'PLAN_NEXT_20_objecthood_scope_guardrail_hold'
    else:
        assert row['remaining_blockers'] == []
        assert row['next_ticket'] is None


def test_readiness_atlas_claim_upgrade_anchors() -> None:
    readiness = _theorem_map(_load('docs/project/readiness_checklist.yaml')['theorems'])
    atlas = _theorem_map(_load('docs/project/theorem_atlas.yaml')['theorems'])
    claims = _claim_map(_load('docs/project/claim_audit_freeze.yaml')['claims'])

    assert readiness['NG_OBJECT_CONTRACTIVE']['analytic_support']['status'] == 'present'
    assert atlas['NG_OBJECT_CONTRACTIVE']['support_snapshot']['analytic_support']['status'] == 'present'
    assert readiness['NG_OBJECT_CONTRACTIVE']['lean_support']['status'] == 'auxiliary_only'
    assert atlas['NG_OBJECT_CONTRACTIVE']['support_snapshot']['lean_support']['status'] == 'auxiliary_only'

    assert claims['NG_OBJECT_CONTRACTIVE.core']['support_grade'] == 'direct'
    assert claims['NG_OBJECT_CONTRACTIVE.guardrail']['support_grade'] == 'direct'
    assert claims['NG_OBJECT_CONTRACTIVE.metric_regime_gap']['freeze_status'] != 'blocked'
    if _t44_outcome() == 'direct_theorem_pack':
        assert claims['NG_OBJECT_CONTRACTIVE.core']['next_ticket']['id'] == 'PLAN_NEXT_20_objecthood_scope_guardrail_hold'
    else:
        assert claims['NG_OBJECT_CONTRACTIVE.core']['blockers'] == []
        assert claims['NG_OBJECT_CONTRACTIVE.core']['next_ticket'] is None


def test_regime_resolution_anchors() -> None:
    data = _load('results/T25/objecthood_metric_guardrails_resolution.json')

    assert data['outcome_mode'] == 'resolved_by_metric_regime_freeze'
    assert data['historical_gap_claim_id'] == 'NG_OBJECT_CONTRACTIVE.metric_regime_gap'

    assert data['admissible_metric']['metric_id'] == 'total_variation'
    assert data['admissible_regime']['lambda_condition'] == 'lambda_lt_1'

    assert data['theorem_witness']['witness_id'] == 'contractive_unique_object'
    assert data['theorem_witness']['fixed_point_count'] == 1
    assert data['theorem_witness']['unique_fixed_distribution'] == ['3/4', '1/4']
    assert data['theorem_witness']['stable_point_count'] == 3
    assert data['theorem_witness']['theorem_metric_cluster_count'] == 1

    assert data['proxy_metric_artifact']['cluster_count'] == 2
    assert data['approximate_bound_check']['holds'] is True

    assert data['contextual_noncontractive_case']['witness_id'] == 'noncontractive_multiobject'
    assert 'outside' in data['contextual_noncontractive_case']['note'].lower()


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / 't25'
    proc = subprocess.run(
        [sys.executable, 'scripts/run_t30_lean_objecthood_uniqueness.py', '--output-dir', str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads((out / 'lean_objecthood_uniqueness_summary.json').read_text(encoding='utf-8'))
    assert summary['theorem_count'] == 1
    assert summary['outcome_mode'] == 'direct_uniqueness_theorem'
    assert summary['lean_direct_total'] == 7
    assert summary['lean_auxiliary_total'] == 1
    assert summary['lean_missing_total'] == 0
    assert summary['direct_uniqueness_theorem_present'] is True
    assert summary['formal_boundary_note_present'] is True
    assert summary['objecthood_lean_status_after'] == 'auxiliary_only'
    assert summary['strict_contraction_on_ne_explicit'] is True
    assert summary['at_most_one_fixed_point_formalized'] is True
    assert summary['discrete_model_example_present'] is True
    assert summary['formal_boundary_frozen'] is True
    assert summary['full_tv_bound_bridge_pending'] is False
    assert summary['reproduce_includes_t29'] is True
    assert summary['reproduce_includes_t30'] is True
    assert summary['status'] == 'success'


def test_repro_alignment() -> None:
    text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8')
    assert 'run_t25_objecthood_pack.py' in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
