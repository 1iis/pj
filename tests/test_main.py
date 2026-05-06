from my_package import __version__, main

def test_version():
    assert __version__ is not None

def test_main_runs():
    """Doesn't crash, returns None (implicitly)."""
    main()
