"""Target ranking: gate, geometry, score, bound, refine (design D3-D5).

This is pure core. For the selected night's dark window and the pier's horizon
mask, it ranks the eligible catalog objects (``core/catalog``) into the top few
worth pointing at, reusing the offline astronomy of ``core/sky`` (the pinned
ephemeris and timescale) and the canonical horizon of ``core/horizon``. It has no
Home Assistant, MQTT, or network imports — the boundary test enforces that — so
the same ``(pier, selected night)`` yields a byte-identical target list.

The pipeline (design D3):

1. **Coarse scan.** Sample every candidate's altitude and azimuth on a fixed time
   grid across the dark window, test each grid point against the mask, and derive
   a grid-resolution observable window, peak altitude, and the four sub-scores.
   The moon separation for this pass is computed analytically from the moon's own
   grid alt/az, so the scan needs one vectorized Skyfield call per object and no
   per-object root-finding.
2. **Bound.** Keep the candidates that clear the mask at all, ordered by coarse
   score with an ``id`` tie-break.
3. **Refine and re-gate.** Walk the ordered candidates, and for each replace the
   grid-resolution window edges with bisection root-finds and the transit with
   Skyfield's meridian-transit finder (the daytime transit of a circumpolar target
   included). Re-check the minimum-duration gate against the exact window, recompute
   the score from the refined geometry, and promote passers until ten are emitted
   or the pool is exhausted. Every emitted target is therefore both refined
   (exact whole-second times) and gate-satisfying.

All ranking parameters are fixed module constants this milestone (design D5), so
the ranking depends only on ``(pier, selected night)`` and is cached on that key.
"""

from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from skyfield import almanac
from skyfield.api import Star, wgs84

from .catalog import CatalogObject, load_catalog
from .config import PierConfig
from .horizon import Horizon
from .model import Moon, Target, TargetWindow
from .sky import _ephemeris, _timescale, _to_datetime

# --- Ranking parameters (fixed constants; validated in task 8.2) ----------- #

# The coarse time grid step across the dark window. Well below the minimum window
# so any object observable for the minimum duration lands several grid points
# above the mask and is never missed by the coarse scan (design D3/D5).
GRID_STEP = timedelta(minutes=5)

# The minimum observable window a target must clear to be listed (spec: gates).
MIN_WINDOW = timedelta(minutes=60)

# The list is bounded to the top N targets (design D3, ADR-0009).
TOP_N = 10

# Sub-score weights (design D4). They sum to 1 so the weighted sum stays in [0, 1]
# before scaling to 0-100.
#
# Validated against a known autumn night (task 8.2): the London pier on
# 2026-09-08. The default weights below were validated and RETAINED — the top of
# the list is objectively well placed (high, up most of the night, transiting
# in-window), and a well-placed autumn target such as M31 (NGC0224) scores 95/100.
# M31 is not top-10 on that night because it transits at ~02:00 UTC, well after the
# window midpoint, so several fainter but better-centred circumpolar objects rank
# above it. That is expected: brightness is deliberately NOT a ranking factor this
# milestone (it arrives with the equipment work), so the ranking answers "best
# placed tonight", not "brightest". See docs/roadmap.md M5.
WEIGHT_ALTITUDE = 0.35
WEIGHT_WINDOW = 0.30
WEIGHT_MOON = 0.25
WEIGHT_TRANSIT = 0.10

# The moon sub-score saturates to neutral at this separation (design D4).
_MOON_SEP_SATURATION_DEG = 90.0

# Bisection budget for a window-edge root-find; ~40 halvings of a 5-minute bracket
# reach whole-second precision with margin.
_BISECTION_STEPS = 40


# --------------------------------------------------------------------------- #
# Sub-scores and gates — pure functions over numbers and datetimes (design D4)
# --------------------------------------------------------------------------- #


def altitude_subscore(max_altitude_deg: float) -> float:
    """The altitude factor ``sin(altitude)`` — the inverse-airmass transmission proxy.

    Altitude is clamped to ``[0, 90]`` before the sine, so the factor rises
    monotonically from 0 at the horizon to 1 at the zenith and never leaves the
    unit interval.
    """
    altitude = max(0.0, min(90.0, max_altitude_deg))
    return math.sin(math.radians(altitude))


