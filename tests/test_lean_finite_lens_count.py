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


def test_files_exist_and_parse() -> None:
    for rel in [
        "lean/SixBirdsNoGo/FiniteLensDefinability.lean",
        "lean/SixBirdsNoGo/FiniteLensDefinabilityExample.lean",
        "docs/project/lean_count_bounded_interface.yaml",
        "results/T28/lean_finite_lens_count_summary.json",
    ]:
        assert Path(rel).exists()
    assert isinstance(_load("docs/project/lean_count_bounded_interface.yaml"), dict)


def test_placeholder_free_lean_files() -> None:
    for rel in [
        "lean/SixBirdsNoGo/FiniteLensDefinability.lean",
        "lean/SixBirdsNoGo/FiniteLensDefinabilityExample.lean",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_import_coverage() -> None:
    text = Path("lean/SixBirdsNoGo.lean").read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.FiniteLensDefinability" in text
    assert "import SixBirdsNoGo.FiniteLensDefinabilityExample" in text


def test_readiness_atlas_anchors() -> None:
    readiness = _theorem_map(_load("docs/project/readiness_checklist.yaml")["theorems"])
    atlas = _theorem_map(_load("docs/project/theorem_atlas.yaml")["theorems"])
    assert readiness["NG_LADDER_BOUNDED_INTERFACE"]["lean_support"]["status"] == "direct"
    assert atlas["NG_LADDER_BOUNDED_INTERFACE"]["support_snapshot"]["lean_support"]["status"] == "direct"


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t28"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t28_lean_finite_lens_count.py", "--output-dir", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads((out / "lean_finite_lens_count_summary.json").read_text(encoding="utf-8"))
    assert summary["theorem_count"] == 1
    assert summary["lean_direct_total"] == 7
    assert summary["lean_auxiliary_total"] == 1
    assert summary["lean_missing_total"] == 0
    assert summary["counting_core_formalized"] is True
    assert summary["assignment_family_count_eq_two_pow"] is True
    assert summary["surjective_lens_equiv_explicit"] is True
    assert summary["bounded_interface_still_auxiliary"] is False
    assert summary["full_corollary_pending"] is False
    if shutil.which("lake") is not None:
        assert summary["lake_build_status"] == "passed"
    else:
        assert summary["lake_build_status"] == "skipped_tool_unavailable"
    assert summary["status"] == "success"


def test_repro_alignment() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t28_lean_finite_lens_count.py" in text


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
