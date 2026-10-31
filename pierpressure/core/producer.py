"""The verdict producer (design D4).

Assembles the one verdict document from three pure inputs: the pier, the injected
clock, and an already-obtained :class:`Conditions` value. M2 made the astronomy
real; M3 makes the decision fields real by folding the gates, banded score, and
lead-time confidence (``core/scoring``) over the conditions groups. The signature
and the document shape are the frozen contract; the document is *filled*, never
reshaped.

The core does no I/O: the conditions value is plain data built by the provider
layer outside the core (design D1), so ``produce_verdict`` stays a deterministic
function of its inputs and a pinned conditions value yields a byte-identical
document.
"""

from __future__ import annotations

from datetime import datetime

from .clock import Clock
from .conditions import Conditions
from .config import PierConfig
from .model import Confidence, DarkWindow, TimelineEntry, VerdictDocument
from .ranking import equipment_reasons, rank_targets
from .scoring import MIN_USABLE_WINDOW, evaluate
from .sky import altitudes_at, dark_window, moon_info


def produce_verdict(pier: PierConfig, clock: Clock, conditions: Conditions) -> VerdictDocument:
    """Produce the verdict document for ``pier`` at the injected clock instant.

    ``pier`` is an already-validated :class:`PierConfig`; ``conditions`` is the
    immutable per-source value the provider layer obtained for this evaluation. The
    single evaluation instant comes from the injected ``clock`` and drives
    ``generated_at``, the astronomy, and the lead-time confidence, so the whole
    document is a pure function of ``(pier, clock, conditions)``.

    When the selected night has no dark window, astronomy alone decides the
    verdict (a NO-GO) and ignores the conditions, matching the rule that no dark
    window means conditions are not required. The ``timeline`` still carries every
    hour the providers returned: it is evidence beside the verdict, never an input
    to it (ADR-0025).
    """
    instant = clock.now()
    window = dark_window(pier, instant)
    moon = moon_info(pier, window, instant)
    decision = evaluate(pier, instant, window, conditions, moon)
    targets = rank_targets(pier, instant, window, moon)

    # The verdict's own itemised terms, then additive equipment-aware notes about
    # the top pick where the equipment and its facts are known (design D8). Appending
    # never changes an existing reason, and the notes are a pure function of the
    # pick's facts, so the reasons stay deterministic. The notes are added only on a
    # gate-passing verdict (a non-null score) with a scored window worth setting up
    # for: a NO-GO night has been ruled out, and a span under MIN_USABLE_WINDOW has
    # just said "not worth setting up", so neither advertises a target.
    reasons = list(decision.reasons)
    scored_start, scored_end = decision.scored_window
    worth_setting_up = (
        scored_start is not None
        and scored_end is not None
        and scored_end - scored_start >= MIN_USABLE_WINDOW
    )
    if targets and decision.score is not None and worth_setting_up:
        reasons.extend(equipment_reasons(pier.equipment, targets[0]))

    start, end = window
    return VerdictDocument(
        pier=pier.id,
        generated_at=instant,
        verdict=decision.verdict,
        score=decision.score,
        confidence=Confidence(band=decision.band, value=decision.confidence),
        reasons=reasons,
        targets=targets,
        dark_window=DarkWindow(start=start, end=end),
        # The span the gates and score judged (score-remaining-night design D5).
        scored_window=DarkWindow(start=scored_start, end=scored_end),
        moon=moon,
        timeline=_timeline(pier, conditions),
    )


def _timeline(pier: PierConfig, conditions: Conditions) -> list[TimelineEntry]:
    """One entry per hour either source returned, sorted, with that hour's readings."""
    base, secondary = conditions.base, conditions.secondary
    hours: set[datetime] = set()
    if base is not None:
        hours.update(hour.time for hour in base.hours)
    if secondary is not None:
        hours.update(hour.time for hour in secondary.hours)
    times = sorted(hours)

    entries: list[TimelineEntry] = []
    for time, (sun, moon) in zip(times, altitudes_at(pier, times), strict=True):
        b = base.at(time) if base is not None else None
        s = secondary.at(time) if secondary is not None else None
        entries.append(
            TimelineEntry(
                time=time,
                sun_altitude=sun,
                moon_altitude=moon,
                cloud_cover=b.cloud_cover if b is not None else None,
                cloud_low=b.cloud_low if b is not None else None,
                cloud_mid=b.cloud_mid if b is not None else None,
                cloud_high=b.cloud_high if b is not None else None,
                wind_gust=b.wind_gust if b is not None else None,
                seeing=s.seeing if s is not None else None,
                transparency=s.transparency if s is not None else None,
            )
        )
    return entries
