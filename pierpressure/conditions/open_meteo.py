"""The Open-Meteo provider: hourly cloud, wind and weather (task 3.2).

Open-Meteo returns an hourly forecast; this maps its ``cloud_cover`` (percent),
its ``cloud_cover_low``/``cloud_cover_mid``/``cloud_cover_high`` layer split,
``wind_gusts_10m`` and ``wind_speed_10m`` (km/h, requested explicitly) and the
weather variables in Open-Meteo's default units onto the per-hour readings the
core consumes. Parsing is separated from fetching so it can be tested against a
recorded fixture with no network.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar

import httpx

from pierpressure.core.config import PierConfig
from pierpressure.core.providers import OPEN_METEO, ProviderSpec

from .provider import SourceForecast, SourceReading

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_SECONDS = 10.0


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_hour(value: str) -> datetime:
    """Parse an Open-Meteo ISO timestamp (no offset, UTC) to an aware top-of-hour."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(minute=0, second=0, microsecond=0)


def _as_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _float_at(values: list[Any], index: int) -> float | None:
    return _as_float(values[index]) if index < len(values) else None


def parse_open_meteo(payload: dict[str, Any], issued_at: datetime) -> SourceForecast:
    """Map an Open-Meteo forecast payload to a :class:`SourceForecast`.

    Missing or ``null`` values for an hour are left absent, so a gappy forecast is
    a partial (valid) result rather than an error. Every array is read
    index-guarded, so an absent, short or ``null`` array leaves only that field
    ``None`` while the others remain usable.
    """
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []

    def column(name: str) -> list[Any]:
        return hourly.get(name) or []

    clouds = column("cloud_cover")
    clouds_low = column("cloud_cover_low")
    clouds_mid = column("cloud_cover_mid")
    clouds_high = column("cloud_cover_high")
    gusts = column("wind_gusts_10m")
    temperatures = column("temperature_2m")
    dew_points = column("dew_point_2m")
    humidities = column("relative_humidity_2m")
    wind_speeds = column("wind_speed_10m")
    wind_directions = column("wind_direction_10m")
    precipitation = column("precipitation_probability")
    readings: dict[datetime, SourceReading] = {}
    for index, raw_time in enumerate(times):
        readings[_parse_hour(raw_time)] = SourceReading(
            cloud_cover=_float_at(clouds, index),
            wind_gust=_float_at(gusts, index),
            cloud_low=_float_at(clouds_low, index),
            cloud_mid=_float_at(clouds_mid, index),
            cloud_high=_float_at(clouds_high, index),
            temperature=_float_at(temperatures, index),
            dew_point=_float_at(dew_points, index),
            humidity=_float_at(humidities, index),
            wind_speed=_float_at(wind_speeds, index),
            wind_direction=_float_at(wind_directions, index),
            precipitation_probability=_float_at(precipitation, index),
        )
    return SourceForecast(issued_at=issued_at, readings=readings)


@dataclass
class OpenMeteoProvider:
    """Fetches hourly cloud, wind and weather from Open-Meteo."""

    spec: ClassVar[ProviderSpec] = OPEN_METEO

    client: httpx.Client | None = None
    now: Callable[[], datetime] = _utcnow

    def fetch(self, pier: PierConfig) -> SourceForecast:
        params: dict[str, str | float | int] = {
            "latitude": pier.latitude,
            "longitude": pier.longitude,
            "hourly": ",".join(
                (
                    "cloud_cover",
                    "cloud_cover_low",
                    "cloud_cover_mid",
                    "cloud_cover_high",
                    "wind_gusts_10m",
                    "temperature_2m",
                    "dew_point_2m",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "precipitation_probability",
                )
            ),
            "wind_speed_unit": "kmh",
            "timezone": "UTC",
            "forecast_days": 2,
        }
        client = self.client or httpx.Client(timeout=_TIMEOUT_SECONDS)
        try:
            response = client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            return parse_open_meteo(response.json(), issued_at=self.now())
        finally:
            if self.client is None:
                client.close()
