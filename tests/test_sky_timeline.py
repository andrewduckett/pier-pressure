"""Task 1.2: altitudes_at(pier, times) — sun and moon altitude for each timeline hour."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from pierpressure.core import sky
from pierpressure.core.config import PierConfig
from pierpressure.core.model import DEGREE_DECIMALS
from pierpressure.core.sky import _altitude_deg, _ephemeris, altitudes_at, dark_window

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
