"""Every direct Python package carries a version (#119, design DS7).

Renovate skips a package listed without a version, so it would silently stop
getting update pull requests. `[build-system] requires` is not locked and is left out.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"

# A name, optional extras and optional environment marker, with no specifier between.
_UNVERSIONED = re.compile(r"^\s*[A-Za-z0-9._-]+\s*(\[[^\]]*\])?\s*(;.*)?$")


def _requirements() -> list[str]:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    groups = data.get("dependency-groups", {})
    listed = list(data["project"]["dependencies"])
    for entries in groups.values():
        listed.extend(entry for entry in entries if isinstance(entry, str))
    return listed


@pytest.mark.parametrize("requirement", _requirements())
def test_every_direct_package_has_a_version(requirement: str) -> None:
    assert not _UNVERSIONED.match(requirement), f"{requirement!r} has no version"


@pytest.mark.parametrize(
    "requirement", ["ruff", "PyYAML", "pkg[extra]", "pkg ; python_version>'3'"]
)
def test_the_guard_catches_an_unversioned_package(requirement: str) -> None:
    assert _UNVERSIONED.match(requirement)
