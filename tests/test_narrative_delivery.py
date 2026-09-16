"""Section 4: the optional narrative sensor on the MQTT delivery surface.

Delivery is told once, from config, whether it manages the narrative entity. When
disabled it publishes nothing narrative and its output is byte-identical to the
pre-feature output (4.1, 4.4). When enabled it publishes a retained sensor whose
attributes carry the full prose (4.2), and when no narrative is available it
actively publishes an unavailable state rather than leaving stale prose retained
(4.3). The other entities are unaffected in every case.
"""

from __future__ import annotations

import json

import jsonschema

from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    MqttDelivery,
    attributes_topic,
    build_narrative_discovery,
    discovery_topic,
    narrative_attributes_topic,
    narrative_state_topic,
    top_target_state_topic,
    verdict_state_topic,
)

from .conftest import FakeMqttClient, make_document, make_mqtt_config

BASE = "pierpressure"
PREFIX = "homeassistant"


def _connected(*, manage_narrative: bool) -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client, manage_narrative=manage_narrative)
    delivery.connect()
    return delivery, client


def _narrative_topics() -> set[str]:
    return {
        discovery_topic(PREFIX, "sensor", "backyard", "narrative"),
        narrative_state_topic(BASE, "backyard"),
        narrative_attributes_topic(BASE, "backyard"),
    }


# --------------------------------------------------------------------------- #
# 4.1 / 4.4 — disabled: publishes no narrative, byte-identical to before
# --------------------------------------------------------------------------- #


def test_disabled_delivery_publishes_no_narrative() -> None:
    delivery, client = _connected(manage_narrative=False)
    delivery.publish_verdict(make_document(), narrative="ignored while disabled")

    for topic in _narrative_topics():
        assert client.publishes_to(topic) == []
    # The existing entities still publish exactly as before.
    assert client.publishes_to(verdict_state_topic(BASE, "backyard"))
    assert client.publishes_to(top_target_state_topic(BASE, "backyard"))


def test_disabled_output_is_byte_identical_regardless_of_narrative() -> None:
    # Whether or not a narrative is passed, a non-managing delivery emits the same
    # bytes — the entity is purely additive (task 4.4).
    without, without_client = _connected(manage_narrative=False)
    without.publish_verdict(make_document())

    with_narrative, with_client = _connected(manage_narrative=False)
    with_narrative.publish_verdict(make_document(), narrative="some prose")

    def records(client: FakeMqttClient) -> list[tuple[str, object, int, bool]]:
        return [(p.topic, p.payload, p.qos, p.retain) for p in client.published]

    assert records(without_client) == records(with_client)


# --------------------------------------------------------------------------- #
# 4.2 — enabled + present
# --------------------------------------------------------------------------- #


def test_narrative_discovery_matches_sensor_schema_and_derives_identity() -> None:
    payload = build_narrative_discovery("backyard", BASE)
    jsonschema.validate(payload, SENSOR_SCHEMA)
    assert payload["unique_id"] == "pierpressure_backyard_narrative"
    assert payload["device"]["identifiers"] == ["pierpressure_backyard"]


def test_enabled_present_publishes_prose_in_attributes_with_short_state() -> None:
    delivery, client = _connected(manage_narrative=True)
    prose = "A clear, quiet night — set up and point at Andromeda."
    delivery.publish_verdict(make_document(), narrative=prose)

    disco = client.publishes_to(discovery_topic(PREFIX, "sensor", "backyard", "narrative"))
    assert disco and disco[0].retain is True

    state = client.publishes_to(narrative_state_topic(BASE, "backyard"))
    assert len(state) == 1
    assert state[0].retain is True
    assert len(state[0].payload) <= 255  # HA state length limit
    assert prose not in state[0].payload  # the full prose does not ride in the state

    attrs = client.publishes_to(narrative_attributes_topic(BASE, "backyard"))
    assert len(attrs) == 1 and attrs[0].retain is True
    body = json.loads(attrs[0].payload)
    assert body["available"] is True
    assert body["narrative"] == prose


def test_enabled_present_leaves_other_entities_intact() -> None:
    delivery, client = _connected(manage_narrative=True)
    delivery.publish_verdict(make_document(), narrative="prose")
    assert client.publishes_to(verdict_state_topic(BASE, "backyard"))
    assert client.publishes_to(attributes_topic(BASE, "backyard"))
    assert client.publishes_to(top_target_state_topic(BASE, "backyard"))


# --------------------------------------------------------------------------- #
# 4.3 — enabled + absent
# --------------------------------------------------------------------------- #


def test_enabled_absent_actively_publishes_unavailable() -> None:
    delivery, client = _connected(manage_narrative=True)
    delivery.publish_verdict(make_document(), narrative=None)

    # The narrative sensor is actively published (not skipped) so it resolves to
    # unavailable rather than an empty or stale value.
    state = client.publishes_to(narrative_state_topic(BASE, "backyard"))
    attrs = client.publishes_to(narrative_attributes_topic(BASE, "backyard"))
    assert len(state) == 1 and len(attrs) == 1
    assert json.loads(attrs[0].payload)["available"] is False

    # The other entities still publish.
    assert client.publishes_to(verdict_state_topic(BASE, "backyard"))
    assert client.publishes_to(top_target_state_topic(BASE, "backyard"))


def test_a_prior_retained_narrative_is_not_shown_as_current() -> None:
    delivery, client = _connected(manage_narrative=True)
    delivery.publish_verdict(make_document(), narrative="tonight's prose")
    delivery.publish_verdict(make_document(), narrative=None)  # later recompute: none

    attrs = client.publishes_to(narrative_attributes_topic(BASE, "backyard"))
    assert len(attrs) == 2
    # The later publish overwrites the retained attributes with an unavailable
    # marker, so the earlier prose is not left shown as the current explanation.
    assert json.loads(attrs[0].payload)["narrative"] == "tonight's prose"
    assert json.loads(attrs[1].payload)["available"] is False
    assert json.loads(attrs[1].payload)["narrative"] is None
