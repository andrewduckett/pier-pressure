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
from datetime import UTC, datetime
from typing import Annotated, Any, get_args, get_origin, get_type_hints

import jsonschema
import pytest

from pierpressure.core.model import TimelineEntry, iso_z
from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    PAYLOAD_OFFLINE,
    PAYLOAD_ONLINE,
    RANKS,
    TIMELINE_SENSORS,
    MqttDelivery,
    TimelineSensor,
    availability_topic,
    build_cloud_cover_discovery,
    build_timeline_discovery,
    discovery_topic,
    rank_target_attributes_topic,
    timeline_attributes,
    timeline_attributes_topic,
    timeline_state,
    timeline_state_topic,
)

from .conftest import FakeMqttClient, make_document, make_mqtt_config, make_timeline

BASE = "pierpressure"
PREFIX = "homeassistant"
_GENERATED = datetime(2026, 9, 7, 23, 30, tzinfo=UTC)
_CURRENT_HOUR = datetime(2026, 9, 7, 23, tzinfo=UTC)

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

# The keys a source can leave null; the core always computes the altitudes.
NULLABLE_KEYS = tuple(k for k in NEW_KEYS if not k.endswith("_altitude"))
NEW_SENSORS = TIMELINE_SENSORS[1:]
SENSORS_BY_KEY = {s.key: s for s in TIMELINE_SENSORS}


def _entry(time: datetime, **values: Any) -> TimelineEntry:
    """A full entry at ``time``, as ``make_timeline`` fills it, with ``values`` replaced."""
    [entry] = make_timeline(1, start=time)
    return entry.model_copy(update=values)


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


# --------------------------------------------------------------------------- #
# State and hour
# --------------------------------------------------------------------------- #


def test_the_state_is_the_current_hours_value_as_the_document_emits_it() -> None:
    entry = _entry(_CURRENT_HOUR, wind_gust=18.4, moon_altitude=-12.345)
    doc = make_document(generated_at=_GENERATED, timeline=[entry])

    assert timeline_state(doc, "wind_gust") == "18.4"
    assert timeline_state(doc, "moon_altitude") == "-12.345"
    emitted = json.loads(doc.to_json())["timeline"][0]
    for key in NEW_KEYS:
        assert json.loads(timeline_state(doc, key)) == emitted[key]


@pytest.mark.parametrize("key", NEW_KEYS)
def test_the_hour_is_the_entry_the_state_comes_from(key: str) -> None:
    doc = make_document(generated_at=_GENERATED, timeline=[_entry(_CURRENT_HOUR)])
    assert timeline_attributes(doc, key)["hour"] == "2026-09-07T23:00:00Z"


@pytest.mark.parametrize("key", NULLABLE_KEYS)
def test_a_null_value_renders_unknown_for_that_sensor_only(key: str) -> None:
    doc = make_document(generated_at=_GENERATED, timeline=[_entry(_CURRENT_HOUR, **{key: None})])

    assert timeline_state(doc, key) == "None"
    assert timeline_attributes(doc, key)["hour"] is None
    for other in (k for k in NEW_KEYS if k != key):
        assert timeline_state(doc, other) != "None"
        assert timeline_attributes(doc, other)["hour"] == "2026-09-07T23:00:00Z"


def test_a_null_cloud_cover_leaves_the_other_sensors_known() -> None:
    doc = make_document(generated_at=_GENERATED, timeline=[_entry(_CURRENT_HOUR, cloud_cover=None)])
    assert timeline_state(doc, "cloud_low") == "5.0"


@pytest.mark.parametrize("key", NEW_KEYS)
def test_a_missing_current_hour_renders_unknown(key: str) -> None:
    timeline = make_timeline(2, start=datetime(2026, 9, 7, 20, tzinfo=UTC))
    doc = make_document(generated_at=_GENERATED, timeline=timeline)

    assert timeline_state(doc, key) == "None"
    assert timeline_attributes(doc, key)["hour"] is None


@pytest.mark.parametrize("key", NEW_KEYS)
def test_an_empty_timeline_renders_unknown(key: str) -> None:
    doc = make_document(generated_at=_GENERATED)

    assert timeline_state(doc, key) == "None"
    assert timeline_attributes(doc, key)["hour"] is None


# --------------------------------------------------------------------------- #
# Forecast
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("key", NEW_KEYS)
def test_the_attributes_carry_exactly_hour_and_forecast(key: str) -> None:
    doc = make_document(generated_at=_GENERATED, timeline=make_timeline(3, start=_CURRENT_HOUR))
    assert list(timeline_attributes(doc, key)) == ["hour", "forecast"]


