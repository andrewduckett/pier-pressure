"""Task 3.1-3.2: the structured ``Target`` element and the ``targets`` fill (ADR-0009).

The ``Target`` shape is the additive fill of the reserved-but-shapeless
``targets`` stub: numbers only, no per-target prose. These tests pin its fields,
its whole-second UTC times, its fixed degree rounding, and its JSON key order, and
prove a ``VerdictDocument`` carrying targets round-trips through JSON unchanged.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from pierpressure.core.model import (
    Band,
    Confidence,
    DarkWindow,
    Moon,
    MoonPhase,
    Target,
    TargetWindow,
    Verdict,
    VerdictDocument,
)

_START = datetime(2026, 9, 8, 20, 30, 49, tzinfo=UTC)
_END = datetime(2026, 9, 9, 3, 25, 52, tzinfo=UTC)
_TRANSIT = datetime(2026, 9, 9, 0, 12, 5, tzinfo=UTC)

TARGET_KEY_ORDER = [
    "id",
    "name",
    "type",
    "score",
    "window",
    "max_altitude",
    "transit_time",
    "moon_separation",
    "size_arcmin",
    "magnitude",
    "surface_brightness",
]


def _target(**overrides: object) -> Target:
    base: dict[str, object] = {
        "id": "NGC0224",
        "name": "Andromeda Galaxy",
        "type": "G",
        "score": 88,
        "window": TargetWindow(start=_START, end=_END),
        "max_altitude": 61.234,
        "transit_time": _TRANSIT,
        "moon_separation": 112.5,
        "size_arcmin": 177.83,
        "magnitude": 3.44,
        "surface_brightness": 13.91,
    }
    base.update(overrides)
    return Target(**base)  # type: ignore[arg-type]


def test_target_carries_all_fields() -> None:
    target = _target()
    assert target.id == "NGC0224"
    assert target.name == "Andromeda Galaxy"
    assert target.type == "G"
    assert target.score == 88
    assert target.window.start == _START
    assert target.window.end == _END
    assert target.transit_time == _TRANSIT


def test_target_name_is_nullable() -> None:
    assert _target(name=None).name is None


def test_target_carries_size_and_brightness() -> None:
    target = _target()
    assert target.size_arcmin == 177.83
    assert target.magnitude == 3.44
    assert target.surface_brightness == 13.91


def test_target_size_and_brightness_are_nullable_and_present() -> None:
    # Missing catalog values are null (present, not omitted) rather than guessed.
    target = _target(size_arcmin=None, magnitude=None, surface_brightness=None)
    assert target.size_arcmin is None
    assert target.magnitude is None
    assert target.surface_brightness is None
    payload = json.loads(target.model_dump_json())
    assert payload["size_arcmin"] is None
    assert payload["magnitude"] is None
    assert payload["surface_brightness"] is None


def test_target_catalog_values_round_to_fixed_precision() -> None:
    # The emitted raw facts round to a fixed precision so the document is byte-stable.
    target = _target(size_arcmin=177.8349, magnitude=3.4412, surface_brightness=13.9987)
    assert target.size_arcmin == 177.83
    assert target.magnitude == 3.44
    assert target.surface_brightness == 14.0


def test_target_keys_are_in_fixed_order() -> None:
    payload = json.loads(_target().model_dump_json())
    assert list(payload.keys()) == TARGET_KEY_ORDER


def test_target_window_serializes_with_z_suffix() -> None:
    payload = json.loads(_target().model_dump_json())
    assert payload["window"]["start"] == "2026-09-08T20:30:49Z"
    assert payload["window"]["end"] == "2026-09-09T03:25:52Z"
    assert payload["transit_time"] == "2026-09-09T00:12:05Z"


def test_target_times_are_whole_second_in_memory() -> None:
    target = _target(
        transit_time=datetime(2026, 9, 9, 0, 12, 5, 987654, tzinfo=UTC),
        window=TargetWindow(
            start=_START.replace(microsecond=123456),
            end=_END.replace(microsecond=654321),
        ),
    )
    assert target.transit_time.microsecond == 0
    assert target.window.start.microsecond == 0
    assert target.window.end.microsecond == 0


def test_target_degrees_are_rounded_to_fixed_precision() -> None:
    target = _target(max_altitude=61.23456789, moon_separation=112.98765)
    assert target.max_altitude == 61.235
    assert target.moon_separation == 112.988


def test_target_naive_time_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _target(transit_time=datetime(2026, 9, 9, 0, 12, 5))  # naive


def test_target_non_utc_time_is_normalized() -> None:
    plus_two = timezone(timedelta(hours=2))
    target = _target(transit_time=datetime(2026, 9, 9, 2, 12, 5, tzinfo=plus_two))
    assert json.loads(target.model_dump_json())["transit_time"] == "2026-09-09T00:12:05Z"


@pytest.mark.parametrize("bad_score", [-1, 101])
def test_target_out_of_range_score_is_rejected(bad_score: int) -> None:
    with pytest.raises(ValidationError):
        _target(score=bad_score)


def test_target_round_trips_through_json() -> None:
    target = _target()
    reloaded = Target.model_validate_json(target.model_dump_json())
    assert reloaded == target


# --------------------------------------------------------------------------- #
# Task 3.2 — the document carries a list[Target]
# --------------------------------------------------------------------------- #


def _document(targets: list[Target]) -> VerdictDocument:
    return VerdictDocument(
        pier="backyard",
        generated_at=datetime(2026, 9, 8, 18, 0, tzinfo=UTC),
        verdict=Verdict.GO,
        score=80,
        confidence=Confidence(band=Band.HIGH, value=100),
        reasons=["Score 80/100."],
        targets=targets,
        dark_window=DarkWindow(start=_START, end=_END),
        moon=Moon(illumination=0.1, phase=MoonPhase.WANING_CRESCENT),
    )


def test_document_targets_default_empty() -> None:
    payload = json.loads(_document([]).to_json())
    assert payload["targets"] == []


def test_document_with_targets_round_trips() -> None:
    doc = _document([_target(), _target(id="NGC1976", name=None, score=70)])
    reloaded = VerdictDocument.model_validate_json(doc.to_json())
    assert reloaded == doc


def test_document_targets_preserve_key_order() -> None:
    payload = json.loads(_document([_target()]).to_json())
    assert list(payload["targets"][0].keys()) == TARGET_KEY_ORDER
    # The document's own key order is unchanged: targets sits where it always has.
    assert list(payload.keys()) == [
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
