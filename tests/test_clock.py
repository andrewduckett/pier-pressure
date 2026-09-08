"""Task 2.2: the injectable clock."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pierpressure.core.clock import FixedClock, SystemClock


def test_fixed_clock_returns_the_pinned_instant() -> None:
    instant = datetime(2026, 9, 7, 21, 30, tzinfo=UTC)
    clock = FixedClock(instant)
    assert clock.now() == instant
    assert clock.now() == instant  # stable across reads


def test_fixed_clock_rejects_naive_instant() -> None:
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 9, 7, 21, 30))


def test_system_clock_is_tz_aware_utc() -> None:
    now = SystemClock().now()
    assert now.tzinfo is not None
    assert now.utcoffset() == UTC.utcoffset(None)
