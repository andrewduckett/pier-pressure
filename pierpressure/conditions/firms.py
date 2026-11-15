"""Fire detections near a pier from NASA FIRMS (firms-nearby-fire DD3).

A fire detection is a measurement of the ground, not a forecast: it never fills
a variable, so this module is not a provider and has no place in the provider
order. It turns the FIRMS area API's CSV into the core's
:class:`~pierpressure.core.fire.FireDetection`. Parsing is separated from
fetching so it can be tested against a recorded fixture with no network.
"""

from __future__ import annotations

import csv
import io
import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar

import httpx
from pydantic import SecretStr

from pierpressure.core.config import PierConfig
from pierpressure.core.fire import FireDetection
from pierpressure.health import UNEXPECTED_RESPONSE, ProviderInfo

from .nws import USER_AGENT

FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
# NOAA-20's VIIRS near real time, the source of the recorded fixture (DD8).
_SOURCE = "VIIRS_NOAA20_NRT"
# Today and yesterday in UTC, so the 24 hours before any instant are covered;
# the core cuts the window (brainstorm D5).
_DAY_RANGE = 2
# Half the box's height, in degrees of latitude: about 55.6 km, just over 50 km.
_HALF_SPAN_DEG = 0.5
_TIMEOUT_SECONDS = 10.0
# The same fixed User-Agent as NWS, so there is nothing to configure.
_HEADERS = {"User-Agent": USER_AGENT}

# Who reports FIRMS health. It is not a ProviderSpec and not in the catalog, so
# ``firms`` in the provider order stays an unknown key. It fills no variable.
FIRMS = ProviderInfo(key="firms", name="FIRMS", variables=())

_NEEDED = ("latitude", "longitude", "acq_date", "acq_time", "confidence")


def firms_box(latitude: float, longitude: float) -> str:
    """The FIRMS box ``west,south,east,north`` that holds every point within 50 km.

    Bounds are clamped to the globe, so a box near the antimeridian stops at it.
    Within 0.5° of a pole the box spans every longitude.
    """
    south = max(-90.0, latitude - _HALF_SPAN_DEG)
    north = min(90.0, latitude + _HALF_SPAN_DEG)
    if 90.0 - abs(latitude) <= _HALF_SPAN_DEG:
        west, east = -180.0, 180.0
    else:
        half_width = _HALF_SPAN_DEG / math.cos(math.radians(latitude))
        west = max(-180.0, longitude - half_width)
        east = min(180.0, longitude + half_width)
    return ",".join(f"{bound:.4f}" for bound in (west, south, east, north))


@dataclass
class FirmsFetcher:
    """Fetches a pier's fire detections from the FIRMS area API.

    FIRMS takes the key only in the URL path, so the request URL is a secret too:
    an error that quotes it must never reach a log or health as it is (DD4, DD5).
    """

    map_key: SecretStr
    client: httpx.Client | None = None

    def fetch(self, pier: PierConfig) -> tuple[FireDetection, ...]:
        box = firms_box(pier.latitude, pier.longitude)
        url = f"{FIRMS_AREA_URL}/{self.map_key.get_secret_value()}/{_SOURCE}/{box}/{_DAY_RANGE}"
        client = self.client or httpx.Client(timeout=_TIMEOUT_SECONDS)
        try:
            response = client.get(url, headers=_HEADERS)
            response.raise_for_status()
            return parse_firms(response.text)
        finally:
            if self.client is None:
                client.close()


class UnexpectedResponse(Exception):
    """The body has no CSV header with the columns a detection needs.

    FIRMS answers some errors as plain text, sometimes with a success status.
    """

    description: ClassVar[str] = UNEXPECTED_RESPONSE


def parse_firms(text: str) -> tuple[FireDetection, ...]:
    """The fire detections in a FIRMS CSV body, in the order given.

    Columns are found by name, so an extra column or a new order changes
    nothing. A row that cannot be read is left out, and the rest kept.
    """
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or not set(_NEEDED) <= set(reader.fieldnames):
        raise UnexpectedResponse
    return tuple(_readable(reader))


def _readable(rows: Iterable[dict[str, str | None]]) -> Iterable[FireDetection]:
    for row in rows:
        try:
            yield _detection(row)
        except ValueError:
            continue


def _detection(row: dict[str, str | None]) -> FireDetection:
    """One row as a detection; ``acq_time`` is the pass's UTC hours and minutes, ``HHMM``."""
    time = _cell(row, "acq_time")
    if len(time) != 4:
        raise ValueError("acq_time is not HHMM")
    detected_at = datetime.strptime(f"{_cell(row, 'acq_date')} {time}", "%Y-%m-%d %H%M")
    return FireDetection(
        latitude=float(_cell(row, "latitude")),
        longitude=float(_cell(row, "longitude")),
        detected_at=detected_at.replace(tzinfo=UTC),
        confidence=_cell(row, "confidence"),
    )


def _cell(row: dict[str, str | None], column: str) -> str:
    """The row's text in ``column``; a short row leaves it ``None``."""
    value = row.get(column)
    if not value:
        raise ValueError(f"{column} is empty")
    return value
