"""The MET Norway provider: layered cloud, wind and weather from Locationforecast (#220).

Each step of the ``complete`` forecast fills the hour at its time from its
instant values. Parsing is separated from fetching so it can be tested against
a recorded fixture with no network.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar

from pierpressure.core.conditions import Variable
from pierpressure.core.config import PierConfig
from pierpressure.core.providers import MET_NORWAY, ProviderSpec

from .provider import SourceForecast, SourceReading

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
"""The instant field behind each variable a step fills at its own time (D3)."""


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def parse_met_norway(payload: dict[str, Any]) -> SourceForecast:
    """Map a ``complete`` Locationforecast payload to an hourly :class:`SourceForecast`."""
    properties = payload.get("properties") or {}
    meta = properties.get("meta") or {}
    # The forecast's own update time, not the fetch time (D9).
    updated_at = meta.get("updated_at")
    readings: dict[datetime, SourceReading] = {}
    for step in properties.get("timeseries") or []:
        details = ((step.get("data") or {}).get("instant") or {}).get("details") or {}
        readings[_time(step["time"])] = SourceReading(
            **{
                variable: float(details[name])
                for variable, name in INSTANT.items()
                if details.get(name) is not None
            }
        )
    return SourceForecast(
        issued_at=_time(updated_at) if updated_at else None,
        readings=readings,
    )


@dataclass
class MetNorwayProvider:
    """Fetches MET Norway's complete Locationforecast for a pier."""

    spec: ClassVar[ProviderSpec] = MET_NORWAY

    def fetch(self, pier: PierConfig) -> SourceForecast:
        raise NotImplementedError
