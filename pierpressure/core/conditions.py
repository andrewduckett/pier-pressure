"""The conditions input to the core: one series per variable (provider-order D1).

The provider layer (outside the core) builds this immutable value from external
forecasts; the core only reads it. Keeping the seam a *plain data value* is what
keeps ``produce_verdict`` a pure, deterministic function: a data value cannot
fetch anything, so no I/O can creep back across the boundary and the offline
guarantee stays a hard wall rather than "deterministic if mocked correctly".

Shape (ADR-0027): the snapshot maps each variable to a :class:`Series`, one
variable's hourly values from the one provider that filled it, stamped with that
provider's key and issue time. The core never learns which vendor a provider is,
or its scale or resolution.

Two levels of absence:

- **A variable has a series iff some provider returned it.** ``Conditions()`` is
  the empty value.
- **Each hour within a series is independently present-or-absent** — an hour is
  absent when its value is ``None`` or the hour is missing — so a partial series
  is an ordinary, valid value rather than an error.

Variable conventions the core relies on:

- ``cloud_cover`` — percent, 0 (clear) .. 100 (overcast). The clarity curve that
  turns this into usable-sky weight is a scoring policy and lives in the core.
- ``wind_gust`` — the forecast gust in the same unit as ``PierConfig.max_gust``
  (km/h), compared directly against that limit.
- ``seeing`` and ``transparency`` — normalized quality in ``[0, 1]`` where 1 is
  best. The provider layer maps each provider's native scale onto this range.
- The weather variables pass through to the timeline as reported (°C, %, km/h,
  degrees); no gate, score or confidence term reads them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

# The per-hour quantities the conditions carry, named by their timeline keys, in
# timeline order. Every iteration over variables walks this order, so the fill and
# the document never depend on dict or set order.
Variable = Literal[
    "cloud_cover",
    "cloud_low",
    "cloud_mid",
    "cloud_high",
    "wind_gust",
    "seeing",
    "transparency",
    "temperature",
    "dew_point",
    "humidity",
    "wind_speed",
    "wind_direction",
    "precipitation_probability",
]


@dataclass(frozen=True)
class Series:
    """One variable's hourly values from a single provider (provider-order D1).

    ``provider`` is the key of the provider that filled it, and ``issued_at`` the
    issue time that provider gave for its data on this fetch (aware UTC, ``None``
    when it gave none). ``values`` holds every hour the provider returned, keyed by
    aware-UTC top of hour, with ``None`` where that hour's value was blank. Hours
    the provider did not cover are absent; they are never filled from another
    provider.
    """

    provider: str
    issued_at: datetime | None
    values: Mapping[datetime, float | None]


@dataclass(frozen=True)
class Conditions:
    """The observing-conditions input to the core: one optional series per variable.

    A variable no provider returned has no series. ``Conditions()`` is the empty
    value, the astronomy-only input the service's fallback supplies. The core reads
    through :meth:`value_at` and :meth:`issued_at`, which answer ``None`` for an
    absent series, so missing data degrades the verdict rather than raising.
    """

    series: Mapping[Variable, Series] = field(default_factory=dict)

    def value_at(self, variable: Variable, time: datetime) -> float | None:
        """The variable's value for the hour beginning at ``time``, or ``None``."""
        series = self.series.get(variable)
        return series.values.get(time) if series is not None else None

    def issued_at(self, variable: Variable) -> datetime | None:
        """The issue time of the variable's series, or ``None`` without one."""
        series = self.series.get(variable)
        return series.issued_at if series is not None else None

    def hours(self) -> tuple[datetime, ...]:
        """Every hour any series covers, sorted ascending, each once."""
        return tuple(sorted({time for series in self.series.values() for time in series.values}))
