"""The MET Norway provider: layered cloud, wind and weather from Locationforecast (#220).

Each step of the ``complete`` forecast fills the hour at its time from its
instant values. Rain chance is the exception: a step's chance is for the hour
that starts there, so it is held on the next hour, as NWS's is (D8). Parsing is
separated from fetching so it can be tested against a recorded fixture with no
network.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any, ClassVar

import httpx

from pierpressure.core.conditions import Variable
from pierpressure.core.config import PierConfig
from pierpressure.core.providers import MET_NORWAY, ProviderSpec

from .nws import USER_AGENT
from .provider import SourceForecast, SourceReading

logger = logging.getLogger(__name__)

MET_NORWAY_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
_TIMEOUT_SECONDS = 10.0
# The terms ask for a User-Agent naming the client and a way to reach its
# owner; the repository URL is that way (D11).
_HEADERS = {"User-Agent": USER_AGENT}

INSTANT: Mapping[Variable, str] = {
    "cloud_cover": "cloud_area_fraction",
    "cloud_low": "cloud_area_fraction_low",
    "cloud_mid": "cloud_area_fraction_medium",
    "cloud_high": "cloud_area_fraction_high",
    "wind_gust": "wind_speed_of_gust",
    "wind_speed": "wind_speed",
    "wind_direction": "wind_from_direction",
    "temperature": "air_temperature",
    "dew_point": "dew_point_temperature",
    "humidity": "relative_humidity",
}
"""The instant field behind each variable a step fills at its own time (D3). The
rain chance comes from the step's ``next_1_hours`` instead."""

UNITS: Mapping[str, str] = {
    "cloud_area_fraction": "%",
    "cloud_area_fraction_low": "%",
    "cloud_area_fraction_medium": "%",
    "cloud_area_fraction_high": "%",
    "wind_speed_of_gust": "m/s",
    "wind_speed": "m/s",
    "wind_from_direction": "degrees",
    "air_temperature": "celsius",
    "dew_point_temperature": "celsius",
    "relative_humidity": "%",
    "probability_of_precipitation": "%",
}
"""The one unit each field is read in, keyed as ``meta.units`` keys it. Any other
unit leaves the field's variable absent rather than converted (D5)."""

_RAIN_CHANCE = "probability_of_precipitation"

# MET Norway gives wind only in m/s; the snapshot carries km/h (D6).
_SCALE: Mapping[str, float] = {"wind_speed": 3.6, "wind_speed_of_gust": 3.6}

# The same reach as NWS and 7Timer!, so listing MET Norway never lengthens the
# timeline (D7).
_HORIZON = timedelta(hours=72)
_AN_HOUR = timedelta(hours=1)


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _hourly(timeseries: list[dict[str, Any]]) -> list[tuple[datetime, dict[str, Any]]]:
    """The leading run of steps an hour apart, within 72 hours of the first (D7).

    The forecast turns 6-hourly after two or three days, and the snapshot is
    hourly, so the first step that is not an hour on ends the run.
    """
    kept: list[tuple[datetime, dict[str, Any]]] = []
    for step in timeseries:
        time = _time(step["time"])
        if kept and (time - kept[-1][0] != _AN_HOUR or time >= kept[0][0] + _HORIZON):
            break
        kept.append((time, step))
    return kept


def parse_met_norway(payload: dict[str, Any]) -> SourceForecast:
    """Map a ``complete`` Locationforecast payload to an hourly :class:`SourceForecast`."""
    properties = payload.get("properties") or {}
    meta = properties.get("meta") or {}
    # The forecast's own update time, not the fetch time (D9).
    updated_at = meta.get("updated_at")
    units = meta.get("units") or {}
    instant = {
        variable: name for variable, name in INSTANT.items() if units.get(name) == UNITS[name]
    }
    rain_chance = units.get(_RAIN_CHANCE) == UNITS[_RAIN_CHANCE]
    steps = _hourly(properties.get("timeseries") or [])
    columns: dict[datetime, dict[Variable, float]] = {}
    for time, step in steps:
        details = ((step.get("data") or {}).get("instant") or {}).get("details") or {}
        columns[time] = {
            variable: float(details[name]) * _SCALE.get(name, 1.0)
            for variable, name in instant.items()
            if details.get(name) is not None
        }
    for time, step in steps:
        next_hour = ((step.get("data") or {}).get("next_1_hours") or {}).get("details") or {}
        # The chance for the hour from this step belongs to the hour that ends
        # an hour later, and never adds an hour the steps do not have (D8).
        if rain_chance and next_hour.get(_RAIN_CHANCE) is not None and time + _AN_HOUR in columns:
            columns[time + _AN_HOUR]["precipitation_probability"] = float(next_hour[_RAIN_CHANCE])
    return SourceForecast(
        issued_at=_time(updated_at) if updated_at else None,
        readings={time: SourceReading(**values) for time, values in columns.items()},
    )


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _expires(response: httpx.Response) -> datetime | None:
    """The response's ``Expires`` time, or ``None`` when it is missing or unreadable."""
    try:
        return parsedate_to_datetime(response.headers["Expires"]).astimezone(UTC)
    except KeyError, TypeError, ValueError:
        return None


@dataclass(frozen=True)
class _Remembered:
    """The last good forecast for one pair of coordinates, and when it goes stale."""

    forecast: SourceForecast
    expires: datetime | None
    last_modified: str | None


@dataclass
class MetNorwayProvider:
    """Fetches MET Norway's complete Locationforecast for a pier.

    The terms forbid asking again before a response's ``Expires`` time, so the
    last good forecast is remembered per rounded coordinates for as long as
    this instance lives (D12). Until it expires a fetch returns it with no
    request; after that the request asks with ``If-Modified-Since``, and a 304
    returns it again. Any failed request forgets it. ``now`` is the clock the
    expiry is read against; tests pass a fixed one.
    """

    spec: ClassVar[ProviderSpec] = MET_NORWAY

    client: httpx.Client | None = None
    now: Callable[[], datetime] = _utcnow
    _remembered: dict[tuple[float, float], _Remembered] = field(
        default_factory=dict, init=False, repr=False
    )

    def fetch(self, pier: PierConfig) -> SourceForecast:
        # MET Norway answers 403 for coordinates with more than four decimal
        # places (D10).
        coordinates = (round(pier.latitude, 4), round(pier.longitude, 4))
        remembered = self._remembered.get(coordinates)
        if (
            remembered is not None
            and remembered.expires is not None
            and self.now() < remembered.expires
        ):
            return remembered.forecast
        headers = dict(_HEADERS)
        if remembered is not None and remembered.last_modified is not None:
            headers["If-Modified-Since"] = remembered.last_modified
        client = self.client or httpx.Client(timeout=_TIMEOUT_SECONDS)
        try:
            lat, lon = coordinates
            response = client.get(MET_NORWAY_URL, params={"lat": lat, "lon": lon}, headers=headers)
            if remembered is not None and response.status_code == httpx.codes.NOT_MODIFIED:
                remembered = replace(remembered, expires=_expires(response))
            else:
                response.raise_for_status()
                if response.status_code == httpx.codes.NON_AUTHORITATIVE_INFORMATION:
                    logger.warning("MET Norway says this Locationforecast version is deprecated")
                remembered = _Remembered(
                    forecast=parse_met_norway(response.json()),
                    expires=_expires(response),
                    last_modified=response.headers.get("Last-Modified"),
                )
        except Exception:
            self._remembered.pop(coordinates, None)
            raise
        finally:
            if self.client is None:
                client.close()
        self._remembered[coordinates] = remembered
        return remembered.forecast
