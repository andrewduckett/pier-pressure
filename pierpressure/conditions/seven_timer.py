"""The secondary conditions source: 7Timer! seeing and transparency (task 3.3).

7Timer!'s astro product reports on a 3-hourly cadence, coarser than the hourly
grid the core consumes. This module maps its integer seeing and transparency
indices (1 best .. 8 worst) onto a normalized ``[0, 1]`` quality and **resamples
the 3-hourly series onto the hourly grid here, in the provider layer**, so the
core never learns a coarser resolution existed. The resample holds each 3-hour
value across its three hours (design's simpler hold, not interpolation).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from pierpressure.core.config import PierConfig

from .provider import SourceForecast, SourceReading

SEVEN_TIMER_URL = "https://www.7timer.info/bin/api.pl"
_TIMEOUT_SECONDS = 10.0
# 7Timer! astro reports every three hours; each entry is held across its block.
_BLOCK_HOURS = 3
# Best and worst index of the 1..8 seeing/transparency scales.
_BEST_INDEX = 1
_WORST_INDEX = 8


def _quality_from_index(value: Any) -> float | None:
    """Map a 1 (best) .. 8 (worst) index to a ``[0, 1]`` quality, or ``None``.

    Anything outside the documented 1..8 range (including 7Timer!'s missing
    markers) is treated as absent rather than guessed.
    """
    if not isinstance(value, int) or not (_BEST_INDEX <= value <= _WORST_INDEX):
        return None
    return (_WORST_INDEX - value) / (_WORST_INDEX - _BEST_INDEX)


def _parse_init(init: str) -> datetime:
    """Parse a 7Timer! ``init`` stamp (``YYYYMMDDHH``, UTC) to an aware datetime."""
    return datetime.strptime(init, "%Y%m%d%H").replace(tzinfo=UTC)


def parse_seven_timer(payload: dict[str, Any]) -> SourceForecast:
    """Map a 7Timer! astro payload to an hourly :class:`SourceForecast`.

    Each 3-hourly entry is expanded (held) to its three hourly slots, so the
    result is on the same hourly grid as the base source before it reaches the
    core.
    """
    init = payload.get("init")
    if not isinstance(init, str):
        return SourceForecast()
    issued_at = _parse_init(init)

    readings: dict[datetime, SourceReading] = {}
    for entry in payload.get("dataseries") or []:
        timepoint = entry.get("timepoint")
        if not isinstance(timepoint, int):
            continue
        seeing = _quality_from_index(entry.get("seeing"))
        transparency = _quality_from_index(entry.get("transparency"))
        block_start = issued_at + timedelta(hours=timepoint)
        for offset in range(_BLOCK_HOURS):
            hour = (block_start + timedelta(hours=offset)).replace(
                minute=0, second=0, microsecond=0
            )
            readings[hour] = SourceReading(seeing=seeing, transparency=transparency)
    return SourceForecast(issued_at=issued_at, readings=readings)


@dataclass
class SevenTimerProvider:
    """Fetches 3-hourly seeing and transparency from 7Timer! and resamples hourly."""

    client: httpx.Client | None = None

    def fetch(self, pier: PierConfig) -> SourceForecast:
        params: dict[str, str | float] = {
            "lon": pier.longitude,
            "lat": pier.latitude,
            "product": "astro",
            "output": "json",
            "unit": "metric",
        }
        client = self.client or httpx.Client(timeout=_TIMEOUT_SECONDS)
        try:
            response = client.get(SEVEN_TIMER_URL, params=params)
            response.raise_for_status()
            return parse_seven_timer(response.json())
        finally:
            if self.client is None:
                client.close()