def window_subscore(observable: timedelta, dark: timedelta) -> float:
    """The window factor — observable duration as a fraction of the dark window."""
    if dark.total_seconds() <= 0.0:
        return 0.0
    return max(0.0, min(1.0, observable.total_seconds() / dark.total_seconds()))


def moon_subscore(separation_deg: float, illumination: float, moon_up: bool) -> float:
    """The moon factor ``1 - impact*(1 - sep_score)`` (design D4).

    ``impact`` is the moon's illuminated fraction when it is above the horizon at
    the target's peak, else 0 — so the factor is neutral (1) on a new moon or when
    the moon is down. ``sep_score`` grows linearly with separation to a neutral
    plateau at :data:`_MOON_SEP_SATURATION_DEG` degrees.
    """
    impact = illumination if moon_up else 0.0
    sep_score = max(0.0, min(1.0, separation_deg / _MOON_SEP_SATURATION_DEG))
    return 1.0 - impact * (1.0 - sep_score)


def transit_subscore(transit: datetime, start: datetime, end: datetime) -> float:
    """The transit factor — 1 at the window centre, 0 at an edge or outside it.

    A transit that falls in daylight (before dusk) or otherwise outside the
    observable window scores 0: its best moment is not during darkness.
    """
    half = (end - start).total_seconds() / 2.0
    if half <= 0.0:
        return 0.0
    mid = start + (end - start) / 2
    deviation = abs((transit - mid).total_seconds())
    return max(0.0, min(1.0, 1.0 - deviation / half))


def combined_score(altitude: float, window: float, moon: float, transit: float) -> int:
    """Combine the four sub-scores by weight and scale to an integer 0-100."""
    weighted = (
        WEIGHT_ALTITUDE * altitude
        + WEIGHT_WINDOW * window
        + WEIGHT_MOON * moon
        + WEIGHT_TRANSIT * transit
    )
    return round(100.0 * weighted)


def meets_minimum(start: datetime, end: datetime) -> bool:
    """Whether an observable window spans at least the minimum duration (the gate)."""
    return (end - start) >= MIN_WINDOW


def observable_window(times: list[datetime], above: list[bool]) -> tuple[int, int] | None:
    """The longest contiguous above-mask run as ``(start_index, end_index)``.

    An irregular skyline can leave more than one above-mask interval; the longest
    is the one an observer plans around (design D3). Ties keep the earliest run, so
    the choice is deterministic. Returns ``None`` when no grid point is above the
    mask.
    """
    best: tuple[int, int] | None = None
    best_length = -1
    index = 0
    count = len(above)
    while index < count:
        if above[index]:
            end = index
            while end + 1 < count and above[end + 1]:
                end += 1
            if end - index > best_length:
                best_length = end - index
                best = (index, end)
            index = end + 1
        else:
            index += 1
    return best


# --------------------------------------------------------------------------- #
# Per-target geometry (Skyfield, reusing core/sky's pinned loaders)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Geometry:
    """A target's refined observing geometry for the night (design D3).

    ``window_start``/``window_end`` bound the observable window (whole-second UTC),
    clamped to the dark window. ``max_altitude`` (degrees, rounded to the emitted
    precision) is the peak reached inside the window, at ``max_instant``.
    ``transit_time`` is the meridian crossing for that day and may fall outside the
    window. ``moon_separation`` (degrees, rounded) is measured at ``max_instant``,
    where ``moon_up_at_peak`` records whether the moon was above the horizon.
    """

    window_start: datetime
    window_end: datetime
    max_altitude: float
    max_instant: datetime
    transit_time: datetime
    moon_separation: float
    moon_up_at_peak: bool


def _floor_second(when: datetime) -> datetime:
    """Truncate to whole-second UTC, matching the document's time normalization."""
    return when.replace(microsecond=0)


