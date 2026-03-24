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
from typing import Any

R12_RUNNER = Path('scripts/run_r16_citation_enrichment.py')
RULES_PATH = Path('docs/project/math_paper_validation_rules.yaml')
SHEET_PATH = Path('docs/project/theorem_statement_sheet.yaml')
NOTATION_PATH = Path('docs/project/notation_registry.yaml')
MAIN_ROOT = Path('paper')
SUPP_ROOT = MAIN_ROOT / 'supplement'
MAIN_RESULTS = MAIN_ROOT / 'sections' / '03_main_results.tex'
MACROS_PATH = MAIN_ROOT / 'macros.tex'
SETUP_PATH = MAIN_ROOT / 'sections' / '02_setup.tex'
GENERATED_STATEMENTS = MAIN_ROOT / 'generated' / 'theorem_statements.tex'
SUMMARY_PATH = Path('results/R13/math_paper_validator_summary.json')
OUTPUT_ARTIFACTS = ['main.pdf', 'main.log', 'main.aux', 'main.bbl', 'main.blg', 'main.out']


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def normalize(text: str) -> str:
    return re.sub(r'\s+', '', text)


def build_tree(src_root: Path, out_dir: Path, artifact_prefix: str) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    command = ['latexmk', '-pdf', '-bibtex', '-interaction=nonstopmode', '-halt-on-error', 'main.tex']
    with tempfile.TemporaryDirectory(prefix=f'r13_{artifact_prefix}_') as tmpdir:
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
        pdf_path = out_dir / ('supplement.pdf' if artifact_prefix == 'supplement' else 'main.pdf')
        if not pdf_path.exists():
            fail(f'missing {artifact_prefix} pdf after build')
        return pdf_path.stat().st_size


def theorem_labels_and_envs(text: str) -> tuple[int, list[str], bool]:
    env_pattern = re.compile(r'\\begin\{theorem\}(.*?)\\end\{theorem\}', re.DOTALL)
    theorem_count = 0
    labels: list[str] = []
    for body in env_pattern.findall(text):
        theorem_count += 1
        labels.extend(re.findall(r'\\label\{([^}]+)\}', body))
    theorem_star_present = '\\begin{theorem*}' in text
    return theorem_count, labels, theorem_star_present


def aux_numbering(aux_text: str, labels: list[str]) -> list[str]:
    missing: list[str] = []
    for label in labels:
        match = re.search(r'\\newlabel\{' + re.escape(label) + r'\}\{\{([^}]*)\}', aux_text)
        if match is None:
            missing.append(label)
            continue
        token = match.group(1).strip()
        if not token or token == '??':
            missing.append(label)
    return missing


def proof_coverage(labels: list[str]) -> dict[str, list[str]]:
    search_files = sorted((MAIN_ROOT / 'sections').glob('[0-9][4-9]_*.tex'))
    search_files.extend(sorted((MAIN_ROOT / 'appendices').glob('*.tex')))
    coverage: dict[str, list[str]] = {label: [] for label in labels}
    proof_pattern = re.compile(r'\\begin\{proof\}(?:\[(.*?)\])?(.*?)\\end\{proof\}', re.DOTALL)
    for path in search_files:
        text = path.read_text(encoding='utf-8')
        for title, body in proof_pattern.findall(text):
            haystack = (title or '') + '\n' + (body or '')
            for label in labels:
                if re.search(r'\\(?:Cref|cref|ref)\{' + re.escape(label) + r'\}', haystack):
                    coverage[label].append(path.as_posix())
    return {label: sorted(set(paths)) for label, paths in coverage.items()}


def symbol_candidates(symbol: str) -> list[str]:
    candidates = {normalize(symbol)}
    for cmd in re.findall(r'\\[A-Za-z]+', symbol):
        candidates.add(normalize(cmd))
    bare = re.sub(r'\\[A-Za-z]+', '', symbol)
    bare = normalize(bare)
    if bare:
        candidates.add(bare)
    return [candidate for candidate in candidates if candidate]


def notation_check(sheet: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, str]]:
    registry_rows = registry['notation']
    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in registry_rows:
        by_id.setdefault(row['notation_id'], []).append(row)

    search_space = normalize(MACROS_PATH.read_text(encoding='utf-8') + '\n' + SETUP_PATH.read_text(encoding='utf-8'))
    missing: list[dict[str, str]] = []
    for theorem in sheet['theorems']:
        for notation_id in theorem['required_notation']:
            rows = by_id.get(notation_id, [])
            if len(rows) != 1:
                missing.append({'theorem_id': theorem['theorem_id'], 'notation_id': notation_id, 'symbol_latex': '<missing-or-duplicate-registry-entry>'})
                continue
            symbol = rows[0]['symbol_latex']
            if not any(candidate in search_space for candidate in symbol_candidates(symbol)):
                missing.append({'theorem_id': theorem['theorem_id'], 'notation_id': notation_id, 'symbol_latex': symbol})
    return missing


def scan_hits(paths: list[Path], patterns: list[str], ignore_case: bool = True) -> list[dict[str, Any]]:
    flags = re.IGNORECASE if ignore_case else 0
    compiled = [(pattern, re.compile(pattern, flags)) for pattern in patterns]
    hits: list[dict[str, Any]] = []
    for path in paths:
        for idx, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
            for pattern, regex in compiled:
                if regex.search(line):
                    hits.append({'file': path.as_posix(), 'line': idx, 'pattern': pattern, 'excerpt': line.strip()})
    return hits


