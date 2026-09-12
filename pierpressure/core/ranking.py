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

The ranking's curve and weight parameters are fixed module constants (design
D5/D6), so the ranking depends only on ``(pier, selected night)`` — including the
pier's optional rig, which shapes the field-of-view term — and is cached on that
key.
"""

from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

from skyfield import almanac
from skyfield.api import Star, wgs84

from .catalog import CatalogObject, load_catalog
from .config import PierConfig, Rig
from .horizon import Horizon
from .model import Moon, Target, TargetWindow
from .sky import _ephemeris, _timescale, _to_datetime

# --- Ranking parameters (fixed constants; validated on a real night) -------- #

# The coarse time grid step across the dark window. Well below the minimum window
# so any object observable for the minimum duration lands several grid points
# above the mask and is never missed by the coarse scan (design D3/D5).
GRID_STEP = timedelta(minutes=5)

# The minimum observable window a target must clear to be listed (spec: gates).
MIN_WINDOW = timedelta(minutes=60)

# The list is bounded to the top N targets (design D3, ADR-0009).
TOP_N = 10

# Base sub-score weights (design D5/D6; validated in task 6.1). SIX factors now:
# the four geometry terms plus brightness and field-of-view fit. The base weights
# sum to 1, but the score renormalises over the LIVE factors for each
# (pier, target) — so a rig-less pier, an unknown size, or an unknown brightness
# drops only that factor and the remaining weights are rescaled to sum to 1
# (ADR-0010). Geometry stays dominant (0.80 of the base) and the two new terms are
# deliberately modest (0.20 combined) so neither dominates placement.
#
# Re-validated on the M5 London autumn night (2026-09-08). With brightness now a
# factor, a bright, well-placed showpiece rises where M5 ranked fainter but
# better-centred objects above it; a well-framed bright target (given a rig) ranks
# as expected. The geometry proportions keep M5's ordering-within-geometry
# (altitude > window > moon > transit); brightness enters just below transit's
# neighbourhood and FOV a touch below brightness, so the ranking still answers
# "best placed" first and breaks near-ties on suitability. See docs/roadmap.md M6.
WEIGHT_ALTITUDE = 0.28
WEIGHT_WINDOW = 0.24
WEIGHT_MOON = 0.18
WEIGHT_TRANSIT = 0.10
WEIGHT_BRIGHTNESS = 0.12
WEIGHT_FOV = 0.08

# The pre-scaled renormalised weighted mean (and the derived field of view) are
# rounded to this fixed decimal precision before the final integer scaling
# (design D9), so the added atan/renormalisation float work inherits the same
# stable-precision posture as the rest of the document (ADR-0004).
_SCORE_DECIMALS = 6

# The moon sub-score saturates to neutral at this separation (design D4).
_MOON_SEP_SATURATION_DEG = 90.0

# --- Field-of-view-fit framing curve (design D3; validated in task 6.1) ----- #
#
# The fit sub-score is a curve on ``r = size_arcmin / fov_short_arcmin`` — an
# object's major axis as a fraction of the short edge of the derived field of
# view. Validated against the M5 London autumn night (2026-09-08): with a modest
# refractor rig (600 mm, APS-C), the sweet band selects the framed showpieces
# (mid-size galaxies and nebulae) over both specks and objects too large to fit.
#
# A speck (``r`` near 0) scores this floor rather than 0 — a tiny object is still
# imageable, just not ideal.
_FOV_SPECK_FLOOR = 0.20
# The sweet band [low, high]: a comfortable fraction of the frame scores ~1.0.
_FOV_SWEET_LOW = 0.10
_FOV_SWEET_HIGH = 0.60
# At ``r = 1`` the object exactly spans the short edge — it just fits, so it is
# marked down from the sweet band but not penalised as heavily as an oversize one.
_FOV_FILL_SCORE = 0.60
# Past ``r = 1`` the object no longer fits; the score decays reciprocally toward 0
# so a slightly-too-big (mosaic-able) object beats a hugely-too-big one, with no
# hard cliff (design D3). Larger constant -> steeper decay.
_FOV_OVERSIZE_DECAY = 1.5

# --- Brightness curve anchors, one pair per physical scale (design D4) ------ #
#
# Surface brightness (mag/arcsec², roughly 18-25) and integrated magnitude
# (roughly 0-13) are different physical scales, so each maps through its OWN
# anchors — never one shared curve, which would score a surface-brightness object
# as far fainter than a magnitude object purely because its numbers are larger.
# Brighter (numerically smaller) scores higher; each is a linear ramp clamped to
# ``[0, 1]``. Anchors validated on the M5 London night (task 6.1): the surface
# anchors bracket the catalog's populated SurfBr range and the magnitude anchors
# bracket the candidate pool below the MAGNITUDE_LIMIT cutoff.
_SB_BRIGHT = 18.0  # mag/arcsec² at or below which surface brightness scores 1.0
_SB_FAINT = 25.0  # mag/arcsec² at or above which it scores 0.0
_MAG_BRIGHT = 3.0  # integrated magnitude at or below which brightness scores 1.0
_MAG_FAINT = 13.0  # integrated magnitude at or above which it scores 0.0

# Qualitative thresholds for the additive equipment ``reasons[]`` entries (design
# D8). A framing sub-score at or above the well-framed threshold reads as "frames
# well"; a brightness sub-score at or above the bright threshold reads as "bright".
_WELL_FRAMED_THRESHOLD = 0.80
_BRIGHT_THRESHOLD = 0.60

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


def fov_fit_subscore(r: float) -> float:
    """The framing factor over ``r = size / fov_short`` — a curve, not a cliff (design D3).

    A speck (``r`` near 0) scores :data:`_FOV_SPECK_FLOOR`; the sweet band
    ``[_FOV_SWEET_LOW, _FOV_SWEET_HIGH]`` scores 1.0; between the floor and the
    band the score ramps up linearly; from the band's top to ``r = 1`` (the object
    exactly spanning the short edge) it declines to :data:`_FOV_FILL_SCORE`; past
    ``r = 1`` it decays reciprocally toward 0, so an oversize object is penalised
    progressively rather than dropped at a hard cliff. Clamped to ``[0, 1]``.
    """
    if r <= 0.0:
        return _FOV_SPECK_FLOOR
    if r < _FOV_SWEET_LOW:
        ramp = r / _FOV_SWEET_LOW
        return _FOV_SPECK_FLOOR + (1.0 - _FOV_SPECK_FLOOR) * ramp
    if r <= _FOV_SWEET_HIGH:
        return 1.0
    if r <= 1.0:
        decline = (r - _FOV_SWEET_HIGH) / (1.0 - _FOV_SWEET_HIGH)
        return 1.0 - decline * (1.0 - _FOV_FILL_SCORE)
    # r > 1: the denominator exceeds 1, so the result is always in (0, _FOV_FILL_SCORE]
    # — already within [0, 1], and it approaches but never reaches 0 (no cliff).
    return _FOV_FILL_SCORE / (1.0 + _FOV_OVERSIZE_DECAY * (r - 1.0))


def _ramp(value: float, bright: float, faint: float) -> float:
    """A brightness ramp: 1.0 at or below ``bright``, 0.0 at or above ``faint``.

    ``bright`` and ``faint`` are magnitudes on one scale, where a smaller number is
    brighter, so the ramp falls linearly from the bright anchor to the faint one
    and is clamped to ``[0, 1]``.
    """
    span = faint - bright
    return max(0.0, min(1.0, (faint - value) / span))


def brightness_subscore(surface_brightness: float | None, magnitude: float | None) -> float | None:
    """The brightness factor, or ``None`` when neither input is known (design D4).

    Surface brightness is preferred where recorded — for extended objects it
    predicts detectability far better than integrated magnitude — else integrated
    magnitude, else ``None`` so the caller drops the term. Because the two are
    different physical scales, each maps through its own anchors (:data:`_SB_BRIGHT`
    /:data:`_SB_FAINT` and :data:`_MAG_BRIGHT`/:data:`_MAG_FAINT`), never a single
    shared curve. Brighter scores higher; the result is clamped to ``[0, 1]``.
    """
    if surface_brightness is not None:
        return _ramp(surface_brightness, _SB_BRIGHT, _SB_FAINT)
    if magnitude is not None:
        return _ramp(magnitude, _MAG_BRIGHT, _MAG_FAINT)
    return None


def combined_score(
    altitude: float,
    window: float,
    moon: float,
    transit: float,
    brightness: float | None = None,
    fov_fit: float | None = None,
) -> int:
    """Combine the live sub-scores and scale to an integer 0-100 (design D5, D9).

    The four geometry factors always contribute; ``brightness`` and ``fov_fit``
    contribute only when known (not ``None``). The base weights of the live factors
    are renormalised to sum to 1 before the weighted mean, so a missing rig, an
    unknown size, or an unknown brightness drops only its own factor rather than
    substituting a guessed value (ADR-0010). The pre-scaled weighted mean is
    rounded to a fixed decimal precision before the final integer scaling (design
    D9), shrinking the epsilon surface around integer ``.5`` boundaries so a score
    is far less likely to flip across architectures. The result is clamped to
    ``[0, 100]``.
    """
    terms: list[tuple[float, float]] = [
        (WEIGHT_ALTITUDE, altitude),
        (WEIGHT_WINDOW, window),
        (WEIGHT_MOON, moon),
        (WEIGHT_TRANSIT, transit),
    ]
    if brightness is not None:
        terms.append((WEIGHT_BRIGHTNESS, brightness))
    if fov_fit is not None:
        terms.append((WEIGHT_FOV, fov_fit))
    total_weight = sum(weight for weight, _ in terms)
    weighted = sum(weight * value for weight, value in terms) / total_weight
    weighted = round(weighted, _SCORE_DECIMALS)
    return max(0, min(100, round(100.0 * weighted)))


def _fov_short_arcmin(rig: Rig | None) -> float | None:
    """The rig's short-edge field of view in arcminutes, or ``None`` with no rig.

    The derived field of view (degrees) is rounded to the fixed score precision
    before conversion to arcminutes (design D9), so the ``r = size / fov_short``
    that drives the framing curve inherits the same stable-precision posture as
    the score itself.
    """
    if rig is None:
        return None
    return round(rig.fov_short_deg, _SCORE_DECIMALS) * 60.0


def _fov_fit_for(obj: CatalogObject, fov_short_arcmin: float | None) -> float | None:
    """The framing sub-score for ``obj``, or ``None`` when it does not contribute.

    Contributes only when a rig is configured (``fov_short_arcmin`` is known) and
    the object has a recorded size — otherwise the term drops rather than guessing
    (design D5).
    """
    if fov_short_arcmin is None or obj.size_arcmin is None:
        return None
    return fov_fit_subscore(obj.size_arcmin / fov_short_arcmin)


@lru_cache(maxsize=1)
def _catalog_by_id() -> dict[str, CatalogObject]:
    """An ``id -> object`` index of the catalog, cached like the catalog itself.

    Equipment reasons classify framing and brightness from the SAME raw catalog
    facts the score used, recovered here by the pick's designation — not the values
    carried on the emitted ``Target``, which are rounded to the document's fixed
    precision. Reading the raw facts keeps a reason from ever disagreeing with the
    sub-score that actually drove the score near a rounding boundary.
    """
    return {obj.id: obj for obj in load_catalog()}


def equipment_reasons(rig: Rig | None, target: Target) -> list[str]:
    """Additive equipment-aware ``reasons[]`` entries for the top pick (design D8).

    A framing entry is emitted whenever a rig is configured and the pick has a
    known size, describing how it frames — well framed, small, nearly filling the
    frame, or larger than the field of view. A brightness entry is emitted when the
    pick reads as bright. The classification uses the pick's raw catalog facts (the
    same inputs the score used), so it is deterministic and never contradicts the
    score. Returns an empty list when no equipment input is known, or when the pick
    is not a catalog object.
    """
    obj = _catalog_by_id().get(target.id)
    if obj is None:
        return []
    reasons: list[str] = []
    name = target.name or target.id
    fov_short_arcmin = _fov_short_arcmin(rig)
    if fov_short_arcmin is not None and obj.size_arcmin is not None:
        ratio = obj.size_arcmin / fov_short_arcmin
        if fov_fit_subscore(ratio) >= _WELL_FRAMED_THRESHOLD:
            reasons.append(f"Top pick {name} frames well in your rig.")
        elif ratio > 1.0:
            reasons.append(f"Top pick {name} is larger than your rig's field of view.")
        elif ratio <= _FOV_SWEET_LOW:
            reasons.append(f"Top pick {name} is small in your rig's field of view.")
        else:
            reasons.append(f"Top pick {name} fills most of your rig's field of view.")
    brightness = brightness_subscore(obj.surface_brightness, obj.magnitude)
    if brightness is not None and brightness >= _BRIGHT_THRESHOLD:
        reasons.append(f"Top pick {name} is a bright target.")
    return reasons


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


# Per-night ranking cache keyed by (pier identity + horizon + rig + dark window).
# The ranking's curve/weight parameters are fixed constants, so they do not enter
# the key; design D5/D7 requires adding any that becomes per-pier configuration —
# the rig now does, because framing depends on it (a rig change must change the
# ranking, not serve a stale one). The cache is a bounded
# LRU so a persistent container recomputing night after night keeps only the most
# recent few rankings rather than retaining one entry per night forever. It is a
# performance optimization only, so eviction never affects correctness (design D5).
_CACHE_MAXSIZE = 16
_rank_cache: OrderedDict[tuple[Any, ...], tuple[Target, ...]] = OrderedDict()


def _rig_key(rig: Rig | None) -> tuple[Any, ...] | None:
    """The rig's identity for the cache key, or ``None`` when no rig is configured."""
    if rig is None:
        return None
    return (rig.focal_length_mm, rig.sensor_width_mm, rig.sensor_height_mm, rig.reducer)


