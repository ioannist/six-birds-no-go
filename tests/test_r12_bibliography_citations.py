import json
from pathlib import Path
import subprocess
import sys


def test_r12_bibliography_citations() -> None:
    proc = subprocess.run(
        [sys.executable, 'scripts/run_r12_bibliography_citations.py'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads(Path('results/R12/bibliography_citations_summary.json').read_text(encoding='utf-8'))
    assert summary['main_build_ok'] is True
    assert summary['supp_build_ok'] is True
    assert summary['missing_bib_keys'] == []
    assert summary['placeholder_citation_keys'] == []
    assert summary['sb_citations_outside_allowed'] == []
    assert 'CoverThomas2006' in summary['required_standard_keys_cited']
    assert 'KullbackLeibler1951' in summary['required_standard_keys_cited']
    assert summary['main_non_sb_citation_key_count'] >= 4

    main_pdf = Path('results/R12/latex_build/main.pdf')
    supp_pdf = Path('results/R12/latex_build/supplement.pdf')
    assert main_pdf.exists()
    assert supp_pdf.exists()
    assert main_pdf.stat().st_size > 200_000
    assert supp_pdf.stat().st_size > 80_000

    refs_text = Path('paper/refs.bib').read_text(encoding='utf-8')
    for key in [
        'KullbackLeibler1951',
        'CoverThomas2006',
        'Norris1997',
        'LevinPeresWilmer2017',
        'Diestel2017',
        'Biggs1993',
    ]:
        assert f'{{{key},' in refs_text

    intro = Path('paper/sections/01_introduction.tex').read_text(encoding='utf-8')
    assert 'SB_FOUNDATIONS' in intro
    for rel in [
        'paper/sections/04_arrow_and_protocol.tex',
        'paper/sections/05_graph_and_affinity.tex',
        'paper/sections/06_closure.tex',
        'paper/sections/07_objecthood.tex',
    ]:
        text = Path(rel).read_text(encoding='utf-8')
        assert 'SB_' not in text

    setup = Path('paper/sections/02_setup.tex').read_text(encoding='utf-8')
    assert '\\citep{KullbackLeibler1951,CoverThomas2006}' in setup
    assert '\\citep{Norris1997,LevinPeresWilmer2017}' in setup