def test_the_forecast_mirrors_the_variable_with_nulls_kept() -> None:
    timeline = [
        _entry(datetime(2026, 9, 7, 20, tzinfo=UTC), seeing=0.62),
        _entry(datetime(2026, 9, 7, 21, tzinfo=UTC), seeing=None),
    ]
    doc = make_document(generated_at=_GENERATED, timeline=timeline)

    assert timeline_attributes(doc, "seeing")["forecast"] == [
        {"datetime": "2026-09-07T20:00:00Z", "value": 0.62},
        {"datetime": "2026-09-07T21:00:00Z", "value": None},
    ]


@pytest.mark.parametrize("key", NEW_KEYS)
def test_the_forecast_carries_the_sensors_own_key(key: str) -> None:
    doc = make_document(timeline=make_timeline(2))
    assert [p["value"] for p in timeline_attributes(doc, key)["forecast"]] == [
        getattr(e, key) for e in doc.timeline
    ]


def test_every_sensors_forecast_lines_up_with_the_timeline() -> None:
    doc = make_document(timeline=make_timeline(48))
    times = [iso_z(e.time) for e in doc.timeline]
    for key in NEW_KEYS:
        assert [p["datetime"] for p in timeline_attributes(doc, key)["forecast"]] == times


@pytest.mark.parametrize("key", NEW_KEYS)
def test_an_empty_timeline_publishes_an_empty_forecast(key: str) -> None:
    assert timeline_attributes(make_document(), key) == {"hour": None, "forecast": []}


@pytest.mark.parametrize("key", NEW_KEYS)
def test_120_full_entries_stay_under_the_recorder_limit(key: str) -> None:
    doc = make_document(timeline=make_timeline(120))
    assert len(json.dumps(timeline_attributes(doc, key)).encode()) < 16 * 1024


# --------------------------------------------------------------------------- #
# Publishing
# --------------------------------------------------------------------------- #


def _connected() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    delivery.go_online()
    return delivery, client


def _topics(key: str) -> tuple[str, str, str]:
    """The discovery, state and attributes topics of a timeline sensor."""
    return (
        discovery_topic(PREFIX, "sensor", "backyard", key),
        timeline_state_topic(BASE, "backyard", key),
        timeline_attributes_topic(BASE, "backyard", key),
    )


def _expected_messages(document: Any) -> list[tuple[str, str, bool]]:
    messages = []
    for sensor in TIMELINE_SENSORS:
        config, state, attrs = _topics(sensor.key)
        messages += [
            (config, json.dumps(build_timeline_discovery("backyard", BASE, sensor)), True),
            (state, timeline_state(document, sensor.key), True),
            (attrs, json.dumps(timeline_attributes(document, sensor.key)), True),
        ]
    return messages


@pytest.mark.parametrize("key", NEW_KEYS)
def test_every_publish_sends_a_retained_timeline_discovery(key: str) -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document())

    [config] = client.publishes_to(_topics(key)[0])
    assert config.retain is True
    assert json.loads(config.payload) == build_timeline_discovery(
        "backyard", BASE, SENSORS_BY_KEY[key]
    )


def test_the_nine_sensors_publish_in_table_order_after_the_ranks() -> None:
    document = make_document(
        generated_at=_GENERATED, timeline=make_timeline(3, start=_CURRENT_HOUR)
    )
    delivery, client = _connected()
    delivery.publish_verdict(document)

    sent = [(p.topic, p.payload, p.retain) for p in client.published]
    last_rank = [t for t, _, _ in sent].index(
        rank_target_attributes_topic(BASE, "backyard", RANKS[-1])
    )
    expected = _expected_messages(document)
    assert sent[last_rank + 1 : last_rank + 1 + len(expected)] == expected


def test_the_states_published_are_the_current_hours_values() -> None:
    entry = _entry(_CURRENT_HOUR, transparency=None, cloud_high=5.0)
    delivery, client = _connected()
    delivery.publish_verdict(make_document(generated_at=_GENERATED, timeline=[entry]))

    [transparency] = client.publishes_to(_topics("transparency")[1])
    [cloud_high] = client.publishes_to(_topics("cloud_high")[1])
    assert (transparency.payload, transparency.retain) == ("None", True)
    assert (cloud_high.payload, cloud_high.retain) == ("5.0", True)


@pytest.mark.parametrize("key", NEW_KEYS)
def test_a_later_publish_replaces_the_forecast(key: str) -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document(timeline=make_timeline(72)))
    delivery.publish_verdict(make_document(timeline=make_timeline(48)))

    *_, last = client.publishes_to(_topics(key)[2])
    assert last.retain is True
    assert len(json.loads(last.payload)["forecast"]) == 48


@pytest.mark.parametrize("key", NEW_KEYS)
def test_republishing_introduces_no_new_identity(key: str) -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document())
    delivery.publish_verdict(make_document())

    configs = client.publishes_to(_topics(key)[0])
    assert len(configs) == 2
    assert {json.loads(p.payload)["unique_id"] for p in configs} == {f"pierpressure_backyard_{key}"}
