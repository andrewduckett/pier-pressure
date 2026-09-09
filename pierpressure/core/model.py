"""The verdict-document contract (design D2).

This module defines the single JSON document the whole system is built around.
Its shape is frozen now (M1) with stubbed decision values; later milestones fill
the same fields with real astronomy, conditions, and ranking without reshaping
the document.

Serialization rules for determinism:
- timestamps are UTC ISO-8601 with a ``Z`` suffix;
- keys are emitted in a fixed order (the field definition order below);
- every contract key is always present — a field with no value is emitted as
  JSON ``null``, never omitted (in particular ``score`` on a gated NO-GO).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)


class Verdict(StrEnum):
    """The go/no-go decision. Exactly one of these three values."""

    GO = "GO"
    MAYBE = "MAYBE"
    NO_GO = "NO-GO"


class Band(StrEnum):
    """The confidence band."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MoonPhase(StrEnum):
    """The eight standard moon phases, derived from the sun-moon elongation.

    The continuous phase angle maps to these by 45-degree octants centred on the
    cardinal points (design D4).
    """

    NEW = "new"
    WAXING_CRESCENT = "waxing crescent"
    FIRST_QUARTER = "first quarter"
    WAXING_GIBBOUS = "waxing gibbous"
    FULL = "full"
    WANING_GIBBOUS = "waning gibbous"
    LAST_QUARTER = "last quarter"
    WANING_CRESCENT = "waning crescent"


Score = Annotated[int, Field(ge=0, le=100)]
ConfidenceValue = Annotated[int, Field(ge=0, le=100)]


def _iso_z(dt: datetime) -> str:
    """Render a tz-aware datetime as UTC ISO-8601 (whole seconds) with a ``Z``."""
    text = dt.astimezone(UTC).isoformat(timespec="seconds")
    if text.endswith("+00:00"):
        text = text[:-6] + "Z"
    return text


def _require_aware_utc(value: datetime) -> datetime:
    """Reject naive datetimes; normalize to UTC at whole-second precision (design D3).

    Truncating the sub-second component here — at validation, not only at
    serialization — is what keeps the in-memory document and its JSON in step, so
    a document survives a serialize-then-read-back round trip unchanged.
    """
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC).replace(microsecond=0)


def _round_fraction(value: float) -> float:
    """Round an illuminated fraction to 2 dp (design D3), for byte-identity."""
    return round(value, 2)


IlluminatedFraction = Annotated[float, Field(ge=0.0, le=1.0), AfterValidator(_round_fraction)]


class Confidence(BaseModel):
    """How much to trust the verdict given forecast lead-time and freshness."""

    model_config = ConfigDict(extra="forbid")

    band: Band
    value: ConfidenceValue


class DarkWindow(BaseModel):
    """Astronomical night boundary (dusk -> dawn). Null until the sky-math milestone."""

    model_config = ConfigDict(extra="forbid")

    start: datetime | None = None
    end: datetime | None = None

    @field_validator("start", "end")
    @classmethod
    def _aware_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else _require_aware_utc(value)

    @field_serializer("start", "end")
    def _serialize(self, value: datetime | None) -> str | None:
        return None if value is None else _iso_z(value)


class Moon(BaseModel):
    """The moon's illumination, phase, and behaviour across the dark window.

    ``illumination`` and ``phase`` are always present. ``up_during_dark``,
    ``rise``, and ``set`` describe the moon *within* the astronomical-night
    window and are null when there is no dark window (design D4). ``rise``/``set``
    carry the same aware-UTC + whole-second normalization as
    :class:`DarkWindow`, so no sub-second precision leaks past the truncation
    rule.
    """

    model_config = ConfigDict(extra="forbid")

    illumination: IlluminatedFraction
    phase: MoonPhase
    up_during_dark: bool | None = None
    rise: datetime | None = None
    set: datetime | None = None

    @field_validator("rise", "set")
    @classmethod
    def _aware_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else _require_aware_utc(value)

    @field_serializer("rise", "set")
    def _serialize(self, value: datetime | None) -> str | None:
        return None if value is None else _iso_z(value)


class VerdictDocument(BaseModel):
    """The one JSON document the whole system is built around.

    Fields are declared in the frozen contract order; Pydantic preserves that
    order in ``model_dump``/``model_dump_json``, which is what the fixed-key-order
    determinism guarantee relies on.
    """

    model_config = ConfigDict(extra="forbid")

    pier: str
    generated_at: datetime
    verdict: Verdict
    score: Score | None = None
    confidence: Confidence
    reasons: list[str]
    targets: list[str] = Field(default_factory=list)
    dark_window: DarkWindow
    moon: Moon

    @field_validator("generated_at")
    @classmethod
    def _aware_utc(cls, value: datetime) -> datetime:
        return _require_aware_utc(value)

    @field_serializer("generated_at")
    def _serialize_generated_at(self, value: datetime) -> str:
        return _iso_z(value)

    def to_json(self) -> str:
        """Serialize to the canonical JSON string (fixed order, all keys, ``Z``)."""
        return self.model_dump_json()
