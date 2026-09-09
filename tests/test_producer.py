"""Tasks 4.1 and 4.2: the stub producer and its determinism."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pierpressure.core.clock import FixedClock
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Band, MoonPhase, Verdict
from pierpressure.core.producer import produce_verdict
from pierpressure.delivery.mqtt import DeliveryError

from .conftest import make_pier
from .offline_guard import no_network


def test_decision_fields_are_still_m1_stubs() -> None:
    clock = FixedClock(datetime(2026, 9, 7, 21, 30, tzinfo=UTC))
    with no_network():
        doc = produce_verdict(make_pier(), clock)
    assert doc.verdict is Verdict.MAYBE
    assert doc.score == 50
    assert doc.confidence.band is Band.LOW
    assert doc.confidence.value == 0
    assert len(doc.reasons) == 1 and doc.reasons[0]
    assert doc.targets == []


def test_dark_window_and_moon_are_real_for_a_pinned_site_and_instant() -> None:
    # make_pier() is London; a daytime instant selects that evening's night.
    clock = FixedClock(datetime(2026, 9, 8, 14, 0, tzinfo=UTC))
    with no_network():
        doc = produce_verdict(make_pier(), clock)

    # Real astronomical-night window, not the M1 null stub.
    assert doc.dark_window.start is not None and doc.dark_window.end is not None
    assert doc.dark_window.start < doc.dark_window.end

    # Real moon object across that window.
    assert 0.0 <= doc.moon.illumination <= 1.0
    assert isinstance(doc.moon.phase, MoonPhase)
    assert doc.moon.up_during_dark is True  # the moon rises during this night
    assert doc.moon.rise is not None
    assert doc.dark_window.start <= doc.moon.rise <= doc.dark_window.end


def test_determinism_is_byte_identical_and_pins_the_instant() -> None:
    instant = datetime(2026, 9, 7, 21, 30, tzinfo=UTC)
    clock = FixedClock(instant)
    pier = make_pier()

    first = produce_verdict(pier, clock)
    second = produce_verdict(pier, clock)

    assert first.to_json() == second.to_json()
    assert first.generated_at == instant


def test_invalid_pier_is_rejected_as_a_config_error_not_delivery() -> None:
    # An invalid site is rejected at PierConfig construction (a producer/config
    # domain error), so no document is ever produced.
    with pytest.raises(ValidationError):
        PierConfig(id="bad", latitude=200.0, longitude=-0.12, elevation_m=30.0)

    # Producer/config errors are a distinct type from delivery errors (design D9).
    assert not issubclass(ValidationError, DeliveryError)
    assert not issubclass(DeliveryError, ValidationError)
