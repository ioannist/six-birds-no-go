#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

MAIN_ROOT = Path('paper')
SUPP_ROOT = MAIN_ROOT / 'supplement'
SUMMARY_PATH = Path('results/R12/bibliography_citations_summary.json')
OUTPUT_ARTIFACTS = ['main.pdf', 'main.log', 'main.aux', 'main.bbl', 'main.blg', 'main.out']
PLACEHOLDER_PATTERNS = ('TODO', 'TBD', 'FIXME', 'XXX', 'CITE', 'PLACEHOLDER')
ALLOWED_SB_FILES = {
    'paper/sections/01_introduction.tex',
    'paper/sections/09_discussion.tex',
}
REQUIRED_STANDARD_KEYS = {
    'CoverThomas2006',
    'KullbackLeibler1951',
    'Norris1997',
    'LevinPeresWilmer2017',
    'Diestel2017',
    'Biggs1993',
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def fail(message: str) -> None:
    raise ValueError(message)


def gather_tex_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in [root / 'main.tex', *sorted(root.rglob('*.tex'))]:
        if 'build' in path.parts:
            continue
        if path.exists() and path not in out:
            out.append(path)
    return out


def extract_citations(text: str) -> list[str]:
    keys: list[str] = []
    for match in re.finditer(r'\\cite[a-zA-Z*]*\{([^}]*)\}', text):
        for item in match.group(1).split(','):
            key = item.strip()
            if key:
                keys.append(key)
    return keys


def bib_keys(path: Path) -> set[str]:
    text = path.read_text(encoding='utf-8')
    return set(re.findall(r'@\w+\{\s*([^,\s]+)\s*,', text))


def build_tree(src_root: Path, out_dir: Path, artifact_prefix: str) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    command = ['latexmk', '-pdf', '-bibtex', '-interaction=nonstopmode', '-halt-on-error', 'main.tex']
    with tempfile.TemporaryDirectory(prefix=f'r12_{artifact_prefix}_') as tmpdir:
        work_root = Path(tmpdir) / src_root.name
        shutil.copytree(src_root, work_root)
        proc = subprocess.run(command, cwd=work_root, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            fail(f'{artifact_prefix} build failed\nstdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}')
        for name in OUTPUT_ARTIFACTS:
            src = work_root / name
            if src.exists():
                if artifact_prefix == 'supplement':
                    dst_name = 'supplement.pdf' if name == 'main.pdf' else f'supplement{src.suffix}'
                else:
                    dst_name = name
                shutil.copy2(src, out_dir / dst_name)
        pdf_name = 'supplement.pdf' if artifact_prefix == 'supplement' else 'main.pdf'
        pdf_path = out_dir / pdf_name
        if not pdf_path.exists():
            src_pdf = work_root / 'main.pdf'
            if src_pdf.exists():
                shutil.copy2(src_pdf, pdf_path)
        if not pdf_path.exists():
            fail(f'{artifact_prefix} pdf missing after build')
        return pdf_path.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description='Run R12 bibliography/citation validation')
    parser.add_argument('--output-dir', default='results/R12')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    build_dir = output_dir / 'latex_build'
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        required = [MAIN_ROOT / 'main.tex', MAIN_ROOT / 'refs.bib', SUPP_ROOT / 'main.tex']
        missing_required = [path.as_posix() for path in required if not path.exists()]
        if missing_required:
            fail('baseline missing required files: ' + ', '.join(missing_required))

        main_tex_files = gather_tex_files(MAIN_ROOT)
        supp_tex_files = gather_tex_files(SUPP_ROOT)
        refs_path = MAIN_ROOT / 'refs.bib'
        available_keys = bib_keys(refs_path)

        main_citation_map: dict[str, list[str]] = {}
        cited_keys: list[str] = []
        for path in main_tex_files:
            if SUPP_ROOT in path.parents or path == SUPP_ROOT / 'main.tex':
                continue
            rel = path.as_posix()
            keys = extract_citations(path.read_text(encoding='utf-8'))
            main_citation_map[rel] = keys
            cited_keys.extend(keys)

        supp_cited_keys: list[str] = []
        for path in supp_tex_files:
            supp_cited_keys.extend(extract_citations(path.read_text(encoding='utf-8')))

        missing_bib_keys = sorted({key for key in cited_keys + supp_cited_keys if key not in available_keys})
        placeholder_keys = sorted({key for key in cited_keys + supp_cited_keys if any(token in key.upper() for token in PLACEHOLDER_PATTERNS)})

        sb_citations_outside_allowed = sorted(
            rel for rel, keys in main_citation_map.items() if any(key.startswith('SB_') for key in keys) and rel not in ALLOWED_SB_FILES
        )
        non_sb_cited = {key for key in cited_keys if not key.startswith('SB_')}
        required_standard_keys_cited = sorted(REQUIRED_STANDARD_KEYS & non_sb_cited)

        main_pdf_bytes = build_tree(MAIN_ROOT, build_dir, 'main')
        supp_pdf_bytes = build_tree(SUPP_ROOT, build_dir, 'supplement')

        summary = {
            'generated_at_utc': now_iso(),
            'main_build_ok': True,
            'supp_build_ok': True,
            'missing_bib_keys': missing_bib_keys,
            'placeholder_citation_keys': placeholder_keys,
            'sb_citations_outside_allowed': sb_citations_outside_allowed,
            'main_non_sb_citation_key_count': len(non_sb_cited),
            'required_standard_keys_cited': required_standard_keys_cited,
            'main_pdf_bytes': main_pdf_bytes,
            'supplement_pdf_bytes': supp_pdf_bytes,
            'status': 'success',
        }

        failures = []
        if missing_bib_keys:
            failures.append('missing bibliography keys')
        if placeholder_keys:
            failures.append('placeholder citation keys present')
        if sb_citations_outside_allowed:
            failures.append('Six Birds citations outside allowed background sections')
        if len(non_sb_cited) < 4:
            failures.append('fewer than four non-SB citation keys are cited in main paper')
        if not {'CoverThomas2006', 'KullbackLeibler1951'} <= set(required_standard_keys_cited):
            failures.append('required information-theory references are not cited in main paper')
        if not ({'LevinPeresWilmer2017', 'Norris1997'} & set(required_standard_keys_cited)):
            failures.append('no standard Markov-chain reference cited in main paper')
        if not ({'Diestel2017', 'Biggs1993'} & set(required_standard_keys_cited)):
            failures.append('no standard graph-theory reference cited in main paper')

        if failures:
            summary['status'] = 'failed'
            summary['failures'] = failures
            SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
            SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
            fail('; '.join(failures))

        SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        return 0
    except Exception as exc:
        summary = {
            'generated_at_utc': now_iso(),
            'main_build_ok': False,
            'supp_build_ok': False,
            'missing_bib_keys': [],
            'placeholder_citation_keys': [],
            'sb_citations_outside_allowed': [],
            'main_non_sb_citation_key_count': 0,
            'required_standard_keys_cited': [],
            'status': 'failed',
            'error': str(exc),
        }
        SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
