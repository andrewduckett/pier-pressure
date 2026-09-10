"""The conditions snapshot — the observing-conditions input to the core (design D1, D2).

The provider layer (outside the core) builds this immutable value from external
forecasts; the core only reads it. Keeping the seam a *plain data value* is what
keeps ``produce_verdict`` a pure, deterministic function: a data value cannot
fetch anything, so no I/O can creep back across the boundary and the offline
guarantee stays a hard wall rather than "deterministic if mocked correctly".

Shape (design D2): one availability-stamped hourly grid. Each hour carries cloud
cover, wind gust, seeing, and transparency, and **each field is stamped
present-or-absent** — a field is absent when its value is ``None``, so a partial
snapshot (some fields present, others absent) is an ordinary, valid value rather
than an error. The snapshot also records a per-source issue time so the core can
compute freshness without reading a wall clock:

- ``base_issued_at`` — the cloud/wind source (design's base provider);
- ``secondary_issued_at`` — the seeing/transparency source.

Both are ``None`` when that source contributed nothing. Times are aware UTC.

Field conventions the core relies on:

- ``cloud_cover`` — percent, 0 (clear) .. 100 (overcast). The clarity curve that
  turns this into usable-sky weight is a scoring policy and lives in the core.
- ``wind_gust`` — the forecast gust in the same unit as ``PierConfig.max_gust``
  (km/h), compared directly against that limit.
- ``seeing`` and ``transparency`` — normalized quality in ``[0, 1]`` where 1 is
  best. The provider layer maps each source's native scale onto this range so
  the core never learns a source or a resolution existed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class HourlyConditions:
    """Observing conditions for one clock-hour slot beginning at ``time``.

    ``time`` is the aware-UTC start of the hour (top of hour). Every measurement
    is optional: ``None`` means that field is unavailable for this hour, which is
    the per-field availability stamp the verdict degrades against.
    """

    time: datetime
    cloud_cover: float | None = None
    wind_gust: float | None = None
    seeing: float | None = None
    transparency: float | None = None


@dataclass(frozen=True)
class ConditionsSnapshot:
    """An immutable hourly conditions series with per-source issue times.

    ``hours`` is the forecast grid; the core intersects it with the pier's dark
    window, so a snapshot may span a wider horizon than the window without harm.
    Hours the grid does not reach simply have no slot and read as unavailable.
    """

    hours: tuple[HourlyConditions, ...] = ()
    base_issued_at: datetime | None = None
    secondary_issued_at: datetime | None = None
    # Built once for O(1) hour lookup; excluded from equality/repr so two
    # snapshots with the same hours compare equal.
    _by_time: dict[datetime, HourlyConditions] = field(
        default_factory=dict, compare=False, repr=False, init=False
    )

    def __post_init__(self) -> None:
        # ``self`` is frozen, so populate the lookup via object.__setattr__.
        object.__setattr__(self, "_by_time", {hour.time: hour for hour in self.hours})

    def at(self, time: datetime) -> HourlyConditions | None:
        """The hour slot beginning at ``time``, or ``None`` if the grid omits it."""
        return self._by_time.get(time)
