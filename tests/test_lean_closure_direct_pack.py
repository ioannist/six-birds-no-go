import json
from pathlib import Path
import subprocess
import sys

import sixbirds_nogo


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_files_exist_and_parse() -> None:
    for rel in [
        "docs/project/lean_closure_direct.yaml",
        "docs/project/lean_closure_formal_boundary.md",
        "results/T42/lean_closure_direct_pack_summary.json",
    ]:
        assert Path(rel).exists(), rel
    assert isinstance(_load("docs/project/lean_closure_direct.yaml"), dict)


def test_t41_foldforward_files_exist() -> None:
    for rel in [
        "lean/SixBirdsNoGo/ClosureVariationalCore.lean",
        "lean/SixBirdsNoGo/ClosureVariationalCoreExample.lean",
    ]:
        assert Path(rel).exists(), rel


def test_branch_aware_readiness_and_atlas() -> None:
    summary = _load("results/T42/lean_closure_direct_pack_summary.json")
    readiness = {row["theorem_id"]: row for row in _load("docs/project/readiness_checklist.yaml")["theorems"]}
    atlas = {row["theorem_id"]: row for row in _load("docs/project/theorem_atlas.yaml")["theorems"]}

    if summary["outcome_mode"] == "direct_theorem_pack":
        assert readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] == "direct"
        assert atlas["NG_MACRO_CLOSURE_DEFICIT"]["support_snapshot"]["lean_support"]["status"] == "direct"
    else:
        assert readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] == "auxiliary_only"
        assert atlas["NG_MACRO_CLOSURE_DEFICIT"]["support_snapshot"]["lean_support"]["status"] == "auxiliary_only"


def test_runner_smoke(tmp_path) -> None:
    out_dir = tmp_path / "t42"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t42_lean_closure_direct_pack.py", "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((out_dir / "lean_closure_direct_pack_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "success"
    assert summary["outcome_mode"] == "direct_theorem_pack"
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["closure_direct"] is True
    assert summary["direct_pack_present"] is True
    assert summary["formal_boundary_note_present"] is True
    assert summary["t41_foldforward_present"] is True
    assert summary["t41_core_retained"] is True
    assert summary["variational_identity_present"] is True
    assert summary["positive_deficit_corollary_present"] is True
    assert summary["exact_closed_macro_law_predicate_present"] is True
    assert summary["next_ticket_id"] == "PLAN_NEXT_18_closure_scope_guardrail_hold"


def test_repro_alignment_and_package_version() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t42_lean_closure_direct_pack.py" in text
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
