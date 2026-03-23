import json
import subprocess
import sys
from fractions import Fraction

from sixbirds_nogo.arrow import (
    honest_observed_path_reversal_kl,
    horizon_sweep_arrow,
    micro_path_reversal_kl,
    path_kl_divergence,
    reverse_path,
    reverse_path_law,
)
from sixbirds_nogo.coarse import enumerate_observed_path_law, load_lens_from_witness
from sixbirds_nogo.markov import load_chain_from_witness
from sixbirds_nogo.pathspace import enumerate_path_law


def _hidden_clock_cases() -> list[dict[str, object]]:
    horizons = [0, 1, 2, 3]
    return [
        {"witness_id": "hidden_clock_reversible", "lens_id": "identity", "horizons": horizons},
        {"witness_id": "hidden_clock_reversible", "lens_id": "observe_x_binary", "horizons": horizons},
        {"witness_id": "hidden_clock_reversible", "lens_id": "observe_clock_3", "horizons": horizons},
        {"witness_id": "hidden_clock_driven", "lens_id": "identity", "horizons": horizons},
        {"witness_id": "hidden_clock_driven", "lens_id": "observe_x_binary", "horizons": horizons},
        {"witness_id": "hidden_clock_driven", "lens_id": "observe_clock_3", "horizons": horizons},
    ]


def test_generic_path_reversal_basics() -> None:
    assert reverse_path(("a", "b", "c")) == ("c", "b", "a")

    law = {
        ("a", "b"): Fraction(1, 3),
        ("b", "a"): Fraction(2, 3),
    }
    assert reverse_path_law(reverse_path_law(law)) == law

    k = path_kl_divergence(law, law)
    assert k.kind == "zero"


def test_exact_regime_classification_named_fixtures() -> None:
    rev = load_chain_from_witness("hidden_clock_reversible")
    k_rev = micro_path_reversal_kl(rev, 3)
    assert k_rev.kind == "zero"
    assert k_rev.exact_equal is True

    driven = load_chain_from_witness("hidden_clock_driven")
    k_drv = micro_path_reversal_kl(driven, 1)
    assert k_drv.kind == "finite_positive"
    assert k_drv.decimal_value is not None and k_drv.decimal_value > 0
    assert k_drv.log_terms == (
        (Fraction(1, 2), Fraction(1, 3)),
        (Fraction(2, 1), Fraction(2, 3)),
    )

    p = load_chain_from_witness("positive_closure_deficit")
    k_p = micro_path_reversal_kl(p, 1)
    assert k_p.kind == "infinite"
    assert k_p.support_mismatch_count > 0


def test_honest_observed_macro_arrow_hidden_clock_fixtures() -> None:
    rev = load_chain_from_witness("hidden_clock_reversible")
    for lid in ("observe_x_binary", "observe_clock_3"):
        lens = load_lens_from_witness("hidden_clock_reversible", lid)
        k = honest_observed_path_reversal_kl(rev, lens, 3)
        assert k.kind == "zero"

    drv = load_chain_from_witness("hidden_clock_driven")
    x_lens = load_lens_from_witness("hidden_clock_driven", "observe_x_binary")
    kx = honest_observed_path_reversal_kl(drv, x_lens, 3)
    assert kx.kind == "zero"

    c3 = load_lens_from_witness("hidden_clock_driven", "observe_clock_3")
    kc3 = honest_observed_path_reversal_kl(drv, c3, 3)
    assert kc3.kind == "finite_positive"
    assert kc3.decimal_value is not None and kc3.decimal_value > 0


def test_identity_lens_equality() -> None:
    for wid in ("hidden_clock_reversible", "hidden_clock_driven"):
        chain = load_chain_from_witness(wid)
        lens = load_lens_from_witness(wid, "identity")
        for h in (0, 1, 2, 3):
            micro_law = enumerate_path_law(chain, h, initial_dist=chain.stationary_distribution)
            macro_law = enumerate_observed_path_law(chain, lens, h, initial_dist=chain.stationary_distribution)
            assert micro_law == macro_law

            mk = micro_path_reversal_kl(chain, h)
            gk = honest_observed_path_reversal_kl(chain, lens, h)
            assert mk.kind == gk.kind
            if mk.kind == "finite_positive":
                assert mk.log_terms == gk.log_terms
            else:
                assert mk.kind == "zero"
                assert gk.kind == "zero"


def test_dpi_behavior_hidden_clock_matrix() -> None:
    rows = horizon_sweep_arrow(_hidden_clock_cases(), precision=80)

    strict_loss_count = 0
    equal_count = 0
    for row in rows:
        dpi = row["dpi"]
        assert dpi["holds"] is True
        if dpi["equal_value"]:
            equal_count += 1
        if dpi["strict_loss"]:
            strict_loss_count += 1

    assert equal_count > 0
    assert strict_loss_count > 0

    # Required specific fixtures
    driven_x = [
        r for r in rows if r["witness_id"] == "hidden_clock_driven" and r["lens_id"] == "observe_x_binary"
    ]
    assert any(r["dpi"]["strict_loss"] for r in driven_x)

    rev_rows = [r for r in rows if r["witness_id"] == "hidden_clock_reversible"]
    assert all(r["micro"]["kind"] == "zero" and r["macro"]["kind"] == "zero" for r in rev_rows)


def test_runner_smoke(tmp_path) -> None:
    out = tmp_path / "t08"
    proc = subprocess.run(
        [sys.executable, "scripts/run_t08_arrow_suite.py", "--output-dir", str(out), "--precision", "80"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    csv_path = out / "arrow_metrics.csv"
    json_path = out / "arrow_metrics.json"
    manifest_path = out / "case_manifest.json"
    assert csv_path.exists()
    assert json_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["row_count"] >= 24

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert any(row["dpi"]["strict_loss"] for row in payload["rows"])
