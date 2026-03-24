import json
from pathlib import Path
import subprocess
import sys

import sixbirds_nogo


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _decision_mode() -> str | None:
    p = Path("docs/project/lean_objecthood_tv_feasibility.yaml")
    if not p.exists():
        return None
    return _load(str(p))["decision"]["decision_mode"]


def test_files_exist_and_parse() -> None:
    assert Path("docs/project/lean_probability_scope_charter.yaml").exists()
    assert Path("results/T35/lean_probability_scope_charter_summary.json").exists()
    assert isinstance(_load("docs/project/lean_probability_scope_charter.yaml"), dict)
    assert isinstance(_load("results/T35/lean_probability_scope_charter_summary.json"), dict)


def test_frontier_state_coverage() -> None:
    charter = _load("docs/project/lean_probability_scope_charter.yaml")
    frontier = charter["current_frontier"]
    assert len(frontier["lean_direct_ids"]) == 7
    assert len(frontier["lean_auxiliary_ids"]) == 1
    assert len(frontier["lean_missing_ids"]) == 0
    assert charter["frontier_targets"] == []


def test_allowed_forbidden_coverage() -> None:
    charter = _load("docs/project/lean_probability_scope_charter.yaml")
    ids = {row["foundation_id"] for row in charter["allowed_foundations"]}
    for fid in [
        "FP_MINIMAL_SCALAR_LOG_LAYER",
        "FP_FINITE_DISTRIBUTIONS",
        "FP_DETERMINISTIC_PUSHFORWARD",
        "FP_FIXED_HORIZON_PATH_LAWS",
        "FP_PATH_REVERSAL",
        "FP_FINITE_KL",
        "FP_DETERMINISTIC_DPI",
        "FP_FINITE_MACRO_KERNEL_OBJECTS",
        "FP_FINITE_VARIATIONAL_OBJECTIVES",
        "FP_OBJECTHOOD_METRIC_REVISIT",
    ]:
        assert fid in ids
    forbidden = {row["foundation_id"] for row in charter["forbidden_foundations"]}
    for fid in [
        "FG_MEASURE_THEORY",
        "FG_PROBABILITY_MONAD",
        "FG_GENERIC_CHANNEL_DPI",
        "FG_GENERIC_INFORMATION_LIBRARY",
        "FG_GENERIC_OPTIMIZATION_LIBRARY",
        "FG_BROAD_METRIC_LIBRARY",
        "FG_UNRELATED_GRAPH_LIBRARY",
        "FG_UNUSED_FOUNDATIONS",
    ]:
        assert fid in forbidden
    for row in charter["allowed_foundations"]:
        assert row["theorem_consumers"]


def test_sequence_coverage() -> None:
    charter = _load("docs/project/lean_probability_scope_charter.yaml")
    milestones = charter["milestone_sequence"]
    ids = [row["ticket_id"] for row in milestones]
    assert ids == [f"T{i}" for i in range(36, 45)]
    dep_map = {row["ticket_id"]: row["depends_on"] for row in milestones}
    assert dep_map["T37"] == ["T36"]
    assert dep_map["T38"] == ["T37"]
    assert dep_map["T39"] == ["T38"]
    assert dep_map["T40"] == ["T39"]
    assert dep_map["T43"] == ["T42"]
    assert charter["frontier_targets"] == []
    assert "bounded" in charter["current_frontier"]["note"].lower()


def test_runner_smoke(tmp_path) -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/run_t35_scope_charter.py", "--output-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((tmp_path / "lean_probability_scope_charter_summary.json").read_text(encoding="utf-8"))
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["frontier_target_count"] == 0
    assert summary["allowed_foundation_count"] == 9
    assert summary["deferred_foundation_count"] == 1
    assert summary["milestone_count"] == 9
    assert summary["dpi_before_protocol"] is True
    assert summary["closure_before_objecthood"] is True
    assert summary["charter_fixed"] is True
    assert summary["status"] == "success"


def test_repro_alignment() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t35_scope_charter.py" in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
