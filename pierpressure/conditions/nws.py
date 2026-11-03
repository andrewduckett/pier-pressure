"""The National Weather Service provider: total cloud, wind and weather (#155).

NWS publishes its raw gridpoint forecast as variable-length periods, each an ISO
8601 start and duration such as ``2026-11-03T18:00:00+00:00/PT3H``. This module
**holds each value across every clock hour its period covers, here in the
provider layer**, so the core only ever sees the hourly grid (design DD2).
Parsing is separated from fetching so it can be tested against a recorded
fixture with no network.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from pierpressure.core.conditions import Variable

from .provider import SourceForecast, SourceReading

PROPERTIES: Mapping[Variable, str] = {
    "cloud_cover": "skyCover",
    "wind_gust": "windGust",
    "wind_speed": "windSpeed",
    "wind_direction": "windDirection",
    "temperature": "temperature",
    "dew_point": "dewpoint",
    "humidity": "relativeHumidity",
    "precipitation_probability": "probabilityOfPrecipitation",
}
"""The gridpoint property behind each variable NWS declares."""

UNITS: Mapping[Variable, str] = {
    "cloud_cover": "wmoUnit:percent",
    "wind_gust": "wmoUnit:km_h-1",
    "wind_speed": "wmoUnit:km_h-1",
    "wind_direction": "wmoUnit:degree_(angle)",
    "temperature": "wmoUnit:degC",
    "dew_point": "wmoUnit:degC",
    "humidity": "wmoUnit:percent",
    "precipitation_probability": "wmoUnit:percent",
}
"""The one unit code each variable is carried in. Any other code leaves the
variable absent rather than converted (design DD4)."""

# The same reach as 7Timer!, so listing NWS never lengthens the timeline (D2).
_HORIZON = timedelta(hours=72)

# NWS emits durations in days, hours and minutes only, so this is all the
# ISO 8601 a period needs. The standard library has no duration parser.
_DURATION = re.compile(r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?)?")


def _period(valid_time: str) -> tuple[datetime, timedelta]:
    """Split an NWS ``validTime`` into its start and its duration."""
    start, duration = valid_time.split("/")
    match = _DURATION.fullmatch(duration)
    if match is None:
        raise ValueError(f"unexpected NWS duration {duration!r}")
    parts = {name: int(value or 0) for name, value in match.groupdict().items()}
    return datetime.fromisoformat(start).astimezone(UTC), timedelta(**parts)


def _hours(start: datetime, duration: timedelta) -> list[datetime]:
    """Every top-of-hour the period from ``start`` for ``duration`` covers."""
    hour = start.replace(minute=0, second=0, microsecond=0)
    if hour < start:
        hour += timedelta(hours=1)
    end = start + duration
    covered = []
    while hour < end:
        covered.append(hour)
        hour += timedelta(hours=1)
    return covered


def parse_nws(payload: dict[str, Any]) -> SourceForecast:
    """Map an NWS raw gridpoint payload to an hourly :class:`SourceForecast`.

    Only hours within 72 hours of the earliest period start, across every
    variable, are kept. Each hour is checked, so a period that straddles the
    horizon is cut at it.
    """
    properties = payload.get("properties") or {}
    periods = [
        (variable, *_period(entry["validTime"]), entry.get("value"))
        for variable, name in PROPERTIES.items()
        if (column := properties.get(name) or {}).get("uom") == UNITS[variable]
        for entry in column.get("values") or []
    ]
    if not periods:
        return SourceForecast()
    horizon = min(start for _, start, _, _ in periods) + _HORIZON
    columns: dict[datetime, dict[Variable, float | None]] = defaultdict(dict)
    for variable, start, duration, value in periods:
        for hour in _hours(start, duration):
            if hour < horizon:
                columns[hour][variable] = None if value is None else float(value)
    return SourceForecast(
        readings={hour: SourceReading(**values) for hour, values in sorted(columns.items())}
    )
