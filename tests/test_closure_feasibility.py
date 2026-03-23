import json
from pathlib import Path
import subprocess
import sys

import sixbirds_nogo


REQUIRED_IDS = [
    "CL_BASE_FINITE_LAWS",
    "CL_BASE_FINITE_KL",
    "CL_PACKAGED_FUTURE_LAW_FAMILY",
    "CL_FINITE_MACRO_KERNEL",
    "CL_VARIATIONAL_OBJECTIVE",
    "CL_ROWWISE_MINIMIZER_LEMMA",
    "CL_CLOSED_FORM_BEST_KERNEL",
    "CL_CLOSURE_VARIATIONAL_IDENTITY_AND_COROLLARY",
    "CL_ATTRIBUTION_RESOLUTION_OUT_OF_SCOPE",
]


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_files_exist_and_parse() -> None:
    for rel in [
        "docs/project/lean_closure_feasibility.yaml",
        "docs/project/lean_closure_formal_boundary.md",
        "results/T40/lean_closure_feasibility_summary.json",
    ]:
        assert Path(rel).exists(), rel
    assert isinstance(_load("docs/project/lean_closure_feasibility.yaml"), dict)


def test_frontier_status_no_drift() -> None:
    summary = _load("results/T40/lean_closure_feasibility_summary.json")
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["current_closure_lean_status"] == "direct"
    assert summary["theorem_status_unchanged"] is True


def test_obligation_matrix_anchors() -> None:
    data = _load("docs/project/lean_closure_feasibility.yaml")
    rows = data["obligation_matrix"]
    ids = [row["obligation_id"] for row in rows]
    assert ids == REQUIRED_IDS
    row_map = {row["obligation_id"]: row for row in rows}
    assert row_map["CL_BASE_FINITE_LAWS"]["status"] == "already_formalized"
    assert row_map["CL_BASE_FINITE_KL"]["status"] == "already_formalized"
    assert row_map["CL_ATTRIBUTION_RESOLUTION_OUT_OF_SCOPE"]["status"] == "out_of_scope"


def test_branch_validity() -> None:
    summary = _load("results/T40/lean_closure_feasibility_summary.json")
    if summary["decision_mode"] == "proceed_to_variational_core":
        assert summary["needed_narrow_count"] == 0
        assert summary["requires_forbidden_expansion_count"] == 0
        assert summary["narrow_bridge_possible"] is True
        assert summary["generic_optimization_required"] is False
        assert summary["next_ticket_id"] is None
    else:
        assert summary["requires_forbidden_expansion_count"] >= 1
        assert summary["narrow_bridge_possible"] is False
        assert summary["generic_optimization_required"] is True
        assert summary["next_ticket_id"] is None


def test_runner_smoke(tmp_path) -> None:
    out_dir = tmp_path / "t40"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t40_closure_feasibility.py", "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((out_dir / "lean_closure_feasibility_summary.json").read_text(encoding="utf-8"))
    assert summary["theorem_count"] == 1
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["current_closure_lean_status"] == "direct"
    assert summary["obligation_count"] == 9
    assert summary["already_formalized_count"] == 8
    assert summary["out_of_scope_count"] == 1
    assert summary["attribution_out_of_scope"] is True
    assert summary["objecthood_still_deferred"] is True
    assert summary["theorem_status_unchanged"] is True
    if summary["decision_mode"] == "proceed_to_variational_core":
        assert summary["needed_narrow_count"] == 0
        assert summary["requires_forbidden_expansion_count"] == 0
        assert summary["narrow_bridge_possible"] is True
        assert summary["generic_optimization_required"] is False
        assert summary["next_ticket_id"] is None
    else:
        assert summary["requires_forbidden_expansion_count"] >= 1
        assert summary["narrow_bridge_possible"] is False
        assert summary["generic_optimization_required"] is True
        assert summary["next_ticket_id"] is None
    assert summary["status"] == "success"


def test_repro_alignment_and_package_version() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t40_closure_feasibility.py" in text
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
