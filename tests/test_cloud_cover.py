"""The Cloud cover sensor (spec ha-delivery, ADR-0025).

One sensor per pier carries the timeline's cloud cover: its state is the current
hour's value, and its attributes carry the whole forecast so a chart card can
draw it. Availability follows the rank sensors: the shared LWT AND an
``available`` flag in the attributes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import jsonschema

from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    PAYLOAD_OFFLINE,
    PAYLOAD_ONLINE,
    MqttDelivery,
    availability_topic,
    build_cloud_cover_discovery,
    cloud_cover_attributes,
    cloud_cover_attributes_topic,
    cloud_cover_state,
    cloud_cover_state_topic,
    discovery_topic,
)

from .conftest import FakeMqttClient, make_document, make_mqtt_config, make_timeline

BASE = "pierpressure"
PREFIX = "homeassistant"
_GENERATED = datetime(2026, 9, 7, 23, 30, tzinfo=UTC)
_CURRENT_HOUR = datetime(2026, 9, 7, 23, tzinfo=UTC)


def _connected() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    delivery.go_online()
    return delivery, client


def _discovery_topic(pier: str = "backyard") -> str:
    return discovery_topic(PREFIX, "sensor", pier, "cloud_cover")


def test_cloud_cover_topics_derive_from_the_pier_id() -> None:
    assert cloud_cover_state_topic(BASE, "backyard") == "pierpressure/backyard/cloud_cover/state"
    assert (
        cloud_cover_attributes_topic(BASE, "backyard")
        == "pierpressure/backyard/cloud_cover/attributes"
    )


def test_every_publish_sends_a_retained_cloud_cover_discovery() -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document())

    [config] = client.publishes_to(_discovery_topic())
    assert config.retain is True
    assert json.loads(config.payload) == build_cloud_cover_discovery("backyard", BASE)


def test_cloud_cover_discovery_is_a_percent_sensor_on_the_pier_device() -> None:
    config = build_cloud_cover_discovery("backyard", BASE)
    assert config["name"] == "Cloud cover"
    assert config["has_entity_name"] is True
    assert config["unique_id"] == "pierpressure_backyard_cloud_cover"
    assert config["unit_of_measurement"] == "%"
    assert config.get("enabled_by_default", True) is True
    assert config["state_topic"] == cloud_cover_state_topic(BASE, "backyard")
    assert config["json_attributes_topic"] == cloud_cover_attributes_topic(BASE, "backyard")
    assert config["device"]["identifiers"] == ["pierpressure_backyard"]
    # A forecast rewritten every recompute: long-term statistics would be noise.
    assert "state_class" not in config
    assert "device_class" not in config


def test_cloud_cover_discovery_availability_requires_online_and_available() -> None:
    config = build_cloud_cover_discovery("backyard", BASE)
    assert config["availability_mode"] == "all"
    lwt, flag = config["availability"]
    assert lwt == {
        "topic": availability_topic(BASE),
        "payload_available": PAYLOAD_ONLINE,
        "payload_not_available": PAYLOAD_OFFLINE,
    }
    assert flag["topic"] == cloud_cover_attributes_topic(BASE, "backyard")
    assert "value_json.available" in flag["value_template"]


def test_cloud_cover_discovery_validates_against_the_sensor_schema() -> None:
    assert SENSOR_SCHEMA["properties"]["unit_of_measurement"] == {"type": "string"}
    # Closed to extra keys, so every key the sensor emits must be declared.
    strict = {**SENSOR_SCHEMA, "additionalProperties": False}
    jsonschema.validate(build_cloud_cover_discovery("backyard", BASE), strict)


def test_republishing_introduces_no_new_cloud_cover_discovery_identity() -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document())
    delivery.publish_verdict(make_document())

    configs = client.publishes_to(_discovery_topic())
    assert len(configs) == 2
    assert {json.loads(p.payload)["unique_id"] for p in configs} == {
        "pierpressure_backyard_cloud_cover"
    }


# --------------------------------------------------------------------------- #
# State and attributes
# --------------------------------------------------------------------------- #


def _published_state_and_attributes(client: FakeMqttClient) -> tuple[str, dict[str, object]]:
    [state] = client.publishes_to(cloud_cover_state_topic(BASE, "backyard"))
    [attrs] = client.publishes_to(cloud_cover_attributes_topic(BASE, "backyard"))
    assert state.retain is True and attrs.retain is True
    return state.payload, json.loads(attrs.payload)


def test_the_state_is_the_current_hours_cloud_cover_as_the_document_emits_it() -> None:
    timeline = make_timeline(1, start=_CURRENT_HOUR, cloud_cover=15.0)
    delivery, client = _connected()
    delivery.publish_verdict(make_document(generated_at=_GENERATED, timeline=timeline))

    state, attrs = _published_state_and_attributes(client)
    assert state == "15.0"
    emitted = json.loads(make_document(timeline=timeline).to_json())["timeline"][0]
    assert json.loads(state) == emitted["cloud_cover"]
    assert attrs["hour"] == "2026-09-07T23:00:00Z"
    assert attrs["available"] is True


def test_the_attributes_carry_exactly_available_hour_and_forecast() -> None:
    doc = make_document(generated_at=_GENERATED, timeline=make_timeline(3, start=_CURRENT_HOUR))
    assert list(cloud_cover_attributes(doc)) == ["available", "hour", "forecast"]


def test_the_forecast_mirrors_the_timeline_with_nulls_kept() -> None:
    first = make_timeline(1, start=datetime(2026, 9, 7, 20, tzinfo=UTC), cloud_cover=37.0)
    second = make_timeline(1, start=datetime(2026, 9, 7, 21, tzinfo=UTC), cloud_cover=None)
    delivery, client = _connected()
    delivery.publish_verdict(make_document(generated_at=_GENERATED, timeline=first + second))

    _, attrs = _published_state_and_attributes(client)
    assert attrs["forecast"] == [
        {"datetime": "2026-09-07T20:00:00Z", "value": 37.0},
        {"datetime": "2026-09-07T21:00:00Z", "value": None},
    ]


def test_a_missing_current_hour_publishes_unavailable() -> None:
    timeline = make_timeline(2, start=datetime(2026, 9, 7, 20, tzinfo=UTC))
    delivery, client = _connected()
    delivery.publish_verdict(make_document(generated_at=_GENERATED, timeline=timeline))

    state, attrs = _published_state_and_attributes(client)
    assert state == ""
    assert attrs["available"] is False
    assert attrs["hour"] is None
    assert len(attrs["forecast"]) == 2  # type: ignore[arg-type]


def test_a_null_current_hour_publishes_unavailable() -> None:
    timeline = make_timeline(1, start=_CURRENT_HOUR, cloud_cover=None)
    doc = make_document(generated_at=_GENERATED, timeline=timeline)

    assert cloud_cover_state(doc) == ""
    attrs = cloud_cover_attributes(doc)
    assert attrs["available"] is False
    assert attrs["hour"] is None
    assert attrs["forecast"] == [{"datetime": "2026-09-07T23:00:00Z", "value": None}]


def test_an_empty_timeline_publishes_an_empty_forecast_and_unavailable() -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document(generated_at=_GENERATED))

    state, attrs = _published_state_and_attributes(client)
    assert state == ""
    assert attrs == {"available": False, "hour": None, "forecast": []}


def test_a_later_publish_replaces_the_forecast() -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document(timeline=make_timeline(72)))
    delivery.publish_verdict(make_document(timeline=make_timeline(48)))

    *_, last = client.publishes_to(cloud_cover_attributes_topic(BASE, "backyard"))
    forecast = json.loads(last.payload)["forecast"]
    assert len(forecast) == 48
    assert forecast[0]["datetime"] == "2026-09-07T18:00:00Z"


def test_120_entries_stay_under_the_recorder_limit() -> None:
    doc = make_document(timeline=make_timeline(120, cloud_cover=100.0))
    assert len(json.dumps(cloud_cover_attributes(doc)).encode()) < 16 * 1024
