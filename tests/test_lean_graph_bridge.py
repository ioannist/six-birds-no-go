import json
from pathlib import Path
import subprocess
import sys
import shutil

import sixbirds_nogo


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _theorem_map(rows: list[dict]) -> dict[str, dict]:
    return {row['theorem_id']: row for row in rows}


def test_files_exist_and_parse() -> None:
    for rel in [
        'lean/SixBirdsNoGo/ForestForceBridge.lean',
        'lean/SixBirdsNoGo/ForestForceBridgeExample.lean',
        'lean/SixBirdsNoGo/NullForceBridge.lean',
        'lean/SixBirdsNoGo/NullForceBridgeExample.lean',
        'docs/project/lean_bridge_graph_affinity.yaml',
        'results/T27/lean_graph_bridge_summary.json',
    ]:
        assert Path(rel).exists()
    assert isinstance(_load('docs/project/lean_bridge_graph_affinity.yaml'), dict)


def test_placeholder_free_lean_files() -> None:
    for rel in [
        'lean/SixBirdsNoGo/ForestForceBridge.lean',
        'lean/SixBirdsNoGo/ForestForceBridgeExample.lean',
        'lean/SixBirdsNoGo/NullForceBridge.lean',
        'lean/SixBirdsNoGo/NullForceBridgeExample.lean',
    ]:
        text = Path(rel).read_text(encoding='utf-8')
        assert 'sorry' not in text
        assert 'admit' not in text


def test_import_coverage() -> None:
    text = Path('lean/SixBirdsNoGo.lean').read_text(encoding='utf-8')
    assert 'import SixBirdsNoGo.ForestForceBridge' in text
    assert 'import SixBirdsNoGo.ForestForceBridgeExample' in text
    assert 'import SixBirdsNoGo.NullForceBridge' in text
    assert 'import SixBirdsNoGo.NullForceBridgeExample' in text


def test_readiness_atlas_upgrade_anchors() -> None:
    readiness = _theorem_map(_load('docs/project/readiness_checklist.yaml')['theorems'])
    atlas = _theorem_map(_load('docs/project/theorem_atlas.yaml')['theorems'])

    assert readiness['NG_FORCE_FOREST']['lean_support']['status'] == 'direct'
    assert readiness['NG_FORCE_NULL']['lean_support']['status'] == 'direct'

    assert atlas['NG_FORCE_FOREST']['support_snapshot']['lean_support']['status'] == 'direct'
    assert atlas['NG_FORCE_NULL']['support_snapshot']['lean_support']['status'] == 'direct'


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / 't27'
    proc = subprocess.run(
        [sys.executable, 'scripts/run_t27_lean_graph_bridge.py', '--output-dir', str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads((out / 'lean_graph_bridge_summary.json').read_text(encoding='utf-8'))
    assert summary['theorem_count'] == 2
    assert summary['lean_direct_total'] == 7
    assert summary['lean_auxiliary_total'] == 1
    assert summary['lean_missing_total'] == 0
    assert summary['forest_direct'] is True
    assert summary['null_direct'] is True
    assert summary['forest_bridge_uses_tree_exactness'] is True
    assert summary['forest_bridge_has_zero_closed_walk_corollary'] is True
    assert summary['null_bridge_uses_closed_walk_exactness'] is True
    if shutil.which('lake') is not None:
        assert summary['lake_build_passed'] is True
        assert summary['lake_build_status'] == 'passed'
    else:
        assert summary['lake_build_passed'] is False
        assert summary['lake_build_status'] == 'skipped_tool_unavailable'
    assert summary['status'] == 'success'


def test_repro_alignment() -> None:
    text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8')
    assert 'run_t27_lean_graph_bridge.py' in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
