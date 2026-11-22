"""The Night 2 to Night 4 sensors (spec ha-delivery; later-night-dark-windows DD5).

Each sensor shows one entry of the document's ``later_nights``: its state is
that night's dusk, and its attributes hold the entry. A night the forecast does
not reach makes its sensor unavailable.
"""

from __future__ import annotations

import json

import jsonschema
import pytest

from pierpressure.core.sky import MAX_LATER_NIGHTS
from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    NIGHTS,
    PAYLOAD_OFFLINE,
    PAYLOAD_ONLINE,
    MqttDelivery,
    availability_topic,
    build_night_discovery,
    discovery_topic,
    night_attributes_topic,
    night_state_topic,
)

from .conftest import FakeMqttClient, make_document, make_later_nights, make_mqtt_config

BASE = "pierpressure"
PREFIX = "homeassistant"


def _connected() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    delivery.go_online()
    return delivery, client


def _config_topic(night: int) -> str:
    return discovery_topic(PREFIX, "sensor", "backyard", f"night_{night}")


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #


def test_the_nights_run_from_night_2_to_one_past_the_cores_maximum() -> None:
    assert list(NIGHTS) == list(range(2, MAX_LATER_NIGHTS + 2))
    assert list(NIGHTS) == [2, 3, 4]


@pytest.mark.parametrize("night", NIGHTS)
def test_night_topics_derive_from_the_pier_and_the_night(night: int) -> None:
    assert (
        night_state_topic(BASE, "backyard", night) == f"pierpressure/backyard/night_{night}/state"
    )
    assert (
        night_attributes_topic(BASE, "backyard", night)
        == f"pierpressure/backyard/night_{night}/attributes"
    )
    assert _config_topic(night) == (
        f"homeassistant/sensor/pierpressure_backyard/night_{night}/config"
    )


@pytest.mark.parametrize("night", NIGHTS)
def test_a_night_discovery_is_a_timestamp_sensor_on_the_pier_device(night: int) -> None:
    config = build_night_discovery("backyard", BASE, night)
    assert config["name"] == f"Night {night}"
    assert config["has_entity_name"] is True
    assert config["unique_id"] == f"pierpressure_backyard_night_{night}"
    assert config["device_class"] == "timestamp"
    assert config["state_topic"] == night_state_topic(BASE, "backyard", night)
    assert config["json_attributes_topic"] == night_attributes_topic(BASE, "backyard", night)
    assert config["icon"] == "mdi:weather-night"
    assert config["device"]["identifiers"] == ["pierpressure_backyard"]
    # Enabled by default: Home Assistant would hide a sensor announced as disabled.
    assert "enabled_by_default" not in config


@pytest.mark.parametrize("night", NIGHTS)
def test_a_night_needs_both_online_and_its_available_flag(night: int) -> None:
    config = build_night_discovery("backyard", BASE, night)
    assert config["availability_mode"] == "all"
    assert config["availability"] == [
        {
            "topic": availability_topic(BASE),
            "payload_available": PAYLOAD_ONLINE,
            "payload_not_available": PAYLOAD_OFFLINE,
        },
        {
            "topic": night_attributes_topic(BASE, "backyard", night),
            "value_template": "{{ 'online' if value_json.available else 'offline' }}",
        },
    ]


@pytest.mark.parametrize("night", NIGHTS)
def test_a_night_discovery_validates_against_the_sensor_schema(night: int) -> None:
    strict = {**SENSOR_SCHEMA, "additionalProperties": False}
    jsonschema.validate(build_night_discovery("backyard", BASE, night), strict)


@pytest.mark.parametrize("night", NIGHTS)
def test_each_publish_announces_the_night_retained(night: int) -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document(later_nights=make_later_nights(1)))

    [config] = client.publishes_to(_config_topic(night))
    assert config.retain is True
    assert json.loads(config.payload) == build_night_discovery("backyard", BASE, night)


@pytest.mark.parametrize("night", NIGHTS)
def test_republishing_introduces_no_new_night_identity(night: int) -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document(later_nights=make_later_nights(3)))
    delivery.publish_verdict(make_document())

    configs = client.publishes_to(_config_topic(night))
    assert len(configs) == 2
    assert {json.loads(p.payload)["unique_id"] for p in configs} == {
        f"pierpressure_backyard_night_{night}"
    }
