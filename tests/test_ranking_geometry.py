"""Task 4.1-4.2: per-target observing geometry (design D3).

The geometry (observable window, maximum altitude and its instant, meridian
transit, moon separation) is checked against an independent Skyfield oracle so the
tests verify the astronomy rather than restate the implementation. The night is
2026-09-08 at a London pier, the same instant the golden suite uses.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from skyfield.api import Star, load, load_file, wgs84
from skyfield_data import get_skyfield_data_path

from pierpressure.core.catalog import load_catalog
from pierpressure.core.config import PierConfig
from pierpressure.core.horizon import flat, open_sky
from pierpressure.core.ranking import geometry_for
from pierpressure.core.sky import dark_window

from .offline_guard import no_network

_EPH = load_file(os.path.join(get_skyfield_data_path(), "de421.bsp"))
_TS = load.timescale(builtin=True)
_MOON = _EPH["moon"]
_EARTH = _EPH["earth"]
_INSTANT = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)

_CATALOG = {obj.id: obj for obj in load_catalog()}


def _london(**overrides: object) -> PierConfig:
    return PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0, **overrides)  # type: ignore[arg-type]


def _observer(pier: PierConfig) -> object:
    return _EARTH + wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)


def _oracle_alt(pier: PierConfig, obj_id: str, when: datetime) -> float:
    o = _CATALOG[obj_id]
    star = Star(ra_hours=o.ra_hours, dec_degrees=o.dec_degrees)
    alt, _, _ = _observer(pier).at(_TS.from_datetime(when)).observe(star).apparent().altaz()
    return float(alt.degrees)


def _oracle_moon_sep(pier: PierConfig, obj_id: str, when: datetime) -> float:
    o = _CATALOG[obj_id]
    star = Star(ra_hours=o.ra_hours, dec_degrees=o.dec_degrees)
    at = _observer(pier).at(_TS.from_datetime(when))
    return float(at.observe(star).apparent().separation_from(at.observe(_MOON).apparent()).degrees)


# --------------------------------------------------------------------------- #
# M31: rises high, transits during the night, above open sky all night
# --------------------------------------------------------------------------- #


def test_m31_window_lies_within_dark_window() -> None:
    pier = _london()
    with no_network():
        window = dark_window(pier, _INSTANT)
        geo = geometry_for(pier, _CATALOG["NGC0224"], window, _INSTANT)
    assert geo is not None
    dusk, dawn = window
    assert dusk is not None and dawn is not None
    assert dusk <= geo.window_start < geo.window_end <= dawn


def test_m31_above_open_sky_all_night_has_clamped_window() -> None:
    pier = _london()
    with no_network():
        window = dark_window(pier, _INSTANT)
        geo = geometry_for(pier, _CATALOG["NGC0224"], window, _INSTANT)
    assert geo is not None
    # It never sets below open sky during the night, so both edges clamp.
    assert geo.window_start == window[0]
    assert geo.window_end == window[1]


def test_m31_max_altitude_matches_oracle_peak() -> None:
    pier = _london()
    with no_network():
        window = dark_window(pier, _INSTANT)
        geo = geometry_for(pier, _CATALOG["NGC0224"], window, _INSTANT)
    assert geo is not None
    # The reported peak matches the altitude at the reported instant, and is a
    # true maximum (higher than a few minutes either side).
    assert geo.max_altitude == round(_oracle_alt(pier, "NGC0224", geo.max_instant), 3)
    assert _oracle_alt(pier, "NGC0224", geo.max_instant) >= _oracle_alt(
        pier, "NGC0224", geo.max_instant - timedelta(minutes=10)
    )
    assert _oracle_alt(pier, "NGC0224", geo.max_instant) >= _oracle_alt(
        pier, "NGC0224", geo.max_instant + timedelta(minutes=10)
    )


def test_m31_transit_is_a_meridian_crossing_within_the_window() -> None:
    pier = _london()
    with no_network():
        window = dark_window(pier, _INSTANT)
        geo = geometry_for(pier, _CATALOG["NGC0224"], window, _INSTANT)
    assert geo is not None
    # M31 transits during this night, so the transit lies inside the window and is
    # the altitude maximum (higher than 15 minutes either side).
    assert geo.window_start <= geo.transit_time <= geo.window_end
    at_transit = _oracle_alt(pier, "NGC0224", geo.transit_time)
    assert at_transit >= _oracle_alt(pier, "NGC0224", geo.transit_time - timedelta(minutes=15))
    assert at_transit >= _oracle_alt(pier, "NGC0224", geo.transit_time + timedelta(minutes=15))


def test_m31_moon_separation_measured_at_peak() -> None:
    pier = _london()
    with no_network():
        window = dark_window(pier, _INSTANT)
        geo = geometry_for(pier, _CATALOG["NGC0224"], window, _INSTANT)
    assert geo is not None
    assert geo.moon_separation == round(_oracle_moon_sep(pier, "NGC0224", geo.max_instant), 3)
    assert 0.0 <= geo.moon_separation <= 180.0


# --------------------------------------------------------------------------- #
# NGC6543 (Cat's Eye): circumpolar, transits in daylight before dusk
# --------------------------------------------------------------------------- #


def test_circumpolar_target_has_full_clamped_window() -> None:
    pier = _london()
    with no_network():
        window = dark_window(pier, _INSTANT)
        geo = geometry_for(pier, _CATALOG["NGC6543"], window, _INSTANT)
    assert geo is not None
    # Above the horizon all night -> window is the whole dark window.
    assert geo.window_start == window[0]
    assert geo.window_end == window[1]


def test_circumpolar_daytime_transit_is_outside_the_window() -> None:
    pier = _london()
    with no_network():
        window = dark_window(pier, _INSTANT)
        geo = geometry_for(pier, _CATALOG["NGC6543"], window, _INSTANT)
    assert geo is not None
    # Its meridian crossing falls in daylight before dusk, so it is earlier than
    # the window start; ranking still completed and produced a transit time.
    assert geo.transit_time < geo.window_start
    # Its peak within the night is at the dusk edge (it is descending all night).
    assert abs((geo.max_instant - geo.window_start).total_seconds()) < 60


# --------------------------------------------------------------------------- #
# A horizon mask carves a rising edge out of the window (refined, not grid-snapped)
# --------------------------------------------------------------------------- #


def test_mask_produces_refined_rising_edge() -> None:
    # A flat 45-degree mask: M31 climbs through 45 degrees during the night, so
    # the window starts at that crossing (interior) and clamps to dawn.
    pier = _london(horizon={"min_altitude": 45.0})
    assert pier.horizon_mask.alt_at(90.0) == 45.0
    with no_network():
        window = dark_window(pier, _INSTANT)
        geo = geometry_for(pier, _CATALOG["NGC0224"], window, _INSTANT)
    assert geo is not None
    dusk, dawn = window
    assert geo.window_start > dusk  # rising edge is interior, not clamped
    assert geo.window_end == dawn  # still above 45 at dawn -> clamped
    # At the refined rising edge the target's altitude sits at the 45-degree mask
    # (within a second of resolution).
    assert (
        _oracle_alt(pier, "NGC0224", geo.window_start) == round(45.0, 0)
        or abs(_oracle_alt(pier, "NGC0224", geo.window_start) - 45.0) < 0.05
    )


def test_open_sky_geometry_completes_for_many_targets() -> None:
    pier = PierConfig(id="os", latitude=51.5, longitude=-0.12, elevation_m=30.0)
    assert pier.horizon_mask.alt_at(180.0) == open_sky().alt_at(180.0)
    with no_network():
        window = dark_window(pier, _INSTANT)
        # A handful of real objects all produce consistent geometry or None.
        for obj_id in ("NGC0224", "NGC6205", "NGC7293", "NGC6543"):
            geo = geometry_for(pier, _CATALOG[obj_id], window, _INSTANT)
            if geo is not None:
                assert geo.window_start < geo.window_end
                assert flat(0.0).is_above(0.0, geo.max_altitude)
