"""Task 1.3: produce_verdict fills the hourly timeline beside the verdict."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from pierpressure.core.clock import FixedClock
from pierpressure.core.conditions import Conditions, Series, Variable
from pierpressure.core.config import PierConfig
from pierpressure.core.model import TimelineEntry
from pierpressure.core.producer import produce_verdict
from pierpressure.core.providers import OPEN_METEO, SEVEN_TIMER
from pierpressure.core.sky import dark_window

from .conftest import make_pier, provider_series
from .offline_guard import no_network

_ISSUED = datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
_MID_SESSION = datetime(2026, 9, 8, 23, 30, tzinfo=UTC)


def _hours(start: datetime, count: int) -> list[datetime]:
    return [start + timedelta(hours=i) for i in range(count)]


def _base(times: list[datetime], **fields: float | None) -> dict[Variable, Series]:
    return provider_series(OPEN_METEO, times, issued_at=_ISSUED, **fields)


def _secondary(times: list[datetime], **fields: float | None) -> dict[Variable, Series]:
    return provider_series(SEVEN_TIMER, times, issued_at=_ISSUED, **fields)


def _conditions(
    *, base: dict[Variable, Series] | None = None, secondary: dict[Variable, Series] | None = None
) -> Conditions:
    return Conditions(series={**(base or {}), **(secondary or {})})


def test_the_timeline_spans_the_sorted_union_of_both_providers() -> None:
    day = datetime(2026, 9, 8, 0, tzinfo=UTC)
    base_times = _hours(day, 24)
    secondary_times = _hours(day + timedelta(hours=12), 48)
    # Out of order on input: the timeline must sort, not trust the provider's order.
    conditions = _conditions(
        base=_base(list(reversed(base_times)), cloud_cover=10.0),
        secondary=_secondary(secondary_times, seeing=0.5),
    )
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    assert [entry.time for entry in doc.timeline] == _hours(day, 60)


def test_an_hour_one_provider_lacks_carries_null_for_its_series() -> None:
    day = datetime(2026, 9, 8, 18, tzinfo=UTC)
    conditions = _conditions(
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


def test_a_missing_seven_timer_leaves_seeing_and_transparency_null() -> None:
    day = datetime(2026, 9, 8, 18, tzinfo=UTC)
    conditions = Conditions(series=_base([day], cloud_cover=50.0))
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    [entry] = doc.timeline
    assert entry.cloud_cover == 50.0
    assert entry.seeing is None and entry.transparency is None


_WEATHER = {
    "temperature": 12.3,
    "dew_point": 9.8,
    "humidity": 85.0,
    "wind_speed": 14.2,
    "wind_direction": 230.0,
    "precipitation_probability": 35.0,
}


def _weather(entry: TimelineEntry) -> dict[str, float | None]:
    return {key: getattr(entry, key) for key in _WEATHER}


def test_weather_values_pass_through_unchanged() -> None:
    day = datetime(2026, 9, 8, 18, tzinfo=UTC)
    conditions = Conditions(series=_base([day], cloud_cover=50.0, **_WEATHER))
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    [entry] = doc.timeline
    assert _weather(entry) == _WEATHER


def test_a_weather_value_the_provider_lacks_is_null_on_its_own() -> None:
    day = datetime(2026, 9, 8, 18, tzinfo=UTC)
    reported = {**_WEATHER, "dew_point": None}
    conditions = Conditions(series=_base([day], **reported))
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    [entry] = doc.timeline
    assert _weather(entry) == reported


def test_an_hour_the_weather_series_lack_carries_null_weather_values() -> None:
    day = datetime(2026, 9, 8, 18, tzinfo=UTC)
    conditions = _conditions(
        base=_base([day], **_WEATHER),
        secondary=_secondary([day, day + timedelta(hours=1)], seeing=0.8, transparency=0.7),
    )
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    _, second = doc.timeline
    assert all(value is None for value in _weather(second).values())
    assert (second.seeing, second.transparency) == (0.8, 0.7)


def test_weather_variables_do_not_change_the_verdict() -> None:
    pier = make_pier()
    clock = FixedClock(_MID_SESSION)
    times = _hours(datetime(2026, 9, 8, 12, tzinfo=UTC), 36)

    def _doc(**weather: float | None) -> dict[str, Any]:
        conditions = _conditions(
            base=_base(times, cloud_cover=10.0, wind_gust=5.0, **weather),
            secondary=_secondary(times, seeing=0.8, transparency=0.7),
        )
        with no_network():
            return produce_verdict(pier, clock, conditions).model_dump(mode="json")

    plain, wet = _doc(), _doc(**{**_WEATHER, "precipitation_probability": 95.0})
    for doc in (plain, wet):
        for entry in doc["timeline"]:
            for key in _WEATHER:
                entry.pop(key)
    assert plain == wet


def test_each_key_reads_its_own_series_and_the_hours_are_their_union() -> None:
    first = datetime(2026, 9, 8, 20, tzinfo=UTC)
    second = first + timedelta(hours=1)
    conditions = Conditions(
        series={
            "cloud_cover": Series(provider="a", issued_at=_ISSUED, values={first: 37.0}),
            "wind_gust": Series(provider="b", issued_at=_ISSUED, values={second: 23.4}),
        }
    )
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), conditions
        )

    early, late = doc.timeline
    assert (early.time, early.cloud_cover, early.wind_gust) == (first, 37.0, None)
    assert (late.time, late.cloud_cover, late.wind_gust) == (second, None, 23.4)


def test_empty_conditions_yield_an_empty_timeline() -> None:
    with no_network():
        doc = produce_verdict(
            make_pier(), FixedClock(datetime(2026, 9, 8, 14, tzinfo=UTC)), Conditions()
        )
    assert doc.timeline == []


def test_past_hours_stay_and_the_scored_window_starts_at_the_instant() -> None:
    times = _hours(datetime(2026, 9, 8, 18, tzinfo=UTC), 13)
    conditions = _conditions(
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
    conditions = _conditions(
        base=_base(times, cloud_cover=5.0), secondary=_secondary(times, seeing=0.6)
    )
    with no_network():
        doc = produce_verdict(pier, clock, conditions)
        baseline = produce_verdict(pier, clock, Conditions())

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
        conditions = _conditions(
            base=_base(times, cloud_cover=10.0, wind_gust=5.0),
            secondary=_secondary(times, seeing=0.8, transparency=0.7),
        )
        with no_network():
            return produce_verdict(pier, clock, conditions).model_dump_json(exclude={"timeline"})

    assert _doc(inside) == _doc(wider)


def test_the_docstring_no_longer_says_conditions_are_not_consulted() -> None:
    assert produce_verdict.__doc__ is not None
    assert "not consulted" not in produce_verdict.__doc__
