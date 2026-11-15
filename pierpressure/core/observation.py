"""An observation: what one station measured at one moment (metar-reason DD1).

Unlike a series, an observation is not a forecast. It covers no hours, comes
from no provider in the provider order and never fills a variable, so it reaches
``produce_verdict`` as its own plain value beside the snapshot rather than inside
:class:`~pierpressure.core.conditions.Conditions`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .model import iso_z

# The oldest observation the verdict quotes (metar-reason D7). Airports report
# hourly, so this allows one missed report before the line drops.
MAX_AGE = timedelta(minutes=90)

# How the reason line words each cover code (metar-reason DD4). Any other code,
# such as ``VV``, is given as reported.
COVER_WORDS: dict[str, str] = {
    "FEW": "few cloud",
    "SCT": "scattered cloud",
    "BKN": "broken cloud",
    "OVC": "overcast cloud",
    "OVX": "an obscured sky",
}

# The height a report with no layers vouches for. An automated station sees no
# higher than 12,000 ft; CAVOK promises only 5,000 ft (metar-reason D10).
CLEAR_BELOW_FT = 12000
CAVOK_CLEAR_BELOW_FT = 5000

# The least cover each code proves, in points: the okta lower bound rounded down,
# so the observed cloud never claims more than the report does (metar-confidence
# D5). An obscured sky starts at the surface, so it counts whatever its base.
_COVER_POINTS: dict[str, int] = {"FEW": 12, "SCT": 37, "BKN": 62, "OVC": 100}
_OBSCURED = frozenset({"OVX", "VV"})


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


def observed_cloud(observation: Observation) -> int:
    """The most cloud ``observation``'s layers prove up to :data:`CLEAR_BELOW_FT`, in points."""
    points = [0]
    for layer in observation.clouds:
        if layer.cover in _OBSCURED:
            points.append(100)
        elif layer.base_ft is not None and layer.base_ft <= CLEAR_BELOW_FT:
            points.append(_COVER_POINTS.get(layer.cover, 0))
    return max(points)


def observation_reason(observation: Observation) -> str:
    """The reason line that quotes ``observation``, its layers in the order reported."""
    if observation.clouds:
        sky = _join([_layer(layer) for layer in observation.clouds])
    else:
        below = CAVOK_CLEAR_BELOW_FT if observation.cover == "CAVOK" else CLEAR_BELOW_FT
        sky = f"no cloud below {below:,} ft"
    return f"At {iso_z(observation.observed_at)}, {observation.station} reported {sky}."


def _layer(layer: CloudLayer) -> str:
    cover = COVER_WORDS.get(layer.cover, layer.cover)
    if layer.base_ft is None:
        return f"{cover} at an unknown height"
    return f"{cover} at {layer.base_ft:,} ft"


def _join(parts: list[str]) -> str:
    if len(parts) == 1:
        return parts[0]
    return f"{', '.join(parts[:-1])} and {parts[-1]}"
