"""The timeline sensors (spec ha-delivery, ADR-0025; timeline-sensors design).

Every timeline variable is a sensor on the pier's device, built by one code path
from a table: its state is the current hour's value, and its attributes carry the
variable's whole forecast so a chart card can draw it. Cloud cover is the first
row, and ``tests/test_cloud_cover.py`` covers it on its own.
"""

from __future__ import annotations

import json
import types
import typing
from typing import Annotated, get_args, get_origin, get_type_hints

import jsonschema
import pytest

from pierpressure.core.model import TimelineEntry
from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    PAYLOAD_OFFLINE,
    PAYLOAD_ONLINE,
    TIMELINE_SENSORS,
    TimelineSensor,
    availability_topic,
    build_cloud_cover_discovery,
    build_timeline_discovery,
    timeline_attributes_topic,
    timeline_state_topic,
)

BASE = "pierpressure"

NEW_KEYS = (
    "cloud_low",
    "cloud_mid",
    "cloud_high",
    "wind_gust",
    "seeing",
    "transparency",
    "sun_altitude",
    "moon_altitude",
)

NEW_SENSORS = TIMELINE_SENSORS[1:]
SENSORS_BY_KEY = {s.key: s for s in TIMELINE_SENSORS}


def _unwrap(hint: object) -> object:
    """``hint`` with any ``Annotated`` wrapper removed, inside a union too."""
    if get_origin(hint) is Annotated:
        return get_args(hint)[0]
    if isinstance(hint, types.UnionType) or get_origin(hint) is typing.Union:
        args = tuple(_unwrap(a) for a in get_args(hint))
        return typing.Union[args]  # noqa: UP007 - rebuilt from a runtime tuple
    return hint


# --------------------------------------------------------------------------- #
# The table
# --------------------------------------------------------------------------- #


def test_the_table_lists_cloud_cover_then_the_eight_new_keys() -> None:
    assert tuple(s.key for s in TIMELINE_SENSORS) == ("cloud_cover", *NEW_KEYS)


@pytest.mark.parametrize("sensor", TIMELINE_SENSORS, ids=lambda s: s.key)
def test_every_key_is_a_float_field_of_the_timeline_entry(sensor: TimelineSensor) -> None:
    hints = get_type_hints(TimelineEntry, include_extras=True)
    assert sensor.key in hints
    assert _unwrap(hints[sensor.key]) in (float, float | None)


@pytest.mark.parametrize("sensor", TIMELINE_SENSORS, ids=lambda s: s.key)
def test_every_name_slugs_to_its_key(sensor: TimelineSensor) -> None:
    assert sensor.name.lower().replace(" ", "_") == sensor.key


def test_names_units_and_icons_follow_the_design() -> None:
    assert [(s.key, s.name, s.unit, s.icon) for s in TIMELINE_SENSORS] == [
        ("cloud_cover", "Cloud cover", "%", "mdi:weather-cloudy"),
        ("cloud_low", "Cloud low", "%", "mdi:weather-cloudy"),
        ("cloud_mid", "Cloud mid", "%", "mdi:weather-cloudy"),
        ("cloud_high", "Cloud high", "%", "mdi:weather-cloudy"),
        ("wind_gust", "Wind gust", "km/h", "mdi:weather-windy"),
        ("seeing", "Seeing", None, "mdi:eye"),
        ("transparency", "Transparency", None, "mdi:telescope"),
        ("sun_altitude", "Sun altitude", "°", "mdi:weather-sunny"),
        ("moon_altitude", "Moon altitude", "°", "mdi:weather-night"),
    ]


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("key", NEW_KEYS)
def test_timeline_topics_derive_from_the_pier_id_and_key(key: str) -> None:
    assert timeline_state_topic(BASE, "backyard", key) == f"pierpressure/backyard/{key}/state"
    assert (
        timeline_attributes_topic(BASE, "backyard", key)
        == f"pierpressure/backyard/{key}/attributes"
    )


