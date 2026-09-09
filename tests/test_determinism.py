"""Task 5.1: whole-document determinism and offline production (design D6).

Two runs at a pinned instant must be byte-identical across every field the M2
astronomy fills — ``generated_at``, ``dark_window``, and ``moon`` — and the whole
``produce_verdict`` call must complete with no network access.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from pierpressure.core.clock import FixedClock
from pierpressure.core.producer import produce_verdict

from .conftest import make_pier
from .offline_guard import no_network

# London; a daytime instant selecting a night with a real moonrise, so the
# byte-identity claim covers populated dark_window and moon fields, not nulls.
_PINNED_INSTANT = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)


def test_two_runs_are_byte_identical_offline() -> None:
    pier = make_pier()
    clock = FixedClock(_PINNED_INSTANT)

    with no_network():
        first = produce_verdict(pier, clock).to_json()
        second = produce_verdict(pier, clock).to_json()

    assert first == second

    payload = json.loads(first)
    # The identity spans real astronomy, not the M1 null stubs.
    assert payload["generated_at"] == "2026-09-08T14:00:00Z"
    assert payload["dark_window"]["start"] is not None
    assert payload["dark_window"]["end"] is not None
    assert payload["moon"]["rise"] is not None
    assert 0.0 <= payload["moon"]["illumination"] <= 1.0
    assert payload["moon"]["phase"]


def test_production_makes_no_network_access() -> None:
    # produce_verdict raises nothing under the offline guard: it reaches only the
    # pinned ephemeris and built-in timescale on disk.
    with no_network():
        doc = produce_verdict(make_pier(), FixedClock(_PINNED_INSTANT))
    assert doc.dark_window.start is not None
