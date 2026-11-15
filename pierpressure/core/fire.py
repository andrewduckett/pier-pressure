"""A fire detection: a satellite's report of an active fire (firms-nearby-fire DD1).

Like an observation, a fire detection is a measurement, not a forecast, so it
reaches ``produce_verdict`` as plain data beside the snapshot and never fills a
variable. Unlike an observation it reports the ground, not the sky, so it is a
value of its own. Which detections count is a pure function of the detections,
the pier and the evaluation instant.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .config import PierConfig

# Just over the 45 km CAMS grid, which can miss a fire this close (brainstorm D6).
RADIUS_KM = 50.0
MAX_AGE = timedelta(hours=24)
# VIIRS's low confidence detections are often sun glint or hot surfaces (D7).
COUNTED_CONFIDENCE = frozenset({"nominal", "high"})
# The mean Earth radius. A sphere is well within a 375 m VIIRS pixel at 50 km.
EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class FireDetection:
    """One detection: where, when the satellite passed (aware UTC), and its confidence.

    ``confidence`` is kept as FIRMS gives it: ``low``, ``nominal`` or ``high``.
    """

    latitude: float
    longitude: float
    detected_at: datetime
    confidence: str


def counted(
    fires: Iterable[FireDetection], pier: PierConfig, instant: datetime
) -> tuple[FireDetection, ...]:
    """The detections that count for the verdict at ``instant``, in the order received.

    One counts when its confidence is nominal or high, it is from no later than
    ``instant`` and at most :data:`MAX_AGE` before it, and it is at most
    :data:`RADIUS_KM` from the pier.
    """
    return tuple(
        fire
        for fire in fires
        if fire.confidence in COUNTED_CONFIDENCE
        and timedelta(0) <= instant - fire.detected_at <= MAX_AGE
        and distance_km(pier, fire) <= RADIUS_KM
    )


def distance_km(pier: PierConfig, fire: FireDetection) -> float:
    """The great-circle distance from the pier to ``fire``, by haversine."""
    lat1, lat2 = math.radians(pier.latitude), math.radians(fire.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(fire.longitude - pier.longitude)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))