def _grid_times(start: datetime, end: datetime) -> list[datetime]:
    """Fixed-step grid across ``[start, end]``, always including the ``end`` edge."""
    times: list[datetime] = []
    current = start
    while current < end:
        times.append(current)
        current += GRID_STEP
    times.append(end)
    return times


def _star(obj: CatalogObject) -> Any:
    """A Skyfield ``Star`` for a catalog object; precession is handled downstream."""
    return Star(ra_hours=obj.ra_hours, dec_degrees=obj.dec_degrees)


def _alt_az_at(observer: Any, ts: Any, star: Any, when: datetime) -> tuple[float, float]:
    """Apparent (altitude, azimuth) of ``star`` in degrees at one instant."""
    alt, az, _ = observer.at(ts.from_datetime(when)).observe(star).apparent().altaz()
    return float(alt.degrees), float(az.degrees)


def _peak_measures(
    observer: Any, ts: Any, eph: Any, star: Any, when: datetime
) -> tuple[float, float, bool]:
    """The star's altitude (degrees), its moon separation (degrees), and moon-up at ``when``.

    The observer state and the star's apparent position are computed once and both
    the altitude and the moon separation are read from it, so a finalist's peak
    needs one Skyfield evaluation instead of two.
    """
    at = observer.at(ts.from_datetime(when))
    star_apparent = at.observe(star).apparent()
    moon_apparent = at.observe(eph["moon"]).apparent()
    altitude, _, _ = star_apparent.altaz()
    separation = float(star_apparent.separation_from(moon_apparent).degrees)
    moon_alt, _, _ = moon_apparent.altaz()
    return float(altitude.degrees), separation, float(moon_alt.degrees) >= 0.0


def _sep_from_altaz(alt1: float, az1: float, alt2: float, az2: float) -> float:
    """Angular separation (degrees) between two horizontal coordinates.

    The spherical law of cosines, used for the coarse-pass moon separation so the
    scan needs no extra Skyfield call per object; the emitted separation is
    recomputed exactly from the ephemeris during refinement.
    """
    a1, a2 = math.radians(alt1), math.radians(alt2)
    cosine = math.sin(a1) * math.sin(a2) + math.cos(a1) * math.cos(a2) * math.cos(
        math.radians(az1 - az2)
    )
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _refine_edge(
    observer: Any, ts: Any, star: Any, horizon: Horizon, below: datetime, above: datetime
) -> datetime:
    """Bisect the mask crossing between a below-mask and an above-mask instant.

    ``below`` and ``above`` bracket the crossing (either may be the earlier of the
    two). Returns the above-mask side, truncated to a whole second.
    """
    low, high = below, above
    for _ in range(_BISECTION_STEPS):
        if abs((high - low).total_seconds()) <= 1.0:
            break
        mid = low + (high - low) / 2
        alt, az = _alt_az_at(observer, ts, star, mid)
        if alt - horizon.alt_at(az) >= 0.0:
            high = mid
        else:
            low = mid
    return _floor_second(high)


def _transit_time(
    eph: Any, ts: Any, star: Any, location: Any, window: tuple[datetime, datetime]
) -> datetime:
    """The meridian transit for that day, nearest the window's midpoint (design D3).

    Uses Skyfield's ``meridian_transits`` — the same facility ``core/sky`` uses for
    the sun's transit — over the day around the night, so a circumpolar target's
    daytime transit is captured rather than lost off a night-only grid.
    """
    start, end = window
    midpoint = start + (end - start) / 2
    transits = almanac.meridian_transits(eph, star, location)
    times, values = almanac.find_discrete(
        ts.from_datetime(midpoint - timedelta(days=1)),
        ts.from_datetime(midpoint + timedelta(days=1)),
        transits,
    )
    uppers = [_to_datetime(t) for t, value in zip(times, values, strict=True) if int(value) == 1]
    if not uppers:  # pragma: no cover - only at the exact geographic pole
        return _floor_second(midpoint)
    best = min(uppers, key=lambda upper: abs((upper - midpoint).total_seconds()))
    return _floor_second(best)


