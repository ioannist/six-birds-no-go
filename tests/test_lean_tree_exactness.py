from pathlib import Path


def test_tree_exactness_files_and_placeholders() -> None:
    theorem = Path("lean/SixBirdsNoGo/TreeExactness.lean")
    example = Path("lean/SixBirdsNoGo/TreeExactnessExample.lean")
    top = Path("lean/SixBirdsNoGo.lean")

    assert theorem.exists()
    assert example.exists()
    assert top.exists()

    theorem_text = theorem.read_text(encoding="utf-8")
    example_text = example.read_text(encoding="utf-8")

    assert "sorry" not in theorem_text
    assert "admit" not in theorem_text
    assert "sorry" not in example_text
    assert "admit" not in example_text

    top_text = top.read_text(encoding="utf-8")
    assert "import SixBirdsNoGo.TreeExactness" in top_text
    assert "import SixBirdsNoGo.TreeExactnessExample" in top_text