def _cache_key(pier: PierConfig, window: tuple[datetime, datetime]) -> tuple[Any, ...]:
    return (
        pier.id,
        pier.latitude,
        pier.longitude,
        pier.elevation_m,
        pier.horizon_mask.samples,
        _rig_key(pier.rig),
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

    # The rig's short-edge field of view (arcmin) once per pier; None with no rig.
    fov_short_arcmin = _fov_short_arcmin(pier.rig)

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
            brightness=brightness_subscore(obj.surface_brightness, obj.magnitude),
            fov_fit=_fov_fit_for(obj, fov_short_arcmin),
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
        obj = candidate.obj
        score = combined_score(
            altitude_subscore(geo.max_altitude),
            window_subscore(geo.window_end - geo.window_start, dark_duration),
            moon_subscore(geo.moon_separation, moon.illumination, geo.moon_up_at_peak),
            transit_subscore(geo.transit_time, geo.window_start, geo.window_end),
            brightness=brightness_subscore(obj.surface_brightness, obj.magnitude),
            fov_fit=_fov_fit_for(obj, fov_short_arcmin),
        )
        emitted.append(
            Target(
                id=obj.id,
                name=obj.name,
                type=obj.type,
                score=score,
                window=TargetWindow(start=geo.window_start, end=geo.window_end),
                max_altitude=geo.max_altitude,
                transit_time=geo.transit_time,
                moon_separation=geo.moon_separation,
                # The raw catalog facts, carried additively (design D8, ADR-0009);
                # None (present, not omitted) when the catalog records no value.
                size_arcmin=obj.size_arcmin,
                magnitude=obj.magnitude,
                surface_brightness=obj.surface_brightness,
            )
        )
        if len(emitted) >= TOP_N:
            break

    emitted.sort(key=lambda target: (-target.score, target.id))
    return emitted
