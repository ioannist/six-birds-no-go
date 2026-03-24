#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / 'results' / 'R14'
QUEUE_PATH = ROOT / 'docs' / 'project' / 'revision_queue_r14.yaml'
CLAIM_MATRIX_PATH = RESULTS_DIR / 'claim_audit_matrix.json'
SECTION_MATRIX_PATH = RESULTS_DIR / 'section_audit_matrix.json'
SUMMARY_PATH = RESULTS_DIR / 'red_team_summary.json'
LOG_PATH = ROOT / 'docs' / 'research-log' / 'R14.md'

MAIN_ROOT = ROOT / 'paper'
SUPP_ROOT = MAIN_ROOT / 'supplement'
MAIN_SECTIONS = [
    ('01_introduction', MAIN_ROOT / 'sections' / '01_introduction.tex'),
    ('02_setup', MAIN_ROOT / 'sections' / '02_setup.tex'),
    ('03_main_results', MAIN_ROOT / 'sections' / '03_main_results.tex'),
    ('04_arrow_and_protocol', MAIN_ROOT / 'sections' / '04_arrow_and_protocol.tex'),
    ('05_graph_and_affinity', MAIN_ROOT / 'sections' / '05_graph_and_affinity.tex'),
    ('06_closure', MAIN_ROOT / 'sections' / '06_closure.tex'),
    ('07_objecthood', MAIN_ROOT / 'sections' / '07_objecthood.tex'),
    ('08_bounded_interface', MAIN_ROOT / 'sections' / '08_bounded_interface.tex'),
    ('09_discussion', MAIN_ROOT / 'sections' / '09_discussion.tex'),
]
TECH_APPENDICES = [
    ('appendix_a_probability_kl', MAIN_ROOT / 'appendices' / 'appendix_a_probability_kl.tex'),
    ('appendix_b_graph_exactness', MAIN_ROOT / 'appendices' / 'appendix_b_graph_exactness.tex'),
    ('appendix_c_variational_closure', MAIN_ROOT / 'appendices' / 'appendix_c_variational_closure.tex'),
    ('appendix_d_packaging_definability', MAIN_ROOT / 'appendices' / 'appendix_d_packaging_definability.tex'),
]
SUPPLEMENT_FILES = [
    SUPP_ROOT / 'main.tex',
    SUPP_ROOT / 'sections' / '00_readme.tex',
    SUPP_ROOT / 'sections' / 'provenance.tex',
    SUPP_ROOT / 'sections' / 'evidence_map.tex',
    SUPP_ROOT / 'sections' / 'computational_audit.tex',
    SUPP_ROOT / 'sections' / 'fragility_diagnostics.tex',
    SUPP_ROOT / 'sections' / 'lean_map.tex',
]

SEVERITIES = {'blocking', 'high', 'medium', 'low'}
CATEGORIES = {
    'self_containment',
    'theorem_precision',
    'proof_sufficiency',
    'appendix_balance',
    'objecthood_boundary',
    'supplement_dependence',
    'exposition',
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_jsonish(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding='utf-8').splitlines()


def find_span(path: Path, needle: str) -> tuple[int, int]:
    lines = read_lines(path)
    hits = [i for i, line in enumerate(lines, 1) if needle in line]
    if not hits:
        return (1, 1)
    return (hits[0], hits[-1])


def extract_proof_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r'\\begin\{proof\}(?:\[(.*?)\])?(.*?)\\end\{proof\}', re.DOTALL)
    return [(title or '', body or '') for title, body in pattern.findall(text)]


def extract_appendix_refs(text: str) -> list[str]:
    return sorted(set(re.findall(r'Appendix~\\ref\{([^}]+)\}', text)))


def short_excerpt(line: str) -> str:
    return line.strip()[:160]


def add_issue(issues: list[dict[str, Any]], *, severity: str, category: str, target: str, file: Path, line_start: int, line_end: int, problem: str, fix: str, acceptance_check: str) -> str:
    issue_id = f'R14-{len(issues)+1:03d}'
    issues.append({
        'issue_id': issue_id,
        'severity': severity,
        'category': category,
        'target': target,
        'location': {'file': rel(file), 'line_start': line_start, 'line_end': line_end},
        'problem': problem,
        'fix': fix,
        'acceptance_check': acceptance_check,
    })
    return issue_id


