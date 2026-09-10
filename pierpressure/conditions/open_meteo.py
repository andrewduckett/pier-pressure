"""The base conditions source: Open-Meteo hourly cloud cover and wind gust (task 3.2).

Open-Meteo returns an hourly forecast; this maps its ``cloud_cover`` (percent) and
``wind_gusts_10m`` (km/h, requested explicitly) onto the per-hour readings the
core consumes. Parsing is separated from fetching so it can be tested against a
recorded fixture with no network.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from pierpressure.core.config import PierConfig

from .provider import SourceForecast, SourceReading, _utcnow

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_SECONDS = 10.0


def _parse_hour(value: str) -> datetime:
    """Parse an Open-Meteo ISO timestamp (no offset, UTC) to an aware top-of-hour."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(minute=0, second=0, microsecond=0)


def _as_float(value: Any) -> float | None:
    return None if value is None else float(value)


def parse_open_meteo(payload: dict[str, Any], issued_at: datetime) -> SourceForecast:
    """Map an Open-Meteo forecast payload to a :class:`SourceForecast`.

    Missing or ``null`` cloud/gust values for an hour are left absent, so a gappy
    forecast is a partial (valid) result rather than an error.
    """
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    clouds = hourly.get("cloud_cover") or []
    gusts = hourly.get("wind_gusts_10m") or []
    readings: dict[datetime, SourceReading] = {}
    for index, raw_time in enumerate(times):
        cloud = _as_float(clouds[index]) if index < len(clouds) else None
        gust = _as_float(gusts[index]) if index < len(gusts) else None
        readings[_parse_hour(raw_time)] = SourceReading(cloud_cover=cloud, wind_gust=gust)
    return SourceForecast(issued_at=issued_at, readings=readings)


@dataclass
class OpenMeteoProvider:
    """Fetches hourly cloud and wind gust from Open-Meteo."""

    client: httpx.Client | None = None
    now: Callable[[], datetime] = _utcnow

    def fetch(self, pier: PierConfig) -> SourceForecast:
        params: dict[str, str | float | int] = {
            "latitude": pier.latitude,
            "longitude": pier.longitude,
            "hourly": "cloud_cover,wind_gusts_10m",
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
