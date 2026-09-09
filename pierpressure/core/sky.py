"""Pure, offline, deterministic sky math (design D5).

This module owns the astronomy: the astronomical-night window and the moon's
behaviour across it. It has no Home Assistant or MQTT imports (the core/delivery
boundary test guards that) and reads no network — the ephemeris and timescale
are loaded from the version-pinned ``skyfield-data`` package and Skyfield's
built-in timescale, so a verdict is a pure function of ``(pier, instant)``
(design D2, ADR-0004).

The exposed engine is:

- :func:`dark_window` — the astronomical-night boundary for the night selected
  relative to the evaluation instant, or ``(None, None)`` when there is no
  usable astronomical darkness;
- :func:`moon_info` — the moon's illumination, phase, and behaviour across a
  given dark window.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

from skyfield import almanac
from skyfield.api import load, load_file, wgs84
from skyfield_data import get_skyfield_data_path

from .config import PierConfig
from .model import Moon, MoonPhase

# Skyfield ships no type information, so its objects cross this boundary as
# ``Any`` (see the mypy override in pyproject). The wrapping helpers below keep
# that ``Any`` confined to this module and hand typed values back to callers.

# Astronomical night: the sun's centre is below this altitude (design/ADR-0003).
_ASTRONOMICAL_DEPTH_DEG = -18.0

# Search horizon for the instant-relative night selection (design D1a): a little
# before the instant (to catch a dusk already past when the instant is dark) and
# far enough ahead to contain the next full night.
_SEARCH_BACK = timedelta(hours=24)
_SEARCH_FORWARD = timedelta(hours=48)


@lru_cache(maxsize=1)
def _ephemeris() -> Any:
    """The version-pinned de421 ephemeris, loaded once from local data."""
    return load_file(os.path.join(get_skyfield_data_path(), "de421.bsp"))


@lru_cache(maxsize=1)
def _timescale() -> Any:
    """Skyfield's built-in timescale (offline; frozen by the pinned version)."""
    return load.timescale(builtin=True)


def _observer(pier: PierConfig) -> Any:
    """The topocentric observer at ``pier`` (earth + geographic position)."""
    eph = _ephemeris()
    return eph["earth"] + wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)


def _to_datetime(t: Any) -> datetime:
    """A Skyfield time to an aware-UTC ``datetime``."""
    result: datetime = t.utc_datetime().astimezone(UTC)
    return result


def _second_floor_window(
    start: datetime, end: datetime
) -> tuple[datetime, datetime] | tuple[None, None]:
    """Floor a window to whole seconds; null it if that collapses ``start < end``.

    Document timestamps are emitted at whole-second precision (design D3), so a
    grazing, sub-second night whose floored bounds are no longer strictly ordered
    provides no usable darkness and is reported as ``(None, None)`` — guaranteeing
    a non-null window always has ``start`` strictly before ``end``.
    """
    start = start.replace(microsecond=0)
    end = end.replace(microsecond=0)
    if start >= end:
        return (None, None)
    return (start, end)


def _night_transitions(pier: PierConfig, instant: datetime) -> list[tuple[datetime, bool]]:
    """Astronomical-night on/off flips across the search horizon.

    Returns ``(time, entering_night)`` pairs: ``True`` marks an astronomical dusk
    (the sun descending through -18 degrees), ``False`` an astronomical dawn.
    Built by collapsing Skyfield's five-level twilight classification down to the
    single "is it astronomical night?" boolean, so only true dusk/dawn crossings
    survive (a 3->2 civil/nautical step is not one).
    """
    eph = _ephemeris()
    ts = _timescale()
    location = wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)
    classify = almanac.dark_twilight_day(eph, location)

    t0 = ts.from_datetime(instant - _SEARCH_BACK)
    t1 = ts.from_datetime(instant + _SEARCH_FORWARD)
    times, values = almanac.find_discrete(t0, t1, classify)

    # State just before the first transition, so the first flip is oriented.
    current_night = int(classify(t0)) == 0

    flips: list[tuple[datetime, bool]] = []
    for t, value in zip(times, values, strict=True):
        entering_night = int(value) == 0
        if entering_night != current_night:
            flips.append((_to_datetime(t), entering_night))
            current_night = entering_night
    return flips


def _local_solar_day(pier: PierConfig, instant: datetime) -> tuple[datetime, datetime]:
    """The observer's local solar day (noon->noon) containing ``instant``.

    Anchors a continuous-night window to a stable boundary that does not slide on
    every recompute (design D1a). The solar day runs from one local solar noon
    (the sun's upper meridian transit) to the next, so it is centred on local
    solar midnight and envelops the local night. At the exact geographic poles the
    sun has no meridian transit, so the anchor falls back to the UTC calendar day.
    """
    if abs(pier.latitude) == 90.0:
        day_start = instant.replace(hour=0, minute=0, second=0, microsecond=0)
        return (day_start, day_start + timedelta(days=1))

    eph = _ephemeris()
    ts = _timescale()
    location = wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)
    transits = almanac.meridian_transits(eph, eph["sun"], location)

    t0 = ts.from_datetime(instant - timedelta(days=1))
    t1 = ts.from_datetime(instant + timedelta(days=1))
    times, values = almanac.find_discrete(t0, t1, transits)

    # value == 1 is the upper transit (local solar noon).
    noons = [_to_datetime(t) for t, value in zip(times, values, strict=True) if int(value) == 1]
    before = [n for n in noons if n <= instant]
    after = [n for n in noons if n > instant]
    return (before[-1], after[0])


