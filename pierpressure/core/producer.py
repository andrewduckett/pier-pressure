"""The verdict producer (design D4).

Assembles the one verdict document from three pure inputs: the pier, the injected
clock, and an already-obtained :class:`Conditions` value. M2 made the astronomy
real; M3 makes the decision fields real by folding the gates, banded score, and
lead-time confidence (``core/scoring``) over the conditions series. The signature
and the document shape are the frozen contract; the document is *filled*, never
reshaped.

The core does no I/O: the conditions value is plain data built by the provider
layer outside the core (design D1), so ``produce_verdict`` stays a deterministic
function of its inputs and a pinned conditions value yields a byte-identical
document.
"""

from __future__ import annotations

from datetime import datetime
from typing import get_args

from .clock import Clock
from .conditions import Conditions, Variable
from .config import PierConfig
from .model import Agreement, Confidence, DarkWindow, TimelineEntry, VerdictDocument
from .ranking import equipment_reasons, rank_targets
from .scoring import MIN_USABLE_WINDOW, AgreementTerm, evaluate
from .sky import altitudes_at, dark_window, moon_info


def produce_verdict(pier: PierConfig, clock: Clock, conditions: Conditions) -> VerdictDocument:
    """Produce the verdict document for ``pier`` at the injected clock instant.

    ``pier`` is an already-validated :class:`PierConfig`; ``conditions`` is the
    immutable per-variable value the provider layer obtained for this evaluation. The
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
        agreement=_agreement(decision.agreement),
    )


def _agreement(term: AgreementTerm | None) -> dict[str, Agreement]:
    """The document's ``agreement``: cloud cover only for now, empty without a term."""
    if term is None:
        return {}
    return {
        "cloud_cover": Agreement(band=term.band, spread=term.spread, providers=list(term.providers))
    }


def _timeline(pier: PierConfig, conditions: Conditions) -> list[TimelineEntry]:
    """One entry per hour any filled series covers, sorted, with each series' reading."""
    times = list(conditions.hours(get_args(Variable)))
    return [
        TimelineEntry(
            time=time,
            sun_altitude=sun,
            moon_altitude=moon,
            **{variable: conditions.value_at(variable, time) for variable in get_args(Variable)},
            **_cloud_band(conditions, time),
        )
        for time, (sun, moon) in zip(times, altitudes_at(pier, times), strict=True)
    ]


def _cloud_band(conditions: Conditions, time: datetime) -> dict[str, float | None]:
    """The hour's lowest and highest cloud, null unless two or more providers gave one."""
    values = [value for _, value in conditions.readings_at("cloud_cover", time)]
    if len(values) < 2:
        return {"cloud_cover_min": None, "cloud_cover_max": None}
    return {"cloud_cover_min": min(values), "cloud_cover_max": max(values)}
