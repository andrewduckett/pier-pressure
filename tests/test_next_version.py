"""release-image: the next CalVer release version (design D2, ADR-0013)."""

from __future__ import annotations

from datetime import date

import pytest
from next_version import next_version


@pytest.mark.parametrize(
    ("tags", "today", "expected"),
    [
        pytest.param([], date(2026, 10, 3), "2026.10.0", id="first-release-of-a-month"),
        pytest.param(
            ["2026.10.0", "2026.10.1"], date(2026, 10, 20), "2026.10.2", id="later-same-month"
        ),
        pytest.param(["2026.10.4"], date(2026, 11, 1), "2026.11.0", id="monthly-reset"),
        pytest.param(
            ["2026.10.9", "2026.10.10"], date(2026, 10, 20), "2026.10.11", id="numeric-counter"
        ),
        pytest.param(
            ["v1.0", "2026.10.x", "2026.010.5", "2026.10.07", "v2026.10.3"],
            date(2026, 10, 3),
            "2026.10.0",
            id="non-matching-tags-ignored",
        ),
    ],
)
def test_next_version(tags: list[str], today: date, expected: str) -> None:
    assert next_version(tags, today) == expected
