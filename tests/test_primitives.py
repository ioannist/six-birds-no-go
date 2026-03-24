import csv
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import sixbirds_nogo
from sixbirds_nogo.primitives import (
    PRIMITIVE_IDS,
    build_derived_variant_rows,
    build_primitive_matrix,
    evaluate_theorem_coverage,
    load_primitives_config,
    run_primitive_matrix,
)
from sixbirds_nogo.witnesses import list_witness_ids


def _assignment_map(cfg: dict) -> dict[str, dict]:
    return {a["witness_id"]: a for a in cfg["witness_assignments"]}


def _theorem_map(coverage: dict) -> dict[str, dict]:
    return {t["theorem_id"]: t for t in coverage["theorem_targets"]}


def test_config_schema_and_assignment_coverage() -> None:
    cfg = load_primitives_config()

    assert [p["id"] for p in cfg["primitive_registry"]] == list(PRIMITIVE_IDS)
    assert cfg["toggle_values"] == ["on", "off", "ambiguous"]

    witness_ids = list_witness_ids()
    assignments = cfg["witness_assignments"]
    assigned_ids = [a["witness_id"] for a in assignments]
    assert sorted(assigned_ids) == sorted(witness_ids)
    assert len(assigned_ids) == len(set(assigned_ids))

    for assn in assignments:
        toggles = assn["toggles"]
        assert set(toggles.keys()) == set(PRIMITIVE_IDS)
        for value in toggles.values():
            assert value in {"on", "off", "ambiguous"}
        if any(v == "ambiguous" for v in toggles.values()):
            assert str(assn.get("ambiguity_notes", "")).strip()

    coverage_ids = [t["theorem_id"] for t in cfg["theorem_coverage"]]
    assert len(coverage_ids) == 8
    assert len(set(coverage_ids)) == 8


def test_assignment_anchors() -> None:
    cfg = load_primitives_config()
    assn = _assignment_map(cfg)

    assert assn["rev_tree_4"]["toggles"] == {
        "rewrite": "off",
        "gating": "off",
        "holonomy": "off",
        "staging": "off",
        "packaging": "off",
        "drive": "off",
    }

    assert assn["biased_cycle_3"]["toggles"]["drive"] == "on"
    for p in ("rewrite", "gating", "holonomy", "staging", "packaging"):
        assert assn["biased_cycle_3"]["toggles"][p] == "off"

    assert assn["hidden_clock_reversible"]["toggles"] == {
        "rewrite": "off",
        "gating": "off",
        "holonomy": "on",
        "staging": "off",
        "packaging": "off",
        "drive": "off",
    }

    assert assn["hidden_clock_driven"]["toggles"] == {
        "rewrite": "off",
        "gating": "off",
        "holonomy": "on",
        "staging": "off",
        "packaging": "off",
        "drive": "on",
    }

    assert assn["contractive_unique_object"]["toggles"] == {
        "rewrite": "off",
        "gating": "off",
        "holonomy": "off",
        "staging": "off",
        "packaging": "on",
        "drive": "off",
    }

    assert assn["fixed_idempotent_no_ladder"]["toggles"] == {
        "rewrite": "off",
        "gating": "off",
        "holonomy": "off",
        "staging": "off",
        "packaging": "on",
        "drive": "off",
    }

    assert assn["lens_extension_escape"]["toggles"] == {
        "rewrite": "off",
        "gating": "off",
        "holonomy": "off",
        "staging": "on",
        "packaging": "on",
        "drive": "off",
    }


def test_derived_variant_anchors() -> None:
    rows = {r["row_id"]: r for r in build_derived_variant_rows()}
    assert set(rows.keys()) == {"rev_tree_4__rewrite_add_cd", "biased_cycle_3__gated_path"}

    rewrite = rows["rev_tree_4__rewrite_add_cd"]
    assert rewrite["rewrite"] == "on"
    assert rewrite["cycle_rank"] == 1
    assert rewrite["max_cycle_affinity"] == Fraction(0, 1)

    gated = rows["biased_cycle_3__gated_path"]
    assert gated["gating"] == "on"
    assert gated["drive"] == "on"
    assert gated["cycle_rank"] == 0
    assert gated["max_cycle_affinity"] == Fraction(0, 1)


def test_coverage_anchors() -> None:
    coverage = evaluate_theorem_coverage()
    t = _theorem_map(coverage)

    assert t["NG_FORCE_FOREST"]["satisfied_pair_count"] >= 1
    assert t["NG_FORCE_NULL"]["satisfied_pair_count"] >= 1
    assert t["NG_PROTOCOL_TRAP"]["satisfied_pair_count"] >= 1
    assert t["NG_ARROW_DPI"]["satisfied_pair_count"] >= 1

    assert str(t["NG_MACRO_CLOSURE_DEFICIT"]["gap_note"]).strip()
    assert t["NG_MACRO_CLOSURE_DEFICIT"]["coverage_satisfied"] is True

    assert t["NG_LADDER_IDEM"]["satisfied_pair_count"] >= 1
    assert t["NG_LADDER_BOUNDED_INTERFACE"]["satisfied_pair_count"] >= 1

    assert all(entry["coverage_satisfied"] for entry in coverage["theorem_targets"])


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t14"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t14_primitive_matrix.py", "--output-dir", str(out), "--precision", "80"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    matrix_path = out / "primitive_matrix.csv"
    coverage_path = out / "primitive_coverage.json"
    assert matrix_path.exists()
    assert coverage_path.exists()

    rows = list(csv.DictReader(matrix_path.open(encoding="utf-8")))
    assert len(rows) >= 13

    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    assert coverage["theorem_target_count"] == 8

    matrix_witnesses = {r["witness_id"] for r in rows if r["row_kind"] == "registered"}
    assert matrix_witnesses == set(list_witness_ids())

    assert coverage["gap_note_count"] >= 1
    unsatisfied = [t for t in coverage["theorem_targets"] if not t["coverage_satisfied"]]
    assert len(unsatisfied) == 0


def test_version_alias_repair() -> None:
    assert sixbirds_nogo.version == sixbirds_nogo.__version__


def test_exact_type_checks_before_csv_serialization() -> None:
    matrix = build_primitive_matrix()
    rows = {r["row_id"]: r for r in matrix}

    assert isinstance(rows["biased_cycle_3"]["max_cycle_affinity"], Fraction)
    assert isinstance(rows["contractive_unique_object"]["contraction_lambda"], Fraction)

    manifest = run_primitive_matrix()
    assert isinstance(manifest["rows"][0]["max_cycle_affinity"], Fraction)
