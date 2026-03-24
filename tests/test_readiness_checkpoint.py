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
    readiness_path = Path("docs/project/readiness_checklist.yaml")
    assert readiness_path.exists()

    readiness = _load("docs/project/readiness_checklist.yaml")
    theorems = _load("configs/theorems.yaml")

    ready_ids = sorted(t["theorem_id"] for t in readiness["theorems"])
    theorem_ids = sorted(t["id"] for t in theorems["theorems"])
    assert ready_ids == theorem_ids


def test_schema_coverage() -> None:
    readiness = _load("docs/project/readiness_checklist.yaml")

    for t in readiness["theorems"]:
        for key in [
            "analytic_support",
            "computational_support",
            "lean_support",
            "witness_coverage",
            "proxy_risk",
            "blockers",
            "next_ticket",
        ]:
            assert key in t

        for key in ["analytic_support", "computational_support", "lean_support", "witness_coverage", "proxy_risk"]:
            obj = t[key]
            assert "status" in obj
            assert "evidence" in obj
            assert "note" in obj


def test_current_state_anchors() -> None:
    readiness = _load("docs/project/readiness_checklist.yaml")
    tmap = {t["theorem_id"]: t for t in readiness["theorems"]}

    for t in tmap.values():
        assert t["computational_support"]["status"] == "present"
        assert t["witness_coverage"]["status"] == "covered"

    lean_direct = sum(1 for t in tmap.values() if t["lean_support"]["status"] == "direct")
    lean_aux = sum(1 for t in tmap.values() if t["lean_support"]["status"] == "auxiliary_only")
    lean_missing = sum(1 for t in tmap.values() if t["lean_support"]["status"] == "missing")
    outcome = _t44_outcome()
    assert lean_direct == (8 if outcome == "direct_theorem_pack" else 7)
    assert lean_aux == (0 if outcome == "direct_theorem_pack" else 1)
    assert lean_missing == 0

    assert tmap["NG_LADDER_IDEM"]["lean_support"]["status"] == "direct"
    assert tmap["NG_FORCE_FOREST"]["lean_support"]["status"] == "direct"
    assert tmap["NG_FORCE_NULL"]["lean_support"]["status"] == "direct"
    assert tmap["NG_LADDER_BOUNDED_INTERFACE"]["lean_support"]["status"] == "direct"
    assert tmap["NG_ARROW_DPI"]["lean_support"]["status"] == "direct"
    assert tmap["NG_PROTOCOL_TRAP"]["lean_support"]["status"] == "direct"

    assert tmap["NG_ARROW_DPI"]["proxy_risk"]["status"] == "high"
    assert tmap["NG_OBJECT_CONTRACTIVE"]["proxy_risk"]["status"] == "high"
    expected_objecthood = "direct" if outcome == "direct_theorem_pack" else "auxiliary_only"
    assert tmap["NG_OBJECT_CONTRACTIVE"]["lean_support"]["status"] == expected_objecthood
    assert tmap["NG_OBJECT_CONTRACTIVE"]["analytic_support"]["status"] == "present"
    obj_evidence = tmap["NG_OBJECT_CONTRACTIVE"]["lean_support"]["evidence"]
    assert "lean/SixBirdsNoGo/ContractionUniqueness.lean" in obj_evidence
    assert "lean/SixBirdsNoGo/ContractionUniquenessExample.lean" in obj_evidence
    assert "docs/project/lean_objecthood_uniqueness.yaml" in obj_evidence
    assert tmap["NG_LADDER_BOUNDED_INTERFACE"]["analytic_support"]["status"] == "present"
    assert tmap["NG_LADDER_BOUNDED_INTERFACE"]["lean_support"]["status"] == "direct"

    assert tmap["NG_MACRO_CLOSURE_DEFICIT"]["analytic_support"]["status"] == "present"
    assert tmap["NG_MACRO_CLOSURE_DEFICIT"]["proxy_risk"]["status"] == "medium"
    assert tmap["NG_MACRO_CLOSURE_DEFICIT"]["lean_support"]["status"] == "direct"

    if outcome == "direct_theorem_pack":
        object_blockers = " ".join(tmap["NG_OBJECT_CONTRACTIVE"]["blockers"]).lower()
        assert "scope" in object_blockers or "proxy" in object_blockers
    else:
        assert tmap["NG_OBJECT_CONTRACTIVE"]["blockers"] == []


def test_missing_piece_next_step_rule() -> None:
    readiness = _load("docs/project/readiness_checklist.yaml")
    outcome = _t44_outcome()

    for t in readiness["theorems"]:
        incomplete = (
            t["analytic_support"]["status"] != "present"
            or t["lean_support"]["status"] != "direct"
            or t["proxy_risk"]["status"] != "low"
        )
        if incomplete:
            explicit_boundary = (
                outcome != "direct_theorem_pack"
                and t["theorem_id"] == "NG_OBJECT_CONTRACTIVE"
                and t["lean_support"]["status"] == "auxiliary_only"
                and t["blockers"] == []
                and t["next_ticket"] is None
            )
            if explicit_boundary:
                continue
            assert t["blockers"]
            assert t["next_ticket"] is not None
            assert t["next_ticket"]["id"]
            assert t["next_ticket"]["action"]


def test_strong_theorem_allowance() -> None:
    readiness = _load("docs/project/readiness_checklist.yaml")
    for tid in ["NG_LADDER_IDEM", "NG_LADDER_BOUNDED_INTERFACE"]:
        t = {x["theorem_id"]: x for x in readiness["theorems"]}[tid]

        if (
            t["analytic_support"]["status"] == "present"
            and t["computational_support"]["status"] == "present"
            and t["lean_support"]["status"] == "direct"
            and t["witness_coverage"]["status"] == "covered"
            and t["proxy_risk"]["status"] == "low"
        ):
            assert t["blockers"] == []
            assert t["next_ticket"] is None


def test_runner_smoke() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/run_t20_readiness_checkpoint.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_package_version_alias() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__
