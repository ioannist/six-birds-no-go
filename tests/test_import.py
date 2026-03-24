import sixbirds_nogo


def test_version_is_present_and_non_empty() -> None:
    assert hasattr(sixbirds_nogo, "__version__")
    assert isinstance(sixbirds_nogo.__version__, str)
    assert sixbirds_nogo.__version__
