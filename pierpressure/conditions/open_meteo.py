"""The Open-Meteo provider: hourly cloud, wind and weather (task 3.2).

Open-Meteo returns an hourly forecast; this maps its ``cloud_cover`` (percent),
its ``cloud_cover_low``/``cloud_cover_mid``/``cloud_cover_high`` layer split,
``wind_gusts_10m`` and ``wind_speed_10m`` (km/h, requested explicitly) and the
weather variables in Open-Meteo's default units onto the per-hour readings the
core consumes. Parsing is separated from fetching so it can be tested against a
recorded fixture with no network.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from pierpressure.core.conditions import Variable
from pierpressure.core.config import PierConfig
from pierpressure.core.providers import OPEN_METEO, ProviderSpec

from .provider import SourceForecast, SourceReading

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_SECONDS = 10.0


COLUMNS: Mapping[Variable, str] = {
    "cloud_cover": "cloud_cover",
    "cloud_low": "cloud_cover_low",
    "cloud_mid": "cloud_cover_mid",
    "cloud_high": "cloud_cover_high",
    "wind_gust": "wind_gusts_10m",
    "temperature": "temperature_2m",
    "dew_point": "dew_point_2m",
    "humidity": "relative_humidity_2m",
    "wind_speed": "wind_speed_10m",
    "wind_direction": "wind_direction_10m",
    "precipitation_probability": "precipitation_probability",
    "aerosol_optical_depth": "aerosol_optical_depth",
    "pm2_5": "pm2_5",
}
"""The Open-Meteo hourly column behind each variable. The request and the parser
both read it, so there is one list of column names (design D3)."""


MODELS: Mapping[str, str] = {
    "open_meteo_hrrr": "ncep_hrrr_conus",
    "open_meteo_hrdps": "gem_hrdps_continental",
    "open_meteo_rdps": "gem_regional",
    "open_meteo_icon": "icon_seamless",
    "open_meteo_gfs": "gfs_global",
}
"""The Open-Meteo ``models=`` value behind each model provider's key. It is a
request detail, so it lives here rather than in the core spec (design D1)."""


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
    columns = {variable: hourly.get(name) or [] for variable, name in COLUMNS.items()}
    readings: dict[datetime, SourceReading] = {}
    for index, raw_time in enumerate(times):
        readings[_parse_hour(raw_time)] = SourceReading(
            **{variable: _float_at(values, index) for variable, values in columns.items()}
        )
    return SourceForecast(issued_at=issued_at, readings=readings)


@dataclass
class OpenMeteoProvider:
    """Fetches hourly cloud, wind and weather from Open-Meteo.

    With no ``model`` it asks for Open-Meteo's best match. With a model it asks
    for that model alone, so each model is its own provider (design D2).
    """

    spec: ProviderSpec = OPEN_METEO
    model: str | None = None
    client: httpx.Client | None = None
    now: Callable[[], datetime] = _utcnow

    def fetch(self, pier: PierConfig) -> SourceForecast:
        params: dict[str, str | float | int] = {
            "latitude": pier.latitude,
            "longitude": pier.longitude,
            "hourly": ",".join(COLUMNS[variable] for variable in self.spec.variables),
            "wind_speed_unit": "kmh",
            "timezone": "UTC",
            "forecast_days": 2,
        }
        if self.model is not None:
            params["models"] = self.model
        client = self.client or httpx.Client(timeout=_TIMEOUT_SECONDS)
        try:
            response = client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            return parse_open_meteo(response.json(), issued_at=self.now())
        finally:
            if self.client is None:
                client.close()
