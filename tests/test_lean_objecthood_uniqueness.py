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


def _branch_a() -> bool:
    return Path("lean/SixBirdsNoGo/ContractionUniqueness.lean").exists()


def _t43_decision() -> str | None:
    p = Path("docs/project/lean_objecthood_tv_feasibility.yaml")
    if not p.exists():
        return None
    return _load(str(p))["decision"]["decision_mode"]


def _t44_outcome() -> str | None:
    p = Path("results/T44/lean_objecthood_direct_pack_summary.json")
    if not p.exists():
        return None
    return _load(str(p))["outcome_mode"]


def test_files_exist_and_parse() -> None:
    for rel in [
        "docs/project/lean_objecthood_uniqueness.yaml",
        "docs/project/lean_objecthood_formal_boundary.md",
        "results/T30/lean_objecthood_uniqueness_summary.json",
    ]:
        assert Path(rel).exists()
    assert Path("docs/research-log/T29.md").exists()
    assert Path("docs/research-log/T29.md").read_text(encoding="utf-8").strip()
    assert isinstance(_load("docs/project/lean_objecthood_uniqueness.yaml"), dict)


def test_placeholder_free_lean_files_if_present() -> None:
    if not _branch_a():
        return
    for rel in [
        "lean/SixBirdsNoGo/ContractionUniqueness.lean",
        "lean/SixBirdsNoGo/ContractionUniquenessExample.lean",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_readiness_atlas_branch_sensitive_anchors() -> None:
    readiness = _theorem_map(_load("docs/project/readiness_checklist.yaml")["theorems"])
    atlas = _theorem_map(_load("docs/project/theorem_atlas.yaml")["theorems"])

    if _branch_a():
        assert readiness["NG_OBJECT_CONTRACTIVE"]["lean_support"]["status"] == "auxiliary_only"
        assert atlas["NG_OBJECT_CONTRACTIVE"]["support_snapshot"]["lean_support"]["status"] == "auxiliary_only"
    else:
        assert readiness["NG_OBJECT_CONTRACTIVE"]["lean_support"]["status"] == "missing"
        assert atlas["NG_OBJECT_CONTRACTIVE"]["support_snapshot"]["lean_support"]["status"] == "missing"


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t30"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t30_lean_objecthood_uniqueness.py", "--output-dir", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary = json.loads((out / "lean_objecthood_uniqueness_summary.json").read_text(encoding="utf-8"))
    assert summary["theorem_count"] == 1
    assert summary["outcome_mode"] in {"direct_uniqueness_theorem", "formal_boundary_note"}
    assert summary["formal_boundary_note_present"] is True
    assert summary["formal_boundary_frozen"] is True
    if summary["outcome_mode"] == "direct_uniqueness_theorem":
        outcome = _t44_outcome()
        assert summary["lean_direct_total"] == (8 if outcome == "direct_theorem_pack" else 7)
        assert summary["lean_auxiliary_total"] == (0 if outcome == "direct_theorem_pack" else 1)
        assert summary["lean_missing_total"] == 0
        assert summary["direct_uniqueness_theorem_present"] is True
        assert summary["objecthood_lean_status_after"] == ("direct" if outcome == "direct_theorem_pack" else "auxiliary_only")
        assert summary["strict_contraction_on_ne_explicit"] is True
        assert summary["at_most_one_fixed_point_formalized"] is True
        assert summary["discrete_model_example_present"] is True
        assert summary["full_tv_bound_bridge_pending"] is False
    else:
        assert summary["lean_direct_total"] == 4
        assert summary["lean_auxiliary_total"] == 0
        assert summary["lean_missing_total"] == 4
        assert summary["direct_uniqueness_theorem_present"] is False
        assert summary["objecthood_lean_status_after"] == "missing"
        assert summary["strict_contraction_on_ne_explicit"] is False
        assert summary["at_most_one_fixed_point_formalized"] is False
        assert summary["discrete_model_example_present"] is False
        assert summary["full_tv_bound_bridge_pending"] is False

    if shutil.which("lake") is not None:
        assert summary["lake_build_status"] == "passed"
    else:
        assert summary["lake_build_status"] == "skipped_tool_unavailable"
    assert summary["reproduce_includes_t30"] is True
    assert summary["reproduce_includes_t29"] is True
    assert summary["status"] == "success"


def test_repro_alignment() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t30_lean_objecthood_uniqueness.py" in text


def test_t43_rebase_consistency() -> None:
    uniq = _load("docs/project/lean_objecthood_uniqueness.yaml")["theorem_fronts"][0]
    assert uniq["readiness_delta"]["full_tv_bound_bridge_pending"] is False
    assert uniq["next_ticket"] is None


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
