"""The verdict producer (design D4).

In M1 this is a deterministic, honest-but-coarse stub: it names itself a
skeleton and returns fixed decision values. M2/M3 replace the body behind this
signature with real astronomy and conditions math. The signature and the
returned document shape are the frozen contract.
"""

from __future__ import annotations

from .clock import Clock
from .config import PierConfig
from .model import Band, Confidence, DarkWindow, Verdict, VerdictDocument
from .sky import dark_window, moon_info

_SKELETON_REASON = "Walking skeleton: real verdict logic not yet implemented"


def produce_verdict(pier: PierConfig, clock: Clock) -> VerdictDocument:
    """Produce the verdict document for ``pier`` at the injected clock instant.

    ``pier`` is an already-validated :class:`PierConfig`; an invalid site is
    rejected earlier at config validation (a producer/config error, distinct
    from a delivery error — design D9). The single evaluation instant comes from
    the injected ``clock`` and drives ``generated_at`` as well as the astronomy,
    so the whole document is a pure function of ``(pier, clock)``.

    M2 fills ``dark_window`` and ``moon`` with real, offline sky math (core/sky).
    ``verdict``/``score``/``confidence``/``targets`` remain the M1 stubs until the
    milestones that make them real; the signature and document key order are the
    frozen contract.
    """
    instant = clock.now()
    window = dark_window(pier, instant)
    start, end = window
    return VerdictDocument(
        pier=pier.id,
        generated_at=instant,
        verdict=Verdict.MAYBE,
        score=50,
        confidence=Confidence(band=Band.LOW, value=0),
        reasons=[_SKELETON_REASON],
        targets=[],
        dark_window=DarkWindow(start=start, end=end),
        moon=moon_info(pier, window, instant),
    )
