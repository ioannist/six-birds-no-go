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


def test_files_exist_and_pack_parse() -> None:
    assert Path('docs/project/theorem_pack_arrow_protocol.yaml').exists()
    assert Path('results/T22/dpi_protocol_pack_summary.json').exists()

    pack = _load('docs/project/theorem_pack_arrow_protocol.yaml')
    assert isinstance(pack, dict)


def test_pack_schema_coverage() -> None:
    pack = _load('docs/project/theorem_pack_arrow_protocol.yaml')
    rows = pack['theorem_fronts']
    assert [r['theorem_id'] for r in rows] == ['NG_ARROW_DPI', 'NG_PROTOCOL_TRAP']

    for row in rows:
        assert row['pack_status'] == 'direct_ready'
        assert row['proof_spine']
        assert row['guardrails']
        assert row['evidence_refs']


def test_readiness_atlas_claim_upgrade_anchors() -> None:
    readiness = _theorem_map(_load('docs/project/readiness_checklist.yaml')['theorems'])
    atlas = _theorem_map(_load('docs/project/theorem_atlas.yaml')['theorems'])
    claims = _claim_map(_load('docs/project/claim_audit_freeze.yaml')['claims'])

    assert readiness['NG_ARROW_DPI']['analytic_support']['status'] == 'present'
    assert readiness['NG_PROTOCOL_TRAP']['analytic_support']['status'] == 'present'
    assert readiness['NG_ARROW_DPI']['lean_support']['status'] == 'direct'

    assert atlas['NG_ARROW_DPI']['support_snapshot']['analytic_support']['status'] == 'present'
    assert atlas['NG_PROTOCOL_TRAP']['support_snapshot']['analytic_support']['status'] == 'present'
    assert atlas['NG_ARROW_DPI']['support_snapshot']['lean_support']['status'] == 'direct'
    assert readiness['NG_PROTOCOL_TRAP']['lean_support']['status'] == 'direct'
    assert atlas['NG_PROTOCOL_TRAP']['support_snapshot']['lean_support']['status'] == 'direct'

    assert claims['NG_ARROW_DPI.core']['support_grade'] == 'direct'
    assert claims['NG_PROTOCOL_TRAP.core']['support_grade'] == 'direct'
    assert 'lean/SixBirdsNoGo/ProtocolTrap.lean' in _theorem_map(_load('docs/project/theorem_pack_arrow_protocol.yaml')['theorem_fronts'])['NG_PROTOCOL_TRAP']['evidence_refs']['lean']
    assert 'lean/SixBirdsNoGo/ArrowDPI.lean' in _theorem_map(_load('docs/project/theorem_pack_arrow_protocol.yaml')['theorem_fronts'])['NG_ARROW_DPI']['evidence_refs']['lean']


def test_protocol_scope_correction_anchor() -> None:
    pack = _theorem_map(_load('docs/project/theorem_pack_arrow_protocol.yaml')['theorem_fronts'])
    row = pack['NG_PROTOCOL_TRAP']
    text = ' '.join([row['theorem_statement'], *row['theorem_core']['scope_limits']]).lower()
    assert 'stationary' in text or 'initial' in text


def test_guardrail_anchors() -> None:
    claims = _claim_map(_load('docs/project/claim_audit_freeze.yaml')['claims'])

    dpi_text = claims['NG_ARROW_DPI.guardrail']['claim_text'].lower()
    assert ('proxy' in dpi_text or 'fitted' in dpi_text)
    assert 'initial' in dpi_text

    trap_text = claims['NG_PROTOCOL_TRAP.guardrail']['claim_text'].lower()
    assert ('lifted' in trap_text or 'honest observed' in trap_text)
    assert ('stationary' in trap_text or 'initial' in trap_text)
    assert ('proxy' in trap_text or 'stroboscopic' in trap_text)


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / 't22'
    proc = subprocess.run(
        [sys.executable, 'scripts/run_t22_dpi_protocol_pack.py', '--output-dir', str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary_path = out / 'dpi_protocol_pack_summary.json'
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding='utf-8'))

    assert summary['theorem_count'] == 2
    assert summary['analytic_present_total'] == 8
    assert summary['pack_direct_core_count'] == 2
    assert summary['overall_direct_core_count'] == 8
    assert summary['protocol_scope_has_initial_law'] is True
    assert summary['status'] == 'success'


def test_repro_alignment() -> None:
    text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8')
    assert 'run_t22_dpi_protocol_pack.py' in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
