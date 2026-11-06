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

Beside the filled series, ``alternates`` keeps the series of every later provider
that also returned the variable (cloud-agreement DD1). The core reads them only to
measure agreement; an alternate never fills an hour and never adds one.

Variable conventions the core relies on:

- ``cloud_cover`` — percent, 0 (clear) .. 100 (overcast). The clarity curve that
  turns this into usable-sky weight is a scoring policy and lives in the core.
- ``wind_gust`` — the forecast gust in the same unit as ``PierConfig.max_gust``
  (km/h), compared directly against that limit.
- ``seeing`` and ``transparency`` — normalized quality in ``[0, 1]`` where 1 is
  best. The provider layer maps each provider's native scale onto this range.
- The weather variables pass through to the timeline as reported (°C, %, km/h,
  degrees); no gate, score or confidence term reads them. Temperature and dew
  point feed only the dew reason line.
- ``aerosol_optical_depth`` (no unit), ``pm2_5`` (µg/m³) and
  ``column_water_vapour`` (kg/m²) are carried as reported. The timeline does not
  show them, and the verdict never reads them. The provider layer derives the
  computed source's transparency from aerosol and water vapour.
- The seeing column (:data:`SEEING_COLUMN`) is carried as reported: level
  temperatures in °C, geopotential heights in metres above sea level, the
  300 hPa wind in km/h and boundary-layer height in metres above ground. Like
  the air-quality variables, only the computed source reads it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

# The per-hour quantities the conditions carry. Every iteration over variables
# walks this order, so the fill and the document never depend on dict or set
# order. New variables append last so every earlier one keeps its fill place.
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
    "aerosol_optical_depth",
    "pm2_5",
    "column_water_vapour",
    "temperature_1000hpa",
    "geopotential_height_1000hpa",
    "temperature_975hpa",
    "geopotential_height_975hpa",
    "temperature_950hpa",
    "geopotential_height_950hpa",
    "temperature_925hpa",
    "geopotential_height_925hpa",
    "temperature_900hpa",
    "geopotential_height_900hpa",
    "temperature_850hpa",
    "geopotential_height_850hpa",
    "temperature_800hpa",
    "geopotential_height_800hpa",
    "temperature_700hpa",
    "geopotential_height_700hpa",
    "temperature_600hpa",
    "geopotential_height_600hpa",
    "temperature_500hpa",
    "geopotential_height_500hpa",
    "temperature_400hpa",
    "geopotential_height_400hpa",
    "temperature_300hpa",
    "geopotential_height_300hpa",
    "temperature_250hpa",
    "geopotential_height_250hpa",
    "temperature_200hpa",
    "geopotential_height_200hpa",
    "temperature_150hpa",
    "geopotential_height_150hpa",
    "temperature_100hpa",
    "geopotential_height_100hpa",
    "temperature_50hpa",
    "geopotential_height_50hpa",
    "wind_speed_300hpa",
    "boundary_layer_height",
]

# The pressure levels of the seeing column, in hPa, from the ground up.
SEEING_LEVELS: tuple[int, ...] = (
    1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50
)  # fmt: skip

# The variables computed seeing reads (computed-seeing DD1). They fill as one
# bundle, so the column always comes from one provider.
SEEING_COLUMN: tuple[Variable, ...] = (
    "temperature_1000hpa",
    "geopotential_height_1000hpa",
    "temperature_975hpa",
    "geopotential_height_975hpa",
    "temperature_950hpa",
    "geopotential_height_950hpa",
    "temperature_925hpa",
    "geopotential_height_925hpa",
    "temperature_900hpa",
    "geopotential_height_900hpa",
    "temperature_850hpa",
    "geopotential_height_850hpa",
    "temperature_800hpa",
    "geopotential_height_800hpa",
    "temperature_700hpa",
    "geopotential_height_700hpa",
    "temperature_600hpa",
    "geopotential_height_600hpa",
    "temperature_500hpa",
    "geopotential_height_500hpa",
    "temperature_400hpa",
    "geopotential_height_400hpa",
    "temperature_300hpa",
    "geopotential_height_300hpa",
    "temperature_250hpa",
    "geopotential_height_250hpa",
    "temperature_200hpa",
    "geopotential_height_200hpa",
    "temperature_150hpa",
    "geopotential_height_150hpa",
    "temperature_100hpa",
    "geopotential_height_100hpa",
    "temperature_50hpa",
    "geopotential_height_50hpa",
    "wind_speed_300hpa",
    "boundary_layer_height",
)

# The variables the timeline shows, named by their timeline keys, in timeline
# order. The timeline's keys and its hours both come from this, so a variable
# left out of it never reaches the document (air-quality-provider DD1).
TIMELINE_VARIABLES: tuple[Variable, ...] = (
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
)


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

    ``alternates`` holds, per variable, the series that lost the fill, in
    configured order. Only :meth:`readings_at` reads them.
    """

    series: Mapping[Variable, Series] = field(default_factory=dict)
    alternates: Mapping[Variable, tuple[Series, ...]] = field(default_factory=dict)

    def value_at(self, variable: Variable, time: datetime) -> float | None:
        """The variable's value for the hour beginning at ``time``, or ``None``."""
        series = self.series.get(variable)
        return series.values.get(time) if series is not None else None

    def issued_at(self, variable: Variable) -> datetime | None:
        """The issue time of the variable's series, or ``None`` without one."""
        series = self.series.get(variable)
        return series.issued_at if series is not None else None

    def readings_at(self, variable: Variable, time: datetime) -> tuple[tuple[str, float], ...]:
        """Each ``(provider, value)`` present for the hour, filled series first, then alternates."""
        filled = self.series.get(variable)
        every = ((filled,) if filled is not None else ()) + self.alternates.get(variable, ())
        return tuple(
            (series.provider, value)
            for series in every
            if (value := series.values.get(time)) is not None
        )

    def hours(self, variables: Iterable[Variable]) -> tuple[datetime, ...]:
        """Every hour the given variables' filled series cover, sorted ascending, each once.

        The variables are required so that no caller counts a variable's hours by
        forgetting to leave it out (air-quality-provider DD2).
        """
        filled = (self.series[variable] for variable in variables if variable in self.series)
        return tuple(sorted({time for series in filled for time in series.values}))
