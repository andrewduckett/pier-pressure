"""The horizon mask feeds only ``targets`` (M5 additive contract).

In M4 the horizon mask was configuration and a query seam with no consumer in the
verdict document. M5 gives it its consumer — target ranking — so a configured
horizon now changes ``targets`` (a restrictive mask hides objects) while leaving
every other document field byte-identical to the same pier, instant, and
conditions with no horizon. This locks the additive-only boundary: the horizon
reaches the document through ``targets`` and nowhere else.
"""

from __future__ import annotations

import json
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


def _without_targets(document_json: str) -> dict:
    payload = json.loads(document_json)
    payload.pop("targets")
    return payload


def test_horizon_changes_only_targets() -> None:
    instant = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)
    conditions = make_conditions()

    without_horizon = _pier(None)
    # A near-zenith flat mask hides almost the whole sky, so the visible target
    # set genuinely differs from open sky.
    with_horizon = _pier(HorizonConfig(min_altitude=85.0))

    # Sanity: the horizon really is configured (a non-open-sky mask).
    assert with_horizon.horizon_mask.alt_at(90) == 85.0
    assert without_horizon.horizon_mask.alt_at(90) == 0.0

    with no_network():
        doc_without = produce_verdict(without_horizon, FixedClock(instant), conditions)
        doc_with = produce_verdict(with_horizon, FixedClock(instant), conditions)

    # Every field except targets is byte-identical: the horizon is not a consumer
    # of verdict, score, confidence, reasons, dark_window, or moon.
    assert _without_targets(doc_with.to_json()) == _without_targets(doc_without.to_json())

    # But the horizon IS a consumer of targets now: the restrictive mask changes
    # the ranked list, and every surviving target clears the 85-degree mask.
    assert doc_with.targets != doc_without.targets
    assert all(t.max_altitude >= 85.0 for t in doc_with.targets)