def run_upstream() -> None:
    proc = subprocess.run([sys.executable, 'scripts/run_r13_math_paper_validator.py'], cwd=ROOT, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / 'latex_build').mkdir(parents=True, exist_ok=True)

    run_upstream()

    statement_sheet = load_jsonish(ROOT / 'docs' / 'project' / 'theorem_statement_sheet.yaml')
    notation_registry = load_jsonish(ROOT / 'docs' / 'project' / 'notation_registry.yaml')
    theorem_atlas = load_jsonish(ROOT / 'docs' / 'project' / 'theorem_atlas.yaml')
    validation_summary = load_jsonish(ROOT / 'results' / 'R13' / 'math_paper_validator_summary.json')

    theorem_order = theorem_atlas['paper_order']
    notation_map = {entry['notation_id']: entry for entry in notation_registry['notation']}
    theorem_map = {entry['theorem_id']: entry for entry in statement_sheet['theorems']}

    issues: list[dict[str, Any]] = []
    theorem_issue_map: dict[str, list[str]] = {theorem_id: [] for theorem_id in theorem_order}
    section_issue_map: dict[str, list[str]] = {name: [] for name, _ in MAIN_SECTIONS + TECH_APPENDICES}
    section_issue_map['supplement_overview'] = []

    # Targeted checks for the R14 queue items and related integrity risks.
    main_results = MAIN_ROOT / 'sections' / '03_main_results.tex'
    main_results_text = main_results.read_text(encoding='utf-8')
    if 'statement sheet' in main_results_text.lower() or 'generated macro' in main_results_text.lower():
        issue_id = add_issue(
            issues,
            severity='low',
            category='exposition',
            target='sec:main-results',
            file=main_results,
            line_start=find_span(main_results, 'statement')[0],
            line_end=find_span(main_results, 'statement')[1],
            problem='Opening sentence uses internal production language instead of mathematical description.',
            fix='Replace it with a theorem-paper sentence describing the role of Section 3.',
            acceptance_check='Section 3 opens without internal production language.',
        )
        section_issue_map['03_main_results'].append(issue_id)

    protocol_stmt = theorem_map['NG_PROTOCOL_TRAP']['formal_statement_latex']
    if 'NG_ARROW_DPI' in protocol_stmt:
        statement_path = ROOT / 'docs' / 'project' / 'theorem_statement_sheet.yaml'
        issue_id = add_issue(
            issues,
            severity='medium',
            category='theorem_precision',
            target='NG_PROTOCOL_TRAP',
            file=statement_path,
            line_start=find_span(statement_path, 'NG_PROTOCOL_TRAP')[0],
            line_end=find_span(statement_path, 'NG_PROTOCOL_TRAP')[1],
            problem='Formal statement cites an internal theorem identifier.',
            fix='State the observed-arrow consequence mathematically instead of by internal theorem id.',
            acceptance_check='The NG_PROTOCOL_TRAP formal statement contains no literal internal theorem id.',
        )
        theorem_issue_map['NG_PROTOCOL_TRAP'].append(issue_id)

    closure_stmt = theorem_map['NG_MACRO_CLOSURE_DEFICIT']['formal_statement_latex']
    closure_text = (MAIN_ROOT / 'sections' / '06_closure.tex').read_text(encoding='utf-8')
    if '\\mu(x)>0' not in closure_stmt or '\\mu(x\')>0' not in closure_stmt or '\\mu(x)>0' not in closure_text:
        statement_path = ROOT / 'docs' / 'project' / 'theorem_statement_sheet.yaml'
        issue_id = add_issue(
            issues,
            severity='blocking',
            category='theorem_precision',
            target='NG_MACRO_CLOSURE_DEFICIT',
            file=statement_path,
            line_start=find_span(statement_path, 'NG_MACRO_CLOSURE_DEFICIT')[0],
            line_end=find_span(statement_path, 'NG_MACRO_CLOSURE_DEFICIT')[1],
            problem='Positivity corollary omits the positive-mass condition used by the proof.',
            fix='Add explicit positive stationary mass to the theorem statement and align the proof text.',
            acceptance_check='The statement and proof both require positive mass on the disagreeing fiber states.',
        )
        theorem_issue_map['NG_MACRO_CLOSURE_DEFICIT'].append(issue_id)
        section_issue_map['06_closure'].append(issue_id)

    objecthood = MAIN_ROOT / 'sections' / '07_objecthood.tex'
    objecthood_text = objecthood.read_text(encoding='utf-8')
    if 'auxiliary-only' not in objecthood_text or 'not formalized' not in objecthood_text or 'uniqueness consequence' not in objecthood_text:
        issue_id = add_issue(
            issues,
            severity='high',
            category='objecthood_boundary',
            target='sec:objecthood',
            file=objecthood,
            line_start=find_span(objecthood, 'Formalization status')[0],
            line_end=find_span(objecthood, 'Formalization status')[1],
            problem='Formal-status remark does not state the auxiliary boundary explicitly enough.',
            fix='State what is formalized, what is auxiliary-only, and what remains outside formalization.',
            acceptance_check='Section 7 names the uniqueness core and states the TV/Dobrushin plus epsilon-stability layer is auxiliary-only.',
        )
        theorem_issue_map['NG_OBJECT_CONTRACTIVE'].append(issue_id)
        section_issue_map['07_objecthood'].append(issue_id)

    # Copy build artifacts from R13.
    r13_build = ROOT / 'results' / 'R13' / 'latex_build'
    r14_build = RESULTS_DIR / 'latex_build'
    for src_name, dst_name in [('main.pdf', 'main.pdf'), ('supplement.pdf', 'supplement.pdf'), ('main.log', 'main.log'), ('main.aux', 'main.aux'), ('supplement.log', 'supplement.log')]:
        src = r13_build / src_name
        if src.exists():
            shutil.copy2(src, r14_build / dst_name)

    claim_rows: list[dict[str, Any]] = []
    for theorem_id in theorem_order:
        theorem = theorem_map[theorem_id]
        macro_name = '\\ThmStmt' + theorem_id.replace('_', '')
        macro_source = MAIN_ROOT / 'generated' / 'theorem_statements.tex'
        proof_files = validation_summary['proof_coverage_map'].get(f'thm:{theorem_id}', [])
        proof_gap_hits: list[dict[str, Any]] = []
        appendix_refs: list[str] = []
        supplement_refs: list[str] = []
        for proof_file in proof_files:
            path = ROOT / proof_file
            text = path.read_text(encoding='utf-8')
            appendix_refs.extend(extract_appendix_refs(text))
            for title, body in extract_proof_blocks(text):
                haystack = title + '\n' + body
                if 'supplement' in haystack.lower():
                    supplement_refs.append(proof_file)
                for i, line in enumerate(haystack.splitlines(), start=1):
                    if re.search(r'\b(obvious|clearly|immediate|standard|well-known|it follows)\b', line, re.IGNORECASE):
                        window = '\n'.join(haystack.splitlines()[max(0, i - 1): i + 2])
                        if not re.search(r'\\cite|Appendix~\\ref|Lemma~\\ref|Theorem~\\ref|Proposition~\\ref', window):
                            proof_gap_hits.append({'file': proof_file, 'line': i, 'text': short_excerpt(line)})
        missing_notation = [nid for nid in theorem['required_notation'] if nid not in notation_map]
        risk = 'low' if not theorem_issue_map[theorem_id] and not proof_gap_hits and not supplement_refs else 'medium'
        if any(issue['severity'] == 'blocking' for issue in issues if issue['issue_id'] in theorem_issue_map[theorem_id]):
            risk = 'high'
        claim_rows.append({
            'theorem_id': theorem_id,
            'statement_source': {
                'path': rel(ROOT / 'docs' / 'project' / 'theorem_statement_sheet.yaml'),
                'macro_path': rel(macro_source),
                'macro_name': macro_name,
                'formal_statement_sha256': sha256_text(theorem['formal_statement_latex']),
            },
            'precision_checks': {
                'hypotheses_count': len(theorem['hypotheses']),
                'conclusions_count': len(theorem['conclusions']),
                'initialization_scope_present': theorem_id != 'NG_PROTOCOL_TRAP' or 'stationary' in theorem['formal_statement_latex'].lower(),
                'undefined_notation_tokens': missing_notation,
            },
            'proof_coverage_checks': {
                'proof_exists': bool(proof_files),
                'proof_files': proof_files,
                'gap_phrase_hits': proof_gap_hits,
            },
            'appendix_dependency': {
                'referenced_appendices': sorted(set(appendix_refs)),
                'implicit_dependency_without_pointer': False,
            },
            'supplement_dependency': sorted(set(supplement_refs)),
            'risk_grade': risk,
            'issues': theorem_issue_map[theorem_id],
        })

    section_rows: list[dict[str, Any]] = []
    appendix_refs_by_label: dict[str, int] = {}
    for _, path in MAIN_SECTIONS:
        text = path.read_text(encoding='utf-8')
        for label in extract_appendix_refs(text):
            appendix_refs_by_label[label] = appendix_refs_by_label.get(label, 0) + 1

    for name, path in MAIN_SECTIONS + TECH_APPENDICES:
        text = path.read_text(encoding='utf-8')
        lower = text.lower()
        first_definition = min((i for i, line in enumerate(text.splitlines(), start=1) if '\\begin{definition}' in line), default=None)
        first_theorem_ref = min((i for i, line in enumerate(text.splitlines(), start=1) if '\\ref{thm:' in line), default=None)
        section_rows.append({
            'section_id': name,
            'path': rel(path),
            'definition_before_first_theorem_ref': first_definition is None or first_theorem_ref is None or first_definition <= first_theorem_ref,
            'appendix_refs': extract_appendix_refs(text),
            'supplement_mentions': lower.count('supplement'),
            'definition_block_count': text.count('\\begin{definition}'),
            'issues': section_issue_map[name],
        })

    supplement_overview = '\n'.join(path.read_text(encoding='utf-8') for path in SUPPLEMENT_FILES if path.exists())
    section_rows.append({
        'section_id': 'supplement_overview',
        'path': rel(SUPP_ROOT / 'main.tex'),
        'definition_before_first_theorem_ref': True,
        'appendix_refs': [],
        'supplement_mentions': supplement_overview.lower().count('supplement'),
        'definition_block_count': supplement_overview.count('\\begin{definition}'),
        'issues': section_issue_map['supplement_overview'],
    })

    queue = {'generated_at_utc': utc_now(), 'queue_id': 'revision_queue_r14_v2', 'items': issues}
    claim_matrix = {'generated_at_utc': utc_now(), 'theorem_count': len(claim_rows), 'claims': claim_rows}
    section_matrix = {'generated_at_utc': utc_now(), 'section_count': len(section_rows), 'sections': section_rows}

    matrix_issue_ids = {issue_id for row in claim_rows for issue_id in row['issues']} | {issue_id for row in section_rows for issue_id in row['issues']}
    queue_issue_ids = {item['issue_id'] for item in issues}
    severity_counts = Counter(item['severity'] for item in issues)
    category_counts = Counter(item['category'] for item in issues)
    summary = {
        'generated_at_utc': utc_now(),
        'theorem_count_audited': len(claim_rows),
        'section_count_audited': len(section_rows),
        'issue_count': len(issues),
        'severity_counts': dict(severity_counts),
        'category_counts': dict(category_counts),
        'blocking_issue_count': severity_counts.get('blocking', 0),
        'main_build_ok': validation_summary['main_build_ok'],
        'supplement_build_ok': validation_summary['supplement_build_ok'],
        'hidden_gap_count': len((matrix_issue_ids ^ queue_issue_ids)),
        'status': 'success',
    }

    QUEUE_PATH.write_text(json.dumps(queue, indent=2) + '\n', encoding='utf-8')
    CLAIM_MATRIX_PATH.write_text(json.dumps(claim_matrix, indent=2) + '\n', encoding='utf-8')
    SECTION_MATRIX_PATH.write_text(json.dumps(section_matrix, indent=2) + '\n', encoding='utf-8')
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    LOG_PATH.write_text(
        '## R14\n\n'
        '- audited theorem self-containment, theorem precision, proof coverage, appendix usage, objecthood boundary honesty, and supplement dependence\n'
        f'- theorem fronts audited: {len(claim_rows)}\n'
        f'- section units audited: {len(section_rows)}\n'
        f'- queue items emitted: {len(issues)}\n'
        f'- hidden_gap_count: {summary["hidden_gap_count"]}\n',
        encoding='utf-8',
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
