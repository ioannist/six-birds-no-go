from fractions import Fraction
import subprocess
import sys

from sixbirds_nogo.witnesses import list_witness_ids, load_witness, parse_rational


REQUIRED_WITNESS_IDS = {
    "rev_tree_4",
    "rev_cycle_3",
    "biased_cycle_3",
    "hidden_clock_reversible",
    "hidden_clock_driven",
    "zero_closure_deficit_lumpable",
    "positive_closure_deficit",
    "contractive_unique_object",
    "noncontractive_multiobject",
    "fixed_idempotent_no_ladder",
    "lens_extension_escape",
}


def test_validate_witnesses_script_passes() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/validate_witnesses.py", "--summary"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS" in proc.stdout


def test_loader_returns_required_ids_and_theorem_targets() -> None:
    ids = set(list_witness_ids())
    assert REQUIRED_WITNESS_IDS.issubset(ids)
    for witness_id in REQUIRED_WITNESS_IDS:
        witness = load_witness(witness_id)
        assert witness.raw.get("theorem_targets")


def test_parse_rational_smoke() -> None:
    assert parse_rational("1/3") == Fraction(1, 3)
