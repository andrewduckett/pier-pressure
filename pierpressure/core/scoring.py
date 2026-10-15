"""Pure, deterministic verdict math over the conditions groups (design D3-D6).

This module turns astronomy plus a :class:`Conditions` value into the verdict's
decision terms: the hard gates, the banded 0-100 score, and lead-time confidence.
It has no Home Assistant, MQTT, or network imports — it is pure logic over its
inputs, so the same inputs yield byte-identical output (the offline guard and the
boundary test enforce this).

The organising idea (design D3) is a single per-hour **clarity weight** ``q`` and
**coverage weight** ``w``. Every quantity — the overcast gate, the cloud score,
the atmosphere factor, the moon penalty — is a clarity-weighted sum over the
scored window, so the whole verdict rests on one concept rather than many ad-hoc
rules.

The score is a product of factors, each at most 1: how much usable sky there is
(the cloud term), scaled by how good it is (the atmosphere factor from seeing and
transparency), the moon, and high cloud. Seeing and transparency scale the cloud
term rather than adding to it, so they can never stand in for sky that is not
there (score-remaining-night design D3).

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

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta

from .conditions import BaseHour, Conditions, SecondaryHour
from .config import PierConfig
from .model import MIN_USABLE_WINDOW, Band, Moon, Verdict, iso_z

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


def _cloud_high_at(conditions: Conditions, slot: datetime) -> float | None:
    hour = _base_hour(conditions, slot)
    return hour.cloud_high if hour is not None else None


def _seeing_at(conditions: Conditions, slot: datetime) -> float | None:
    hour = _secondary_hour(conditions, slot)
    return hour.seeing if hour is not None else None


def _transparency_at(conditions: Conditions, slot: datetime) -> float | None:
    hour = _secondary_hour(conditions, slot)
    return hour.transparency if hour is not None else None


def _clear_weights(
    window: tuple[datetime, datetime], conditions: Conditions
) -> Iterator[tuple[datetime, float]]:
    """Each window slot with cloud data, paired with its clear weight ``w·q``.

    Every clarity-weighted sum in this module (the overcast gate, the cloud term,
    the atmosphere factor, the moon and high-cloud penalties) walks exactly this
    sequence, so the one place that defines "usable dark time per slot" is here.
    Slots without cloud data are skipped: they are neither clear nor overcast.
    """
    start, end = window
    for slot in hour_slots(start, end):
        cloud = _cloud_at(conditions, slot)
        if cloud is None:
            continue
        yield slot, coverage_weight(slot, start, end) * clarity_weight(cloud)


def clear_hours_total(window: tuple[datetime, datetime], conditions: Conditions) -> float:
    """``W = Σ_{h∈C}(w·q)`` — effective clear hours over slots with cloud data.

    ``C`` is the set of window hours whose cloud cover is available. This is the
    integrated usable dark time the observer actually reasons about, and it drives
    both the overcast gate (``W ≈ 0``) and the cloud score term.
    """
    return sum(weight for _, weight in _clear_weights(window, conditions))


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


def _optional_term(
    window: tuple[datetime, datetime],
    conditions: Conditions,
    selector: Callable[[SecondaryHour], float | None],
) -> tuple[float | None, float]:
    """``(mean, coverage)`` of an optional term over the usably clear hours, in one pass.

    ``mean`` is the clarity-weighted mean over hours where **both** the base
    group's cloud and the secondary group's term are available, correlated by
    top-of-hour across the two groups, with the denominator restricted to those
    same hours (design D3, D6) — or ``None`` when no such hour exists.
    ``coverage`` is that same restricted weight as a share of all usable weight.
    """
    numerator = 0.0
    denominator = 0.0
    usable = 0.0
    for slot, weight in _clear_weights(window, conditions):
        usable += weight
        secondary_hour = _secondary_hour(conditions, slot)
        if secondary_hour is None:
            continue
        value = selector(secondary_hour)
        if value is None:
            continue
        numerator += weight * value
        denominator += weight
    mean = None if denominator <= 0.0 else numerator / denominator
    coverage = 0.0 if usable <= 0.0 else denominator / usable
    return mean, coverage


def optional_term_mean(
    window: tuple[datetime, datetime],
    conditions: Conditions,
    selector: Callable[[SecondaryHour], float | None],
) -> float | None:
    """Clarity-weighted mean of an optional term (seeing, transparency) or ``None``.

    Restricting the denominator to the hours that carry the term keeps a
    partial-coverage gap from artificially depressing the mean — three clear hours
    of good seeing read as good seeing, not as good seeing diluted by the hours
    that carried none. ``None`` when the term has no usable hour, so the caller
    omits its reason line. The score itself does not read this mean: it flows
    through :func:`atmosphere_mean`.
    """
    return _optional_term(window, conditions, selector)[0]


def optional_term_coverage(
    window: tuple[datetime, datetime],
    conditions: Conditions,
    selector: Callable[[SecondaryHour], float | None],
) -> float:
    """The share of the usable sky ``Σ(w·q)`` over hours that carry an optional term.

    This is the weight :func:`optional_term_mean` averages over, as a share of the
    weight :func:`atmosphere_mean` averages over, so a reason can say how much of
    the atmosphere factor a term's mean actually stands behind. 0 when no hour is
    usably clear.
    """
    return _optional_term(window, conditions, selector)[1]


def _hour_atmosphere(hour: SecondaryHour | None) -> float:
    """The hour's atmosphere quality ``a``: the mean of the seeing and transparency it carries.

    An hour that carries neither has ``a = 1``, so missing atmosphere data never
    lowers the score (score-remaining-night design D3).
    """
    if hour is None:
        return 1.0
    values = [v for v in (hour.seeing, hour.transparency) if v is not None]
    if not values:
        return 1.0
    return sum(values) / len(values)


def atmosphere_mean(window: tuple[datetime, datetime], conditions: Conditions) -> float:
    """``A = Σ(w·q·a) / Σ(w·q)`` over the hours with cloud data, in ``[0, 1]``.

    Unlike :func:`optional_term_mean`, an hour without seeing or transparency stays
    in the mean at ``a = 1`` rather than dropping out. With that, the cloud and
    atmosphere product is a sum of per-hour terms, each increasing in that hour's
    clarity, so more cloud in any hour can never raise it (score-remaining-night
    design D3). Returns 1 when no hour is usably clear.
    """
    numerator = 0.0
    denominator = 0.0
    for slot, weight in _clear_weights(window, conditions):
        numerator += weight * _hour_atmosphere(_secondary_hour(conditions, slot))
        denominator += weight
    if denominator <= 0.0:
        return 1.0
    return numerator / denominator


def high_cloud_penalty(window: tuple[datetime, datetime], conditions: Conditions) -> float | None:
    """The high/thin-cloud penalty in ``[0, 1]`` or ``None`` (design D2).

    The clarity-weighted mean of ``cloud_high / 100`` over exactly the hours that
    carry **both** total ``cloud_cover`` and the ``cloud_high`` component, with the
    denominator restricted to those same hours — computed like
    :func:`optional_term_mean`, **not** like :func:`moon_penalty`. Restricting the
    denominator keeps an hour missing ``cloud_high`` from diluting the penalty
    (which would read missing cirrus as clear sky); ``moon_penalty`` can divide by
    every clear hour only because moon-up is defined for every hour, whereas
    ``cloud_high`` is optional. Clarity-weighting means a fully-overcast hour
    (``q = 0``) adds nothing — it is already penalised by the total-cloud term — so
    the penalty bites on hours that read otherwise clear but carry cirrus aloft.
    Returns ``None`` when no hour qualifies, so the caller drops the term entirely.
    """
    numerator = 0.0
    denominator = 0.0
    for slot, weight in _clear_weights(window, conditions):
        high = _cloud_high_at(conditions, slot)
        if high is None:
            continue
        numerator += weight * (high / 100.0)
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
    for slot, weight in _clear_weights(window, conditions):
        covered_start = max(slot, start)
        covered_end = min(slot + _HOUR, end)
        midpoint = covered_start + (covered_end - covered_start) / 2
        if moon_up_at(midpoint, moon, window):
            up_clear += weight
    return moon.illumination * (up_clear / total_clear)


# --- Score assembly (design D4; task 5.1) ---------------------------------- #
# The atmosphere factor for the worst seeing and transparency. Seeing and
# transparency scale the cloud term between this floor and 1 rather than adding
# to it, so good atmosphere refines a clear night but cannot lift a cloudy one
# (score-remaining-night design D3). Not 0: poor atmosphere still leaves a night
# for bright targets, and a factor of 0 would be a gate by another name.
ATMOSPHERE_FLOOR = 0.7
# The most a full moon, up throughout the usable darkness, can cut the score: a
# penalty rather than a gate, because a bright moon spoils faint targets but
# never makes a night impossible (design D4).
_MOON_MAX_PENALTY = 0.50
# The most high, thin cirrus over the whole usable darkness can cut the score. Kept
# below the moon's penalty (design D2): high cloud is a meaningful transparency hit
# but not as ruinous as a full moon, and it compounds *multiplicatively* with the
# moon penalty rather than adding to it, so it is tuned in that awareness.
_HIGH_CLOUD_MAX_PENALTY = 0.30


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


def atmosphere_factor(window: tuple[datetime, datetime], conditions: Conditions) -> float:
    """The atmosphere factor ``ATMOSPHERE_FLOOR + (1 - ATMOSPHERE_FLOOR) · A`` in ``[0.7, 1]``."""
    return ATMOSPHERE_FLOOR + (1.0 - ATMOSPHERE_FLOOR) * atmosphere_mean(window, conditions)


@dataclass(frozen=True)
class ScoreTerms:
    """The terms behind one banded score, computed once and shared with the reasons.

    Holding them together means the score and the lines that explain it cannot
    drift apart: :func:`_score_reasons` formats exactly these numbers.
    """

    cloud_term: float
    atmosphere_factor: float
    high_cloud: float | None
    moon_penalty: float
    score: int


def score_terms(
    window: tuple[datetime, datetime], conditions: Conditions, moon: Moon
) -> ScoreTerms:
    """The banded 0-100 score and its terms: cloud scaled by atmosphere, moon, and high cloud.

    ``cloud_term × atmosphere_factor × moon factor × high-cloud factor``, rounded to
    the nearest integer (half to even) and clamped to ``[0, 100]`` — so identical
    inputs yield an identical integer (design D4). Every factor is at most 1, so the
    score never exceeds the cloud term (score-remaining-night design D3). A ``None``
    high-cloud penalty (no ``cloud_high`` data for the window) leaves its factor at
    1, so the term drops out entirely.
    """
    cloud_term = cloud_score_term(window, conditions)
    atmosphere = atmosphere_factor(window, conditions)
    high_cloud = high_cloud_penalty(window, conditions)
    high_cloud_factor = 1.0 if high_cloud is None else 1.0 - _HIGH_CLOUD_MAX_PENALTY * high_cloud
    moon_term = moon_penalty(window, conditions, moon)
    score01 = cloud_term * atmosphere * (1.0 - _MOON_MAX_PENALTY * moon_term) * high_cloud_factor
    score = max(0, min(100, round(100.0 * _clamp01(score01))))
    return ScoreTerms(cloud_term, atmosphere, high_cloud, moon_term, score)


def assemble_score(window: tuple[datetime, datetime], conditions: Conditions, moon: Moon) -> int:
    """The banded 0-100 score alone; see :func:`score_terms`."""
    return score_terms(window, conditions, moon).score


# --- Confidence (design D5; task 5.1) -------------------------------------- #
# Lead time L: 1 within L_FULL hours of dusk (or once mid-session), decaying to
# L_MIN by L_FAR hours out. Freshness F: 1 within F_FRESH hours of the base
# source's issue, decaying to F_MIN by F_STALE hours, the age at which base data
# reaches the freshness floor. K: completeness.
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
    scored: tuple[datetime, datetime],
    conditions: Conditions,
) -> tuple[Band, int]:
    """The forecast-based confidence ``(band, value)`` = ``max(floor, 100·L·F)·K``.

    Lead time reads the dark ``window``'s start, so it is 1 once the night has
    begun; completeness reads the ``scored`` window, so a gap in hours that have
    passed no longer lowers it (score-remaining-night design D1).

    Freshness reads the base group's issue time only (design D2): the secondary
    group's issue time is carried for provenance but never folded in, so a lagging
    secondary source never lowers confidence.
    """
    lead = lead_time_factor(instant, window)
    base_issued_at = conditions.base.meta.issued_at if conditions.base is not None else None
    fresh = freshness_factor(instant, base_issued_at)
    complete = completeness_factor(scored, conditions, pier.max_gust)
    value = round(max(_CONFIDENCE_FLOOR, lead * fresh) * complete * 100.0)
    value = max(0, min(100, value))
    return _band_for(value), value


# --- The verdict itself: gates, score, degradation ladder (design D4, D6) --- #


@dataclass(frozen=True)
class Decision:
    """The decision terms the producer folds into the verdict document.

    ``score`` is ``None`` exactly when ``verdict`` is NO-GO (a failed gate), so the
    invariant NO-GO ⟺ null score holds for the delivery layer. ``scored_window`` is
    the span the gates and score judged: the dark window from the scoring instant on
    (score-remaining-night design D1), or ``(None, None)`` without a dark window.
    """

    verdict: Verdict
    score: int | None
    band: Band
    confidence: int
    reasons: list[str]
    scored_window: tuple[datetime, datetime] | tuple[None, None]


# A scored window shorter than this is never a GO, however clear: it is not worth
# setting up for (score-remaining-night design D2). The ranking's MIN_WINDOW is
# the same object, so the verdict and the target list agree on a usable span.
MIN_SCORED = MIN_USABLE_WINDOW

_REASON_NO_WINDOW = "No astronomical night tonight: the sun never drops below -18°."
_REASON_NO_DARK_TIME = "No dark time remains to score."
_REASON_SHORT_WINDOW = "Less than an hour of dark time to score: not worth setting up."
_REASON_OVERCAST = "Overcast for the whole dark window: no usably clear sky."
# "In the forecast": remaining hours without cloud data are unknown, not overcast.
_REASON_OVERCAST_REST = "No usably clear sky in the forecast for the rest of the night."
_REASON_CONDITIONS_UNAVAILABLE = "Conditions unavailable — astronomy only, no cloud forecast."
# Mid-session the forecast may simply have run out, so claim only the remaining hours.
_REASON_CONDITIONS_UNAVAILABLE_REST = (
    "Conditions unavailable for the rest of the night: no cloud forecast for the"
    " remaining hours, astronomy only."
)


def _wind_reason(max_gust: float, narrowed: bool) -> str:
    span = "the rest of the night" if narrowed else "the dark window"
    return f"Wind gust over the {max_gust:g} km/h limit during {span}."


def _span_reason(scored: tuple[datetime, datetime]) -> str:
    """The span line: the scored window in the document's own timestamp strings."""
    return f"Scored from {iso_z(scored[0])} to {iso_z(scored[1])} (the rest of tonight)."


