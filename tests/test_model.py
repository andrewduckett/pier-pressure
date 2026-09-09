"""Tasks 2.1 and 2.3: verdict-document model, serialization, and bounds."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timezone

import pytest
from pydantic import ValidationError

from pierpressure.core.model import (
    Band,
    Confidence,
    DarkWindow,
    Moon,
    MoonPhase,
    Verdict,
    VerdictDocument,
)

EXPECTED_KEY_ORDER = [
    "pier",
    "generated_at",
    "verdict",
    "score",
    "confidence",
    "reasons",
    "targets",
    "dark_window",
    "moon",
]

_STUB_MOON = Moon(illumination=0.0, phase=MoonPhase.NEW)


def _gated_no_go() -> VerdictDocument:
    return VerdictDocument(
        pier="backyard",
        generated_at=datetime(2026, 9, 7, 21, 30, tzinfo=UTC),
        verdict=Verdict.NO_GO,
        score=None,
        confidence=Confidence(band=Band.LOW, value=0),
        reasons=["No dark window tonight"],
        targets=[],
        dark_window=DarkWindow(start=None, end=None),
        moon=_STUB_MOON,
    )


def test_gated_no_go_score_is_present_and_null() -> None:
    payload = json.loads(_gated_no_go().to_json())
    assert "score" in payload
    assert payload["score"] is None


def test_keys_are_in_fixed_order() -> None:
    payload = json.loads(_gated_no_go().to_json())
    assert list(payload.keys()) == EXPECTED_KEY_ORDER


def test_generated_at_serializes_with_z_suffix() -> None:
    payload = json.loads(_gated_no_go().to_json())
    assert payload["generated_at"].endswith("Z")
    assert payload["generated_at"] == "2026-09-07T21:30:00Z"


def test_round_trips_through_json() -> None:
    doc = _gated_no_go()
    reloaded = VerdictDocument.model_validate_json(doc.to_json())
    assert reloaded == doc


def test_naive_generated_at_is_rejected() -> None:
    with pytest.raises(ValidationError):
        VerdictDocument(
            pier="backyard",
            generated_at=datetime(2026, 9, 7, 21, 30),  # naive
            verdict=Verdict.MAYBE,
            score=50,
            confidence=Confidence(band=Band.LOW, value=0),
            reasons=["x"],
            targets=[],
            dark_window=DarkWindow(),
            moon=_STUB_MOON,
        )


def test_non_utc_timezone_is_normalized_to_utc() -> None:
    from datetime import timedelta

    plus_two = timezone(timedelta(hours=2))
    doc = VerdictDocument(
        pier="backyard",
        generated_at=datetime(2026, 9, 7, 23, 30, tzinfo=plus_two),
        verdict=Verdict.MAYBE,
        score=50,
        confidence=Confidence(band=Band.LOW, value=0),
        reasons=["x"],
        targets=[],
        dark_window=DarkWindow(),
        moon=_STUB_MOON,
    )
    assert json.loads(doc.to_json())["generated_at"] == "2026-09-07T21:30:00Z"


@pytest.mark.parametrize("bad_score", [-1, 101])
def test_out_of_range_score_is_rejected(bad_score: int) -> None:
    with pytest.raises(ValidationError):
        VerdictDocument(
            pier="backyard",
            generated_at=datetime(2026, 9, 7, 21, 30, tzinfo=UTC),
            verdict=Verdict.MAYBE,
            score=bad_score,
            confidence=Confidence(band=Band.LOW, value=0),
            reasons=["x"],
            targets=[],
            dark_window=DarkWindow(),
            moon=_STUB_MOON,
        )


@pytest.mark.parametrize("bad_value", [-5, 200])
def test_out_of_range_confidence_value_is_rejected(bad_value: int) -> None:
    with pytest.raises(ValidationError):
        Confidence(band=Band.HIGH, value=bad_value)


def test_unknown_verdict_is_rejected() -> None:
    with pytest.raises(ValidationError):
        VerdictDocument(
            pier="backyard",
            generated_at=datetime(2026, 9, 7, 21, 30, tzinfo=UTC),
            verdict="PROBABLY",  # type: ignore[arg-type]
            score=50,
            confidence=Confidence(band=Band.LOW, value=0),
            reasons=["x"],
            targets=[],
            dark_window=DarkWindow(),
            moon=_STUB_MOON,
        )


def test_unknown_confidence_band_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Confidence(band="SORTOF", value=50)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Task 2.2: whole-second precision normalized at validation (design D3)
# --------------------------------------------------------------------------- #


def _doc_with_generated_at(instant: datetime) -> VerdictDocument:
    return VerdictDocument(
        pier="backyard",
        generated_at=instant,
        verdict=Verdict.MAYBE,
        score=50,
        confidence=Confidence(band=Band.LOW, value=0),
        reasons=["x"],
        targets=[],
        dark_window=DarkWindow(),
        moon=_STUB_MOON,
    )


def test_generated_at_microseconds_are_stripped_in_memory() -> None:
    doc = _doc_with_generated_at(datetime(2026, 9, 7, 21, 30, 15, 123456, tzinfo=UTC))
    # Normalized at validation, not only at serialization.
    assert doc.generated_at.microsecond == 0
    assert doc.generated_at == datetime(2026, 9, 7, 21, 30, 15, tzinfo=UTC)


def test_generated_at_serializes_at_whole_second_precision() -> None:
    doc = _doc_with_generated_at(datetime(2026, 9, 7, 21, 30, 15, 999999, tzinfo=UTC))
    assert json.loads(doc.to_json())["generated_at"] == "2026-09-07T21:30:15Z"


def test_microsecond_bearing_generated_at_round_trips() -> None:
    doc = _doc_with_generated_at(datetime(2026, 9, 7, 21, 30, 15, 123456, tzinfo=UTC))
    reloaded = VerdictDocument.model_validate_json(doc.to_json())
    assert reloaded == doc


def test_dark_window_microseconds_are_stripped_in_memory() -> None:
    window = DarkWindow(
        start=datetime(2026, 9, 7, 20, 15, 30, 654321, tzinfo=UTC),
        end=datetime(2026, 9, 8, 4, 45, 10, 111111, tzinfo=UTC),
    )
    assert window.start is not None and window.start.microsecond == 0
    assert window.end is not None and window.end.microsecond == 0
