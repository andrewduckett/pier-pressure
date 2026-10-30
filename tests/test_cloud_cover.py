"""The Cloud cover sensor (spec ha-delivery, ADR-0025).

One sensor per pier carries the timeline's cloud cover: its state is the current
hour's value, and its attributes carry the whole forecast so a chart card can
draw it. Availability follows the rank sensors: the shared LWT AND an
``available`` flag in the attributes.
"""

from __future__ import annotations

import json

import jsonschema

from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    PAYLOAD_OFFLINE,
    PAYLOAD_ONLINE,
    MqttDelivery,
    availability_topic,
    build_cloud_cover_discovery,
    cloud_cover_attributes_topic,
    cloud_cover_state_topic,
    discovery_topic,
)

from .conftest import FakeMqttClient, make_document, make_mqtt_config

BASE = "pierpressure"
PREFIX = "homeassistant"


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
