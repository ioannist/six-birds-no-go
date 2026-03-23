import json
from pathlib import Path
import subprocess
import sys

import sixbirds_nogo


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _theorem_map(rows: list[dict]) -> dict[str, dict]:
    return {row['theorem_id']: row for row in rows}


def test_files_exist_and_parse() -> None:
    for rel in [
        'docs/project/lean_objecthood_tv_feasibility.yaml',
        'docs/project/lean_objecthood_tv_formal_boundary.md',
        'results/T43/lean_objecthood_tv_feasibility_summary.json',
    ]:
        assert Path(rel).exists()
    assert isinstance(_load('docs/project/lean_objecthood_tv_feasibility.yaml'), dict)


def test_frontier_status_no_drift() -> None:
    summary = _load('results/T43/lean_objecthood_tv_feasibility_summary.json')
    assert summary['direct_front_count'] == 7
    assert summary['auxiliary_front_count'] == 1
    assert summary['missing_front_count'] == 0
    assert summary['current_objecthood_lean_status'] == 'auxiliary_only'
    assert summary['theorem_status_unchanged'] is True


def test_obligation_matrix_coverage() -> None:
    data = _load('docs/project/lean_objecthood_tv_feasibility.yaml')
    obligations = data['obligation_matrix']
    ids = [row['obligation_id'] for row in obligations]
    assert ids == [
        'OBJ_BASE_FINITE_LAWS',
        'OBJ_STRICT_CONTRACTION_UNIQUENESS_CORE',
        'OBJ_TV_DISTANCE_ON_FINITE_LAWS',
        'OBJ_TV_TRIANGLE_AND_ZERO_LEMMAS',
        'OBJ_DOBRUSHIN_CONTRACTION_INTERFACE',
        'OBJ_FIXED_DISTRIBUTION_ON_FINITE_LAWS',
        'OBJ_TV_EPS_STABILITY_PREDICATE',
        'OBJ_APPROXIMATE_OBJECT_SEPARATION_BOUND',
        'OBJ_PROXY_AND_NONCONTRACTIVE_CONTEXT_OUT_OF_SCOPE',
    ]
    status = {row['obligation_id']: row['status'] for row in obligations}
    assert status['OBJ_BASE_FINITE_LAWS'] == 'already_formalized'
    assert status['OBJ_STRICT_CONTRACTION_UNIQUENESS_CORE'] == 'already_formalized'
    assert status['OBJ_PROXY_AND_NONCONTRACTIVE_CONTEXT_OUT_OF_SCOPE'] == 'out_of_scope'


def test_branch_validity() -> None:
    summary = _load('results/T43/lean_objecthood_tv_feasibility_summary.json')
    if summary['decision_mode'] == 'proceed_to_tv_bridge':
        assert summary['needed_narrow_count'] == 6
        assert summary['requires_forbidden_expansion_count'] == 0
        assert summary['narrow_bridge_possible'] is True
        assert summary['generic_metric_or_analysis_required'] is False
        assert summary['next_ticket_id'] == 'T44'
        assert summary['t44_branch'] == 'attempt_direct_pack'
    else:
        assert summary['requires_forbidden_expansion_count'] >= 1
        assert summary['narrow_bridge_possible'] is False
        assert summary['generic_metric_or_analysis_required'] is True
        assert summary['next_ticket_id'] is None
        assert summary['t44_branch'] == 'freeze_permanent_auxiliary_boundary'


def test_t30_provenance_rebased() -> None:
    uniq = _load('docs/project/lean_objecthood_uniqueness.yaml')['theorem_fronts'][0]
    summary = _load('results/T43/lean_objecthood_tv_feasibility_summary.json')
    if summary['decision_mode'] == 'proceed_to_tv_bridge':
        assert uniq['readiness_delta']['full_tv_bound_bridge_pending'] is True
        assert uniq['next_ticket']['id'] == 'T44'
    else:
        assert uniq['readiness_delta']['full_tv_bound_bridge_pending'] is False
        assert uniq['next_ticket'] is None


def test_runner_smoke(tmp_path) -> None:
    proc = subprocess.run(
        [sys.executable, 'scripts/run_t43_objecthood_tv_feasibility.py', '--output-dir', str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((tmp_path / 'lean_objecthood_tv_feasibility_summary.json').read_text(encoding='utf-8'))
    assert summary['theorem_count'] == 1
    assert summary['direct_front_count'] == 7
    assert summary['auxiliary_front_count'] == 1
    assert summary['missing_front_count'] == 0
    assert summary['current_objecthood_lean_status'] == 'auxiliary_only'
    assert summary['obligation_count'] == 9
    assert summary['already_formalized_count'] >= 2
    assert summary['out_of_scope_count'] == 1
    assert summary['uniqueness_core_retained'] is True
    assert summary['proxy_metrics_out_of_scope'] is True
    assert summary['noncontractive_context_out_of_scope'] is True
    assert summary['theorem_status_unchanged'] is True
    if summary['decision_mode'] == 'proceed_to_tv_bridge':
        assert summary['next_ticket_id'] == 'T44'
        assert summary['needed_narrow_count'] == 6
        assert summary['requires_forbidden_expansion_count'] == 0
        assert summary['narrow_bridge_possible'] is True
        assert summary['generic_metric_or_analysis_required'] is False
        assert summary['t44_branch'] == 'attempt_direct_pack'
    else:
        assert summary['next_ticket_id'] is None
        assert summary['requires_forbidden_expansion_count'] >= 1
        assert summary['narrow_bridge_possible'] is False
        assert summary['generic_metric_or_analysis_required'] is True
        assert summary['t44_branch'] == 'freeze_permanent_auxiliary_boundary'
    assert summary['status'] == 'success'


def test_repro_alignment() -> None:
    text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8')
    assert 'run_t43_objecthood_tv_feasibility.py' in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
