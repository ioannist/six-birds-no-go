import csv
import json
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction

from sixbirds_nogo.master_suite import REQUIRED_METRICS, run_master_suite
from sixbirds_nogo.witnesses import list_witness_ids


def _row(rows: list[dict[str, str]], witness_id: str) -> dict[str, str]:
    for row in rows:
        if row["witness_id"] == witness_id:
            return row
    raise AssertionError(f"missing row for {witness_id}")


def _is_positive_decimal_text(value: str) -> bool:
    return Decimal(value) > Decimal(0)


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "master"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_t13_master_witness_suite.py",
            "--output-dir",
            str(out),
            "--precision",
            "80",
            "--eps-denominator",
            "4",
            "--eps-epsilon",
            "1/4",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    manifest_path = out / "witness_manifest.json"
    csv_path = out / "witness_metrics.csv"
    assert manifest_path.exists()
    assert csv_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["witness_count"] == 11
    assert manifest["success_count"] == 11
    assert manifest["partial_count"] == 0
    assert manifest["failed_count"] == 0
    assert manifest["unexplained_missing_count"] == 0


def test_csv_schema_coverage() -> None:
    rows = list(csv.DictReader(open("results/master/witness_metrics.csv", encoding="utf-8")))
    assert len(rows) == 11
    header = rows[0].keys()

    required = [
        "witness_id",
        "micro_arrow_kl",
        "macro_arrow_kl",
        "cycle_rank",
        "max_cycle_affinity",
        "exactness_flag",
        "closure_deficit",
        "best_macro_gap",
        "contraction_lambda",
        "fixed_point_count",
        "eps_stable_count",
        "definable_predicate_count",
        "interface_size",
    ]
    for col in required:
        assert col in header
    for col in required:
        if col == "witness_id":
            continue
        assert f"{col}_explanation" in header


def test_no_missing_metric_without_explanation() -> None:
    rows = list(csv.DictReader(open("results/master/witness_metrics.csv", encoding="utf-8")))
    for row in rows:
        for metric in REQUIRED_METRICS:
            value = row[metric]
            explanation = row[f"{metric}_explanation"]
            assert value != "" or explanation != ""


def test_anchor_value_checks() -> None:
    rows = list(csv.DictReader(open("results/master/witness_metrics.csv", encoding="utf-8")))

    rev_tree = _row(rows, "rev_tree_4")
    assert rev_tree["cycle_rank"] == "0"
    assert rev_tree["max_cycle_affinity"] == "0"
    assert rev_tree["exactness_flag"] == "True"
    assert rev_tree["micro_arrow_kl"] == ""
    assert rev_tree["micro_arrow_kl_explanation"] != ""
    assert rev_tree["definable_predicate_count"] == "16"
    assert rev_tree["interface_size"] == "4"

    hrev = _row(rows, "hidden_clock_reversible")
    assert hrev["micro_arrow_kl"] == "0"
    assert hrev["macro_arrow_kl"] == "0"
    assert hrev["cycle_rank"] == "1"
    assert hrev["max_cycle_affinity"] == "0"
    assert hrev["exactness_flag"] == "True"
    assert hrev["representative_lens_id"] == "observe_clock_3"
    assert hrev["definable_predicate_count"] == "8"
    assert hrev["interface_size"] == "3"

    hdrv = _row(rows, "hidden_clock_driven")
    assert _is_positive_decimal_text(hdrv["micro_arrow_kl"])
    assert _is_positive_decimal_text(hdrv["macro_arrow_kl"])
    assert hdrv["cycle_rank"] == "1"
    assert hdrv["max_cycle_affinity"] == "15"
    assert hdrv["exactness_flag"] == "False"
    assert hdrv["representative_lens_id"] == "observe_clock_3"
    assert hdrv["definable_predicate_count"] == "8"
    assert hdrv["interface_size"] == "3"

    pcd = _row(rows, "positive_closure_deficit")
    assert _is_positive_decimal_text(pcd["closure_deficit"])
    assert _is_positive_decimal_text(pcd["best_macro_gap"])
    assert pcd["cycle_rank"] == "1"
    assert pcd["max_cycle_affinity"] == "0"
    assert pcd["exactness_flag"] == "True"
    assert pcd["representative_lens_id"] == "macro_AB"
    assert pcd["definable_predicate_count"] == "4"
    assert pcd["interface_size"] == "2"

    cuo = _row(rows, "contractive_unique_object")
    assert cuo["contraction_lambda"] == "0"
    assert cuo["fixed_point_count"] == "1"
    assert cuo["eps_stable_count"] == "3"
    assert cuo["representative_lens_id"] == "identity"
    assert cuo["definable_predicate_count"] == "4"
    assert cuo["interface_size"] == "2"

    lee = _row(rows, "lens_extension_escape")
    assert lee["representative_lens_id"] == "extended_ternary"
    assert lee["definable_predicate_count"] == "8"
    assert lee["interface_size"] == "3"


def test_manifest_structure_and_strongest_signal() -> None:
    manifest = json.loads(open("results/master/witness_manifest.json", encoding="utf-8").read())
    rows = manifest["rows"]
    assert len(rows) == 11
    for row in rows:
        assert row["execution_status"] == "success"
        assert "metrics" in row
        assert "strongest_signal" in row
        assert isinstance(row["strongest_signal"], str)
        assert row["strongest_signal"].strip()


def test_research_log_coverage() -> None:
    text = open("docs/research-log/T13.md", encoding="utf-8").read()
    assert text.strip()
    for wid in list_witness_ids():
        assert wid in text


def test_exact_type_checks_before_csv_serialization() -> None:
    manifest = run_master_suite()
    rows = {r["witness_id"]: r for r in manifest["rows"]}

    assert isinstance(rows["hidden_clock_driven"]["metrics"]["max_cycle_affinity"]["value"], Fraction)
    assert isinstance(rows["contractive_unique_object"]["metrics"]["contraction_lambda"]["value"], Fraction)
    assert isinstance(manifest["eps_epsilon"], Fraction)
    assert manifest["eps_epsilon"] == Fraction(1, 4)
