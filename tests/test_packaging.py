from fractions import Fraction

from sixbirds_nogo.packaging import (
    apply_packaging_to_distribution,
    apply_packaging_to_state,
    idempotence_defect,
    induced_operator_matrix,
    is_idempotent,
    load_packaging_from_witness,
    make_state_map_package,
    max_state_saturation_step,
    state_fixed_points,
    state_saturation_steps,
    state_trajectory,
)


def test_loader_and_family_anchors() -> None:
    assert load_packaging_from_witness("contractive_unique_object").family == "stochastic_operator"
    assert load_packaging_from_witness("noncontractive_multiobject").family == "state_map"
    assert load_packaging_from_witness("fixed_idempotent_no_ladder").family == "state_map"

    p_fix = load_packaging_from_witness("fixed_idempotent_no_ladder")
    p_ext = load_packaging_from_witness("lens_extension_escape")
    assert p_ext.family == "state_map"
    assert p_ext.states == p_fix.states
    assert p_ext.mapping == p_fix.mapping


def test_exact_action_anchors() -> None:
    c = load_packaging_from_witness("contractive_unique_object")
    assert apply_packaging_to_distribution(c, (Fraction(1, 1), Fraction(0, 1))) == (Fraction(3, 4), Fraction(1, 4))
    assert apply_packaging_to_distribution(c, (Fraction(0, 1), Fraction(1, 1))) == (Fraction(3, 4), Fraction(1, 4))

    f = load_packaging_from_witness("fixed_idempotent_no_ladder")
    assert apply_packaging_to_state(f, "z", 1) == "y"
    assert state_trajectory(f, "z", 2) == ("z", "y", "y")

    n = load_packaging_from_witness("noncontractive_multiobject")
    assert state_trajectory(n, "w", 2) == ("w", "u", "u")


def test_idempotence_and_saturation_anchors() -> None:
    ids = ["contractive_unique_object", "noncontractive_multiobject", "fixed_idempotent_no_ladder"]
    for wid in ids:
        pkg = load_packaging_from_witness(wid)
        assert idempotence_defect(pkg) == Fraction(0, 1)
        assert is_idempotent(pkg) is True

    n = load_packaging_from_witness("noncontractive_multiobject")
    f = load_packaging_from_witness("fixed_idempotent_no_ladder")

    assert state_fixed_points(n) == ("u", "v")
    assert state_fixed_points(f) == ("x", "y")

    assert state_saturation_steps(n) == {"u": 0, "v": 0, "w": 1}
    assert state_saturation_steps(f) == {"x": 0, "y": 0, "z": 1}

    assert max_state_saturation_step(n) == 1
    assert max_state_saturation_step(f) == 1


def test_synthetic_non_idempotent_constructor_check() -> None:
    pkg = make_state_map_package(("a", "b", "c"), {"a": "b", "b": "c", "c": "c"})
    assert idempotence_defect(pkg) == Fraction(1, 1)
    assert state_saturation_steps(pkg) == {"a": 2, "b": 1, "c": 0}
    assert max_state_saturation_step(pkg) == 2
    assert is_idempotent(pkg) is False


def test_exact_type_checks() -> None:
    pkg = load_packaging_from_witness("noncontractive_multiobject")
    mat = induced_operator_matrix(pkg)
    assert all(isinstance(x, Fraction) for row in mat for x in row)
    assert isinstance(idempotence_defect(pkg), Fraction)
