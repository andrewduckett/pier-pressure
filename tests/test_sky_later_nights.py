"""later_night_windows: one dark window per local solar day after the selected night.

The expected bounds are the spec's scenario values (night-verdict, later nights),
checked against the bundled ephemeris.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from pierpressure.core import sky
from pierpressure.core.config import PierConfig
from pierpressure.core.sky import (
    MAX_LATER_NIGHTS,
    dark_window,
    later_night_windows,
    night_solar_day,
)

from .offline_guard import no_network

LONDON = PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0)
LONDON_INSTANT = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)


def _windows(
    pier: PierConfig, instant: datetime, reach_end: datetime | None
) -> list[tuple[datetime, datetime] | tuple[None, None]]:
    with no_network():
        return later_night_windows(pier, instant, dark_window(pier, instant), reach_end)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def test_no_reach_gives_no_later_nights() -> None:
    assert _windows(LONDON, LONDON_INSTANT, None) == []


def test_two_london_nights_have_the_spec_bounds() -> None:
    windows = _windows(LONDON, LONDON_INSTANT, _at("2026-09-10T19:00:00Z"))
    assert windows == [
        (_at("2026-09-09T20:27:57Z"), _at("2026-09-10T03:28:02Z")),
        (_at("2026-09-10T20:25:07Z"), _at("2026-09-11T03:30:11Z")),
    ]


def test_a_long_forecast_stops_at_three_later_nights() -> None:
    windows = _windows(LONDON, LONDON_INSTANT, _at("2026-09-14T19:00:00Z"))
    assert MAX_LATER_NIGHTS == 3
    assert [start for start, _ in windows] == [
        _at("2026-09-09T20:27:57Z"),
        _at("2026-09-10T20:25:07Z"),
        _at("2026-09-11T20:22:18Z"),
    ]


def test_a_reach_just_after_the_solar_noon_counts_that_solar_day() -> None:
    assert len(_windows(LONDON, LONDON_INSTANT, _at("2026-09-10T12:00:00Z"))) == 2


def test_a_reach_just_before_the_solar_noon_does_not_count_that_solar_day() -> None:
    windows = _windows(LONDON, LONDON_INSTANT, _at("2026-09-10T11:00:00Z"))
    assert [start for start, _ in windows] == [_at("2026-09-09T20:27:57Z")]


def test_the_first_later_night_is_in_the_solar_day_after_the_selected_night() -> None:
    with no_network():
        _, selected_end = night_solar_day(
            LONDON, LONDON_INSTANT, dark_window(LONDON, LONDON_INSTANT)
        )
    start, end = _windows(LONDON, LONDON_INSTANT, _at("2026-09-10T19:00:00Z"))[0]
    assert start is not None and end is not None
    assert selected_end < start


def test_a_day_without_darkness_does_not_borrow_the_next_night() -> None:
    pier = PierConfig(id="may", latitude=52.0, longitude=0.0, elevation_m=0.0)
    instant = datetime(2026, 5, 19, 15, 0, tzinfo=UTC)
    assert dark_window(pier, instant) == (
        _at("2026-05-19T23:42:13Z"),
        _at("2026-05-20T00:10:20Z"),
    )
    assert _windows(pier, instant, _at("2026-05-21T19:00:00Z")) == [(None, None), (None, None)]


def test_later_nights_follow_a_selected_night_with_no_dark_window() -> None:
    pier = PierConfig(id="june", latitude=55.0, longitude=-3.0, elevation_m=0.0)
    instant = datetime(2026, 6, 21, 8, 0, tzinfo=UTC)
    assert dark_window(pier, instant) == (None, None)
    assert _windows(pier, instant, _at("2026-06-23T19:00:00Z")) == [(None, None), (None, None)]


def test_continuous_polar_night_windows_meet_noon_to_noon_at_whole_seconds() -> None:
    pier = PierConfig(id="polar", latitude=88.0, longitude=0.0, elevation_m=0.0)
    instant = datetime(2026, 12, 10, 12, 0, tzinfo=UTC)
    with no_network():
        _, selected_end = night_solar_day(pier, instant, dark_window(pier, instant))
    windows = _windows(pier, instant, _at("2026-12-14T13:00:00Z"))

    assert len(windows) == 3
    bounds = [selected_end]
    for start, end in windows:
        assert start is not None and end is not None
        assert start.microsecond == 0 and end.microsecond == 0
        assert start == bounds[-1]
        assert abs(end - start - timedelta(days=1)) < timedelta(minutes=1)
        bounds.append(end)


def test_a_continuous_night_a_second_off_the_day_bounds_takes_the_day_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Real noon lookups rarely floor a second apart, so the window is substituted.
    pier = PierConfig(id="polar", latitude=88.0, longitude=0.0, elevation_m=0.0)
    instant = datetime(2026, 12, 10, 12, 0, tzinfo=UTC)
    with no_network():
        selected = dark_window(pier, instant)
        _, day_start = night_solar_day(pier, instant, selected)
    real = sky.dark_window

    def jittered(pier: PierConfig, at: datetime) -> tuple[datetime, datetime] | tuple[None, None]:
        start, end = real(pier, at)
        if start is None or end is None:
            return (None, None)
        return (start - timedelta(seconds=1), end + timedelta(seconds=1))

    monkeypatch.setattr(sky, "dark_window", jittered)
    with no_network():
        windows = later_night_windows(pier, instant, selected, _at("2026-12-11T13:00:00Z"))

    start, end = windows[0]
    assert start == day_start
    assert end is not None and end.microsecond == 0


def test_each_later_night_holds_its_chained_solar_day() -> None:
    with no_network():
        nights = sky.later_nights(
            LONDON, LONDON_INSTANT, dark_window(LONDON, LONDON_INSTANT), _at("2026-09-10T19:00:00Z")
        )
    assert [night.solar_day for night in nights] == [
        (_at("2026-09-09T11:57:48Z"), _at("2026-09-10T11:57:27Z")),
        (_at("2026-09-10T11:57:27Z"), nights[1].solar_day[1]),
    ]
    assert nights[0].dark_window == (_at("2026-09-09T20:27:57Z"), _at("2026-09-10T03:28:02Z"))


def test_a_later_night_sky_is_frozen() -> None:
    with no_network():
        night = sky.later_nights(
            LONDON, LONDON_INSTANT, dark_window(LONDON, LONDON_INSTANT), _at("2026-09-10T19:00:00Z")
        )[0]
    with pytest.raises(AttributeError):
        night.dark_window = (None, None)  # type: ignore[misc]