def theorem_statement_hits(sheet: dict[str, Any], generated_text: str, patterns: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    compiled = [(pattern, re.compile(pattern, re.IGNORECASE)) for pattern in patterns]
    for theorem in sheet['theorems']:
        stmt = theorem['formal_statement_latex']
        for pattern, regex in compiled:
            if regex.search(stmt):
                hits.append({'source': f"theorem_statement_sheet:{theorem['theorem_id']}", 'pattern': pattern})
    for idx, line in enumerate(generated_text.splitlines(), start=1):
        for pattern, regex in compiled:
            if regex.search(line):
                hits.append({'source': f'generated_theorem_statements:{idx}', 'pattern': pattern})
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description='Run R13 math-paper validator')
    parser.add_argument('--output-dir', default='results/R13')
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    build_dir = output_dir / 'latex_build'
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        required = [MAIN_ROOT / 'main.tex', MAIN_RESULTS, SHEET_PATH, NOTATION_PATH, R12_RUNNER]
        missing_required = [path.as_posix() for path in required if not path.exists()]
        if missing_required:
            fail('baseline missing required files: ' + ', '.join(missing_required))

        proc = subprocess.run([sys.executable, str(R12_RUNNER)], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            fail('R12 runner failed before R13\nstdout:\n' + proc.stdout + '\n\nstderr:\n' + proc.stderr)

        rules = load_json(RULES_PATH)
        sheet = load_json(SHEET_PATH)
        registry = load_json(NOTATION_PATH)
        expected_ids = rules.get('expected_theorem_ids') or [row['theorem_id'] for row in sheet['theorems']]
        expected_labels = [f'thm:{theorem_id}' for theorem_id in expected_ids]

        main_pdf_bytes = build_tree(MAIN_ROOT, build_dir, 'main')
        supplement_pdf_bytes = build_tree(SUPP_ROOT, build_dir, 'supplement')

        main_results_text = MAIN_RESULTS.read_text(encoding='utf-8')
        theorem_count_found, labels_found, theorem_star_present = theorem_labels_and_envs(main_results_text)
        labels_missing = [label for label in expected_labels if label not in labels_found]
        labels_duplicate = sorted({label for label in labels_found if labels_found.count(label) > 1})
        unexpected_labels = [label for label in labels_found if label not in expected_labels]
        if theorem_star_present:
            labels_duplicate.append('theorem* environment present')
        if unexpected_labels:
            labels_duplicate.extend(sorted(f'unexpected:{label}' for label in unexpected_labels))

        main_aux = (build_dir / 'main.aux').read_text(encoding='utf-8')
        numbering_missing = aux_numbering(main_aux, expected_labels)

        proof_map = proof_coverage(expected_labels)
        proof_missing_labels = [label for label, paths in proof_map.items() if not paths]

        notation_missing = notation_check(sheet, registry)

        main_sources = [MAIN_ROOT / 'main.tex', MAIN_ROOT / 'macros.tex']
        main_sources.extend(sorted((MAIN_ROOT / 'sections').glob('*.tex')))
        main_sources.extend(sorted((MAIN_ROOT / 'appendices').glob('*.tex')))
        forbidden_token_hits = scan_hits(main_sources, rules['forbidden_tokens_main'], ignore_case=True)
        repo_path_hits_main = scan_hits(main_sources, rules['forbidden_repo_paths_in_main'], ignore_case=False)
        theorem_statement_repo_hits = theorem_statement_hits(sheet, GENERATED_STATEMENTS.read_text(encoding='utf-8'), rules['forbidden_in_theorem_statements'])

        summary = {
            'generated_at_utc': now_iso(),
            'theorem_count_expected': len(expected_ids),
            'theorem_count_found': theorem_count_found,
            'labels_missing': labels_missing,
            'labels_duplicate': labels_duplicate,
            'numbering_missing': numbering_missing,
            'proof_missing_labels': proof_missing_labels,
            'proof_coverage_map': proof_map,
            'notation_missing': notation_missing,
            'forbidden_token_hits': forbidden_token_hits,
            'repo_path_hits_main': repo_path_hits_main,
            'theorem_statement_repo_hits': theorem_statement_repo_hits,
            'main_build_ok': True,
            'supplement_build_ok': True,
            'main_pdf_bytes': main_pdf_bytes,
            'supplement_pdf_bytes': supplement_pdf_bytes,
            'status': 'success',
        }

        failures = []
        if theorem_count_found != len(expected_ids):
            failures.append('theorem count mismatch')
        if labels_missing:
            failures.append('missing theorem labels')
        if labels_duplicate:
            failures.append('duplicate or unexpected theorem labels')
        if numbering_missing:
            failures.append('missing theorem numbering in aux')
        if proof_missing_labels:
            failures.append('missing theorem proof coverage')
        if notation_missing:
            failures.append('notation required by theorem statements is not defined before use')
        if forbidden_token_hits:
            failures.append('forbidden tokens present in main paper')
        if repo_path_hits_main:
            failures.append('repo-path leakage present in main paper')
        if theorem_statement_repo_hits:
            failures.append('repo-only references present in theorem statements')

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
            'theorem_count_expected': 0,
            'theorem_count_found': 0,
            'labels_missing': [],
            'labels_duplicate': [],
            'numbering_missing': [],
            'proof_missing_labels': [],
            'notation_missing': [],
            'forbidden_token_hits': [],
            'repo_path_hits_main': [],
            'theorem_statement_repo_hits': [],
            'main_build_ok': False,
            'supplement_build_ok': False,
            'status': 'failed',
            'error': str(exc),
        }
        SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
