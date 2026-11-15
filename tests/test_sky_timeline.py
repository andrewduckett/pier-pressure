"""Task 1.2: altitudes_at(pier, times) — sun and moon altitude for each timeline hour."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from pierpressure.core import sky
from pierpressure.core.config import PierConfig
from pierpressure.core.model import DEGREE_DECIMALS
from pierpressure.core.sky import (
    _altitude_deg,
    _ephemeris,
    altitudes_at,
    dark_window,
    night_hours,
    night_solar_day,
)

from .offline_guard import no_network

_INSTANT = datetime(2026, 9, 7, 21, 30, tzinfo=UTC)


def _london() -> PierConfig:
    return PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0)


def _hours(start: datetime, count: int) -> list[datetime]:
    return [start + timedelta(hours=i) for i in range(count)]


def test_no_times_return_an_empty_list_without_calling_skyfield(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _explode() -> object:
        raise AssertionError("Skyfield was consulted for an empty timeline")

    monkeypatch.setattr(sky, "_timescale", _explode)
    monkeypatch.setattr(sky, "_ephemeris", _explode)
    assert altitudes_at(_london(), []) == []


def test_one_pair_per_hour_matching_the_single_instant_astronomy() -> None:
    pier = _london()
    times = _hours(datetime(2026, 9, 7, 0, tzinfo=UTC), 72)
    eph = _ephemeris()
    with no_network():
        pairs = altitudes_at(pier, times)
    assert len(pairs) == len(times)
    for when, (sun, moon) in zip(times, pairs, strict=True):
        assert round(sun, DEGREE_DECIMALS) == round(
            _altitude_deg(pier, eph["sun"], when), DEGREE_DECIMALS
        )
        assert round(moon, DEGREE_DECIMALS) == round(
            _altitude_deg(pier, eph["moon"], when), DEGREE_DECIMALS
        )


def test_a_single_hour_returns_one_pair() -> None:
    pier = _london()
    when = datetime(2026, 9, 7, 23, tzinfo=UTC)
    [(sun, moon)] = altitudes_at(pier, [when])
    eph = _ephemeris()
    assert round(sun, DEGREE_DECIMALS) == round(
        _altitude_deg(pier, eph["sun"], when), DEGREE_DECIMALS
    )
    assert round(moon, DEGREE_DECIMALS) == round(
        _altitude_deg(pier, eph["moon"], when), DEGREE_DECIMALS
    )


def test_every_hour_inside_the_dark_window_reads_at_or_below_minus_18() -> None:
    pier = _london()
    start, end = dark_window(pier, _INSTANT)
    assert start is not None and end is not None
    first = start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    inside = [t for t in _hours(first, 24) if start <= t <= end]
    assert inside
    for sun, _ in altitudes_at(pier, inside):
        assert round(sun, DEGREE_DECIMALS) <= -18.0


# --------------------------------------------------------------------------- #
# The selected night's local solar day
# --------------------------------------------------------------------------- #

_SCOTLAND = PierConfig(id="scotland", latitude=55.0, longitude=-3.0, elevation_m=0.0)
_HIGH_ARCTIC = PierConfig(id="high-arctic", latitude=88.0, longitude=0.0, elevation_m=0.0)


def _solar_day(pier: PierConfig, instant: datetime) -> tuple[datetime, datetime]:
    with no_network():
        return night_solar_day(pier, instant, dark_window(pier, instant))


def test_a_dark_window_selects_the_solar_day_that_holds_its_start() -> None:
    assert _solar_day(_london(), datetime(2026, 9, 8, 18, tzinfo=UTC)) == (
        datetime(2026, 9, 8, 11, 58, 9, tzinfo=UTC),
        datetime(2026, 9, 9, 11, 57, 48, tzinfo=UTC),
    )


def test_without_a_dark_window_past_the_midpoint_the_next_solar_day_applies() -> None:
    start, _ = _solar_day(_SCOTLAND, datetime(2026, 6, 21, 8, tzinfo=UTC))
    assert start.replace(second=0) == datetime(2026, 6, 21, 12, 13, tzinfo=UTC)


def test_without_a_dark_window_before_the_midpoint_the_current_solar_day_applies() -> None:
    start, _ = _solar_day(_SCOTLAND, datetime(2026, 6, 20, 22, tzinfo=UTC))
    assert start.date() == datetime(2026, 6, 20, tzinfo=UTC).date()


def test_in_continuous_polar_night_the_solar_day_is_the_dark_window() -> None:
    instant = datetime(2026, 12, 21, 15, tzinfo=UTC)
    assert _solar_day(_HIGH_ARCTIC, instant) == dark_window(_HIGH_ARCTIC, instant)


# --------------------------------------------------------------------------- #
# The night's hours
# --------------------------------------------------------------------------- #


def _night_hours(pier: PierConfig, instant: datetime) -> list[datetime]:
    with no_network():
        return night_hours(pier, instant, dark_window(pier, instant))


def _span(first: datetime, last: datetime) -> list[datetime]:
    return _hours(first, int((last - first) / timedelta(hours=1)) + 1)


def test_the_night_hours_are_every_hour_that_starts_inside_the_solar_day() -> None:
    assert _night_hours(_london(), datetime(2026, 9, 8, 18, tzinfo=UTC)) == _span(
        datetime(2026, 9, 8, 12, tzinfo=UTC), datetime(2026, 9, 9, 11, tzinfo=UTC)
    )


def test_the_night_hours_start_at_the_current_hour_when_it_comes_first() -> None:
    assert _night_hours(_london(), datetime(2026, 9, 9, 6, 30, tzinfo=UTC)) == _span(
        datetime(2026, 9, 9, 6, tzinfo=UTC), datetime(2026, 9, 10, 11, tzinfo=UTC)
    )


def test_without_a_dark_window_the_hours_run_from_now_to_tomorrows_noon() -> None:
    assert _night_hours(_SCOTLAND, datetime(2026, 6, 21, 8, tzinfo=UTC)) == _span(
        datetime(2026, 6, 21, 8, tzinfo=UTC), datetime(2026, 6, 22, 12, tzinfo=UTC)
    )


def test_without_a_dark_window_before_the_midpoint_the_hours_are_tonights() -> None:
    assert _night_hours(_SCOTLAND, datetime(2026, 6, 20, 22, tzinfo=UTC)) == _span(
        datetime(2026, 6, 20, 13, tzinfo=UTC), datetime(2026, 6, 21, 12, tzinfo=UTC)
    )
