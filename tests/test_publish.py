"""Tasks 5.2, 5.3, 5.4: state/attributes publishing, availability, failures."""

from __future__ import annotations

import json

import pytest

from pierpressure.core.model import Verdict
from pierpressure.delivery.mqtt import (
    PAYLOAD_OFFLINE,
    PAYLOAD_ONLINE,
    DeliveryError,
    MqttDelivery,
    attributes_topic,
    availability_topic,
    discovery_topic,
    verdict_state_topic,
)

from .conftest import FakeMqttClient, make_document, make_mqtt_config


def _connected_delivery() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    delivery.go_online()
    return delivery, client


def test_verdict_state_and_attributes_are_published_from_the_document() -> None:
    delivery, client = _connected_delivery()
    doc = make_document(verdict=Verdict.MAYBE, score=50)
    delivery.publish_verdict(doc)

    state = client.publishes_to(verdict_state_topic("pierpressure", "backyard"))
    assert len(state) == 1
    assert state[0].payload == "MAYBE"
    assert state[0].retain is True

    attrs = client.publishes_to(attributes_topic("pierpressure", "backyard"))
    assert len(attrs) == 1
    assert attrs[0].retain is True
    payload = json.loads(attrs[0].payload)
    assert payload["verdict"] == "MAYBE"
    assert payload["score"] == 50
    assert payload["confidence"] == {"band": "LOW", "value": 0}
    assert payload["reasons"] == ["test reason"]


def test_discovery_state_and_availability_are_all_retained() -> None:
    delivery, client = _connected_delivery()
    delivery.publish_verdict(make_document())

    prefix = "homeassistant"
    discovery_topics = [
        discovery_topic(prefix, "sensor", "backyard", "verdict"),
        discovery_topic(prefix, "sensor", "backyard", "score"),
        discovery_topic(prefix, "button", "backyard", "refresh"),
    ]
    for topic in discovery_topics:
        published = client.publishes_to(topic)
        assert published and all(p.retain for p in published)

    # Availability was published online + retained by go_online().
    avail = client.publishes_to(availability_topic("pierpressure"))
    assert avail and avail[-1].payload == PAYLOAD_ONLINE and avail[-1].retain is True


def test_null_score_is_published_as_null() -> None:
    delivery, client = _connected_delivery()
    delivery.publish_verdict(make_document(verdict=Verdict.NO_GO, score=None))

    attrs = client.publishes_to(attributes_topic("pierpressure", "backyard"))
    payload = json.loads(attrs[0].payload)
    assert "score" in payload
    assert payload["score"] is None


def test_last_will_is_registered_retained_offline() -> None:
    delivery, client = _connected_delivery()
    assert client.will is not None
    assert client.will.topic == availability_topic("pierpressure")
    assert client.will.payload == PAYLOAD_OFFLINE
    assert client.will.retain is True


def test_publish_failure_rc_is_reported() -> None:
    client = FakeMqttClient(publish_rc=4)  # non-zero rc
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    with pytest.raises(DeliveryError):
        delivery.go_online()  # the online publish fails with rc=4


def test_connect_registers_the_will_but_does_not_go_online() -> None:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    assert client.connected and client.will is not None
    assert client.published == []


def test_go_online_publishes_retained_online() -> None:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    delivery.go_online()
    assert [(p.topic, p.payload, p.retain) for p in client.published] == [
        (availability_topic("pierpressure"), PAYLOAD_ONLINE, True)
    ]
