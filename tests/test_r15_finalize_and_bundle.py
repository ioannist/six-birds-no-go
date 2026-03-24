import json
from pathlib import Path
import subprocess
import sys
import zipfile


def test_r15_finalize_and_bundle() -> None:
    proc = subprocess.run(
        [sys.executable, 'scripts/run_r15_finalize_and_bundle.py'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    queue = json.loads(Path('docs/project/revision_queue_r15.yaml').read_text(encoding='utf-8'))
    summary = json.loads(Path('results/R15/revision_pass_summary.json').read_text(encoding='utf-8'))

    assert [item['issue_id'] for item in queue['items']] == ['R14-001', 'R14-002', 'R14-003', 'R14-004']
    assert all(item['status'] == 'closed' for item in queue['items'])
    assert summary['blocking_open_count'] == 0

    forbidden_paths = [
        Path('paper/draft_v1.md'),
        Path('paper/draft_v2.md'),
        Path('paper/draft_v3.md'),
        Path('paper/writing_track'),
        Path('paper/legacy_internal'),
        Path('paper/rewrite_tex'),
        Path('paper/submission_bundle'),
        Path('paper/math_rewrite'),
        Path('results/paper_build'),
        Path('results/supplement_build'),
        Path('paper/manuscript_skeleton.md'),
    ]
    for path in forbidden_paths:
        assert not path.exists(), path

    paper_build = Path('paper/build')
    supp_build = Path('paper/supplement/build')
    assert sorted(p.name for p in paper_build.iterdir()) == ['main.pdf', 'main_flat.tex']
    assert sorted(p.name for p in supp_build.iterdir()) == ['supplement.pdf', 'supplement_flat.tex']
    assert (paper_build / 'main.pdf').stat().st_size > 200_000
    assert (paper_build / 'main_flat.tex').stat().st_size > 10_000
    assert (supp_build / 'supplement.pdf').stat().st_size > 80_000
    assert (supp_build / 'supplement_flat.tex').stat().st_size > 5_000

    bundle = Path('results/submission_bundle/source.zip')
    assert bundle.exists()
    assert (Path('results/submission_bundle') / 'main_flat.tex').exists()
    assert (Path('results/submission_bundle') / 'supplement_flat.tex').exists()
    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
    required_prefixes = [
        'main.tex',
        'macros.tex',
        'refs.bib',
        'sections/01_introduction.tex',
        'appendices/appendix_a_probability_kl.tex',
        'generated/theorem_statements.tex',
        'supplement/main.tex',
        'supplement/sections/lean_map.tex',
    ]
    for name in required_prefixes:
        assert name in names