def _refine(
    observer: Any,
    ts: Any,
    eph: Any,
    location: Any,
    horizon: Horizon,
    window: tuple[datetime, datetime],
    times: list[datetime],
    obj: CatalogObject,
    start_index: int,
    end_index: int,
) -> Geometry:
    """Turn a grid-resolution above-mask run into exact, whole-second geometry."""
    dusk, dawn = window
    star = _star(obj)
    last = len(times) - 1

    # A run touching a grid edge is clamped to the dark-window boundary; an
    # interior edge is the true mask crossing found by bisection (design D3).
    if start_index == 0:
        window_start = dusk
    else:
        window_start = _refine_edge(
            observer, ts, star, horizon, times[start_index - 1], times[start_index]
        )
    if end_index == last:
        window_end = dawn
    else:
        window_end = _refine_edge(
            observer, ts, star, horizon, times[end_index + 1], times[end_index]
        )
    window_start = max(window_start, dusk)
    window_end = min(window_end, dawn)

    transit = _transit_time(eph, ts, star, location, window)

    # The peak is at the transit when the transit is within the window, otherwise
    # at the nearer window edge (the target is monotone across the window there).
    if window_start <= transit <= window_end:
        max_instant = transit
    elif transit < window_start:
        max_instant = window_start
    else:
        max_instant = window_end

    max_altitude, separation, moon_up = _peak_measures(observer, ts, eph, star, max_instant)
    return Geometry(
        window_start=window_start,
        window_end=window_end,
        max_altitude=round(max_altitude, 3),
        max_instant=max_instant,
        transit_time=transit,
        moon_separation=round(separation, 3),
        moon_up_at_peak=moon_up,
    )


def geometry_for(
    pier: PierConfig,
    obj: CatalogObject,
    window: tuple[datetime, datetime] | tuple[None, None],
    instant: datetime,
) -> Geometry | None:
    """The refined geometry of one catalog object, or ``None`` if it never clears the mask.

    Exposed for testing the per-target geometry directly; the pipeline shares the
    same coarse-scan and refinement code.
    """
    start, end = window
    if start is None or end is None:
        return None
    eph = _ephemeris()
    ts = _timescale()
    location = wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)
    observer = eph["earth"] + location
    star = _star(obj)
    times = _grid_times(start, end)
    alt, az, _ = observer.at(ts.from_datetimes(times)).observe(star).apparent().altaz()
    alt_deg, az_deg = alt.degrees, az.degrees
    above = [
        pier.horizon_mask.is_above(float(az_deg[i]), float(alt_deg[i])) for i in range(len(times))
    ]
    run = observable_window(times, above)
    if run is None:
        return None
    return _refine(
        observer, ts, eph, location, pier.horizon_mask, (start, end), times, obj, run[0], run[1]
    )


# --------------------------------------------------------------------------- #
# The pipeline and its per-night cache (design D3, D5)
# --------------------------------------------------------------------------- #


# One scored candidate carried from the coarse scan into the refinement walk.
@dataclass(frozen=True)
class _Scored:
    score: int
    obj: CatalogObject
    start_index: int
    end_index: int


# Per-night ranking cache keyed by (pier identity + horizon + dark window). The
# ranking parameters are fixed constants, so they do not enter the key; design D5
# requires adding any that becomes per-pier configuration. The cache is a bounded
# LRU so a persistent container recomputing night after night keeps only the most
# recent few rankings rather than retaining one entry per night forever. It is a
# performance optimization only, so eviction never affects correctness (design D5).
_CACHE_MAXSIZE = 16
_rank_cache: OrderedDict[tuple[Any, ...], tuple[Target, ...]] = OrderedDict()


def _cache_key(pier: PierConfig, window: tuple[datetime, datetime]) -> tuple[Any, ...]:
    return (
        pier.id,
        pier.latitude,
        pier.longitude,
        pier.elevation_m,
        pier.horizon_mask.samples,
        window[0],
        window[1],
    )


