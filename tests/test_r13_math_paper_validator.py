import json
from pathlib import Path
import subprocess
import sys


def test_r13_math_paper_validator() -> None:
    proc = subprocess.run(
        [sys.executable, 'scripts/run_r13_math_paper_validator.py'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads(Path('results/R13/math_paper_validator_summary.json').read_text(encoding='utf-8'))
    assert summary['theorem_count_found'] == summary['theorem_count_expected'] == 8
    assert summary['labels_missing'] == []
    assert summary['labels_duplicate'] == []
    assert summary['numbering_missing'] == []
    assert summary['proof_missing_labels'] == []
    assert summary['notation_missing'] == []
    assert summary['forbidden_token_hits'] == []
    assert summary['repo_path_hits_main'] == []
    assert summary['theorem_statement_repo_hits'] == []
    assert summary['main_build_ok'] is True
    assert summary['supplement_build_ok'] is True

    pdf = Path('results/R13/latex_build/main.pdf')
    assert pdf.exists()
    assert pdf.stat().st_size > 50_000
