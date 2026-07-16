"""
Placeholder test to satisfy CI until Phase 1 adds real tests.
This file is deleted in Phase 1 when real tests are added.
"""


def test_examina_version() -> None:
    """Verify the package version string is set."""
    from examina import __version__
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_constitution_exists() -> None:
    """Verify the Constitution specification file exists."""
    from pathlib import Path
    constitution = Path("specs/CONSTITUTION_v1.0.md")
    assert constitution.exists(), (
        "CONSTITUTION_v1.0.md must exist — it is the source of truth "
        "for all implementation decisions."
    )


def test_spec_version_exists() -> None:
    """Verify the specification version file exists."""
    from pathlib import Path
    spec_version = Path("specs/SPEC_VERSION.md")
    assert spec_version.exists()
