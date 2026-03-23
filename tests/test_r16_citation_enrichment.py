import json
from pathlib import Path
import subprocess
import sys


def test_r16_citation_enrichment() -> None:
    proc = subprocess.run(
        [sys.executable, 'scripts/run_r16_citation_enrichment.py'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads(Path('results/R16/citation_enrichment_summary.json').read_text(encoding='utf-8'))
    assert summary['main_build_ok'] is True
    assert summary['supp_build_ok'] is True
    assert summary['missing_bib_keys'] == []
    assert summary['placeholder_citation_keys'] == []

    refs_text = Path('paper/refs.bib').read_text(encoding='utf-8')
    target_text = '\n'.join(
        Path(path).read_text(encoding='utf-8')
        for path in [
            'paper/sections/02_setup.tex',
            'paper/sections/04_arrow_and_protocol.tex',
            'paper/sections/05_graph_and_affinity.tex',
            'paper/sections/06_closure.tex',
            'paper/sections/07_objecthood.tex',
        ]
    )

    required_keys = [
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
    for key in required_keys:
        assert f'{{{key},' in refs_text
        assert key in target_text

    main_pdf = Path('results/R16/latex_build/main.pdf')
    supp_pdf = Path('results/R16/latex_build/supplement.pdf')
    assert main_pdf.exists()
    assert supp_pdf.exists()
    assert main_pdf.stat().st_size > 200_000
    assert supp_pdf.stat().st_size > 80_000