def _wind_unavailable_reason() -> str:
    return "Wind data unavailable: the safety limit cannot be confirmed, so not a GO."


_ATMOSPHERE_TERMS: tuple[tuple[str, Callable[[SecondaryHour], float | None]], ...] = (
    ("Seeing", lambda h: h.seeing),
    ("Transparency", lambda h: h.transparency),
)


def _score_reasons(
    window: tuple[datetime, datetime],
    conditions: Conditions,
    terms: ScoreTerms,
    narrowed: bool,
) -> list[str]:
    """Itemise the terms behind a scored verdict, so the explanation follows the math.

    The seeing and transparency lines are explanatory only (the score reads the
    atmosphere factor), so their means are computed here rather than in ``terms``.
    """
    span = "the remaining night" if narrowed else "the dark window"
    reasons = [f"Cloud: {round(terms.cloud_term * 100)}% of {span} usable."]
    reasons.append(f"Atmosphere factor {round(terms.atmosphere_factor * 100)}%.")
    for label, selector in _ATMOSPHERE_TERMS:
        mean, coverage = _optional_term(window, conditions, selector)
        if mean is None:
            continue
        # A mean over part of the usable sky says so, so a 0% line beside a 97%
        # factor reads as what it is (score-remaining-night design D4).
        covers = round(coverage * 100)
        note = "" if covers >= 100 else f" (covers {covers}% of the usable sky)"
        reasons.append(f"{label} quality {round(mean * 100)}%{note}.")
    high_cloud = terms.high_cloud
    # Guard on the *rounded* percentage (not the raw > 0.0 the moon line uses), so a
    # sub-half-percent penalty never emits a confusing "High cloud penalty 0%" line
    # (design D3). Kept distinct from the total-cloud "Cloud:" line above.
    if high_cloud is not None and round(high_cloud * 100) > 0:
        reasons.append(f"High cloud penalty {round(high_cloud * 100)}% (thin cirrus aloft).")
    if terms.moon_penalty > 0.0:
        reasons.append(
            f"Moon penalty {round(terms.moon_penalty * 100)}% (illuminated and up during darkness)."
        )
    reasons.append(f"Score {terms.score}/100.")
    return reasons


