"""Injectable clock (design D3).

``produce_verdict`` reads the current time only from a :class:`Clock`, so tests
can pin the evaluation instant and get byte-identical documents.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Anything that can report the current tz-aware UTC time."""

    def now(self) -> datetime: ...


class SystemClock:
    """Production clock: the real wall-clock time, as tz-aware UTC."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """Test clock: always returns a pinned tz-aware UTC instant."""

    def __init__(self, instant: datetime) -> None:
        if instant.tzinfo is None:
            raise ValueError("FixedClock requires a timezone-aware instant")
        self._instant = instant.astimezone(UTC)

    def now(self) -> datetime:
        return self._instant
