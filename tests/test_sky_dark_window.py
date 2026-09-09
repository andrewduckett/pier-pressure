"""Task 3.1: dark_window(pier, instant) — astronomical-night boundary (design D1a).

Boundaries are verified against an independent Skyfield sun-altitude oracle (the
sun's geometric/apparent centre at -18 degrees), not hard-coded magic numbers, so
the tests assert the math rather than echo the implementation.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from skyfield.api import load, load_file, wgs84
from skyfield_data import get_skyfield_data_path

from pierpressure.core.config import PierConfig
from pierpressure.core.sky import _second_floor_window, dark_window

from .offline_guard import no_network

# Independent oracle: load Skyfield ourselves to measure the sun's altitude.
_EPH = load_file(os.path.join(get_skyfield_data_path(), "de421.bsp"))
_TS = load.timescale(builtin=True)
_SUN = _EPH["sun"]
_EARTH = _EPH["earth"]


def _sun_alt_deg(pier: PierConfig, when: datetime) -> float:
    observer = _EARTH + wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)
    alt, _, _ = observer.at(_TS.from_datetime(when)).observe(_SUN).apparent().altaz()
    return float(alt.degrees)


def _london() -> PierConfig:
    return PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0)


def test_normal_midlatitude_night_from_daytime_instant() -> None:
    pier = _london()
    instant = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)  # daytime

    with no_network():
        start, end = dark_window(pier, instant)

    assert start is not None and end is not None
    assert start < end
    assert start >= instant  # the upcoming night's dusk is ahead of a daytime instant

    # start is astronomical dusk: sun crossing -18 going down.
    assert abs(_sun_alt_deg(pier, start) - (-18.0)) < 0.05
    assert _sun_alt_deg(pier, start - timedelta(minutes=2)) > -18.0
    assert _sun_alt_deg(pier, start + timedelta(minutes=2)) < -18.0

    # end is astronomical dawn: sun crossing -18 going up.
    assert abs(_sun_alt_deg(pier, end) - (-18.0)) < 0.05
    assert _sun_alt_deg(pier, end - timedelta(minutes=2)) < -18.0
    assert _sun_alt_deg(pier, end + timedelta(minutes=2)) > -18.0


def test_instant_already_within_night_selects_the_current_night() -> None:
    pier = _london()
    # 01:00 UTC sits inside the Sep 8->9 night (dusk ~20:30, dawn ~03:26).
    instant = datetime(2026, 9, 9, 1, 0, tzinfo=UTC)

    with no_network():
        start, end = dark_window(pier, instant)

    assert start is not None and end is not None
    assert start < instant  # dusk already past
    assert end > instant  # dawn ahead
    # end is the FIRST dawn at or after the instant.
    assert end < instant + timedelta(hours=4)
    assert abs(_sun_alt_deg(pier, end) - (-18.0)) < 0.05


def test_continuous_non_night_yields_null_window() -> None:
    # Tromso around midsummer: the sun never falls below -18 degrees.
    pier = PierConfig(id="tromso", latitude=69.65, longitude=18.96, elevation_m=10.0)
    instant = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)

    with no_network():
        start, end = dark_window(pier, instant)

    assert start is None
    assert end is None


def test_continuous_astronomical_night_is_nonnull_and_stable() -> None:
    # 88N in deep winter: the sun stays below -18 all solar day (continuous night).
    pier = PierConfig(id="high-arctic", latitude=88.0, longitude=0.0, elevation_m=0.0)
    instant_a = datetime(2026, 12, 21, 15, 0, tzinfo=UTC)
    instant_b = datetime(2026, 12, 21, 23, 0, tzinfo=UTC)  # same solar day (noon ~11:58)

    with no_network():
        window_a = dark_window(pier, instant_a)
        window_b = dark_window(pier, instant_b)

    start_a, end_a = window_a
    assert start_a is not None and end_a is not None
    assert start_a < end_a
    # Anchored window envelops the night and is ~one solar day long.
    assert start_a <= instant_a <= end_a
    assert timedelta(hours=23) <= (end_a - start_a) <= timedelta(hours=25)
    # Stable across two recomputes in the same anchored period (no sliding).
    assert window_a == window_b


def test_exact_pole_falls_back_to_utc_day_anchor() -> None:
    # At the exact pole the sun does not transit a meridian, so the anchor falls
    # back to the UTC calendar day (design D1a). Winter => continuous night.
    pier = PierConfig(id="north-pole", latitude=90.0, longitude=0.0, elevation_m=0.0)
    instant = datetime(2026, 12, 21, 12, 0, tzinfo=UTC)

    with no_network():
        start, end = dark_window(pier, instant)

    assert start == datetime(2026, 12, 21, 0, 0, 0, tzinfo=UTC)
    assert end == datetime(2026, 12, 22, 0, 0, 0, tzinfo=UTC)


def test_subsecond_night_collapses_to_null_on_whole_second_truncation() -> None:
    # A grazing night whose whole-second floor gives start >= end has no usable
    # darkness and is reported null; a genuine >=1s night survives.
    base = datetime(2026, 9, 8, 0, 0, 0, tzinfo=UTC)
    graze = _second_floor_window(
        base.replace(microsecond=400_000), base.replace(microsecond=900_000)
    )
    assert graze == (None, None)

    kept = _second_floor_window(
        base.replace(second=0, microsecond=900_000), base.replace(second=1, microsecond=200_000)
    )
    assert kept == (
        datetime(2026, 9, 8, 0, 0, 0, tzinfo=UTC),
        datetime(2026, 9, 8, 0, 0, 1, tzinfo=UTC),
    )
