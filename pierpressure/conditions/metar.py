"""The latest METAR from the airport a pier names (metar-reason DD3).

A METAR is an observation, not a forecast: it never fills a variable, so this
module is not a provider and has no place in the provider order. It turns the
aviationweather.gov Data API's JSON into the core's
:class:`~pierpressure.core.observation.Observation`. Parsing is separated from
fetching so it can be tested against a recorded fixture with no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar

import httpx

from pierpressure.core.observation import CloudLayer, Observation
from pierpressure.health import NO_REPORT

from .nws import USER_AGENT

METAR_URL = "https://aviationweather.gov/api/data/metar"
_TIMEOUT_SECONDS = 10.0
# The same fixed User-Agent as NWS, so there is nothing to configure.
_HEADERS = {"User-Agent": USER_AGENT}

# Layer codes that say there is no cloud. A report can carry one as a layer
# with no base; naming it would read "CLR at an unknown height".
_NO_CLOUD = frozenset({"CLR", "SKC", "NCD", "NSC"})


class NoReport(Exception):
    """The response held no report for the station.

    An unknown station answers 204 with an empty body, not an error status.
    """

    description: ClassVar[str] = NO_REPORT


def parse_metar(payload: list[dict[str, Any]], station: str) -> Observation:
    """The observation in ``payload`` for ``station``.

    The time is the report's ``obsTime``, when the station measured. The layers
    keep the order reported, and a layer with no base keeps it unknown.
    """
    for report in payload:
        if report.get("icaoId") == station:
            return Observation(
                station=station,
                observed_at=datetime.fromtimestamp(report["obsTime"], UTC),
                cover=report["cover"],
                clouds=tuple(
                    CloudLayer(cover=layer["cover"], base_ft=layer.get("base"))
                    for layer in report.get("clouds") or []
                    if layer["cover"] not in _NO_CLOUD
                ),
            )
    raise NoReport(station)


@dataclass
class MetarFetcher:
    """Fetches one station's latest METAR from the aviationweather.gov Data API."""

    client: httpx.Client | None = None

    def fetch(self, station: str) -> Observation:
        client = self.client or httpx.Client(timeout=_TIMEOUT_SECONDS)
        try:
            response = client.get(
                METAR_URL, params={"ids": station, "format": "json"}, headers=_HEADERS
            )
            response.raise_for_status()
            if response.status_code == httpx.codes.NO_CONTENT or not response.content:
                raise NoReport(station)
            return parse_metar(response.json(), station)
        finally:
            if self.client is None:
                client.close()