def rank_targets(
    pier: PierConfig,
    instant: datetime,
    window: tuple[datetime, datetime] | tuple[None, None],
    moon: Moon,
) -> list[Target]:
    """The ordered top-:data:`TOP_N` targets for the selected night (empty if none).

    Returns an empty list when the night has no dark window. Otherwise the result
    is cached per ``(pier, selected night)``: a recompute within the same night
    reuses the same ranking rather than rescanning the catalog (design D5).
    """
    start, end = window
    if start is None or end is None:
        return []
    key = _cache_key(pier, (start, end))
    cached = _rank_cache.get(key)
    if cached is not None:
        _rank_cache.move_to_end(key)  # most-recently-used
        return list(cached)
    result = tuple(_rank(pier, (start, end), moon))
    _rank_cache[key] = result
    if len(_rank_cache) > _CACHE_MAXSIZE:
        _rank_cache.popitem(last=False)  # evict the least-recently-used night
    return list(result)


def _rank(pier: PierConfig, window: tuple[datetime, datetime], moon: Moon) -> list[Target]:
    """The full gate-geometry-score-bound-refine pipeline for one night."""
    start, end = window
    eph = _ephemeris()
    ts = _timescale()
    location = wgs84.latlon(pier.latitude, pier.longitude, elevation_m=pier.elevation_m)
    observer = eph["earth"] + location
    horizon = pier.horizon_mask
    dark_duration = end - start

    times = _grid_times(start, end)
    positions = observer.at(ts.from_datetimes(times))
    # The moon's grid alt/az once, so the coarse moon separation is analytic.
    moon_alt, moon_az, _ = positions.observe(eph["moon"]).apparent().altaz()
    moon_alt_deg, moon_az_deg = moon_alt.degrees, moon_az.degrees

    scored: list[_Scored] = []
    for obj in load_catalog():
        alt, az, _ = positions.observe(_star(obj)).apparent().altaz()
        alt_deg, az_deg = alt.degrees, az.degrees
        above = [horizon.is_above(float(az_deg[i]), float(alt_deg[i])) for i in range(len(times))]
        run = observable_window(times, above)
        if run is None:
            continue
        start_index, end_index = run
        peak = max(range(start_index, end_index + 1), key=lambda i: float(alt_deg[i]))
        coarse_separation = _sep_from_altaz(
            float(alt_deg[peak]),
            float(az_deg[peak]),
            float(moon_alt_deg[peak]),
            float(moon_az_deg[peak]),
        )
        coarse_score = combined_score(
            altitude_subscore(float(alt_deg[peak])),
            window_subscore(times[end_index] - times[start_index], dark_duration),
            moon_subscore(coarse_separation, moon.illumination, float(moon_alt_deg[peak]) >= 0.0),
            # Coarse transit proxy: the grid peak, refined exactly for finalists.
            transit_subscore(times[peak], times[start_index], times[end_index]),
        )
        scored.append(_Scored(coarse_score, obj, start_index, end_index))

    # Order by coarse score, ties by designation, then refine top-down until TOP_N
    # pass the exact gate (design D3, step 6).
    scored.sort(key=lambda item: (-item.score, item.obj.id))

    emitted: list[Target] = []
    for candidate in scored:
        geo = _refine(
            observer,
            ts,
            eph,
            location,
            horizon,
            window,
            times,
            candidate.obj,
            candidate.start_index,
            candidate.end_index,
        )
        if not meets_minimum(geo.window_start, geo.window_end):
            continue
        score = combined_score(
            altitude_subscore(geo.max_altitude),
            window_subscore(geo.window_end - geo.window_start, dark_duration),
            moon_subscore(geo.moon_separation, moon.illumination, geo.moon_up_at_peak),
            transit_subscore(geo.transit_time, geo.window_start, geo.window_end),
        )
        emitted.append(
            Target(
                id=candidate.obj.id,
                name=candidate.obj.name,
                type=candidate.obj.type,
                score=score,
                window=TargetWindow(start=geo.window_start, end=geo.window_end),
                max_altitude=geo.max_altitude,
                transit_time=geo.transit_time,
                moon_separation=geo.moon_separation,
            )
        )
        if len(emitted) >= TOP_N:
            break

    emitted.sort(key=lambda target: (-target.score, target.id))
    return emitted
