"""release-image: the package version comes from the git tag (design D1, ADR-0013)."""

from __future__ import annotations

import importlib.metadata

import pierpressure


def test_version_matches_package_metadata() -> None:
    assert pierpressure.__version__ == importlib.metadata.version("pierpressure")
