import json
from pathlib import Path
import shutil
import subprocess
import sys

import sixbirds_nogo


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _theorem_map(rows: list[dict]) -> dict[str, dict]:
    return {row["theorem_id"]: row for row in rows}


def _claim_map(rows: list[dict]) -> dict[str, dict]:
    return {row["claim_id"]: row for row in rows}


def test_files_exist_and_parse() -> None:
    for rel in [
        "lean/SixBirdsNoGo/BoundedInterfaceNoLadder.lean",
        "lean/SixBirdsNoGo/BoundedInterfaceNoLadderExample.lean",
        "docs/project/lean_corollary_bounded_interface.yaml",
        "results/T29/lean_bounded_interface_corollary_summary.json",
    ]:
        assert Path(rel).exists()
    assert Path("docs/research-log/T29.md").exists()
    assert Path("docs/research-log/T29.md").read_text(encoding="utf-8").strip()
    assert isinstance(_load("docs/project/lean_corollary_bounded_interface.yaml"), dict)


def test_placeholder_free_lean_files() -> None:
    for rel in [
        "lean/SixBirdsNoGo/BoundedInterfaceNoLadder.lean",
        "lean/SixBirdsNoGo/BoundedInterfaceNoLadderExample.lean",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_import_coverage() -> None:
    text = Path("lean/SixBirdsNoGo.lean").read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.BoundedInterfaceNoLadder" in text
    assert "import SixBirdsNoGo.BoundedInterfaceNoLadderExample" in text


def test_readiness_atlas_anchors() -> None:
    readiness = _theorem_map(_load("docs/project/readiness_checklist.yaml")["theorems"])
    atlas = _theorem_map(_load("docs/project/theorem_atlas.yaml")["theorems"])
    claims = _claim_map(_load("docs/project/claim_audit_freeze.yaml")["claims"])

    assert readiness["NG_LADDER_BOUNDED_INTERFACE"]["lean_support"]["status"] == "direct"
    assert atlas["NG_LADDER_BOUNDED_INTERFACE"]["support_snapshot"]["lean_support"]["status"] == "direct"
    assert claims["NG_LADDER_BOUNDED_INTERFACE.core"]["support_grade"] == "direct"
    assert claims["NG_LADDER_BOUNDED_INTERFACE.core"]["blockers"] == []
    assert claims["NG_LADDER_BOUNDED_INTERFACE.core"]["next_ticket"] is None


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t29"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t29_lean_bounded_interface_corollary.py", "--output-dir", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads((out / "lean_bounded_interface_corollary_summary.json").read_text(encoding="utf-8"))
    assert summary["theorem_count"] == 1
    assert summary["lean_direct_total"] == 7
    assert summary["lean_auxiliary_total"] == 1
    assert summary["lean_missing_total"] == 0
    assert summary["bounded_interface_direct"] is True
    assert summary["corollary_formalized"] is True
    assert summary["count_core_retained"] is True
    assert summary["idempotence_bridge_used"] is True
    assert summary["signature_stabilization_formalized"] is True
    assert summary["observed_predicate_stabilization_formalized"] is True
    assert summary["no_ladder_corollary_present"] is True
    assert summary["extension_escape_scoped_outside_theorem"] is True
    assert summary["strong_front_blockers_cleared"] is True
    if shutil.which("lake") is not None:
        assert summary["lake_build_status"] == "passed"
    else:
        assert summary["lake_build_status"] == "skipped_tool_unavailable"
    assert summary["status"] == "success"


def test_repro_alignment() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t29_lean_bounded_interface_corollary.py" in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
