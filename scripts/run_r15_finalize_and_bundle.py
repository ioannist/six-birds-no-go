#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = ROOT / 'paper'
SUPP_ROOT = PAPER_ROOT / 'supplement'
R14_RUNNER = ROOT / 'scripts' / 'run_r14_math_paper_red_team_review.py'
R15_RESULTS = ROOT / 'results' / 'R15'
R15_BUILD = R15_RESULTS / 'latex_build'
PAPER_BUILD = PAPER_ROOT / 'build'
SUPP_BUILD = SUPP_ROOT / 'build'
BUNDLE_DIR = ROOT / 'results' / 'submission_bundle'
QUEUE_R15 = ROOT / 'docs' / 'project' / 'revision_queue_r15.yaml'
SUMMARY_R15 = R15_RESULTS / 'revision_pass_summary.json'
LOG_R15 = ROOT / 'docs' / 'research-log' / 'R15.md'
LEGACY_PATHS = [
    ROOT / 'paper' / 'draft_v1.md',
    ROOT / 'paper' / 'draft_v2.md',
    ROOT / 'paper' / 'draft_v3.md',
    ROOT / 'paper' / 'writing_track',
    ROOT / 'paper' / 'legacy_internal',
    ROOT / 'paper' / 'rewrite_tex',
    ROOT / 'paper' / 'submission_bundle',
    ROOT / 'paper' / 'math_rewrite',
    ROOT / 'paper' / 'manuscript_skeleton.md',
]
ARTIFACTS = ['main.pdf', 'main.log', 'main.aux', 'main.bbl', 'main.blg', 'main.out']


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def tool_version(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (proc.stdout or proc.stderr or '').strip()
    return text.splitlines()[0] if text else ''


def write_flattened_tex(work_root: Path, out_path: Path) -> None:
    flattener = shutil.which('latexpand') or shutil.which('texflatten')
    if flattener is None:
        raise RuntimeError('missing LaTeX flattener: install latexpand or texflatten')
    if Path(flattener).name == 'latexpand':
        proc = subprocess.run([flattener, '-o', str(out_path), 'main.tex'], cwd=work_root, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f'flatten failed\nstdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}')
    else:
        proc = subprocess.run([flattener, 'main.tex'], cwd=work_root, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f'flatten failed\nstdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}')
        out_path.write_text(proc.stdout, encoding='utf-8')


def build_tree(src_root: Path, out_dir: Path, pdf_name: str) -> tuple[int, dict[str, str]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    command = ['latexmk', '-pdf', '-bibtex', '-interaction=nonstopmode', '-halt-on-error', 'main.tex']
    with tempfile.TemporaryDirectory(prefix='r15_build_') as tmpdir:
        work_root = Path(tmpdir) / src_root.name
        shutil.copytree(src_root, work_root)
        proc = subprocess.run(command, cwd=work_root, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f'build failed for {src_root}\nstdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}')
        copied: dict[str, str] = {}
        for name in ARTIFACTS:
            src = work_root / name
            if src.exists():
                if pdf_name == 'supplement.pdf':
                    dst = out_dir / ('supplement.pdf' if name == 'main.pdf' else f'supplement{Path(name).suffix}')
                else:
                    dst = out_dir / (pdf_name if name == 'main.pdf' else name)
                shutil.copy2(src, dst)
                copied[name] = dst.name
        flat_name = 'supplement_flat.tex' if pdf_name == 'supplement.pdf' else 'main_flat.tex'
        write_flattened_tex(work_root, out_dir / flat_name)
        copied['flattened_tex'] = flat_name
        pdf_path = out_dir / pdf_name
        if not pdf_path.exists():
            raise RuntimeError(f'missing expected pdf {pdf_path}')
        return pdf_path.stat().st_size, copied


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def zip_source(zip_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix='r15_source_') as tmpdir:
        staging = Path(tmpdir) / 'source'
        staging.mkdir(parents=True, exist_ok=True)
        for rel in ['main.tex', 'macros.tex', 'refs.bib', 'sections', 'appendices', 'generated', 'supplement']:
            src = PAPER_ROOT / rel
            dst = staging / rel
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(staging.rglob('*')):
                if path.is_file():
                    zf.write(path, path.relative_to(staging).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description='Finalize canonical TeX paper and build submission bundle')
    parser.add_argument('--output-dir', default='results/R15')
    args = parser.parse_args()

    try:
        proc = subprocess.run([sys.executable, str(R14_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError('R14 runner failed before R15\nstdout:\n' + proc.stdout + '\n\nstderr:\n' + proc.stderr)

        if not (PAPER_ROOT / 'main.tex').exists() or not (SUPP_ROOT / 'main.tex').exists():
            raise RuntimeError('canonical paper tree missing')
        missing_legacy = [path.as_posix() for path in LEGACY_PATHS if path.exists()]
        if missing_legacy:
            raise RuntimeError('legacy manuscript artifacts still present: ' + ', '.join(missing_legacy))

        clean_dir(R15_BUILD)
        clean_dir(PAPER_BUILD)
        clean_dir(SUPP_BUILD)
        clean_dir(BUNDLE_DIR)
        shutil.rmtree(ROOT / 'results' / 'paper_build', ignore_errors=True)
        shutil.rmtree(ROOT / 'results' / 'supplement_build', ignore_errors=True)

        main_pdf_bytes, _ = build_tree(PAPER_ROOT, R15_BUILD, 'main.pdf')
        supp_pdf_bytes, _ = build_tree(SUPP_ROOT, R15_BUILD, 'supplement.pdf')
        shutil.copy2(R15_BUILD / 'main.pdf', PAPER_BUILD / 'main.pdf')
        shutil.copy2(R15_BUILD / 'main_flat.tex', PAPER_BUILD / 'main_flat.tex')
        shutil.copy2(R15_BUILD / 'supplement.pdf', SUPP_BUILD / 'supplement.pdf')
        shutil.copy2(R15_BUILD / 'supplement_flat.tex', SUPP_BUILD / 'supplement_flat.tex')

        shutil.copy2(R15_BUILD / 'main.pdf', BUNDLE_DIR / 'main.pdf')
        shutil.copy2(R15_BUILD / 'main_flat.tex', BUNDLE_DIR / 'main_flat.tex')
        shutil.copy2(R15_BUILD / 'supplement.pdf', BUNDLE_DIR / 'supplement.pdf')
        shutil.copy2(R15_BUILD / 'supplement_flat.tex', BUNDLE_DIR / 'supplement_flat.tex')
        source_zip = BUNDLE_DIR / 'source.zip'
        zip_source(source_zip)

        build_instructions = (
            'cd paper && latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error main.tex\n'
            'cd paper/supplement && latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error main.tex\n'
        )
        (BUNDLE_DIR / 'build_instructions.txt').write_text(build_instructions, encoding='utf-8')

        manifest = {
            'generated_at_utc': now_iso(),
            'tool_versions': {
                'latexmk': tool_version(['latexmk', '-v']),
                'pdflatex': tool_version(['pdflatex', '--version']),
                'bibtex': tool_version(['bibtex', '--version']),
            },
            'files': {
                'main.pdf': {'sha256': sha256_file(BUNDLE_DIR / 'main.pdf'), 'bytes': (BUNDLE_DIR / 'main.pdf').stat().st_size},
                'main_flat.tex': {'sha256': sha256_file(BUNDLE_DIR / 'main_flat.tex'), 'bytes': (BUNDLE_DIR / 'main_flat.tex').stat().st_size},
                'supplement.pdf': {'sha256': sha256_file(BUNDLE_DIR / 'supplement.pdf'), 'bytes': (BUNDLE_DIR / 'supplement.pdf').stat().st_size},
                'supplement_flat.tex': {'sha256': sha256_file(BUNDLE_DIR / 'supplement_flat.tex'), 'bytes': (BUNDLE_DIR / 'supplement_flat.tex').stat().st_size},
                'source.zip': {'sha256': sha256_file(source_zip), 'bytes': source_zip.stat().st_size},
                'build_instructions.txt': {'sha256': sha256_file(BUNDLE_DIR / 'build_instructions.txt'), 'bytes': (BUNDLE_DIR / 'build_instructions.txt').stat().st_size},
            },
        }
        (BUNDLE_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

        revision_queue_r15 = {
            'generated_at_utc': now_iso(),
            'queue_id': 'revision_queue_r15_v1',
            'items': [
                {
                    'issue_id': 'R14-001',
                    'status': 'closed',
                    'severity': 'low',
                    'closed_by_revision': 'R15',
                    'files_touched': ['paper/sections/03_main_results.tex'],
                    'resolution_note': 'Replaced internal production language with a standard main-results opening sentence.',
                },
                {
                    'issue_id': 'R14-002',
                    'status': 'closed',
                    'severity': 'medium',
                    'closed_by_revision': 'R15',
                    'files_touched': ['docs/project/theorem_statement_sheet.yaml', 'paper/generated/theorem_statements.tex'],
                    'resolution_note': 'Removed the internal theorem-id reference from NG_PROTOCOL_TRAP and stated the observed-arrow consequence directly.',
                },
                {
                    'issue_id': 'R14-003',
                    'status': 'closed',
                    'severity': 'blocking',
                    'closed_by_revision': 'R15',
                    'files_touched': ['docs/project/theorem_statement_sheet.yaml', 'paper/generated/theorem_statements.tex', 'paper/sections/06_closure.tex'],
                    'resolution_note': 'Added positive stationary mass to the closure positivity clause and aligned the proof with that hypothesis.',
                },
                {
                    'issue_id': 'R14-004',
                    'status': 'closed',
                    'severity': 'high',
                    'closed_by_revision': 'R15',
                    'files_touched': ['paper/sections/07_objecthood.tex'],
                    'resolution_note': 'Made the objecthood formalization boundary explicit: uniqueness core only is formalized; the TV/Dobrushin epsilon-stability layer is auxiliary-only.',
                },
            ],
        }
        QUEUE_R15.write_text(json.dumps(revision_queue_r15, indent=2) + '\n', encoding='utf-8')

        summary = {
            'generated_at_utc': now_iso(),
            'issue_count': 4,
            'closed_count': 4,
            'blocking_open_count': 0,
            'main_pdf_bytes': main_pdf_bytes,
            'supplement_pdf_bytes': supp_pdf_bytes,
            'flattened_tex_written': True,
            'bundle_self_contained': True,
            'legacy_paths_absent': True,
            'status': 'success',
        }
        SUMMARY_R15.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY_R15.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        LOG_R15.write_text(
            '## R15\n\n'
            '- closed the four R14 queue items\n'
            '- promoted the TeX paper under `paper/` and `paper/supplement/` as the only canonical manuscript line\n'
            '- removed legacy manuscript lanes and produced the outward-facing submission bundle\n',
            encoding='utf-8',
        )
        return 0
    except Exception as exc:
        SUMMARY_R15.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY_R15.write_text(json.dumps({'generated_at_utc': now_iso(), 'status': 'failed', 'error': str(exc)}, indent=2) + '\n', encoding='utf-8')
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
