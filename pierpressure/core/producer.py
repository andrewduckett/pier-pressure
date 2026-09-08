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

_SKELETON_REASON = "Walking skeleton: real verdict logic not yet implemented"


def produce_verdict(pier: PierConfig, clock: Clock) -> VerdictDocument:
    """Produce the deterministic M1 stub verdict document for ``pier``.

    ``pier`` is an already-validated :class:`PierConfig`; an invalid site is
    rejected earlier at config validation (a producer/config error, distinct
    from a delivery error — design D9). The only time-varying field,
    ``generated_at``, comes solely from the injected ``clock``.
    """
    return VerdictDocument(
        pier=pier.id,
        generated_at=clock.now(),
        verdict=Verdict.MAYBE,
        score=50,
        confidence=Confidence(band=Band.LOW, value=0),
        reasons=[_SKELETON_REASON],
        targets=[],
        dark_window=DarkWindow(start=None, end=None),
    )
