import json
from pathlib import Path
import shutil
import subprocess
import sys

import sixbirds_nogo


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_files_exist_and_parse() -> None:
    for rel in [
        "lean/SixBirdsNoGo/ClosureVariationalCore.lean",
        "lean/SixBirdsNoGo/ClosureVariationalCoreExample.lean",
        "docs/project/lean_closure_variational_core.yaml",
        "results/T41/lean_closure_variational_core_summary.json",
    ]:
        assert Path(rel).exists(), rel
    assert isinstance(_load("docs/project/lean_closure_variational_core.yaml"), dict)


def test_placeholder_free() -> None:
    for rel in [
        "lean/SixBirdsNoGo/ClosureVariationalCore.lean",
        "lean/SixBirdsNoGo/ClosureVariationalCoreExample.lean",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_imports_present() -> None:
    text = Path("lean/SixBirdsNoGo.lean").read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.ClosureVariationalCore" in text
    assert "import SixBirdsNoGo.ClosureVariationalCoreExample" in text


def test_readiness_and_atlas_anchors() -> None:
    readiness = {row["theorem_id"]: row for row in _load("docs/project/readiness_checklist.yaml")["theorems"]}
    atlas = {row["theorem_id"]: row for row in _load("docs/project/theorem_atlas.yaml")["theorems"]}
    assert readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] == "direct"
    assert atlas["NG_MACRO_CLOSURE_DEFICIT"]["support_snapshot"]["lean_support"]["status"] == "direct"


def test_runner_smoke(tmp_path) -> None:
    out_dir = tmp_path / "t41"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t41_lean_closure_variational_core.py", "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((out_dir / "lean_closure_variational_core_summary.json").read_text(encoding="utf-8"))
    assert summary["theorem_count"] == 1
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["closure_auxiliary"] is False
    assert summary["packaged_future_laws_formalized"] is True
    assert summary["macro_kernel_objects_formalized"] is True
    assert summary["variational_objective_formalized"] is True
    assert summary["rowwise_minimizer_present"] is True
    assert summary["best_macro_kernel_formula_present"] is True
    assert summary["best_macro_gap_present"] is True
    assert summary["t40_decision_preserved"] is True
    assert summary["full_closure_theorem_pending"] is False
    assert summary["attribution_out_of_scope"] is True
    assert summary["next_ticket_id"] is None
    assert summary["status"] == "success"
    expected_lake = "passed" if shutil.which("lake") else "skipped_tool_unavailable"
    assert summary["lake_build_status"] == expected_lake


def test_t40_preservation_coverage() -> None:
    data = _load("docs/project/lean_closure_feasibility.yaml")
    assert data["decision"]["decision_mode"] == "proceed_to_variational_core"
    assert data["theorem_target"]["current_lean_status"] == "direct"
    row_map = {row["obligation_id"]: row for row in data["obligation_matrix"]}
    for oid in [
        "CL_PACKAGED_FUTURE_LAW_FAMILY",
        "CL_FINITE_MACRO_KERNEL",
        "CL_VARIATIONAL_OBJECTIVE",
        "CL_ROWWISE_MINIMIZER_LEMMA",
        "CL_CLOSED_FORM_BEST_KERNEL",
    ]:
        assert row_map[oid]["status"] == "already_formalized"
    assert row_map["CL_CLOSURE_VARIATIONAL_IDENTITY_AND_COROLLARY"]["status"] == "already_formalized"


def test_repro_alignment_and_package_version() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t41_lean_closure_variational_core.py" in text
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