@pytest.mark.parametrize("sensor", NEW_SENSORS, ids=lambda s: s.key)
def test_a_timeline_discovery_is_a_sensor_on_the_pier_device(sensor: TimelineSensor) -> None:
    config = build_timeline_discovery("backyard", BASE, sensor)
    assert config["name"] == sensor.name
    assert config["has_entity_name"] is True
    assert config["unique_id"] == f"pierpressure_backyard_{sensor.key}"
    assert config["state_topic"] == timeline_state_topic(BASE, "backyard", sensor.key)
    assert config["json_attributes_topic"] == timeline_attributes_topic(
        BASE, "backyard", sensor.key
    )
    assert config.get("enabled_by_default", True) is True
    assert config["icon"] == sensor.icon
    assert config["device"]["identifiers"] == ["pierpressure_backyard"]
    assert "state_class" not in config


@pytest.mark.parametrize("sensor", NEW_SENSORS, ids=lambda s: s.key)
def test_a_timeline_discovery_carries_no_device_class(sensor: TimelineSensor) -> None:
    assert "device_class" not in build_timeline_discovery("backyard", BASE, sensor)


@pytest.mark.parametrize(
    ("key", "unit"),
    [
        ("cloud_low", "%"),
        ("cloud_mid", "%"),
        ("cloud_high", "%"),
        ("wind_gust", "km/h"),
        ("sun_altitude", "°"),
        ("moon_altitude", "°"),
    ],
)
def test_a_timeline_discovery_carries_its_unit(key: str, unit: str) -> None:
    config = build_timeline_discovery("backyard", BASE, SENSORS_BY_KEY[key])
    assert config["unit_of_measurement"] == unit


@pytest.mark.parametrize("key", ["seeing", "transparency"])
def test_seeing_and_transparency_carry_no_unit(key: str) -> None:
    config = build_timeline_discovery("backyard", BASE, SENSORS_BY_KEY[key])
    assert "unit_of_measurement" not in config


@pytest.mark.parametrize("sensor", NEW_SENSORS, ids=lambda s: s.key)
def test_a_timeline_discovery_availability_is_only_the_shared_online_topic(
    sensor: TimelineSensor,
) -> None:
    config = build_timeline_discovery("backyard", BASE, sensor)
    assert config["availability_topic"] == availability_topic(BASE)
    assert config["payload_available"] == PAYLOAD_ONLINE
    assert config["payload_not_available"] == PAYLOAD_OFFLINE
    # No condition on the current hour: an unavailable entity loses its forecast.
    assert "availability" not in config
    assert "availability_mode" not in config


@pytest.mark.parametrize("sensor", NEW_SENSORS, ids=lambda s: s.key)
def test_a_timeline_discovery_validates_against_the_sensor_schema(
    sensor: TimelineSensor,
) -> None:
    strict = {**SENSOR_SCHEMA, "additionalProperties": False}
    jsonschema.validate(build_timeline_discovery("backyard", BASE, sensor), strict)


def test_the_cloud_cover_discovery_is_byte_identical_to_before() -> None:
    before = {
        "name": "Cloud cover",
        "has_entity_name": True,
        "unique_id": "pierpressure_backyard_cloud_cover",
        "state_topic": "pierpressure/backyard/cloud_cover/state",
        "json_attributes_topic": "pierpressure/backyard/cloud_cover/attributes",
        "unit_of_measurement": "%",
        "availability_topic": "pierpressure/status",
        "payload_available": "online",
        "payload_not_available": "offline",
        "icon": "mdi:weather-cloudy",
        "device": {
            "identifiers": ["pierpressure_backyard"],
            "name": "PierPressure backyard",
            "manufacturer": "PierPressure",
            "model": "night-verdict",
        },
    }
    assert json.dumps(build_cloud_cover_discovery("backyard", BASE)) == json.dumps(before)
