from pathlib import Path


def test_lean_scaffold_or_blocker() -> None:
    lean_dir = Path("lean")
    if lean_dir.exists():
        assert (lean_dir / "lakefile.lean").exists()
        assert (lean_dir / "lean-toolchain").exists()
        theorem_file = lean_dir / "SixBirdsNoGo" / "Idempotence.lean"
        assert theorem_file.exists()
        text = theorem_file.read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text
    else:
        blocker = Path("docs/project/lean_blocker.md")
        assert blocker.exists()
        assert blocker.read_text(encoding="utf-8").strip()
