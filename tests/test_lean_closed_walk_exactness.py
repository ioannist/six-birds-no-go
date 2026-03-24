from pathlib import Path


def test_closed_walk_exactness_files_and_imports() -> None:
    theorem = Path("lean/SixBirdsNoGo/ClosedWalkExactness.lean")
    example = Path("lean/SixBirdsNoGo/ClosedWalkExactnessExample.lean")
    top = Path("lean/SixBirdsNoGo.lean")

    assert theorem.exists()
    assert example.exists()
    assert top.exists()

    t_text = theorem.read_text(encoding="utf-8")
    e_text = example.read_text(encoding="utf-8")
    assert "sorry" not in t_text
    assert "admit" not in t_text
    assert "sorry" not in e_text
    assert "admit" not in e_text

    top_text = top.read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.ClosedWalkExactness" in top_text
    assert "import SixBirdsNoGo.ClosedWalkExactnessExample" in top_text