def evaluate(
    pier: PierConfig,
    instant: datetime,
    window: tuple[datetime, datetime] | tuple[None, None],
    conditions: Conditions,
    moon: Moon,
) -> Decision:
    """Decide the verdict from astronomy, the conditions groups, and the moon.

    Every condition rule judges the **scored window**: the dark window clamped to
    start no earlier than the scoring instant, the evaluation instant floored to a
    whole second as ``generated_at`` is. Before dusk that is the whole night; once
    the night has started, hours that have passed no longer count
    (score-remaining-night design D1).

    The degradation ladder runs in a fixed precedence so the cases never
    contradict (design D6): no dark window → no dark time left → wind gate → cloud
    entirely missing → cloud present (overcast gate, else score). A NO-GO is only
    ever a failed hard gate; a missing observation or a scored window under
    ``MIN_SCORED`` caps the verdict at MAYBE but never fails one.
    """
    start, end = window
    # 1. No dark window: astronomy alone decides, with no forecast to distrust.
    if start is None or end is None:
        return Decision(Verdict.NO_GO, None, Band.HIGH, 100, [_REASON_NO_WINDOW], (None, None))
    bounded: tuple[datetime, datetime] = (start, end)
    # The inner max drops the hours that have passed; the outer min keeps the start
    # from passing the end when the instant lies in the window's last partial second.
    now = instant.replace(microsecond=0)
    scored: tuple[datetime, datetime] = (min(max(now, start), end), end)
    # Narrowed: hours have passed, so every reason speaks of the rest of the night,
    # after a first line naming the span judged (score-remaining-night design D4).
    narrowed = scored[0] > start
    span = [_span_reason(scored)] if narrowed else []

    # 1a. No dark time left: the instant lies in the window's last partial second.
    #     An empty window tiles no usable hour, so letting it fall through would
    #     read as "conditions unavailable", which is false (design D2). Confidence
    #     is 0 in LOW by construction: completeness over no coverage is 0, and it
    #     multiplies the whole value, so there is nothing for lead time to add.
    if scored[0] == scored[1]:
        return Decision(Verdict.MAYBE, 0, Band.LOW, 0, [*span, _REASON_NO_DARK_TIME], scored)

    band, conf_value = confidence(pier, instant, bounded, scored, conditions)

    # 2. Wind gate (opt-in). A forecast gust over the limit is a safety NO-GO,
    #    evaluated before any cloud logic so a missing cloud observation cannot
    #    override it. If the limit is set but wind is not fully covered, the limit
    #    cannot be confirmed: cap at MAYBE (never GO) rather than fail-open.
    wind_capped = False
    if pier.max_gust is not None:
        if wind_exceeds_limit(scored, conditions, pier.max_gust):
            reasons = [*span, _wind_reason(pier.max_gust, narrowed)]
            return Decision(Verdict.NO_GO, None, band, conf_value, reasons, scored)
        if not wind_fully_covered(scored, conditions):
            wind_capped = True

    # 3. Cloud entirely missing: no evidence the sky is clear, but absence is not
    #    a dealbreaker. MAYBE with a zero score and zero confidence.
    if not cloud_available(scored, conditions):
        unavailable = (
            _REASON_CONDITIONS_UNAVAILABLE_REST if narrowed else _REASON_CONDITIONS_UNAVAILABLE
        )
        reasons = [*span, unavailable]
        if wind_capped:
            reasons.append(_wind_unavailable_reason())
        return Decision(Verdict.MAYBE, 0, Band.LOW, 0, reasons, scored)

    # 4. Cloud present: the overcast gate can fire; otherwise score the night.
    if is_overcast(scored, conditions):
        overcast = _REASON_OVERCAST_REST if narrowed else _REASON_OVERCAST
        return Decision(Verdict.NO_GO, None, band, conf_value, [*span, overcast], scored)

    terms = score_terms(scored, conditions, moon)
    score = terms.score
    reasons = [*span, *_score_reasons(scored, conditions, terms, narrowed)]
    if wind_capped:
        reasons.append(_wind_unavailable_reason())
    # A short window keeps its honest score, but is never worth setting up for.
    short = scored[1] - scored[0] < MIN_SCORED
    if short:
        reasons.append(_REASON_SHORT_WINDOW)
    is_go = score >= pier.go_threshold and not wind_capped and not short
    verdict = Verdict.GO if is_go else Verdict.MAYBE
    return Decision(verdict, score, band, conf_value, reasons, scored)
