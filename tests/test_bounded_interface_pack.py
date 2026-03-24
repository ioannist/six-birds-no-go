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
    assert Path('docs/project/theorem_pack_bounded_interface.yaml').exists()
    assert Path('results/T26/bounded_interface_pack_summary.json').exists()
    assert Path('docs/project/lean_corollary_bounded_interface.yaml').exists()
    assert Path('results/T29/lean_bounded_interface_corollary_summary.json').exists()
    assert isinstance(_load('docs/project/theorem_pack_bounded_interface.yaml'), dict)


def test_theorem_pack_schema() -> None:
    pack = _load('docs/project/theorem_pack_bounded_interface.yaml')
    fronts = pack['theorem_fronts']
    assert len(fronts) == 1
    row = fronts[0]
    assert row['theorem_id'] == 'NG_LADDER_BOUNDED_INTERFACE'
    assert row['pack_status'] == 'direct_ready'
    assert row['proof_spine']
    assert row['guardrails']
    assert row['evidence_refs']


def test_readiness_atlas_claim_upgrade_anchors() -> None:
    readiness = _theorem_map(_load('docs/project/readiness_checklist.yaml')['theorems'])
    atlas = _theorem_map(_load('docs/project/theorem_atlas.yaml')['theorems'])
    claims = _claim_map(_load('docs/project/claim_audit_freeze.yaml')['claims'])

    assert readiness['NG_LADDER_BOUNDED_INTERFACE']['analytic_support']['status'] == 'present'
    assert readiness['NG_LADDER_BOUNDED_INTERFACE']['lean_support']['status'] == 'direct'
    assert atlas['NG_LADDER_BOUNDED_INTERFACE']['support_snapshot']['analytic_support']['status'] == 'present'
    assert atlas['NG_LADDER_BOUNDED_INTERFACE']['support_snapshot']['lean_support']['status'] == 'direct'

    assert claims['NG_LADDER_BOUNDED_INTERFACE.core']['support_grade'] == 'direct'
    assert 'NG_LADDER_BOUNDED_INTERFACE.guardrail' in claims
    assert claims['NG_LADDER_BOUNDED_INTERFACE.guardrail']['support_grade'] == 'direct'
    assert claims['NG_LADDER_BOUNDED_INTERFACE.core']['next_ticket'] is None


def test_theorem_core_anchors() -> None:
    pack = _load('docs/project/theorem_pack_bounded_interface.yaml')
    row = pack['theorem_fronts'][0]
    text = ' '.join([row['theorem_statement'], *row['theorem_core']['antecedent'], *row['proof_spine']]).lower()
    assert 'interface' in text
    assert ('definable' in text) or ('2^' in text)
    assert ('idempotent' in text) or ('saturat' in text)


def test_guardrail_anchors() -> None:
    claims = _claim_map(_load('docs/project/claim_audit_freeze.yaml')['claims'])
    text = claims['NG_LADDER_BOUNDED_INTERFACE.guardrail']['claim_text'].lower()
    assert 'fixed' in text
    assert ('lens' in text) or ('domain' in text)
    assert ('extension' in text) or ('scope' in text)


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / 't26'
    proc = subprocess.run(
        [sys.executable, 'scripts/run_t26_bounded_interface_pack.py', '--output-dir', str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads((out / 'bounded_interface_pack_summary.json').read_text(encoding='utf-8'))

    assert summary['theorem_count'] == 1
    assert summary['analytic_present_total'] == 8
    assert summary['overall_direct_core_count'] == 8
    assert summary['pack_direct_core_count'] == 1
    assert summary['fixed_interface_frozen'] is True
    assert summary['fixed_domain_frozen'] is True
    assert summary['fixed_package_frozen'] is True
    assert summary['definability_bound_explicit'] is True
    assert summary['idempotent_saturation_explicit'] is True
    assert summary['extension_escape_scoped_outside_theorem'] is True
    assert summary['theorem_guardrails_frozen'] is True
    assert summary['low_proxy_risk_preserved'] is True
    assert summary['status'] == 'success'


def test_theorem_pack_lean_evidence_refs() -> None:
    pack = _load('docs/project/theorem_pack_bounded_interface.yaml')
    row = pack['theorem_fronts'][0]
    lean_refs = row['evidence_refs']['lean']
    assert 'lean/SixBirdsNoGo/FiniteLensDefinability.lean' in lean_refs
    assert 'lean/SixBirdsNoGo/FiniteLensDefinabilityExample.lean' in lean_refs
    assert 'lean/SixBirdsNoGo/BoundedInterfaceNoLadder.lean' in lean_refs
    assert 'lean/SixBirdsNoGo/BoundedInterfaceNoLadderExample.lean' in lean_refs
    assert 'docs/project/lean_count_bounded_interface.yaml' in lean_refs
    assert 'docs/project/lean_corollary_bounded_interface.yaml' in lean_refs
    assert 'results/T28/lean_finite_lens_count_summary.json' in lean_refs
    assert 'results/T29/lean_bounded_interface_corollary_summary.json' in lean_refs


def test_repro_alignment() -> None:
    text = Path('src/sixbirds_nogo/repro.py').read_text(encoding='utf-8')
    assert 'run_t26_bounded_interface_pack.py' in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
