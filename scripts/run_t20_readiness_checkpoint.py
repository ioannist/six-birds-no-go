#!/usr/bin/env python3
"""Validate T20 readiness checklist structure and consistency."""

from __future__ import annotations

import json
from pathlib import Path
import sys


CHECKLIST_PATH = Path("docs/project/readiness_checklist.yaml")
THEOREMS_PATH = Path("configs/theorems.yaml")


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _fail(f"cannot parse JSON from {path}: {exc}")
    if not isinstance(data, dict):
        _fail(f"{path} must parse to an object")
    return data


def main() -> int:
    if not CHECKLIST_PATH.exists():
        _fail(f"missing {CHECKLIST_PATH}")
    if not THEOREMS_PATH.exists():
        _fail(f"missing {THEOREMS_PATH}")

    checklist = _load_json(CHECKLIST_PATH)
    theorem_cfg = _load_json(THEOREMS_PATH)

    top_required = {"version", "generated_at_utc", "source_context", "status_enums", "theorems"}
    missing_top = sorted(top_required - set(checklist.keys()))
    if missing_top:
        _fail(f"missing top-level keys: {missing_top}")

    src = checklist["source_context"]
    if not isinstance(src, dict):
        _fail("source_context must be an object")

    for key in ["theorem_registry", "master_manifest", "primitive_coverage", "fragility_summary", "lean_files", "vision_present"]:
        if key not in src:
            _fail(f"source_context missing key: {key}")

    # source context path checks
    for path_key in ["theorem_registry", "master_manifest", "primitive_coverage", "fragility_summary"]:
        p = Path(src[path_key])
        if not p.exists():
            _fail(f"source_context file missing: {p}")

    lean_files = src["lean_files"]
    if not isinstance(lean_files, list) or not lean_files:
        _fail("source_context.lean_files must be a non-empty list")
    for rel in lean_files:
        if not Path(rel).exists():
            _fail(f"lean evidence file missing: {rel}")

    vision_present_runtime = Path("vision.md").exists()
    if bool(src["vision_present"]) != vision_present_runtime:
        _fail("vision_present does not match runtime repo state")
    if vision_present_runtime:
        if src.get("vision_path") != "vision.md":
            _fail("vision_path must be 'vision.md' when vision_present is true")
    else:
        if "vision_path" in src and src["vision_path"] is not None:
            _fail("vision_path must be null/omitted when vision_present is false")

    enums = checklist["status_enums"]
    required_enums = {
        "analytic_support": ["present", "partial", "missing"],
        "computational_support": ["present", "partial", "missing"],
        "lean_support": ["direct", "auxiliary_only", "missing"],
        "witness_coverage": ["covered", "partial", "missing"],
        "proxy_risk": ["low", "medium", "high"],
    }
    if enums != required_enums:
        _fail("status_enums does not match required enum sets")

    theorem_items = theorem_cfg.get("theorems")
    if not isinstance(theorem_items, list):
        _fail("configs/theorems.yaml missing theorem list")
    theorem_ids = [t["id"] for t in theorem_items if isinstance(t, dict) and isinstance(t.get("id"), str)]

    entries = checklist["theorems"]
    if not isinstance(entries, list):
        _fail("theorems must be a list")

    entry_ids = [e.get("theorem_id") for e in entries if isinstance(e, dict)]
    if sorted(entry_ids) != sorted(theorem_ids) or len(entry_ids) != len(set(entry_ids)):
        _fail("readiness theorem IDs must match configs/theorems.yaml exactly once")

    support_keys = ["analytic_support", "computational_support", "lean_support", "witness_coverage", "proxy_risk"]
    for e in entries:
        if not isinstance(e, dict):
            _fail("theorem entry must be object")

        for k in ["theorem_id", "short_name", *support_keys, "blockers", "next_ticket"]:
            if k not in e:
                _fail(f"theorem entry missing key: {k}")

        for sk in support_keys:
            v = e[sk]
            if not isinstance(v, dict):
                _fail(f"{e['theorem_id']}:{sk} must be object")
            for req in ["status", "evidence", "note"]:
                if req not in v:
                    _fail(f"{e['theorem_id']}:{sk} missing {req}")
            if not isinstance(v["evidence"], list):
                _fail(f"{e['theorem_id']}:{sk}.evidence must be list")
            if not isinstance(v["note"], str) or not v["note"].strip():
                _fail(f"{e['theorem_id']}:{sk}.note must be non-empty")
            if "placeholder" in v["note"].lower() or "tbd" in v["note"].lower():
                _fail(f"{e['theorem_id']}:{sk}.note contains placeholder text")

        # enum checks
        if e["analytic_support"]["status"] not in required_enums["analytic_support"]:
            _fail(f"invalid analytic_support status for {e['theorem_id']}")
        if e["computational_support"]["status"] not in required_enums["computational_support"]:
            _fail(f"invalid computational_support status for {e['theorem_id']}")
        if e["lean_support"]["status"] not in required_enums["lean_support"]:
            _fail(f"invalid lean_support status for {e['theorem_id']}")
        if e["witness_coverage"]["status"] not in required_enums["witness_coverage"]:
            _fail(f"invalid witness_coverage status for {e['theorem_id']}")
        if e["proxy_risk"]["status"] not in required_enums["proxy_risk"]:
            _fail(f"invalid proxy_risk status for {e['theorem_id']}")

        blockers = e["blockers"]
        if not isinstance(blockers, list):
            _fail(f"{e['theorem_id']}:blockers must be list")

        nxt = e["next_ticket"]
        if nxt is not None:
            if not isinstance(nxt, dict):
                _fail(f"{e['theorem_id']}:next_ticket must be object or null")
            if not isinstance(nxt.get("id"), str) or not nxt["id"].strip():
                _fail(f"{e['theorem_id']}:next_ticket.id missing")
            if not isinstance(nxt.get("action"), str) or not nxt["action"].strip():
                _fail(f"{e['theorem_id']}:next_ticket.action missing")

        # missing-piece rule
        incompleteness = (
            e["analytic_support"]["status"] != "present"
            or e["lean_support"]["status"] != "direct"
            or e["proxy_risk"]["status"] != "low"
            or len(blockers) > 0
        )
        explicit_boundary = (
            e["theorem_id"] == "NG_OBJECT_CONTRACTIVE"
            and e["lean_support"]["status"] == "auxiliary_only"
            and len(blockers) == 0
            and nxt is None
            and "permanent lean boundary" in e["lean_support"]["note"].lower()
        )
        if incompleteness:
            if len(blockers) == 0 and not explicit_boundary:
                _fail(f"{e['theorem_id']}:incomplete theorem must have non-empty blockers")
            if nxt is None and not explicit_boundary:
                _fail(f"{e['theorem_id']}:incomplete theorem must have next_ticket")

        if e["lean_support"]["status"] == "direct" and len(e["lean_support"]["evidence"]) == 0:
            _fail(f"{e['theorem_id']}:direct lean support requires evidence")

    analytic_counts = {k: 0 for k in required_enums["analytic_support"]}
    lean_counts = {k: 0 for k in required_enums["lean_support"]}
    proxy_counts = {k: 0 for k in required_enums["proxy_risk"]}
    for e in entries:
        analytic_counts[e["analytic_support"]["status"]] += 1
        lean_counts[e["lean_support"]["status"]] += 1
        proxy_counts[e["proxy_risk"]["status"]] += 1

    print("PASS: readiness checklist valid")
    print("analytic_support:", analytic_counts)
    print("lean_support:", lean_counts)
    print("proxy_risk:", proxy_counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
