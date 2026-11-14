"""The latest METAR from the airport a pier names (metar-reason DD3).

A METAR is an observation, not a forecast: it never fills a variable, so this
module is not a provider and has no place in the provider order. It turns the
aviationweather.gov Data API's JSON into the core's
:class:`~pierpressure.core.observation.Observation`. Parsing is separated from
fetching so it can be tested against a recorded fixture with no network.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pierpressure.core.observation import CloudLayer, Observation

# Layer codes that say there is no cloud. A report can carry one as a layer
# with no base; naming it would read "CLR at an unknown height".
_NO_CLOUD = frozenset({"CLR", "SKC", "NCD", "NSC"})


class NoReport(Exception):
    """The response held no report for the station."""


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
