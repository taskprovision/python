"""
A minimal test file to debug pytest issues.
"""

def test_minimal():
    """A minimal test that should always pass."""
    assert 1 + 1 == 2

if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main(["-v"]))
