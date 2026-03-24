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
        "lean/SixBirdsNoGo/ArrowDPI.lean",
        "lean/SixBirdsNoGo/ArrowDPIExample.lean",
        "docs/project/lean_arrow_dpi.yaml",
        "results/T38/lean_arrow_dpi_summary.json",
    ]:
        assert Path(rel).exists(), rel
    assert isinstance(_load("docs/project/lean_arrow_dpi.yaml"), dict)


def test_placeholder_free() -> None:
    for rel in [
        "lean/SixBirdsNoGo/ArrowDPI.lean",
        "lean/SixBirdsNoGo/ArrowDPIExample.lean",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_imports_present() -> None:
    text = Path("lean/SixBirdsNoGo.lean").read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.ArrowDPI" in text
    assert "import SixBirdsNoGo.ArrowDPIExample" in text


def test_readiness_and_atlas_anchors() -> None:
    readiness = {row["theorem_id"]: row for row in _load("docs/project/readiness_checklist.yaml")["theorems"]}
    atlas = {row["theorem_id"]: row for row in _load("docs/project/theorem_atlas.yaml")["theorems"]}
    assert readiness["NG_ARROW_DPI"]["lean_support"]["status"] == "direct"
    assert readiness["NG_PROTOCOL_TRAP"]["lean_support"]["status"] == "direct"
    assert atlas["NG_ARROW_DPI"]["support_snapshot"]["lean_support"]["status"] == "direct"


def test_runner_smoke(tmp_path) -> None:
    out_dir = tmp_path / "t38"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t38_lean_arrow_dpi.py", "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((out_dir / "lean_arrow_dpi_summary.json").read_text(encoding="utf-8"))
    assert summary["theorem_count"] == 1
    assert summary["lean_direct_total"] == 7
    assert summary["lean_auxiliary_total"] == 1
    assert summary["lean_missing_total"] == 0
    assert summary["arrow_direct"] is True
    assert summary["deterministic_pathlaw_dpi_present"] is True
    assert summary["reverse_pushforward_commutation_present"] is True
    assert summary["equality_form_zero_arrow_corollary_present"] is True
    assert summary["honest_observation_scope_frozen"] is True
    assert summary["protocol_still_missing"] is False
    assert summary["baseline_build_passed"] is True
    assert summary["status"] == "success"
    expected_lake = "passed" if shutil.which("lake") else "skipped_tool_unavailable"
    assert summary["lake_build_status"] == expected_lake


def test_repro_alignment_and_package_version() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t38_lean_arrow_dpi.py" in text
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
