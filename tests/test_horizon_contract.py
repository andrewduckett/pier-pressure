"""Task 5.1: a configured horizon leaves the verdict document byte-identical.

In M4 the horizon mask is configuration and a query seam only — it has no consumer
in the verdict document. Producing a verdict for a pier with a horizon configured
MUST yield a document byte-identical to the same pier, instant, and conditions with
no horizon, with ``targets`` empty in both. This locks the frozen delivery contract
until a later milestone gives the horizon a consumer.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pierpressure.core.clock import FixedClock
from pierpressure.core.config import HorizonConfig, PierConfig
from pierpressure.core.producer import produce_verdict

from .conftest import make_conditions
from .offline_guard import no_network


def _pier(horizon: HorizonConfig | None) -> PierConfig:
    return PierConfig(
        id="backyard",
        latitude=51.5,
        longitude=-0.12,
        elevation_m=30.0,
        horizon=horizon,
    )


def test_a_configured_horizon_leaves_the_verdict_document_unchanged() -> None:
    instant = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)
    conditions = make_conditions()

    without_horizon = _pier(None)
    with_horizon = _pier(HorizonConfig(points=[(0, 10), (90, 30), (270, 25)]))

    # Sanity: the horizon really is configured (a non-open-sky mask).
    assert with_horizon.horizon_mask.alt_at(90) == 30.0
    assert without_horizon.horizon_mask.alt_at(90) == 0.0

    with no_network():
        doc_without = produce_verdict(without_horizon, FixedClock(instant), conditions)
        doc_with = produce_verdict(with_horizon, FixedClock(instant), conditions)

    assert doc_with.to_json() == doc_without.to_json()
    assert doc_with.targets == []
    assert doc_without.targets == []
