"""Task 1.2: the immutable ConditionsSnapshot data model in the pure core."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from pierpressure.core.conditions import ConditionsSnapshot, HourlyConditions


def _hour(h: int, **kw: float | None) -> HourlyConditions:
    return HourlyConditions(time=datetime(2026, 9, 8, h, 0, tzinfo=UTC), **kw)


def test_hourly_conditions_defaults_all_fields_absent() -> None:
    hour = _hour(21)
    assert hour.cloud_cover is None
    assert hour.wind_gust is None
    assert hour.seeing is None
    assert hour.transparency is None


def test_hourly_conditions_stamps_each_field_independently() -> None:
    hour = _hour(21, cloud_cover=40.0, wind_gust=20.0)
    assert hour.cloud_cover == 40.0
    assert hour.wind_gust == 20.0
    # The other two fields remain absent — availability is per field.
    assert hour.seeing is None
    assert hour.transparency is None


def test_snapshot_carries_hours_and_per_source_issue_times() -> None:
    base_issued = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    secondary_issued = datetime(2026, 9, 8, 11, 0, tzinfo=UTC)
    snap = ConditionsSnapshot(
        hours=(_hour(21, cloud_cover=10.0), _hour(22, cloud_cover=20.0)),
        base_issued_at=base_issued,
        secondary_issued_at=secondary_issued,
    )
    assert len(snap.hours) == 2
    assert snap.base_issued_at == base_issued
    assert snap.secondary_issued_at == secondary_issued


def test_snapshot_issue_times_default_to_none() -> None:
    snap = ConditionsSnapshot(hours=())
    assert snap.base_issued_at is None
    assert snap.secondary_issued_at is None


def test_snapshot_is_immutable() -> None:
    snap = ConditionsSnapshot(hours=(_hour(21),))
    with pytest.raises(dataclasses.FrozenInstanceError):
        snap.base_issued_at = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)  # type: ignore[misc]


def test_hourly_conditions_is_immutable() -> None:
    hour = _hour(21, cloud_cover=10.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        hour.cloud_cover = 90.0  # type: ignore[misc]


def test_snapshot_lookup_by_hour_returns_matching_slot() -> None:
    h21 = _hour(21, cloud_cover=10.0)
    snap = ConditionsSnapshot(hours=(h21, _hour(22, cloud_cover=20.0)))
    assert snap.at(datetime(2026, 9, 8, 21, 0, tzinfo=UTC)) is h21
    assert snap.at(datetime(2026, 9, 8, 23, 0, tzinfo=UTC)) is None
