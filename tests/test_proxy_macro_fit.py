import json
from fractions import Fraction
from pathlib import Path

from sixbirds_nogo.coarse import enumerate_observed_path_law, load_lens_from_witness
from sixbirds_nogo.markov import load_chain_from_witness
from sixbirds_nogo.proxy_macro_fit import fit_proxy_macro_chain, proxy_path_law


def test_proxy_labeling_and_config_alignment() -> None:
    chain = load_chain_from_witness("positive_closure_deficit")
    lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    fit = fit_proxy_macro_chain(chain, lens, initial_dist=chain.stationary_distribution)

    assert fit.proxy_id == "PROXY_MACRO_MARKOV_ARROW"
    notes = fit.notes.lower()
    assert "proxy" in notes and "diagnostic" in notes

    proxies = json.loads(Path("configs/proxies.yaml").read_text(encoding="utf-8"))
    ids = {p["id"] for p in proxies["proxy_audits"]}
    assert "PROXY_MACRO_MARKOV_ARROW" in ids


def test_one_step_consistency_by_construction() -> None:
    chain = load_chain_from_witness("positive_closure_deficit")
    lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    fit = fit_proxy_macro_chain(chain, lens, initial_dist=chain.stationary_distribution)

    assert fit.initial_distribution == (Fraction(3, 5), Fraction(2, 5))
    assert fit.macro_chain.matrix == (
        (Fraction(1, 3), Fraction(2, 3)),
        (Fraction(1, 1), Fraction(0, 1)),
    )

    proxy1 = proxy_path_law(fit, 1)
    honest1 = enumerate_observed_path_law(chain, lens, 1, initial_dist=chain.stationary_distribution)
    assert proxy1 == honest1


def test_proxy_divergence_on_non_lumpable_witness() -> None:
    chain = load_chain_from_witness("positive_closure_deficit")
    lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    fit = fit_proxy_macro_chain(chain, lens, initial_dist=chain.stationary_distribution)

    proxy2 = proxy_path_law(fit, 2)
    honest2 = enumerate_observed_path_law(chain, lens, 2, initial_dist=chain.stationary_distribution)
    assert proxy2 != honest2

    assert honest2[("A", "A", "A")] == Fraction(1, 10)
    assert proxy2[("A", "A", "A")] == Fraction(1, 15)

    assert honest2[("B", "A", "B")] == Fraction(3, 10)
    assert proxy2[("B", "A", "B")] == Fraction(4, 15)


def test_proxy_agreement_on_lumpable_witness() -> None:
    chain = load_chain_from_witness("zero_closure_deficit_lumpable")
    lens = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    fit = fit_proxy_macro_chain(chain, lens, initial_dist=chain.stationary_distribution)

    proxy2 = proxy_path_law(fit, 2)
    honest2 = enumerate_observed_path_law(chain, lens, 2, initial_dist=chain.stationary_distribution)
    assert proxy2 == honest2


def test_exact_fraction_types_in_proxy_outputs() -> None:
    chain = load_chain_from_witness("positive_closure_deficit")
    lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    fit = fit_proxy_macro_chain(chain, lens, initial_dist=chain.stationary_distribution)

    assert all(isinstance(x, Fraction) for row in fit.macro_chain.matrix for x in row)
    law = proxy_path_law(fit, 2)
    assert all(isinstance(mass, Fraction) for mass in law.values())
