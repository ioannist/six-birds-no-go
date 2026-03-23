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
        'docs/project/lean_objecthood_direct.yaml',
        'docs/project/lean_objecthood_tv_formal_boundary.md',
        'results/T44/lean_objecthood_direct_pack_summary.json',
    ]:
        assert Path(rel).exists()
    assert isinstance(_load('docs/project/lean_objecthood_direct.yaml'), dict)


def test_t30_t43_provenance_exists() -> None:
    for rel in [
        'docs/project/lean_objecthood_uniqueness.yaml',
        'docs/project/lean_objecthood_formal_boundary.md',
        'docs/project/lean_objecthood_tv_feasibility.yaml',
    ]:
        assert Path(rel).exists()


def test_branch_aware_readiness_and_atlas() -> None:
    summary = _load('results/T44/lean_objecthood_direct_pack_summary.json')
    readiness = _theorem_map(_load('docs/project/readiness_checklist.yaml')['theorems'])
    atlas = _theorem_map(_load('docs/project/theorem_atlas.yaml')['theorems'])
    if summary['outcome_mode'] == 'direct_theorem_pack':
        assert readiness['NG_OBJECT_CONTRACTIVE']['lean_support']['status'] == 'direct'
        assert atlas['NG_OBJECT_CONTRACTIVE']['support_snapshot']['lean_support']['status'] == 'direct'
    else:
        assert readiness['NG_OBJECT_CONTRACTIVE']['lean_support']['status'] == 'auxiliary_only'
        assert atlas['NG_OBJECT_CONTRACTIVE']['support_snapshot']['lean_support']['status'] == 'auxiliary_only'


def test_runner_smoke(tmp_path) -> None:
    proc = subprocess.run(
        [sys.executable, 'scripts/run_t44_lean_objecthood_direct_pack.py', '--output-dir', str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((tmp_path / 'lean_objecthood_direct_pack_summary.json').read_text(encoding='utf-8'))
    assert summary['status'] == 'success'
    if summary['outcome_mode'] == 'direct_theorem_pack':
        assert summary['objecthood_direct'] is True
        assert summary['direct_pack_present'] is True
    else:
        assert summary['objecthood_direct'] is False
        assert summary['direct_pack_present'] is False
        assert summary['next_ticket_id'] is None


def test_repro_alignment() -> None:
    text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8')
    assert 'run_t44_lean_objecthood_direct_pack.py' in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
