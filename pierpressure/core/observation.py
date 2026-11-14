"""An observation: what one station measured at one moment (metar-reason DD1).

Unlike a series, an observation is not a forecast. It covers no hours, comes
from no provider in the provider order and never fills a variable, so it reaches
``produce_verdict`` as its own plain value beside the snapshot rather than inside
:class:`~pierpressure.core.conditions.Conditions`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

# The oldest observation the verdict quotes (metar-reason D7). Airports report
# hourly, so this allows one missed report before the line drops.
MAX_AGE = timedelta(minutes=90)


@dataclass(frozen=True)
class CloudLayer:
    """One reported cloud layer: its cover code and base in feet above ground.

    ``base_ft`` is ``None`` when the report gives no base.
    """

    cover: str
    base_ft: int | None


@dataclass(frozen=True)
class Observation:
    """A station's report: when it was measured, its overall cover and its layers.

    ``observed_at`` is aware UTC: when the station measured, not when the report
    was issued or fetched. ``clouds`` keeps the layers in the order reported.
    """

    station: str
    observed_at: datetime
    cover: str
    clouds: tuple[CloudLayer, ...]


def usable(observation: Observation, instant: datetime) -> bool:
    """Whether the verdict at ``instant`` may quote ``observation``.

    It must be measured no later than ``instant`` and at most :data:`MAX_AGE`
    before it.
    """
    age = instant - observation.observed_at
    return timedelta(0) <= age <= MAX_AGE