def dark_window(
    pier: PierConfig, instant: datetime
) -> tuple[datetime, datetime] | tuple[None, None]:
    """The astronomical-night window for the night selected at ``instant``.

    Selects the night whose astronomical dawn is the first dawn at or after
    ``instant`` (design D1a): if the instant is already dark, the current night;
    otherwise the next upcoming one. Returns UTC dusk/dawn instants at whole-second
    precision with ``start`` strictly before ``end``, or ``(None, None)`` when
    there is no usable astronomical darkness.

    The two extreme-latitude cases both report zero twilight crossings and are
    told apart by the sun's altitude: continuously below -18 degrees is polar
    night (a non-null window anchored to the local solar day); continuously above
    is polar day (a null window).
    """
    flips = _night_transitions(pier, instant)

    if not flips:
        # No twilight crossings: continuous night or continuous day.
        eph = _ephemeris()
        ts = _timescale()
        observer = _observer(pier)
        alt, _, _ = observer.at(ts.from_datetime(instant)).observe(eph["sun"]).apparent().altaz()
        if alt.degrees < _ASTRONOMICAL_DEPTH_DEG:
            start, end = _local_solar_day(pier, instant)
            return _second_floor_window(start, end)
        return (None, None)

    # end = first astronomical dawn (leaving night) at or after the instant.
    dawns = [t for t, entering_night in flips if not entering_night and t >= instant]
    if not dawns:
        return (None, None)
    end = dawns[0]

    # start = the dusk (entering night) immediately preceding that dawn.
    dusks = [t for t, entering_night in flips if entering_night and t < end]
    if not dusks:
        return (None, None)
    start = dusks[-1]

    return _second_floor_window(start, end)


# Phase octants centred on the cardinal points (design D4). Each entry is the
# exclusive upper bound of a 45-degree octant; the new-moon octant wraps the
# 0/360 seam and is handled separately.
_PHASE_OCTANTS: tuple[tuple[float, MoonPhase], ...] = (
    (67.5, MoonPhase.WAXING_CRESCENT),
    (112.5, MoonPhase.FIRST_QUARTER),
    (157.5, MoonPhase.WAXING_GIBBOUS),
    (202.5, MoonPhase.FULL),
    (247.5, MoonPhase.WANING_GIBBOUS),
    (292.5, MoonPhase.LAST_QUARTER),
    (337.5, MoonPhase.WANING_CRESCENT),
)


def _phase_from_angle(angle_deg: float) -> MoonPhase:
    """Map a phase angle (moon-minus-sun elongation) to one of the eight phases.

    The angle is taken ``mod 360`` first, so a bare subtraction that went negative
    still lands in the right octant (design D4). New moon is the octant straddling
    the 0/360 seam, tested as ``>= 337.5 or < 22.5``.
    """
    angle = angle_deg % 360.0
    if angle >= 337.5 or angle < 22.5:
        return MoonPhase.NEW
    for upper_bound, phase in _PHASE_OCTANTS:
        if angle < upper_bound:
            return phase
    return MoonPhase.NEW  # unreachable: angle < 337.5 is covered above


def _altitude_deg(pier: PierConfig, target: object, when: datetime) -> float:
    """Apparent (refraction-free) altitude of ``target``'s centre in degrees."""
    ts = _timescale()
    observer = _observer(pier)
    alt, _, _ = observer.at(ts.from_datetime(when)).observe(target).apparent().altaz()
    return float(alt.degrees)


def moon_info(
    pier: PierConfig,
    window: tuple[datetime, datetime] | tuple[None, None],
    instant: datetime,
) -> Moon:
    """The moon's illumination, phase, and behaviour across ``window`` (design D4).

    ``illumination`` and ``phase`` are computed at ``instant`` and always present.
    ``up_during_dark``/``rise``/``set`` describe the moon within the dark window
    and are null when ``window`` is ``(None, None)``. "Above the horizon",
    moonrise, and moonset are pinned to the moon's **geometric centre crossing 0
    degrees** (no refraction or lunar-radius correction), so the boundary does not
    drift with a library's refraction defaults.
    """
    eph = _ephemeris()
    ts = _timescale()
    t = ts.from_datetime(instant)

    illumination = float(almanac.fraction_illuminated(eph, "moon", t))
    phase = _phase_from_angle(float(almanac.moon_phase(eph, t).degrees))

    start, end = window
    if start is None or end is None:
        return Moon(
            illumination=illumination,
            phase=phase,
            up_during_dark=None,
            rise=None,
            set=None,
        )

    location = wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)
    events = almanac.risings_and_settings(
        eph, eph["moon"], location, horizon_degrees=0.0, radius_degrees=0.0
    )
    times, values = almanac.find_discrete(
        ts.from_datetime(start),
        ts.from_datetime(end),
        events,
    )
    rises = [_to_datetime(t) for t, value in zip(times, values, strict=True) if int(value) == 1]
    sets = [_to_datetime(t) for t, value in zip(times, values, strict=True) if int(value) == 0]

    # Up at any point in the window: already up at dusk, or it rises during it.
    up_at_start = _altitude_deg(pier, eph["moon"], start) >= 0.0
    up_during_dark = up_at_start or bool(rises)

    return Moon(
        illumination=illumination,
        phase=phase,
        up_during_dark=up_during_dark,
        rise=rises[0] if rises else None,
        set=sets[0] if sets else None,
    )
