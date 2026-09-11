"""Pure, deterministic verdict math over the conditions groups (design D3-D6).

This module turns astronomy plus a :class:`Conditions` value into the verdict's
decision terms: the hard gates, the banded 0-100 score, and lead-time confidence.
It has no Home Assistant, MQTT, or network imports — it is pure logic over its
inputs, so the same inputs yield byte-identical output (the offline guard and the
boundary test enforce this).

The organising idea (design D3) is a single per-hour **clarity weight** ``q`` and
**coverage weight** ``w``. Every quantity — the overcast gate, the cloud score,
the optional terms, the moon penalty — is a clarity-weighted sum over the dark
window, so the whole verdict rests on one concept rather than many ad-hoc rules.

Cloud and wind live on the base group and seeing/transparency on the secondary
group (design D1); the scoring reads each slot through its group's ``at`` lookup,
guarding an absent (``None``) group first (design D6). Because both groups are
hourly-keyed, the optional-term and completeness helpers cross-reference cloud and
seeing by the same top-of-hour timestamp across the two groups.

All tuning constants live at the top of this module (task 5.1). They are fixed in
code, not configuration: the system decides, and a change to a curve is a
deliberate, reviewed diff rather than silent drift.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .conditions import BaseHour, Conditions, SecondaryHour
from .config import PierConfig
from .model import Band, Moon, Verdict

_HOUR = timedelta(hours=1)

# --- Clarity curve q(cloud) (design D3; task 5.1) -------------------------- #
# Percent cloud at or below which the hour counts as fully usable sky (q = 1),
# and at or above which it counts as no usable sky (q = 0). Between the two the
# weight falls linearly. Placing the overcast knee below 100% is what lets the
# overcast gate fire on a genuinely socked-in sky rather than only on a
# mathematically perfect 100%.
CLOUD_CLEAR = 10.0
CLOUD_OVERCAST = 90.0

# Below this effective-clear-hours total the window counts as overcast (design
# D4). It is a floating-point guard around zero, not a tuning knob.
OVERCAST_EPSILON = 1e-9


def clarity_weight(cloud_cover: float) -> float:
    """The per-hour clarity weight ``q`` in ``[0, 1]`` from percent cloud cover.

    Clear sky (``<= CLOUD_CLEAR``) weighs 1; an overcast sky (``>= CLOUD_OVERCAST``)
    weighs 0; between them the weight falls linearly. Monotonic non-increasing in
    cloud cover, so more cloud never scores as more usable sky.
    """
    span = CLOUD_OVERCAST - CLOUD_CLEAR
    return max(0.0, min(1.0, (CLOUD_OVERCAST - cloud_cover) / span))


def coverage_weight(hour_start: datetime, window_start: datetime, window_end: datetime) -> float:
    """The coverage weight ``w`` in ``[0, 1]``: the fraction of the hour that is dark.

    A one-hour slot beginning at ``hour_start`` is weighted by how much of it lies
    inside ``[window_start, window_end]``. A boundary hour only partly inside the
    dark window contributes ``w < 1``; a fully-enclosed hour contributes 1. This
    normalisation is what keeps every weighted sum bounded when the window does
    not fall on whole-hour boundaries.
    """
    hour_end = hour_start + _HOUR
    overlap = min(hour_end, window_end) - max(hour_start, window_start)
    if overlap <= timedelta(0):
        return 0.0
    return min(1.0, overlap / _HOUR)


def hour_slots(window_start: datetime, window_end: datetime) -> list[datetime]:
    """The top-of-hour slots that intersect ``[window_start, window_end]``.

    Slots are aligned to the clock hour (matching hourly forecast timestamps), so
    the window's start and end may fall partway into the first and last slots.
    """
    first = window_start.replace(minute=0, second=0, microsecond=0)
    slots: list[datetime] = []
    slot = first
    while slot < window_end:
        slots.append(slot)
        slot += _HOUR
    return slots


# --- Group reads, each guarding an absent group (design D6) ----------------- #


def _base_hour(conditions: Conditions, slot: datetime) -> BaseHour | None:
    return conditions.base.at(slot) if conditions.base is not None else None


def _secondary_hour(conditions: Conditions, slot: datetime) -> SecondaryHour | None:
    return conditions.secondary.at(slot) if conditions.secondary is not None else None


def _cloud_at(conditions: Conditions, slot: datetime) -> float | None:
    hour = _base_hour(conditions, slot)
    return hour.cloud_cover if hour is not None else None


def _wind_at(conditions: Conditions, slot: datetime) -> float | None:
    hour = _base_hour(conditions, slot)
    return hour.wind_gust if hour is not None else None


def _seeing_at(conditions: Conditions, slot: datetime) -> float | None:
    hour = _secondary_hour(conditions, slot)
    return hour.seeing if hour is not None else None


def _transparency_at(conditions: Conditions, slot: datetime) -> float | None:
    hour = _secondary_hour(conditions, slot)
    return hour.transparency if hour is not None else None


def clear_hours_total(window: tuple[datetime, datetime], conditions: Conditions) -> float:
    """``W = Σ_{h∈C}(w·q)`` — effective clear hours over slots with cloud data.

    ``C`` is the set of window hours whose cloud cover is available. This is the
    integrated usable dark time the observer actually reasons about, and it drives
    both the overcast gate (``W ≈ 0``) and the cloud score term.
    """
    start, end = window
    total = 0.0
    for slot in hour_slots(start, end):
        cloud = _cloud_at(conditions, slot)
        if cloud is None:
            continue
        total += coverage_weight(slot, start, end) * clarity_weight(cloud)
    return total


def total_coverage(window: tuple[datetime, datetime]) -> float:
    """``Σ_{all h}(w)`` — the window's whole coverage in hours, cloud data or not.

    This is the denominator of the cloud score term. Because it spans every hour
    of the window (not only hours with data), a window hour whose cloud is missing
    adds nothing to the numerator yet still counts here — so missing cloud
    depresses the score rather than inflating it.
    """
    start, end = window
    return sum(coverage_weight(slot, start, end) for slot in hour_slots(start, end))


def cloud_score_term(window: tuple[datetime, datetime], conditions: Conditions) -> float:
    """The cloud score term ``W / Σ_{all h}(w)`` in ``[0, 1]`` (design D3).

    The numerator sums only hours with cloud data; the denominator is the whole
    window. Hours without cloud data therefore count as not-known-usable — never
    clear (which would inflate the score) and never overcast (which would risk a
    false gate).
    """
    denominator = total_coverage(window)
    if denominator <= 0.0:
        return 0.0
    return clear_hours_total(window, conditions) / denominator


def optional_term_mean(
    window: tuple[datetime, datetime],
    conditions: Conditions,
    selector: Callable[[SecondaryHour], float | None],
) -> float | None:
    """Clarity-weighted mean of an optional term (seeing, transparency) or ``None``.

    The mean runs over hours where **both** the base group's cloud and the
    secondary group's term are available, correlated by top-of-hour across the two
    groups, and its denominator is restricted to those same hours (design D3, D6).
    Restricting the denominator keeps a partial-coverage gap from artificially
    depressing the mean — three clear hours of good seeing read as good seeing, not
    as good seeing diluted by the hours that carried none. Returns ``None`` when
    the term has no usable hour, so the caller drops it from the score entirely.
    """
    start, end = window
    numerator = 0.0
    denominator = 0.0
    for slot in hour_slots(start, end):
        cloud = _cloud_at(conditions, slot)
        if cloud is None:
            continue
        secondary_hour = _secondary_hour(conditions, slot)
        if secondary_hour is None:
            continue
        value = selector(secondary_hour)
        if value is None:
            continue
        weight = coverage_weight(slot, start, end) * clarity_weight(cloud)
        numerator += weight * value
        denominator += weight
    if denominator <= 0.0:
        return None
    return numerator / denominator


def moon_up_at(instant: datetime, moon: Moon, window: tuple[datetime, datetime]) -> bool:
    """Whether the moon is above the horizon at ``instant`` within ``window``.

    Reconstructed from M2's first moonrise and moonset in the window (design D3).
    Because the window is at most a solar day, the moon crosses the horizon at
    most twice, so the first rise and first set fully describe the up-intervals:

    - rise then set: down before the rise, up between, down after the set;
    - set then rise: up before the set, down between, up after the rise;
    - only a rise (or only a set): down-then-up (or up-then-down);
    - neither event: the moon holds one state, given by ``up_during_dark``.
    """
    rise, sets = moon.rise, moon.set
    if rise is not None and sets is not None:
        if rise < sets:
            return rise <= instant < sets
        return instant < sets or instant >= rise
    if rise is not None:
        return instant >= rise
    if sets is not None:
        return instant < sets
    return bool(moon.up_during_dark)


def moon_penalty(window: tuple[datetime, datetime], conditions: Conditions, moon: Moon) -> float:
    """The moon term in ``[0, 1]``: illumination × clarity-weighted up-fraction (design D3).

    ``illumination × Σ_{h∈C}(w·q·up_h) / W`` — how much of the usable dark time
    the moon is up, weighted by clarity and scaled by its brightness. A dark or
    absent moon gives 0; a full moon up throughout the usable darkness approaches
    the illumination. Zero when there is no usable dark time to spoil.
    """
    total_clear = clear_hours_total(window, conditions)
    if total_clear <= 0.0:
        return 0.0
    start, end = window
    up_clear = 0.0
    for slot in hour_slots(start, end):
        cloud = _cloud_at(conditions, slot)
        if cloud is None:
            continue
        covered_start = max(slot, start)
        covered_end = min(slot + _HOUR, end)
        midpoint = covered_start + (covered_end - covered_start) / 2
        if moon_up_at(midpoint, moon, window):
            up_clear += coverage_weight(slot, start, end) * clarity_weight(cloud)
    return moon.illumination * (up_clear / total_clear)


# --- Score assembly (design D4; task 5.1) ---------------------------------- #
# Weights of the quality terms in the score. Cloud dominates (design D3); seeing
# and transparency each nudge it. The weights are normalised over whichever terms
# are present, so a missing optional term drops out rather than counting as zero.
_W_CLOUD = 0.70
_W_SEEING = 0.15
_W_TRANSPARENCY = 0.15
# The most a full moon, up throughout the usable darkness, can cut the score: a
# penalty rather than a gate, because a bright moon spoils faint targets but
# never makes a night impossible (design D4).
_MOON_MAX_PENALTY = 0.50


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def cloud_available(window: tuple[datetime, datetime], conditions: Conditions) -> bool:
    """Whether any hour of the window carries cloud data (design D6, gate precedence)."""
    start, end = window
    return any(_cloud_at(conditions, slot) is not None for slot in hour_slots(start, end))


def is_overcast(window: tuple[datetime, datetime], conditions: Conditions) -> bool:
    """The overcast gate: cloud data is available **and** no hour is usably clear.

    Requiring cloud to be present is what keeps an empty cloud set (``W = 0`` for
    lack of data) from firing this gate — that case is the missing-cloud MAYBE
    (design D6), not a NO-GO.
    """
    return cloud_available(window, conditions) and clear_hours_total(window, conditions) <= (
        OVERCAST_EPSILON
    )


def wind_exceeds_limit(
    window: tuple[datetime, datetime], conditions: Conditions, max_gust: float
) -> bool:
    """Whether any hour with wind data forecasts a gust over ``max_gust``."""
    start, end = window
    for slot in hour_slots(start, end):
        gust = _wind_at(conditions, slot)
        if gust is not None and gust > max_gust:
            return True
    return False


def wind_fully_covered(window: tuple[datetime, datetime], conditions: Conditions) -> bool:
    """Whether every hour of the window carries wind data.

    A configured safety limit can only be trusted when the whole dark window is
    covered; any gap means the limit cannot be confirmed there (design D6).
    """
    start, end = window
    return all(_wind_at(conditions, slot) is not None for slot in hour_slots(start, end))


def assemble_score(window: tuple[datetime, datetime], conditions: Conditions, moon: Moon) -> int:
    """The banded 0-100 score from the cloud, seeing, transparency, and moon terms.

    A weighted mean of the available quality terms (cloud dominant), cut by the
    moon penalty, rounded to the nearest integer and clamped to ``[0, 100]`` — so
    identical inputs yield an identical integer (design D4).
    """
    weighted = [(_W_CLOUD, cloud_score_term(window, conditions))]
    seeing = optional_term_mean(window, conditions, lambda h: h.seeing)
    if seeing is not None:
        weighted.append((_W_SEEING, seeing))
    transparency = optional_term_mean(window, conditions, lambda h: h.transparency)
    if transparency is not None:
        weighted.append((_W_TRANSPARENCY, transparency))

    quality = sum(w * term for w, term in weighted) / sum(w for w, _ in weighted)
    score01 = quality * (1.0 - _MOON_MAX_PENALTY * moon_penalty(window, conditions, moon))
    return max(0, min(100, round(100.0 * _clamp01(score01))))


# --- Confidence (design D5; task 5.1) -------------------------------------- #
# Lead time L: 1 within L_FULL hours of dusk (or once mid-session), decaying to
# L_MIN by L_FAR hours out. Freshness F: 1 within F_FRESH hours of issue, decaying
# to F_MIN by F_STALE hours (the cache max staleness). K: completeness.
_L_FULL_HOURS = 3.0
_L_FAR_HOURS = 24.0
_L_MIN = 0.5
_F_FRESH_HOURS = 1.0
_F_STALE_HOURS = 12.0
_F_MIN = 0.2
# The floor lifts the L·F sub-product so a merely middling lead-time/freshness
# does not read LOW; completeness K multiplies in *after* the floor, so missing
# data still pulls confidence down and the floor cannot rescue it (design D5).
_CONFIDENCE_FLOOR = 0.50
# How much a fully-absent field trims K. Cloud coverage multiplies K directly, so
# it needs no separate trim weight.
_K_TRIM_SEEING = 0.15
_K_TRIM_TRANSPARENCY = 0.15
_K_TRIM_WIND = 0.30
# Band thresholds on the 0-100 value (design D5, ~40 / ~70).
_BAND_MEDIUM = 40
_BAND_HIGH = 70


def _decay(x: float, full: float, far: float, floor: float) -> float:
    """1 at or below ``full``, linearly down to ``floor`` at ``far``, ``floor`` beyond."""
    if x <= full:
        return 1.0
    if x >= far:
        return floor
    return 1.0 - (x - full) / (far - full) * (1.0 - floor)


def lead_time_factor(instant: datetime, window: tuple[datetime, datetime]) -> float:
    """``L``: rises toward 1 as the evaluation instant approaches the dark window."""
    start, _ = window
    hours_until = (start - instant) / _HOUR
    if hours_until <= 0.0:  # mid-session or later: fully led.
        return 1.0
    return _decay(hours_until, _L_FULL_HOURS, _L_FAR_HOURS, _L_MIN)


def freshness_factor(instant: datetime, issued_at: datetime | None) -> float:
    """``F``: 1 for a just-issued forecast, decaying with the base group's age.

    A missing issue time is treated as maximally stale, because data whose age
    cannot be established should not be trusted as fresh.
    """
    if issued_at is None:
        return _F_MIN
    age_hours = (instant - issued_at) / _HOUR
    if age_hours <= 0.0:
        return 1.0
    return _decay(age_hours, _F_FRESH_HOURS, _F_STALE_HOURS, _F_MIN)


def _field_coverage(
    window: tuple[datetime, datetime],
    value_at: Callable[[datetime], float | None],
) -> float:
    """Fraction of the window (by coverage weight) for which ``value_at`` has data."""
    total = total_coverage(window)
    if total <= 0.0:
        return 0.0
    start, end = window
    covered = 0.0
    for slot in hour_slots(start, end):
        if value_at(slot) is not None:
            covered += coverage_weight(slot, start, end)
    return covered / total


def completeness_factor(
    window: tuple[datetime, datetime], conditions: Conditions, max_gust: float | None
) -> float:
    """``K``: 1 when every field fully covers the window, trimmed as data thins.

    Cloud coverage multiplies K directly, so K collapses toward 0 as the cloud
    grid thins (and is 0 when cloud is entirely absent). Each optional field is
    trimmed proportionally to the fraction of the window it is missing; when a
    wind limit is configured, missing wind trims K too (design D5, D6).
    """
    cloud_cov = _field_coverage(window, lambda s: _cloud_at(conditions, s))
    seeing_cov = _field_coverage(window, lambda s: _seeing_at(conditions, s))
    transparency_cov = _field_coverage(window, lambda s: _transparency_at(conditions, s))

    factor = cloud_cov
    factor *= 1.0 - _K_TRIM_SEEING * (1.0 - seeing_cov)
    factor *= 1.0 - _K_TRIM_TRANSPARENCY * (1.0 - transparency_cov)
    if max_gust is not None:
        wind_cov = _field_coverage(window, lambda s: _wind_at(conditions, s))
        factor *= 1.0 - _K_TRIM_WIND * (1.0 - wind_cov)
    return _clamp01(factor)


def _band_for(value: int) -> Band:
    if value >= _BAND_HIGH:
        return Band.HIGH
    if value >= _BAND_MEDIUM:
        return Band.MEDIUM
    return Band.LOW


def confidence(
    pier: PierConfig,
    instant: datetime,
    window: tuple[datetime, datetime],
    conditions: Conditions,
) -> tuple[Band, int]:
    """The forecast-based confidence ``(band, value)`` = ``max(floor, 100·L·F)·K``.

    Freshness reads the base group's issue time only (design D2): the secondary
    group's issue time is carried for provenance but never folded in, so a lagging
    secondary source never lowers confidence.
    """
    lead = lead_time_factor(instant, window)
    base_issued_at = conditions.base.meta.issued_at if conditions.base is not None else None
    fresh = freshness_factor(instant, base_issued_at)
    complete = completeness_factor(window, conditions, pier.max_gust)
    value = round(max(_CONFIDENCE_FLOOR, lead * fresh) * complete * 100.0)
    value = max(0, min(100, value))
    return _band_for(value), value


# --- The verdict itself: gates, score, degradation ladder (design D4, D6) --- #


@dataclass(frozen=True)
class Decision:
    """The decision terms the producer folds into the verdict document.

    ``score`` is ``None`` exactly when ``verdict`` is NO-GO (a failed gate), so the
    invariant NO-GO ⟺ null score holds for the delivery layer.
    """

    verdict: Verdict
    score: int | None
    band: Band
    confidence: int
    reasons: list[str]


_REASON_NO_WINDOW = "No astronomical night tonight: the sun never drops below -18°."
_REASON_OVERCAST = "Overcast for the whole dark window: no usably clear sky."
_REASON_CONDITIONS_UNAVAILABLE = "Conditions unavailable — astronomy only, no cloud forecast."


def _wind_reason(max_gust: float) -> str:
    return f"Wind gust over the {max_gust:g} km/h limit during the dark window."


def _wind_unavailable_reason() -> str:
    return "Wind data unavailable: the safety limit cannot be confirmed, so not a GO."


def _score_reasons(
    window: tuple[datetime, datetime], conditions: Conditions, moon: Moon, score: int
) -> list[str]:
    """Itemise the terms behind a scored verdict, so the explanation follows the math."""
    reasons = [
        f"Cloud: {round(cloud_score_term(window, conditions) * 100)}% of the dark window usable."
    ]
    seeing = optional_term_mean(window, conditions, lambda h: h.seeing)
    if seeing is not None:
        reasons.append(f"Seeing quality {round(seeing * 100)}%.")
    transparency = optional_term_mean(window, conditions, lambda h: h.transparency)
    if transparency is not None:
        reasons.append(f"Transparency quality {round(transparency * 100)}%.")
    penalty = moon_penalty(window, conditions, moon)
    if penalty > 0.0:
        reasons.append(
            f"Moon penalty {round(penalty * 100)}% (illuminated and up during darkness)."
        )
    reasons.append(f"Score {score}/100.")
    return reasons


def evaluate(
    pier: PierConfig,
    instant: datetime,
    window: tuple[datetime, datetime] | tuple[None, None],
    conditions: Conditions,
    moon: Moon,
) -> Decision:
    """Decide the verdict from astronomy, the conditions groups, and the moon.

    The degradation ladder runs in a fixed precedence so the cases never
    contradict (design D6): no dark window → wind gate → cloud entirely missing →
    cloud present (overcast gate, else score). A NO-GO is only ever a failed hard
    gate; a missing observation caps the verdict at MAYBE but never fails one.
    """
    start, end = window
    # 1. No dark window: astronomy alone decides, with no forecast to distrust.
    if start is None or end is None:
        return Decision(Verdict.NO_GO, None, Band.HIGH, 100, [_REASON_NO_WINDOW])
    bounded: tuple[datetime, datetime] = (start, end)

    band, conf_value = confidence(pier, instant, bounded, conditions)

    # 2. Wind gate (opt-in). A forecast gust over the limit is a safety NO-GO,
    #    evaluated before any cloud logic so a missing cloud observation cannot
    #    override it. If the limit is set but wind is not fully covered, the limit
    #    cannot be confirmed: cap at MAYBE (never GO) rather than fail-open.
    wind_capped = False
    if pier.max_gust is not None:
        if wind_exceeds_limit(bounded, conditions, pier.max_gust):
            return Decision(Verdict.NO_GO, None, band, conf_value, [_wind_reason(pier.max_gust)])
        if not wind_fully_covered(bounded, conditions):
            wind_capped = True

    # 3. Cloud entirely missing: no evidence the sky is clear, but absence is not
    #    a dealbreaker. MAYBE with a zero score and zero confidence.
    if not cloud_available(bounded, conditions):
        reasons = [_REASON_CONDITIONS_UNAVAILABLE]
        if wind_capped:
            reasons.append(_wind_unavailable_reason())
        return Decision(Verdict.MAYBE, 0, Band.LOW, 0, reasons)

    # 4. Cloud present: the overcast gate can fire; otherwise score the night.
    if is_overcast(bounded, conditions):
        return Decision(Verdict.NO_GO, None, band, conf_value, [_REASON_OVERCAST])

    score = assemble_score(bounded, conditions, moon)
    reasons = _score_reasons(bounded, conditions, moon, score)
    if wind_capped:
        reasons.append(_wind_unavailable_reason())
    is_go = score >= pier.go_threshold and not wind_capped
    verdict = Verdict.GO if is_go else Verdict.MAYBE
    return Decision(verdict, score, band, conf_value, reasons)
