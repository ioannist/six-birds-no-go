"""Check that current coverage uses fresh checked targets, not legacy labels."""

import hashlib
import json
from pathlib import Path


def test_current_proof_receipt_covers_all_theorem_targets():
    receipt = json.loads(Path("review/current-theorem-coverage.json").read_text())
    registry = json.loads(Path("configs/theorems.yaml").read_text())
    assert receipt["status"] == "passed"
    assert {r["theorem_id"] for r in receipt["theorems"]} == {r["id"] for r in registry["theorems"]}
    assert all(r["status"] == "direct" for r in receipt["theorems"])
    assert all(v == "passed" for v in receipt["verification"].values())
    for row in receipt["theorems"]:
        assert all(name in receipt["axioms"] for name in row["declarations"])
    assert all(set(a) <= {"propext", "Classical.choice", "Quot.sound"}
               for a in receipt["axioms"].values())
    for path, digest in receipt["source_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, f"Stale proof receipt: {path}"


def test_historical_schema_checks_are_not_proof_certificates():
    for path in ("docs/project/readiness_checklist.yaml", "docs/project/theorem_atlas.yaml",
                 "docs/project/lean_closure_direct.yaml", "docs/project/lean_objecthood_direct.yaml"):
        record = json.loads(Path(path).read_text())
        assert record["mathematical_proof_certificate"] is False
        assert record["superseded_by"] == "review/current-theorem-coverage.json"
