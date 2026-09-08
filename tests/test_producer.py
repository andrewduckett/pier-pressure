"""Tasks 4.1 and 4.2: the stub producer and its determinism."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pierpressure.core.clock import FixedClock
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Band, Verdict
from pierpressure.core.producer import produce_verdict
from pierpressure.delivery.mqtt import DeliveryError

from .conftest import make_pier


def test_stub_document_shape() -> None:
    clock = FixedClock(datetime(2026, 9, 7, 21, 30, tzinfo=UTC))
    doc = produce_verdict(make_pier(), clock)
    assert doc.verdict is Verdict.MAYBE
    assert doc.score == 50
    assert doc.confidence.band is Band.LOW
    assert doc.confidence.value == 0
    assert len(doc.reasons) == 1 and doc.reasons[0]
    assert doc.targets == []
    assert doc.dark_window.start is None and doc.dark_window.end is None


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
