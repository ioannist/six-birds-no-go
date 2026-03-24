import json
from pathlib import Path
import shutil
import subprocess
import sys

import sixbirds_nogo


def test_files_exist_and_parse() -> None:
    for rel in [
        "lean/SixBirdsNoGo/FiniteProbabilityCore.lean",
        "lean/SixBirdsNoGo/FiniteProbabilityCoreExample.lean",
        "docs/project/lean_probability_core.yaml",
        "results/T36/lean_probability_core_summary.json",
    ]:
        assert Path(rel).exists(), rel

    data = json.loads(Path("docs/project/lean_probability_core.yaml").read_text(encoding="utf-8"))
    assert data["version"] == "T36"


def test_new_lean_files_are_placeholder_free() -> None:
    for rel in [
        "lean/SixBirdsNoGo/FiniteProbabilityCore.lean",
        "lean/SixBirdsNoGo/FiniteProbabilityCoreExample.lean",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_root_imports_present() -> None:
    text = Path("lean/SixBirdsNoGo.lean").read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.FiniteProbabilityCore" in text
    assert "import SixBirdsNoGo.FiniteProbabilityCoreExample" in text


def test_frontier_status_and_formalization_summary() -> None:
    summary = json.loads(Path("results/T36/lean_probability_core_summary.json").read_text(encoding="utf-8"))
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["implemented_foundation_count"] == 3
    assert summary["pending_foundation_count"] == 0
    assert summary["no_theorem_status_drift"] is True
    assert summary["finite_distributions_formalized"] is True
    assert summary["deterministic_pushforward_formalized"] is True
    assert summary["marginals_formalized"] is True
    assert summary["fixed_horizon_path_laws_formalized"] is True


def test_runner_smoke(tmp_path) -> None:
    out_dir = tmp_path / "t36"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t36_lean_probability_core.py", "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary_path = out_dir / "lean_probability_core_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["implemented_foundation_count"] == 3
    assert summary["pending_foundation_count"] == 0
    assert summary["finite_distributions_formalized"] is True
    assert summary["deterministic_pushforward_formalized"] is True
    assert summary["marginals_formalized"] is True
    assert summary["fixed_horizon_path_laws_formalized"] is True
    assert summary["no_theorem_status_drift"] is True
    assert summary["status"] == "success"
    expected_lake = "passed" if shutil.which("lake") else "skipped_tool_unavailable"
    assert summary["lake_build_status"] == expected_lake


def test_repro_alignment_and_package_version() -> None:
    repro_text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t36_lean_probability_core.py" in repro_text
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
