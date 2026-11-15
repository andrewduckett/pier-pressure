"""firms-nearby-fire 1.2 and 2.1: which fire detections count, and the line they give."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from pierpressure.core.config import PierConfig
from pierpressure.core.fire import EARTH_RADIUS_KM, FireDetection, counted

PIER = PierConfig(id="quebec", latitude=46.8, longitude=-71.2, elevation_m=10.0)
INSTANT = datetime(2026, 11, 14, 3, 0, tzinfo=UTC)


def _place(distance_km: float, bearing_deg: float) -> tuple[float, float]:
    """The point ``distance_km`` from the pier along ``bearing_deg``, on the core's sphere."""
    lat1 = math.radians(PIER.latitude)
    lon1 = math.radians(PIER.longitude)
    theta = math.radians(bearing_deg)
    delta = distance_km / EARTH_RADIUS_KM
    lat2 = math.asin(
        math.sin(lat1) * math.cos(delta) + math.cos(lat1) * math.sin(delta) * math.cos(theta)
    )
    lon2 = lon1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(lat1),
        math.cos(delta) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


def _fire(
    distance_km: float,
    *,
    bearing_deg: float = 0.0,
    age: timedelta = timedelta(hours=3),
    confidence: str = "nominal",
) -> FireDetection:
    latitude, longitude = _place(distance_km, bearing_deg)
    return FireDetection(
        latitude=latitude,
        longitude=longitude,
        detected_at=INSTANT - age,
        confidence=confidence,
    )


# --------------------------------------------------------------------------- #
# 1.2: only a confident, recent detection within 50 km counts
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("confidence", ["nominal", "high"])
def test_counted_keeps_a_confident_recent_near_detection(confidence: str) -> None:
    fire = _fire(10.0, confidence=confidence)

    assert counted((fire,), PIER, INSTANT) == (fire,)


@pytest.mark.parametrize(
    "fire",
    [
        _fire(10.0, confidence="low"),
        _fire(10.0, confidence="high", age=timedelta(hours=25)),
        _fire(10.0, confidence="high", age=timedelta(minutes=-1)),
        _fire(51.0),
    ],
    ids=["low-confidence", "25-hours-old", "1-minute-ahead", "51-km-away"],
)
def test_counted_leaves_out_a_detection_that_fails_a_rule(fire: FireDetection) -> None:
    assert counted((fire,), PIER, INSTANT) == ()


def test_counted_keeps_a_detection_exactly_24_hours_old() -> None:
    fire = _fire(10.0, age=timedelta(hours=24))

    assert counted((fire,), PIER, INSTANT) == (fire,)


def test_counted_keeps_a_detection_at_the_instant() -> None:
    fire = _fire(10.0, age=timedelta(0))

    assert counted((fire,), PIER, INSTANT) == (fire,)


def test_counted_keeps_a_detection_just_inside_50_km() -> None:
    fire = _fire(49.9, bearing_deg=135.0)

    assert counted((fire,), PIER, INSTANT) == (fire,)


def test_counted_keeps_the_order_received() -> None:
    near, far, low = _fire(30.0), _fire(5.0), _fire(1.0, confidence="low")

    assert counted((near, low, far), PIER, INSTANT) == (near, far)
