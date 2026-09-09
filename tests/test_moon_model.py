"""Tasks 2.1 and 2.3: the MoonPhase enum and the Moon model."""

from __future__ import annotations

import json
from datetime import UTC, datetime

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


def test_moon_phase_has_the_eight_standard_phases() -> None:
    assert {p.value for p in MoonPhase} == {
        "new",
        "waxing crescent",
        "first quarter",
        "waxing gibbous",
        "full",
        "waning gibbous",
        "last quarter",
        "waning crescent",
    }


def test_moon_phase_members_stringify_to_their_values() -> None:
    # StrEnum members are their string value (matches Verdict/Band).
    assert MoonPhase.NEW == "new"
    assert MoonPhase.WAXING_CRESCENT == "waxing crescent"
    assert MoonPhase.FIRST_QUARTER == "first quarter"
    assert MoonPhase.WAXING_GIBBOUS == "waxing gibbous"
    assert MoonPhase.FULL == "full"
    assert MoonPhase.WANING_GIBBOUS == "waning gibbous"
    assert MoonPhase.LAST_QUARTER == "last quarter"
    assert MoonPhase.WANING_CRESCENT == "waning crescent"


# --------------------------------------------------------------------------- #
# Task 2.3: the Moon model
# --------------------------------------------------------------------------- #


def test_moon_across_window_fields_default_to_null() -> None:
    moon = Moon(illumination=0.5, phase=MoonPhase.FIRST_QUARTER)
    assert moon.up_during_dark is None
    assert moon.rise is None
    assert moon.set is None


def test_moon_illumination_is_rounded_to_two_places() -> None:
    assert Moon(illumination=0.123456, phase=MoonPhase.NEW).illumination == 0.12
    assert Moon(illumination=0.985, phase=MoonPhase.FULL).illumination == 0.98


@pytest.mark.parametrize("bad", [-0.01, 1.01])
def test_moon_illumination_out_of_bounds_is_rejected(bad: float) -> None:
    with pytest.raises(ValidationError):
        Moon(illumination=bad, phase=MoonPhase.NEW)


def test_moon_rise_set_reject_naive_datetimes() -> None:
    with pytest.raises(ValidationError):
        Moon(
            illumination=0.5,
            phase=MoonPhase.FULL,
            rise=datetime(2026, 9, 7, 22, 0, 0),  # naive
        )


def test_moon_rise_set_microseconds_are_stripped_in_memory() -> None:
    moon = Moon(
        illumination=0.5,
        phase=MoonPhase.FULL,
        up_during_dark=True,
        rise=datetime(2026, 9, 7, 22, 15, 30, 424242, tzinfo=UTC),
        set=datetime(2026, 9, 8, 3, 5, 10, 999999, tzinfo=UTC),
    )
    assert moon.rise is not None and moon.rise.microsecond == 0
    assert moon.set is not None and moon.set.microsecond == 0


def test_moon_serializes_rise_set_with_z_and_whole_seconds() -> None:
    moon = Moon(
        illumination=0.5,
        phase=MoonPhase.FULL,
        up_during_dark=True,
        rise=datetime(2026, 9, 7, 22, 15, 30, 424242, tzinfo=UTC),
        set=None,
    )
    payload = json.loads(moon.model_dump_json())
    assert payload["rise"] == "2026-09-07T22:15:30Z"
    assert payload["set"] is None


def _document_with_moon(moon: Moon) -> VerdictDocument:
    return VerdictDocument(
        pier="backyard",
        generated_at=datetime(2026, 9, 7, 21, 30, tzinfo=UTC),
        verdict=Verdict.MAYBE,
        score=50,
        confidence=Confidence(band=Band.LOW, value=0),
        reasons=["x"],
        targets=[],
        dark_window=DarkWindow(),
        moon=moon,
    )


def test_verdict_document_has_moon_as_last_key() -> None:
    moon = Moon(illumination=0.5, phase=MoonPhase.FIRST_QUARTER)
    payload = json.loads(_document_with_moon(moon).to_json())
    assert "moon" in payload
    assert list(payload.keys())[-1] == "moon"
    assert payload["moon"]["illumination"] == 0.5
    assert payload["moon"]["phase"] == "first quarter"


def test_document_with_moon_round_trips() -> None:
    moon = Moon(
        illumination=0.73,
        phase=MoonPhase.WANING_GIBBOUS,
        up_during_dark=True,
        rise=datetime(2026, 9, 7, 22, 15, 30, tzinfo=UTC),
        set=datetime(2026, 9, 8, 3, 5, 10, tzinfo=UTC),
    )
    doc = _document_with_moon(moon)
    assert VerdictDocument.model_validate_json(doc.to_json()) == doc
