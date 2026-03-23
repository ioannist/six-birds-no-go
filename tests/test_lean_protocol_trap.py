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
        "lean/SixBirdsNoGo/ProtocolTrap.lean",
        "lean/SixBirdsNoGo/ProtocolTrapExample.lean",
        "docs/project/lean_protocol_trap.yaml",
        "results/T39/lean_protocol_trap_summary.json",
    ]:
        assert Path(rel).exists(), rel
    assert isinstance(_load("docs/project/lean_protocol_trap.yaml"), dict)


def test_placeholder_free() -> None:
    for rel in [
        "lean/SixBirdsNoGo/ProtocolTrap.lean",
        "lean/SixBirdsNoGo/ProtocolTrapExample.lean",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_imports_present() -> None:
    text = Path("lean/SixBirdsNoGo.lean").read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.ProtocolTrap" in text
    assert "import SixBirdsNoGo.ProtocolTrapExample" in text


def test_readiness_and_atlas_anchors() -> None:
    readiness = {row["theorem_id"]: row for row in _load("docs/project/readiness_checklist.yaml")["theorems"]}
    atlas = {row["theorem_id"]: row for row in _load("docs/project/theorem_atlas.yaml")["theorems"]}
    assert readiness["NG_PROTOCOL_TRAP"]["lean_support"]["status"] == "direct"
    assert readiness["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] == "direct"
    assert atlas["NG_PROTOCOL_TRAP"]["support_snapshot"]["lean_support"]["status"] == "direct"


def test_runner_smoke(tmp_path) -> None:
    out_dir = tmp_path / "t39"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t39_lean_protocol_trap.py", "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summary = json.loads((out_dir / "lean_protocol_trap_summary.json").read_text(encoding="utf-8"))
    assert summary["theorem_count"] == 1
    assert summary["lean_direct_total"] == 7
    assert summary["lean_auxiliary_total"] == 1
    assert summary["lean_missing_total"] == 0
    assert summary["protocol_direct"] is True
    assert summary["autonomous_lifted_wrapper_present"] is True
    assert summary["stationary_initial_scope_explicit"] is True
    assert summary["stationary_lifted_arrow_dpi_present"] is True
    assert summary["stationary_macro_reversibility_corollary_present"] is True
    assert summary["protocol_no_honest_arrow_wrapper_present"] is True
    assert summary["arrow_dependency_used"] is True
    assert summary["arrow_followup_rebased"] is True
    assert summary["closure_still_missing"] is False
    assert summary["status"] == "success"
    expected_lake = "passed" if shutil.which("lake") else "skipped_tool_unavailable"
    assert summary["lake_build_status"] == expected_lake


def test_repro_alignment_and_package_version() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t39_lean_protocol_trap.py" in text
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
