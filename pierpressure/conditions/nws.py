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
    """Map an NWS raw gridpoint payload to an hourly :class:`SourceForecast`."""
    properties = payload.get("properties") or {}
    columns: dict[datetime, dict[Variable, float | None]] = defaultdict(dict)
    for variable, name in PROPERTIES.items():
        for entry in (properties.get(name) or {}).get("values") or []:
            start, duration = _period(entry["validTime"])
            value = entry.get("value")
            for hour in _hours(start, duration):
                columns[hour][variable] = None if value is None else float(value)
    return SourceForecast(
        readings={hour: SourceReading(**values) for hour, values in sorted(columns.items())}
    )
