"""Reproducibility helpers for the current canonical theorem-paper line."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any

ROOT = Path('.').resolve()

CURRENT_RESULTS_DIRS = [
    'results/T11',
    'results/T12',
    'results/T13',
    'results/T14',
    'results/T15',
    'results/T20',
    'results/T21',
    'results/T22',
    'results/T23',
    'results/T24',
    'results/T25',
    'results/T26',
    'results/T27',
    'results/T28',
    'results/T29',
    'results/T30',
    'results/T35',
    'results/T36',
    'results/T37',
    'results/T38',
    'results/T39',
    'results/T40',
    'results/T41',
    'results/T42',
    'results/T43',
    'results/T44',
    'results/R12',
    'results/R16',
    'results/R13',
    'results/R14',
    'results/R15',
    'results/submission_bundle',
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    p = Path(path)
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _probe_command(cmd: list[str]) -> dict[str, Any]:
    tool = cmd[0]
    exe = shutil.which(tool)
    if exe is None:
        return {'available': False, 'version': None, 'path': None}
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (proc.stdout or proc.stderr or '').strip()
    first = text.splitlines()[0] if text else None
    return {'available': proc.returncode == 0, 'version': first, 'path': exe}


def probe_tool_versions() -> dict[str, Any]:
    tools = {
        'python': _probe_command(['python3', '--version']),
        'pytest': _probe_command(['pytest', '--version']),
        'make': _probe_command(['make', '--version']),
        'lean': _probe_command(['lean', '--version']),
        'lake': _probe_command(['lake', '--version']),
        'latexmk': _probe_command(['latexmk', '-v']),
        'pdflatex': _probe_command(['pdflatex', '--version']),
        'bibtex': _probe_command(['bibtex', '--version']),
    }
    tools['platform'] = {
        'system': platform.system(),
        'release': platform.release(),
        'machine': platform.machine(),
    }
    return tools


def run_step(name: str, cmd: str, cwd: str | None = None, env: dict[str, str] | None = None, allow_missing: bool = False) -> dict[str, Any]:
    started = utc_now_iso()
    t0 = time.time()
    status = 'passed'

    first_token = None
    try:
        parts = shlex.split(cmd)
        if parts:
            first_token = parts[0]
    except Exception:
        first_token = None

    if allow_missing and first_token and shutil.which(first_token) is None:
        finished = utc_now_iso()
        return {
            'name': name,
            'command': cmd,
            'cwd': cwd or '.',
            'returncode': None,
            'status': 'skipped',
            'started_at_utc': started,
            'finished_at_utc': finished,
            'duration_seconds': round(time.time() - t0, 6),
            'stdout': '',
            'stderr': f'optional tool unavailable: {first_token}',
        }

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    proc = subprocess.run(cmd, shell=True, cwd=cwd, env=merged_env, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        if allow_missing and ('not found' in (proc.stderr or '').lower() or 'command not found' in (proc.stderr or '').lower()):
            status = 'skipped'
        else:
            status = 'failed'

    finished = utc_now_iso()
    return {
        'name': name,
        'command': cmd,
        'cwd': cwd or '.',
        'returncode': proc.returncode,
        'status': status,
        'started_at_utc': started,
        'finished_at_utc': finished,
        'duration_seconds': round(time.time() - t0, 6),
        'stdout': proc.stdout or '',
        'stderr': proc.stderr or '',
    }


def _collect_files(root: Path, exts: set[str]) -> set[str]:
    out: set[str] = set()
    if not root.exists():
        return out
    for path in root.rglob('*'):
        if path.is_file() and path.suffix in exts:
            rel = path.relative_to(ROOT).as_posix()
            if '/r12_' in rel or '/r13_' in rel or '/r15_' in rel:
                continue
            out.add(rel)
    return out


def collect_hashed_paths(repo_root: str = '.') -> tuple[str, ...]:
    root = Path(repo_root).resolve()
    paths: set[str] = set()
    fixed = [
        'Makefile',
        '.package-repo-snapshot.json',
        'docs/project/commands.md',
        'src/sixbirds_nogo/repro.py',
        'docs/project/theorem_statement_sheet.yaml',
        'docs/project/notation_registry.yaml',
        'docs/project/math_paper_validation_rules.yaml',
        'docs/project/revision_queue_r14.yaml',
        'docs/project/revision_queue_r15.yaml',
        'docs/project/theorem_atlas.yaml',
        'docs/project/theorem_evidence_map.yaml',
        'docs/project/claim_audit_freeze.yaml',
        'docs/project/paper_section_contracts.yaml',
        'docs/project/paper_asset_freeze.yaml',
        'paper/main.tex',
        'paper/macros.tex',
        'paper/refs.bib',
        'paper/build/main.pdf',
        'paper/supplement/main.tex',
        'paper/supplement/build/supplement.pdf',
        'scripts/run_t19_repro_pipeline.py',
        'scripts/run_r12_bibliography_citations.py',
        'scripts/run_r16_citation_enrichment.py',
        'scripts/run_r13_math_paper_validator.py',
        'scripts/run_r14_math_paper_red_team_review.py',
        'scripts/run_r15_finalize_and_bundle.py',
        'tests/test_r12_bibliography_citations.py',
        'tests/test_r16_citation_enrichment.py',
        'tests/test_r13_math_paper_validator.py',
        'tests/test_r14_math_paper_red_team_review.py',
        'tests/test_r15_finalize_and_bundle.py',
        'tests/test_repro_pipeline.py',
    ]
    for rel in fixed:
        if (root / rel).exists():
            paths.add(rel)

    paths |= _collect_files(root / 'paper', {'.tex', '.bib'})
    paths |= _collect_files(root / 'docs' / 'research-log', {'.md'})
    paths |= _collect_files(root / 'results', {'.json', '.pdf', '.log', '.bbl', '.blg', '.txt', '.zip', '.tex'})
    return tuple(sorted(paths))


def run_repro_pipeline(manifest_dir: str = 'results/manifest', precision: int = 80, skip_pytest: bool = False, skip_lean: bool = False) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    steps.append(run_step('validate_configs', 'python3 scripts/validate_configs.py'))
    steps.append(run_step('validate_witnesses', 'python3 scripts/validate_witnesses.py'))
    steps.append(run_step('package_import_smoke', "PYTHONPATH=src python3 -c \"import sixbirds_nogo; print(sixbirds_nogo.__version__, sixbirds_nogo.version)\""))
    if not skip_pytest:
        steps.append(run_step('pytest', 'pytest -q'))

    steps.append(run_step('run_t11_definability_suite', 'python3 scripts/run_t11_definability_suite.py'))
    steps.append(run_step('run_t12_witness_manifest', 'python3 scripts/run_t12_witness_manifest.py'))
    steps.append(run_step('run_t13_master_witness_suite', 'python3 scripts/run_t13_master_witness_suite.py'))
    steps.append(run_step('run_t14_primitive_matrix', 'python3 scripts/run_t14_primitive_matrix.py'))
    steps.append(run_step('run_t15_robustness_suite', 'python3 scripts/run_t15_robustness_suite.py'))

    steps.append(run_step('run_t20_readiness_checkpoint', 'python3 scripts/run_t20_readiness_checkpoint.py'))
    steps.append(run_step('run_t21_theorem_atlas', 'python3 scripts/run_t21_theorem_atlas.py'))
    steps.append(run_step('run_t22_dpi_protocol_pack', 'python3 scripts/run_t22_dpi_protocol_pack.py'))
    steps.append(run_step('run_t23_graph_affinity_pack', 'python3 scripts/run_t23_graph_affinity_pack.py'))
    steps.append(run_step('run_t24_closure_pack', 'python3 scripts/run_t24_closure_pack.py'))
    steps.append(run_step('run_t25_objecthood_pack', 'python3 scripts/run_t25_objecthood_pack.py'))
    steps.append(run_step('run_t26_bounded_interface_pack', 'python3 scripts/run_t26_bounded_interface_pack.py'))
    steps.append(run_step('run_t27_lean_graph_bridge', 'python3 scripts/run_t27_lean_graph_bridge.py', allow_missing=skip_lean))
    steps.append(run_step('run_t28_lean_finite_lens_count', 'python3 scripts/run_t28_lean_finite_lens_count.py', allow_missing=skip_lean))
    steps.append(run_step('run_t29_lean_bounded_interface_corollary', 'python3 scripts/run_t29_lean_bounded_interface_corollary.py', allow_missing=skip_lean))
    steps.append(run_step('run_t30_lean_objecthood_uniqueness', 'python3 scripts/run_t30_lean_objecthood_uniqueness.py', allow_missing=skip_lean))
    steps.append(run_step('run_t35_scope_charter', 'python3 scripts/run_t35_scope_charter.py'))
    steps.append(run_step('run_t36_lean_probability_core', 'python3 scripts/run_t36_lean_probability_core.py', allow_missing=skip_lean))
    steps.append(run_step('run_t37_lean_kl_dpi_core', 'python3 scripts/run_t37_lean_kl_dpi_core.py', allow_missing=skip_lean))
    steps.append(run_step('run_t38_lean_arrow_dpi', 'python3 scripts/run_t38_lean_arrow_dpi.py', allow_missing=skip_lean))
    steps.append(run_step('run_t39_lean_protocol_trap', 'python3 scripts/run_t39_lean_protocol_trap.py', allow_missing=skip_lean))
    steps.append(run_step('run_t40_closure_feasibility', 'python3 scripts/run_t40_closure_feasibility.py'))
    steps.append(run_step('run_t41_lean_closure_variational_core', 'python3 scripts/run_t41_lean_closure_variational_core.py', allow_missing=skip_lean))
    steps.append(run_step('run_t42_lean_closure_direct_pack', 'python3 scripts/run_t42_lean_closure_direct_pack.py', allow_missing=skip_lean))
    steps.append(run_step('run_t43_objecthood_tv_feasibility', 'python3 scripts/run_t43_objecthood_tv_feasibility.py'))
    steps.append(run_step('run_t44_lean_objecthood_direct_pack', 'python3 scripts/run_t44_lean_objecthood_direct_pack.py', allow_missing=skip_lean))

    steps.append(run_step('run_r12_bibliography_citations', 'python3 scripts/run_r12_bibliography_citations.py'))
    steps.append(run_step('run_r16_citation_enrichment', 'python3 scripts/run_r16_citation_enrichment.py'))
    steps.append(run_step('run_r13_math_paper_validator', 'python3 scripts/run_r13_math_paper_validator.py'))
    steps.append(run_step('run_r14_math_paper_red_team_review', 'python3 scripts/run_r14_math_paper_red_team_review.py'))
    steps.append(run_step('run_r15_finalize_and_bundle', 'python3 scripts/run_r15_finalize_and_bundle.py'))

    status = 'success' if all(step['status'] in {'passed', 'skipped'} for step in steps) else 'failed'

    manifest_path = Path(manifest_dir)
    manifest_path.mkdir(parents=True, exist_ok=True)
    hashes = {rel: sha256_file(ROOT / rel) for rel in collect_hashed_paths(ROOT)}
    manifest = {
        'generated_at_utc': utc_now_iso(),
        'canonical_command': 'make reproduce',
        'status': status,
        'precision': precision,
        'skip_pytest': skip_pytest,
        'skip_lean': skip_lean,
        'seeds': {'pythonhashseed': os.environ.get('PYTHONHASHSEED', 'not-set')},
        'tool_versions': probe_tool_versions(),
        'steps': steps,
        'file_hashes': hashes,
    }
    (manifest_path / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest
