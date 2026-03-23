import json
from pathlib import Path
import subprocess
import sys

import sixbirds_nogo


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _t44_outcome() -> str | None:
    p = Path("results/T44/lean_objecthood_direct_pack_summary.json")
    if not p.exists():
        return None
    return _load(str(p))["outcome_mode"]


def test_file_existence_and_parse() -> None:
    assert Path("docs/project/theorem_atlas.yaml").exists()
    assert Path("docs/project/claim_audit_freeze.yaml").exists()

    atlas = _load("docs/project/theorem_atlas.yaml")
    theorems = _load("configs/theorems.yaml")

    atlas_ids = sorted(t["theorem_id"] for t in atlas["theorems"])
    theorem_ids = sorted(t["id"] for t in theorems["theorems"])
    assert atlas_ids == theorem_ids


def test_atlas_schema_coverage() -> None:
    atlas = _load("docs/project/theorem_atlas.yaml")
    for t in atlas["theorems"]:
        for key in [
            "theorem_statement",
            "theorem_schema",
            "assumption_refs",
            "dependency_refs",
            "support_snapshot",
            "evidence_handles",
            "blockers",
            "next_ticket",
        ]:
            assert key in t


def test_support_snapshot_alignment_anchors() -> None:
    atlas = _load("docs/project/theorem_atlas.yaml")
    tmap = {t["theorem_id"]: t for t in atlas["theorems"]}

    for t in tmap.values():
        assert t["support_snapshot"]["computational_support"]["status"] == "present"
        assert t["support_snapshot"]["witness_coverage"]["status"] == "covered"

    assert tmap["NG_LADDER_IDEM"]["support_snapshot"]["analytic_support"]["status"] == "present"
    assert tmap["NG_LADDER_IDEM"]["support_snapshot"]["lean_support"]["status"] == "direct"

    assert tmap["NG_FORCE_FOREST"]["support_snapshot"]["lean_support"]["status"] == "direct"
    assert tmap["NG_FORCE_NULL"]["support_snapshot"]["lean_support"]["status"] == "direct"
    assert tmap["NG_LADDER_BOUNDED_INTERFACE"]["support_snapshot"]["lean_support"]["status"] == "direct"
    assert tmap["NG_ARROW_DPI"]["support_snapshot"]["lean_support"]["status"] == "direct"
    assert tmap["NG_PROTOCOL_TRAP"]["support_snapshot"]["lean_support"]["status"] == "direct"
    assert tmap["NG_MACRO_CLOSURE_DEFICIT"]["support_snapshot"]["lean_support"]["status"] == "direct"

    assert tmap["NG_ARROW_DPI"]["support_snapshot"]["proxy_risk"]["status"] == "high"
    assert tmap["NG_OBJECT_CONTRACTIVE"]["support_snapshot"]["proxy_risk"]["status"] == "high"
    expected_objecthood = "direct" if _t44_outcome() == "direct_theorem_pack" else "auxiliary_only"
    assert tmap["NG_OBJECT_CONTRACTIVE"]["support_snapshot"]["lean_support"]["status"] == expected_objecthood
    assert "lean/SixBirdsNoGo/ContractionUniqueness.lean" in tmap["NG_OBJECT_CONTRACTIVE"]["dependency_refs"]["lean_refs"]
    assert "docs/project/lean_objecthood_uniqueness.yaml" in tmap["NG_OBJECT_CONTRACTIVE"]["evidence_handles"]["lean"]
    assert "docs/project/lean_objecthood_formal_boundary.md" in tmap["NG_OBJECT_CONTRACTIVE"]["evidence_handles"]["lean"]
    assert "results/T30/lean_objecthood_uniqueness_summary.json" in tmap["NG_OBJECT_CONTRACTIVE"]["evidence_handles"]["lean"]


def test_claim_audit_anchor_coverage() -> None:
    claims = _load("docs/project/claim_audit_freeze.yaml")
    c = {x["claim_id"]: x for x in claims["claims"]}

    core_ids = {
        "NG_ARROW_DPI.core",
        "NG_PROTOCOL_TRAP.core",
        "NG_FORCE_FOREST.core",
        "NG_FORCE_NULL.core",
        "NG_MACRO_CLOSURE_DEFICIT.core",
        "NG_OBJECT_CONTRACTIVE.core",
        "NG_LADDER_IDEM.core",
        "NG_LADDER_BOUNDED_INTERFACE.core",
    }
    assert core_ids.issubset(set(c.keys()))

    assert c["NG_LADDER_IDEM.core"]["freeze_status"] == "frozen"
    assert c["NG_LADDER_IDEM.core"]["support_grade"] == "direct"

    assert c["NG_ARROW_DPI.core"]["freeze_status"] == "frozen"
    assert c["NG_ARROW_DPI.core"]["support_grade"] == "direct"
    assert c["NG_PROTOCOL_TRAP.core"]["support_grade"] == "direct"
    assert c["NG_MACRO_CLOSURE_DEFICIT.core"]["support_grade"] == "direct"
    assert c["NG_OBJECT_CONTRACTIVE.core"]["support_grade"] == "direct"
    assert c["NG_LADDER_BOUNDED_INTERFACE.core"]["support_grade"] == "direct"
    assert c["NG_LADDER_BOUNDED_INTERFACE.guardrail"]["freeze_status"] == "frozen"
    assert c["NG_LADDER_BOUNDED_INTERFACE.guardrail"]["support_grade"] == "direct"
    assert c["NG_LADDER_BOUNDED_INTERFACE.core"]["blockers"] == []
    assert c["NG_LADDER_BOUNDED_INTERFACE.core"]["next_ticket"] is None
    if _t44_outcome() == "direct_theorem_pack":
        assert c["NG_OBJECT_CONTRACTIVE.core"]["next_ticket"]["id"] == "PLAN_NEXT_20_objecthood_scope_guardrail_hold"
    else:
        assert c["NG_OBJECT_CONTRACTIVE.core"]["blockers"] == []
        assert c["NG_OBJECT_CONTRACTIVE.core"]["next_ticket"] is None

    for tid in [
        "NG_ARROW_DPI",
        "NG_PROTOCOL_TRAP",
        "NG_FORCE_FOREST",
        "NG_FORCE_NULL",
        "NG_MACRO_CLOSURE_DEFICIT",
        "NG_OBJECT_CONTRACTIVE",
    ]:
        assert f"{tid}.guardrail" in c

    g1 = c["NG_MACRO_CLOSURE_DEFICIT.primitive_attribution_gap"]
    assert g1["freeze_status"] != "blocked"
    txt1 = (g1["claim_text"] + " " + g1["note"]).lower()
    assert "resolv" in txt1

    g2 = c["NG_OBJECT_CONTRACTIVE.metric_regime_gap"]
    assert g2["freeze_status"] != "blocked"
    txt2 = (g2["claim_text"] + " " + g2["note"]).lower()
    assert "resolv" in txt2


def test_counts_structure_coverage() -> None:
    claims = _load("docs/project/claim_audit_freeze.yaml")
    claim_count = len(claims["claims"])
    frozen = sum(1 for x in claims["claims"] if x["freeze_status"] == "frozen")
    blocked = sum(1 for x in claims["claims"] if x["freeze_status"] == "blocked")

    assert claim_count >= 16
    assert frozen >= 14
    assert blocked == 0


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t21"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t21_theorem_atlas.py", "--output-dir", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    summary_path = out / "theorem_atlas_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["theorem_count"] == 8
    assert summary["claim_count"] >= 16
    assert summary["blocked_claim_count"] == 0
    assert summary["status"] == "success"


def test_repro_alignment_coverage() -> None:
    text = Path("src/sixbirds_nogo/repro.py").read_text(encoding="utf-8")
    assert "run_t20_readiness_checkpoint.py" in text
    assert "run_t21_theorem_atlas.py" in text

    atlas = _load("docs/project/theorem_atlas.yaml")
    if atlas["source_context"]["vision_present"] is True:
        assert Path("vision.md").exists()
        if Path(".package-repo-snapshot.json").exists():
            snap = _load(".package-repo-snapshot.json")
            assert "vision.md" in snap.get("allowed_root_files", [])


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
