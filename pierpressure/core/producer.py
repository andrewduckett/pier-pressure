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

from .clock import Clock
from .conditions import Conditions
from .config import PierConfig
from .model import Confidence, DarkWindow, VerdictDocument
from .scoring import evaluate
from .sky import dark_window, moon_info


def produce_verdict(pier: PierConfig, clock: Clock, conditions: Conditions) -> VerdictDocument:
    """Produce the verdict document for ``pier`` at the injected clock instant.

    ``pier`` is an already-validated :class:`PierConfig`; ``conditions`` is the
    immutable per-source value the provider layer obtained for this evaluation. The
    single evaluation instant comes from the injected ``clock`` and drives
    ``generated_at``, the astronomy, and the lead-time confidence, so the whole
    document is a pure function of ``(pier, clock, conditions)``.

    When the selected night has no dark window, astronomy alone decides
    (a NO-GO) and the conditions value is not consulted — matching the rule that no
    dark window means conditions are not required.
    """
    instant = clock.now()
    window = dark_window(pier, instant)
    moon = moon_info(pier, window, instant)
    decision = evaluate(pier, instant, window, conditions, moon)

    start, end = window
    return VerdictDocument(
        pier=pier.id,
        generated_at=instant,
        verdict=decision.verdict,
        score=decision.score,
        confidence=Confidence(band=decision.band, value=decision.confidence),
        reasons=decision.reasons,
        targets=[],
        dark_window=DarkWindow(start=start, end=end),
        moon=moon,
    )
