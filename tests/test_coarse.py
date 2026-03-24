from fractions import Fraction

from sixbirds_nogo.coarse import (
    block_transition_rows,
    enumerate_observed_path_law,
    enumerate_observed_path_law_bruteforce,
    is_strongly_lumpable,
    load_lens_from_witness,
    pushforward_distribution_through_lens,
    strong_lumpable_macro_chain,
)
from sixbirds_nogo.markov import load_chain_from_witness
from sixbirds_nogo.pathspace import path_law_total_mass


def test_lens_loading_and_canonical_image_order() -> None:
    lens_ab = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    assert lens_ab.image_states == ("A", "B")

    lens_clock = load_lens_from_witness("hidden_clock_reversible", "observe_clock_3")
    assert lens_clock.image_states == ("A", "B", "C")

    lens_id = load_lens_from_witness("rev_cycle_3", "identity")
    assert lens_id.image_states == ("0", "1", "2")


def test_distribution_pushforward() -> None:
    rev = load_chain_from_witness("rev_cycle_3")
    lens_id = load_lens_from_witness("rev_cycle_3", "identity")
    pushed = pushforward_distribution_through_lens(rev.stationary_distribution, lens_id)
    assert pushed == rev.stationary_distribution

    z = load_chain_from_witness("zero_closure_deficit_lumpable")
    lens_ab = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    pushed_ab = pushforward_distribution_through_lens(z.stationary_distribution, lens_ab)
    assert pushed_ab == (Fraction(1, 2), Fraction(1, 2))
    assert all(isinstance(x, Fraction) for x in pushed_ab)


def test_honest_observed_path_law_matches_bruteforce() -> None:
    fixtures = [
        ("positive_closure_deficit", "macro_AB"),
        ("hidden_clock_reversible", "observe_x_binary"),
    ]
    for wid, lid in fixtures:
        chain = load_chain_from_witness(wid)
        lens = load_lens_from_witness(wid, lid)
        for horizon in (0, 1, 2):
            law_push = enumerate_observed_path_law(chain, lens, horizon, initial_dist=chain.stationary_distribution)
            law_brute = enumerate_observed_path_law_bruteforce(chain, lens, horizon, initial_dist=chain.stationary_distribution)
            assert law_push == law_brute
            assert path_law_total_mass(law_push) == Fraction(1, 1)

    chain = load_chain_from_witness("positive_closure_deficit")
    lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    law = enumerate_observed_path_law(chain, lens, 2, initial_dist=chain.stationary_distribution)
    assert law[("A", "B", "A")] == Fraction(2, 5)


def test_strong_lumpability_checks() -> None:
    rev = load_chain_from_witness("rev_cycle_3")
    rev_id = load_lens_from_witness("rev_cycle_3", "identity")
    assert is_strongly_lumpable(rev, rev_id) is True

    z = load_chain_from_witness("zero_closure_deficit_lumpable")
    z_lens = load_lens_from_witness("zero_closure_deficit_lumpable", "macro_AB")
    assert is_strongly_lumpable(z, z_lens) is True
    macro = strong_lumpable_macro_chain(z, z_lens)
    assert macro.states == ("A", "B")
    assert macro.matrix == (
        (Fraction(1, 2), Fraction(1, 2)),
        (Fraction(1, 2), Fraction(1, 2)),
    )
    assert macro.stationary_distribution == (Fraction(1, 2), Fraction(1, 2))

    p = load_chain_from_witness("positive_closure_deficit")
    p_lens = load_lens_from_witness("positive_closure_deficit", "macro_AB")
    assert is_strongly_lumpable(p, p_lens) is False

    rows = block_transition_rows(p, p_lens)
    assert rows["A0"] == (Fraction(1, 2), Fraction(1, 2))
    assert rows["A1"] == (Fraction(0, 1), Fraction(1, 1))

    try:
        strong_lumpable_macro_chain(p, p_lens)
    except ValueError as exc:
        assert "not strongly lumpable" in str(exc)
    else:
        raise AssertionError("expected ValueError for non-lumpable witness")
