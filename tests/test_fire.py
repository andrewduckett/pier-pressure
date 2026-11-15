"""firms-nearby-fire 1.2 and 2.1: which fire detections count, and the line they give."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from pierpressure.core.config import PierConfig
from pierpressure.core.fire import (
    EARTH_RADIUS_KM,
    FireDetection,
    compass_point,
    counted,
    fire_reason,
    whole_km,
)

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


# --------------------------------------------------------------------------- #
# 2.1: the line names the nearest counted detection and the count
# --------------------------------------------------------------------------- #


def _at(fire: FireDetection, when: str) -> FireDetection:
    return FireDetection(
        latitude=fire.latitude,
        longitude=fire.longitude,
        detected_at=datetime.fromisoformat(when),
        confidence=fire.confidence,
    )


def test_reason_words_one_detection() -> None:
    fire = _at(_fire(23.0, bearing_deg=315.0), "2026-11-13T07:35:00+00:00")

    assert fire_reason((fire,), PIER) == (
        "A satellite detected a fire 23 km NW of the pier at 2026-11-13T07:35:00Z"
        " (1 detection within 50 km)."
    )


def test_reason_names_the_nearest_of_several_and_the_count() -> None:
    fires = (
        _at(_fire(30.0, bearing_deg=200.0), "2026-11-13T07:35:00+00:00"),
        _at(_fire(8.0, bearing_deg=90.0), "2026-11-13T05:54:00+00:00"),
        _at(_fire(40.0, bearing_deg=10.0), "2026-11-13T08:00:00+00:00"),
        _at(_fire(12.0, bearing_deg=270.0), "2026-11-13T09:00:00+00:00"),
    )

    assert fire_reason(fires, PIER) == (
        "A satellite detected a fire 8 km E of the pier at 2026-11-13T05:54:00Z"
        " (4 detections within 50 km)."
    )


def test_reason_says_1_km_for_a_fire_close_to_the_pier() -> None:
    fire = _fire(0.3, bearing_deg=180.0)

    assert "1 km S of the pier" in fire_reason((fire,), PIER)


def test_reason_names_the_latest_of_equally_near_detections() -> None:
    fires = (
        _at(_fire(12.1, bearing_deg=45.0), "2026-11-13T05:54:00+00:00"),
        _at(_fire(12.4, bearing_deg=225.0), "2026-11-13T07:35:00+00:00"),
    )

    assert "12 km SW of the pier at 2026-11-13T07:35:00Z" in fire_reason(fires, PIER)


def test_reason_names_the_first_received_of_equally_near_and_equally_late() -> None:
    fires = (
        _at(_fire(12.1, bearing_deg=45.0), "2026-11-13T07:35:00+00:00"),
        _at(_fire(12.4, bearing_deg=225.0), "2026-11-13T07:35:00+00:00"),
    )

    assert "12 km NE of the pier" in fire_reason(fires, PIER)


@pytest.mark.parametrize(
    ("distance", "expected"),
    [(0.0, 1), (0.3, 1), (1.49, 1), (2.5, 3), (12.5, 13), (49.6, 50)],
)
def test_whole_km_rounds_half_up_and_is_at_least_1(distance: float, expected: int) -> None:
    assert whole_km(distance) == expected


@pytest.mark.parametrize(
    ("bearing", "expected"),
    [
        (0.0, "N"),
        (22.4, "N"),
        (22.5, "NE"),
        (67.5, "E"),
        (157.5, "S"),
        (247.5, "W"),
        (315.0, "NW"),
        (337.5, "N"),
        (359.9, "N"),
    ],
)
def test_compass_point_sends_a_boundary_clockwise(bearing: float, expected: str) -> None:
    assert compass_point(bearing) == expected
