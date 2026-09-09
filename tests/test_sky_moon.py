"""Task 3.2: moon_info(pier, dark_window, instant) — the moon across the window.

Uses an independent Skyfield oracle for illumination and the moon's geometric
centre altitude, so the tests check the astronomy rather than restate it.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from skyfield import almanac
from skyfield.api import load, load_file, wgs84
from skyfield_data import get_skyfield_data_path

from pierpressure.core.config import PierConfig
from pierpressure.core.model import MoonPhase
from pierpressure.core.sky import _phase_from_angle, dark_window, moon_info

from .offline_guard import no_network

_EPH = load_file(os.path.join(get_skyfield_data_path(), "de421.bsp"))
_TS = load.timescale(builtin=True)
_MOON = _EPH["moon"]
_EARTH = _EPH["earth"]


def _london() -> PierConfig:
    return PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0)


def _moon_alt_deg(pier: PierConfig, when: datetime) -> float:
    observer = _EARTH + wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)
    alt, _, _ = observer.at(_TS.from_datetime(when)).observe(_MOON).apparent().altaz()
    return float(alt.degrees)


def _oracle_illumination(when: datetime) -> float:
    return float(almanac.fraction_illuminated(_EPH, "moon", _TS.from_datetime(when)))


# --------------------------------------------------------------------------- #
# Phase octant mapping (design D4)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("angle", "phase"),
    [
        (0.0, MoonPhase.NEW),
        (22.4, MoonPhase.NEW),
        (22.5, MoonPhase.WAXING_CRESCENT),
        (67.5, MoonPhase.FIRST_QUARTER),
        (90.0, MoonPhase.FIRST_QUARTER),
        (112.5, MoonPhase.WAXING_GIBBOUS),
        (157.5, MoonPhase.FULL),
        (180.0, MoonPhase.FULL),
        (202.5, MoonPhase.WANING_GIBBOUS),
        (247.5, MoonPhase.LAST_QUARTER),
        (292.5, MoonPhase.WANING_CRESCENT),
        (337.4, MoonPhase.WANING_CRESCENT),
        (337.5, MoonPhase.NEW),
        (350.0, MoonPhase.NEW),
        (359.9, MoonPhase.NEW),
    ],
)
def test_phase_octant_mapping(angle: float, phase: MoonPhase) -> None:
    assert _phase_from_angle(angle) is phase


def test_phase_angle_is_taken_mod_360() -> None:
    # A negative or over-360 raw difference must fold back into the octants.
    assert _phase_from_angle(-10.0) is MoonPhase.NEW  # 350 deg
    assert _phase_from_angle(370.0) is MoonPhase.NEW  # 10 deg
    assert _phase_from_angle(-90.0) is MoonPhase.LAST_QUARTER  # 270 deg


# --------------------------------------------------------------------------- #
# Illumination and phase are always present
# --------------------------------------------------------------------------- #


def test_illumination_is_in_range_and_matches_oracle() -> None:
    pier = _london()
    instant = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)
    with no_network():
        window = dark_window(pier, instant)
        moon = moon_info(pier, window, instant)

    assert 0.0 <= moon.illumination <= 1.0
    assert moon.illumination == round(_oracle_illumination(instant), 2)
    assert isinstance(moon.phase, MoonPhase)


# --------------------------------------------------------------------------- #
# Behaviour across the dark window
# --------------------------------------------------------------------------- #


def test_moon_rises_within_window_is_reported_and_up_during_dark() -> None:
    pier = _london()
    instant = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)  # Sep 8->9 night
    with no_network():
        window = dark_window(pier, instant)
        moon = moon_info(pier, window, instant)

    start, end = window
    assert start is not None and end is not None
    # The moon is below the horizon at dusk and rises during the night.
    assert moon.rise is not None
    assert start <= moon.rise <= end
    assert moon.set is None
    assert moon.up_during_dark is True
    # rise is pinned to the geometric centre crossing 0 degrees.
    assert abs(_moon_alt_deg(pier, moon.rise)) < 0.05
    assert _moon_alt_deg(pier, moon.rise - timedelta(minutes=3)) < 0.0
    assert _moon_alt_deg(pier, moon.rise + timedelta(minutes=3)) > 0.0


def test_moon_sets_within_window_is_reported() -> None:
    pier = _london()
    instant = datetime(2026, 9, 18, 14, 0, tzinfo=UTC)  # moon up at dusk, sets in-window
    with no_network():
        window = dark_window(pier, instant)
        moon = moon_info(pier, window, instant)

    start, end = window
    assert start is not None and end is not None
    assert moon.set is not None
    assert start <= moon.set <= end
    assert moon.up_during_dark is True  # up at dusk
    assert abs(_moon_alt_deg(pier, moon.set)) < 0.05


def test_moon_down_all_night_is_not_up_during_dark() -> None:
    pier = _london()
    instant = datetime(2026, 9, 10, 14, 0, tzinfo=UTC)  # new-ish moon, below horizon all night
    with no_network():
        window = dark_window(pier, instant)
        moon = moon_info(pier, window, instant)

    assert moon.up_during_dark is False
    assert moon.rise is None
    assert moon.set is None


def test_across_window_fields_null_when_no_dark_window() -> None:
    pier = _london()
    instant = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)
    with no_network():
        moon = moon_info(pier, (None, None), instant)

    assert moon.up_during_dark is None
    assert moon.rise is None
    assert moon.set is None
    # illumination and phase remain present.
    assert 0.0 <= moon.illumination <= 1.0
    assert isinstance(moon.phase, MoonPhase)
