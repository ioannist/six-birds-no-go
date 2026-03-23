import json
from pathlib import Path
import re
import subprocess
import sys

import sixbirds_nogo
from sixbirds_nogo import repro


def test_helper_smoke(tmp_path) -> None:
    p = tmp_path / 'x.txt'
    p.write_text('abc', encoding='utf-8')
    d = repro.sha256_file(p)
    assert len(d) == 64
    assert re.fullmatch(r'[0-9a-f]{64}', d)

    tools = repro.probe_tool_versions()
    assert 'python' in tools
    assert 'pytest' in tools
    assert 'make' in tools


def test_makefile_and_commands_doc() -> None:
    make = Path('Makefile').read_text(encoding='utf-8')
    assert 'reproduce:' in make

    commands = Path('docs/project/commands.md').read_text(encoding='utf-8')
    assert 'make reproduce' in commands


def test_runner_smoke_skip_pytest(tmp_path) -> None:
    out = tmp_path / 'manifest'
    proc = subprocess.run(
        [
            sys.executable,
            'scripts/run_t19_repro_pipeline.py',
            '--manifest-dir',
            str(out),
            '--skip-pytest',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    manifest_path = out / 'artifact_manifest.json'
    assert manifest_path.exists()

    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert data['canonical_command'] == 'make reproduce'
    assert data['status'] == 'success'
    assert 'generated_at_utc' in data
    assert 'tool_versions' in data
    assert 'steps' in data
    assert 'file_hashes' in data

    step_names = [s['name'] for s in data['steps']]
    required = [
        'validate_configs',
        'validate_witnesses',
        'package_import_smoke',
        'run_t11_definability_suite',
        'run_t12_witness_manifest',
        'run_t13_master_witness_suite',
        'run_t14_primitive_matrix',
        'run_t15_robustness_suite',
        'run_t20_readiness_checkpoint',
        'run_t21_theorem_atlas',
        'run_t22_dpi_protocol_pack',
        'run_t23_graph_affinity_pack',
        'run_t24_closure_pack',
        'run_t25_objecthood_pack',
        'run_t26_bounded_interface_pack',
        'run_t27_lean_graph_bridge',
        'run_t28_lean_finite_lens_count',
        'run_t29_lean_bounded_interface_corollary',
        'run_t30_lean_objecthood_uniqueness',
        'run_t35_scope_charter',
        'run_t36_lean_probability_core',
        'run_t37_lean_kl_dpi_core',
        'run_t38_lean_arrow_dpi',
        'run_t39_lean_protocol_trap',
        'run_t40_closure_feasibility',
        'run_t41_lean_closure_variational_core',
        'run_t42_lean_closure_direct_pack',
        'run_t43_objecthood_tv_feasibility',
        'run_t44_lean_objecthood_direct_pack',
        'run_r12_bibliography_citations',
        'run_r16_citation_enrichment',
        'run_r13_math_paper_validator',
        'run_r14_math_paper_red_team_review',
        'run_r15_finalize_and_bundle',
    ]
    for name in required:
        assert name in step_names

    forbidden = [
        'run_t31_paper_skeleton',
        'run_t32_asset_freeze',
        'run_t33_draft_v1',
        'run_t34_red_team_review',
        'run_t45_draft_v2_revision',
        'run_t46_caption_appendix_polish',
        'run_t47_submission_prep',
        'run_w00_narrative_charter',
        'run_w09_draft_v2_revision',
        'run_r00_freeze_and_open_rewrite_lane',
        'run_r11_supplement_split',
    ]
    for name in forbidden:
        assert name not in step_names

    hashes = data['file_hashes']
    for rel in [
        'paper/main.tex',
        'paper/macros.tex',
        'paper/refs.bib',
        'paper/sections/03_main_results.tex',
        'paper/appendices/appendix_a_probability_kl.tex',
        'paper/supplement/main.tex',
        'docs/project/revision_queue_r15.yaml',
        'scripts/run_r15_finalize_and_bundle.py',
        'paper/build/main.pdf',
        'paper/supplement/build/supplement.pdf',
        'results/submission_bundle/source.zip',
    ]:
        assert rel in hashes

    for rel in [
        'paper/draft_v1.md',
        'paper/draft_v2.md',
        'paper/draft_v3.md',
        'paper/manuscript_skeleton.md',
        'paper/rewrite_tex/main.tex',
        'paper/math_rewrite/main.tex',
        'paper/submission_bundle/manuscript_submission.md',
    ]:
        assert rel not in hashes


def test_package_version_smoke() -> None:
    assert hasattr(sixbirds_nogo, '__version__')
    assert sixbirds_nogo.__version__ == sixbirds_nogo.version
