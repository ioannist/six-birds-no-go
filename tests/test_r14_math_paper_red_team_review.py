import json
from pathlib import Path
import subprocess
import sys

VALID_SEVERITIES = {'blocking', 'high', 'medium', 'low'}
VALID_CATEGORIES = {
    'self_containment',
    'theorem_precision',
    'proof_sufficiency',
    'appendix_balance',
    'objecthood_boundary',
    'supplement_dependence',
    'exposition',
}


def test_r14_math_paper_red_team_review() -> None:
    proc = subprocess.run(
        [sys.executable, 'scripts/run_r14_math_paper_red_team_review.py'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    queue_path = Path('docs/project/revision_queue_r14.yaml')
    claim_path = Path('results/R14/claim_audit_matrix.json')
    section_path = Path('results/R14/section_audit_matrix.json')
    summary_path = Path('results/R14/red_team_summary.json')
    pdf_path = Path('results/R14/latex_build/main.pdf')
    supp_pdf_path = Path('results/R14/latex_build/supplement.pdf')

    for path in [queue_path, claim_path, section_path, summary_path, pdf_path, supp_pdf_path]:
        assert path.exists(), path

    queue = json.loads(queue_path.read_text(encoding='utf-8'))
    claim = json.loads(claim_path.read_text(encoding='utf-8'))
    section = json.loads(section_path.read_text(encoding='utf-8'))
    summary = json.loads(summary_path.read_text(encoding='utf-8'))

    assert claim['theorem_count'] == 8
    assert len(claim['claims']) == 8

    section_ids = {row['section_id'] for row in section['sections']}
    expected_sections = {
        '01_introduction',
        '02_setup',
        '03_main_results',
        '04_arrow_and_protocol',
        '05_graph_and_affinity',
        '06_closure',
        '07_objecthood',
        '08_bounded_interface',
        '09_discussion',
        'appendix_a_probability_kl',
        'appendix_b_graph_exactness',
        'appendix_c_variational_closure',
        'appendix_d_packaging_definability',
        'supplement_overview',
    }
    assert expected_sections <= section_ids

    queue_items = queue['items']
    queue_issue_ids = {item['issue_id'] for item in queue_items}
    matrix_issue_ids = set()
    for row in claim['claims']:
        matrix_issue_ids.update(row['issues'])
    for row in section['sections']:
        matrix_issue_ids.update(row['issues'])
    assert matrix_issue_ids == queue_issue_ids

    for item in queue_items:
        assert set(item) == {
            'issue_id',
            'severity',
            'category',
            'target',
            'location',
            'problem',
            'fix',
            'acceptance_check',
        }
        assert item['severity'] in VALID_SEVERITIES
        assert item['category'] in VALID_CATEGORIES
        assert set(item['location']) == {'file', 'line_start', 'line_end'}
        assert item['location']['line_start'] >= 1
        assert item['location']['line_end'] >= item['location']['line_start']

    assert summary['hidden_gap_count'] == 0
    assert summary['theorem_count_audited'] == 8
    assert summary['section_count_audited'] >= len(expected_sections)

    assert pdf_path.stat().st_size > 50_000
    assert supp_pdf_path.stat().st_size > 50_000
