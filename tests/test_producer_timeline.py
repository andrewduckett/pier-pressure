"""Task 1.3: produce_verdict fills the hourly timeline beside the verdict."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pierpressure.core.clock import FixedClock
from pierpressure.core.conditions import (
    BaseGroup,
    BaseHour,
    Conditions,
    GroupMeta,
    SecondaryGroup,
    SecondaryHour,
)
from pierpressure.core.config import PierConfig
from pierpressure.core.producer import produce_verdict
from pierpressure.core.sky import dark_window

from .conftest import make_pier
from .offline_guard import no_network

_ISSUED = datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
_MID_SESSION = datetime(2026, 9, 8, 23, 30, tzinfo=UTC)


def _hours(start: datetime, count: int) -> list[datetime]:
    return [start + timedelta(hours=i) for i in range(count)]


def _base(times: list[datetime], **fields: float | None) -> BaseGroup | None:
    return BaseGroup.of(
        GroupMeta(source="base", issued_at=_ISSUED),
        tuple(BaseHour(time=t, **fields) for t in times),
    )


def _secondary(times: list[datetime], **fields: float | None) -> SecondaryGroup | None:
    return SecondaryGroup.of(
        GroupMeta(source="secondary", issued_at=_ISSUED),
        tuple(SecondaryHour(time=t, **fields) for t in times),
    )


def test_the_timeline_spans_the_sorted_union_of_both_sources() -> None:
    day = datetime(2026, 9, 8, 0, tzinfo=UTC)
    base_times = _hours(day, 24)
    secondary_times = _hours(day + timedelta(hours=12), 48)
    # Out of order on input: the timeline must sort, not trust the provider's order.
    conditions = Conditions(
        base=_base(list(reversed(base_times)), cloud_cover=10.0),
        secondary=_secondary(secondary_times, seeing=0.5),
    )
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    assert [entry.time for entry in doc.timeline] == _hours(day, 60)


def test_an_hour_one_source_lacks_carries_null_for_that_source() -> None:
    day = datetime(2026, 9, 8, 18, tzinfo=UTC)
    conditions = Conditions(
        base=_base(
            [day], cloud_cover=37.0, wind_gust=23.4, cloud_low=1.0, cloud_mid=2.0, cloud_high=3.0
        ),
        secondary=_secondary([day, day + timedelta(hours=1)], seeing=4 / 7, transparency=0.9),
    )
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    first, second = doc.timeline
    assert (first.cloud_cover, first.wind_gust) == (37.0, 23.4)
    assert (first.cloud_low, first.cloud_mid, first.cloud_high) == (1.0, 2.0, 3.0)
    assert (first.seeing, first.transparency) == (0.57, 0.9)
    assert second.cloud_cover is None
    assert second.cloud_low is None and second.cloud_mid is None and second.cloud_high is None
    assert second.wind_gust is None
    assert (second.seeing, second.transparency) == (0.57, 0.9)
    assert second.sun_altitude is not None and second.moon_altitude is not None


def test_a_missing_secondary_source_leaves_seeing_and_transparency_null() -> None:
    day = datetime(2026, 9, 8, 18, tzinfo=UTC)
    conditions = Conditions(base=_base([day], cloud_cover=50.0), secondary=None)
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    [entry] = doc.timeline
    assert entry.cloud_cover == 50.0
    assert entry.seeing is None and entry.transparency is None


def test_empty_conditions_yield_an_empty_timeline() -> None:
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), Conditions(None, None)
        )
    assert doc.timeline == []


def test_past_hours_stay_and_the_scored_window_starts_at_the_instant() -> None:
    times = _hours(datetime(2026, 9, 8, 18, tzinfo=UTC), 13)
    conditions = Conditions(
        base=_base(times, cloud_cover=10.0), secondary=_secondary(times, seeing=0.8)
    )
    with no_network():
        doc = produce_verdict(make_pier(), FixedClock(_MID_SESSION), conditions)

    assert [entry.time for entry in doc.timeline] == times
    assert doc.timeline[0].cloud_cover == 10.0
    assert doc.scored_window.start == _MID_SESSION


def test_the_timeline_fills_without_a_dark_window() -> None:
    # 88N in high summer: the sun never drops below -18, so there is no dark window.
    pier = PierConfig(id="high-arctic", latitude=88.0, longitude=0.0, elevation_m=0.0)
    clock = FixedClock(datetime(2026, 6, 21, 12, tzinfo=UTC))
    times = _hours(datetime(2026, 6, 21, 0, tzinfo=UTC), 48)
    conditions = Conditions(
        base=_base(times, cloud_cover=5.0), secondary=_secondary(times, seeing=0.6)
    )
    with no_network():
        doc = produce_verdict(pier, clock, conditions)
        baseline = produce_verdict(pier, clock, Conditions(None, None))

    assert doc.dark_window.start is None
    assert [entry.time for entry in doc.timeline] == times
    assert doc.model_dump_json(exclude={"timeline"}) == baseline.model_dump_json(
        exclude={"timeline"}
    )


def test_hours_outside_the_dark_window_change_no_other_field() -> None:
    pier = make_pier()
    clock = FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC))
    start, end = dark_window(pier, clock.now())
    assert start is not None and end is not None
    first = start.replace(minute=0, second=0, microsecond=0)
    inside = [t for t in _hours(first, 24) if t <= end]
    wider = _hours(first - timedelta(hours=12), len(inside) + 24)

    def _doc(times: list[datetime]) -> str:
        conditions = Conditions(
            base=_base(times, cloud_cover=10.0, wind_gust=5.0),
            secondary=_secondary(times, seeing=0.8, transparency=0.7),
        )
        with no_network():
            return produce_verdict(pier, clock, conditions).model_dump_json(exclude={"timeline"})

    assert _doc(inside) == _doc(wider)


def test_the_docstring_no_longer_says_conditions_are_not_consulted() -> None:
    assert produce_verdict.__doc__ is not None
    assert "not consulted" not in produce_verdict.__doc__
