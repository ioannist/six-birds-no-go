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

ROOT = Path(__file__).resolve().parents[1]
MAIN_ROOT = ROOT / 'paper'
SUPP_ROOT = MAIN_ROOT / 'supplement'
R12_RUNNER = ROOT / 'scripts' / 'run_r12_bibliography_citations.py'
SUMMARY_PATH = ROOT / 'results' / 'R16' / 'citation_enrichment_summary.json'
OUTPUT_ARTIFACTS = ['main.pdf', 'main.log', 'main.aux', 'main.bbl', 'main.blg', 'main.out']
PLACEHOLDER_PATTERNS = ('TODO', 'TBD', 'FIXME', 'XXX', 'CITE', 'PLACEHOLDER')
TARGET_FILES = [
    ROOT / 'paper' / 'sections' / '02_setup.tex',
    ROOT / 'paper' / 'sections' / '04_arrow_and_protocol.tex',
    ROOT / 'paper' / 'sections' / '05_graph_and_affinity.tex',
    ROOT / 'paper' / 'sections' / '06_closure.tex',
    ROOT / 'paper' / 'sections' / '07_objecthood.tex',
]
REQUIRED_KEYS = [
    'MaesNetocny2003',
    'Seifert2012',
    'Esposito2012',
    'Schnakenberg1976',
    'Lim2020Hodge',
    'KemenySnell1960',
    'Buchholz1994',
    'Csiszar1975',
    'Dobrushin1956',
    'Seneta2006',
    'Kelly1979',
    'FosterEtAl2007',
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def fail(message: str) -> None:
    raise ValueError(message)


def bib_keys(path: Path) -> set[str]:
    text = path.read_text(encoding='utf-8')
    return set(re.findall(r'@\w+\{\s*([^,\s]+)\s*,', text))


def extract_citations(text: str) -> list[str]:
    keys: list[str] = []
    for match in re.finditer(r'\\cite[a-zA-Z*]*\{([^}]*)\}', text):
        for item in match.group(1).split(','):
            key = item.strip()
            if key:
                keys.append(key)
    return keys


def build_tree(src_root: Path, out_dir: Path, artifact_prefix: str) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    command = ['latexmk', '-pdf', '-bibtex', '-interaction=nonstopmode', '-halt-on-error', 'main.tex']
    with tempfile.TemporaryDirectory(prefix=f'r16_{artifact_prefix}_') as tmpdir:
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
            fail(f'{artifact_prefix} pdf missing after build')
        return pdf_path.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description='Run R16 citation enrichment validation')
    parser.add_argument('--output-dir', default='results/R16')
    args = parser.parse_args()

    out_root = ROOT / args.output_dir
    build_dir = out_root / 'latex_build'
    out_root.mkdir(parents=True, exist_ok=True)

    try:
        proc = subprocess.run([sys.executable, str(R12_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            fail('R12 runner failed before R16\nstdout:\n' + proc.stdout + '\n\nstderr:\n' + proc.stderr)

        refs_path = MAIN_ROOT / 'refs.bib'
        available_keys = bib_keys(refs_path)
        missing_required_entries = [key for key in REQUIRED_KEYS if key not in available_keys]
        if missing_required_entries:
            fail('refs.bib missing required entries: ' + ', '.join(missing_required_entries))

        lens_in_main = False
        main_citations_present: dict[str, bool] = {}
        cited_in_targets: set[str] = set()
        for path in TARGET_FILES:
            text = path.read_text(encoding='utf-8')
            if 'lens' in text:
                lens_in_main = True
            cited = set(extract_citations(text))
            cited_in_targets |= cited

        included_keys = REQUIRED_KEYS.copy()
        if not lens_in_main and 'FosterEtAl2007' in included_keys:
            included_keys.remove('FosterEtAl2007')

        for key in included_keys:
            main_citations_present[key] = key in cited_in_targets

        main_tex = [MAIN_ROOT / 'main.tex', *sorted((MAIN_ROOT / 'sections').glob('*.tex')), *sorted((MAIN_ROOT / 'appendices').glob('*.tex'))]
        supp_tex = [SUPP_ROOT / 'main.tex', *sorted((SUPP_ROOT / 'sections').glob('*.tex'))]
        all_cited = set()
        for path in main_tex + supp_tex:
            if path.exists():
                all_cited.update(extract_citations(path.read_text(encoding='utf-8')))

        missing_bib_keys = sorted(key for key in all_cited if key not in available_keys)
        placeholder_keys = sorted(key for key in all_cited if any(token in key.upper() for token in PLACEHOLDER_PATTERNS))

        main_pdf_bytes = build_tree(MAIN_ROOT, build_dir, 'main')
        supp_pdf_bytes = build_tree(SUPP_ROOT, build_dir, 'supplement')

        summary = {
            'generated_at_utc': now_iso(),
            'added_bib_keys': included_keys,
            'main_citations_present': main_citations_present,
            'main_build_ok': True,
            'supp_build_ok': True,
            'missing_bib_keys': missing_bib_keys,
            'placeholder_citation_keys': placeholder_keys,
            'main_pdf_bytes': main_pdf_bytes,
            'supplement_pdf_bytes': supp_pdf_bytes,
            'status': 'success',
        }

        failures: list[str] = []
        if missing_bib_keys:
            failures.append('missing bibliography keys')
        if placeholder_keys:
            failures.append('placeholder citation keys present')
        uncited = sorted(key for key, present in main_citations_present.items() if not present)
        if uncited:
            failures.append('required citation keys not used in main paper: ' + ', '.join(uncited))

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
            'added_bib_keys': [],
            'main_citations_present': {},
            'main_build_ok': False,
            'supp_build_ok': False,
            'missing_bib_keys': [],
            'placeholder_citation_keys': [],
            'status': 'failed',
            'error': str(exc),
        }
        SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
