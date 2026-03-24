import json
from pathlib import Path
import shutil
import subprocess
import sys

import sixbirds_nogo


def test_files_exist_and_parse() -> None:
    for rel in [
        "lean/SixBirdsNoGo/FiniteKLDPI.lean",
        "lean/SixBirdsNoGo/FiniteKLDPIExample.lean",
        "docs/project/lean_kl_dpi_core.yaml",
        "results/T37/lean_kl_dpi_core_summary.json",
    ]:
        assert Path(rel).exists(), rel
    data = json.loads(Path("docs/project/lean_kl_dpi_core.yaml").read_text(encoding="utf-8"))
    assert data["version"] == "T37"


def test_lean_files_placeholder_free() -> None:
    for rel in [
        "lean/SixBirdsNoGo/FiniteKLDPI.lean",
        "lean/SixBirdsNoGo/FiniteKLDPIExample.lean",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_imports_present() -> None:
    text = Path("lean/SixBirdsNoGo.lean").read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.FiniteKLDPI" in text
    assert "import SixBirdsNoGo.FiniteKLDPIExample" in text


def test_summary_anchors() -> None:
    summary = json.loads(Path("results/T37/lean_kl_dpi_core_summary.json").read_text(encoding="utf-8"))
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["total_formalized_foundation_count"] == 9
    assert summary["implemented_foundation_count"] == 4
    assert summary["pending_foundation_count"] == 0
    assert summary["no_theorem_status_drift"] is True
    assert summary["scalar_log_layer_explicit"] is True
    assert summary["path_reversal_formalized"] is True
    assert summary["finite_kl_formalized"] is True
    assert summary["deterministic_dpi_formalized"] is True
    assert summary["reusable_finite_dpi_engine"] is True


def test_runner_smoke(tmp_path) -> None:
    out_dir = tmp_path / "t37"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t37_lean_kl_dpi_core.py", "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((out_dir / "lean_kl_dpi_core_summary.json").read_text(encoding="utf-8"))
    assert summary["direct_front_count"] == 7
    assert summary["auxiliary_front_count"] == 1
    assert summary["missing_front_count"] == 0
    assert summary["total_formalized_foundation_count"] == 9
    assert summary["implemented_foundation_count"] == 4
    assert summary["pending_foundation_count"] == 0
    assert summary["scalar_log_layer_explicit"] is True
    assert summary["path_reversal_formalized"] is True
    assert summary["finite_kl_formalized"] is True
    assert summary["deterministic_dpi_formalized"] is True
    assert summary["reusable_finite_dpi_engine"] is True
    assert summary["no_theorem_status_drift"] is True
    assert summary["status"] == "success"
    expected_lake = "passed" if shutil.which("lake") else "skipped_tool_unavailable"
    assert summary["lake_build_status"] == expected_lake


def test_repro_alignment_and_package_version() -> None:
    repro_text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t37_lean_kl_dpi_core.py" in repro_text
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
