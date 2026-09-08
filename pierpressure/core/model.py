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

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


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


Score = Annotated[int, Field(ge=0, le=100)]
ConfidenceValue = Annotated[int, Field(ge=0, le=100)]


def _iso_z(dt: datetime) -> str:
    """Render a tz-aware datetime as UTC ISO-8601 with a ``Z`` suffix."""
    text = dt.astimezone(UTC).isoformat()
    if text.endswith("+00:00"):
        text = text[:-6] + "Z"
    return text


def _require_aware_utc(value: datetime) -> datetime:
    """Reject naive datetimes and normalize to UTC (design D3)."""
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC)


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
