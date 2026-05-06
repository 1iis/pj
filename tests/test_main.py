from pj import __version__, main

def test_version():
    assert __version__ is not None

def test_main_runs():
    """main is a callable function (no network required)."""
    assert callable(main)
