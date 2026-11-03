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
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

import httpx

from pierpressure import __version__
from pierpressure.core.conditions import Variable
from pierpressure.core.config import PierConfig
from pierpressure.core.providers import NWS, ProviderSpec

from .provider import SourceForecast, SourceReading

NWS_URL = "https://api.weather.gov"
_TIMEOUT_SECONDS = 10.0
# NWS refuses requests without a User-Agent. A fixed one, with no email, so
# there is nothing to configure (D6).
USER_AGENT = f"PierPressure/{__version__} (https://github.com/andrewduckett/pier-pressure)"
_HEADERS = {"User-Agent": USER_AGENT}

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
    # The forecast office's last edit, not the fetch time (D8).
    update_time = properties.get("updateTime")
    issued_at = datetime.fromisoformat(update_time).astimezone(UTC) if update_time else None
    periods = [
        (variable, *_period(entry["validTime"]), entry.get("value"))
        for variable, name in PROPERTIES.items()
        if (column := properties.get(name) or {}).get("uom") == UNITS[variable]
        for entry in column.get("values") or []
    ]
    if not periods:
        return SourceForecast(issued_at=issued_at)
    horizon = min(start for _, start, _, _ in periods) + _HORIZON
    columns: dict[datetime, dict[Variable, float | None]] = defaultdict(dict)
    for variable, start, duration, value in periods:
        for hour in _hours(start, duration):
            if hour < horizon:
                columns[hour][variable] = None if value is None else float(value)
    return SourceForecast(
        issued_at=issued_at,
        readings={hour: SourceReading(**values) for hour, values in sorted(columns.items())},
    )


@dataclass
class NwsProvider:
    """Fetches the NWS raw gridpoint forecast in two steps, and resamples hourly.

    The first fetch for a pier resolves its coordinates to a forecast office and
    grid cell, then fetches that cell's forecast. The cell is remembered for as
    long as this instance lives, so later fetches make only the second request
    (design DD3). A failed resolution leaves nothing remembered, and a gridpoint
    404 forgets the cell.
    """

    spec: ClassVar[ProviderSpec] = NWS

    client: httpx.Client | None = None
    _cells: dict[tuple[float, float], str] = field(default_factory=dict, init=False, repr=False)

    def fetch(self, pier: PierConfig) -> SourceForecast:
        client = self.client or httpx.Client(timeout=_TIMEOUT_SECONDS)
        try:
            response = client.get(self._gridpoint_url(client, pier), headers=_HEADERS)
            if response.status_code == httpx.codes.NOT_FOUND:
                # The cell may have moved; resolve the point again next time.
                del self._cells[(pier.latitude, pier.longitude)]
            response.raise_for_status()
            return parse_nws(response.json())
        finally:
            if self.client is None:
                client.close()

    def _gridpoint_url(self, client: httpx.Client, pier: PierConfig) -> str:
        coordinates = (pier.latitude, pier.longitude)
        if coordinates not in self._cells:
            # NWS redirects coordinates with more than four decimal places.
            response = client.get(
                f"{NWS_URL}/points/{pier.latitude},{pier.longitude}",
                headers=_HEADERS,
                follow_redirects=True,
            )
            response.raise_for_status()
            cell = response.json()["properties"]
            self._cells[coordinates] = (
                f"{NWS_URL}/gridpoints/{cell['gridId']}/{cell['gridX']},{cell['gridY']}"
            )
        return self._cells[coordinates]
