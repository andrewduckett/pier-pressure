"""Task 6.1: the additive top-target MQTT-discovery sensor (spec ha-delivery).

The sensor's state is the top-ranked target's name (its designation when the
catalog records no common name); its attributes carry the full ordered list and
the top target's fields; its discovery payload validates against the HA sensor
schema, is retained, and derives its identity from the pier id; and an empty
target list resolves it to unavailable. Every existing entity stays untouched.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import jsonschema

from pierpressure.core.model import (
    Band,
    Confidence,
    DarkWindow,
    Moon,
    MoonPhase,
    Target,
    TargetWindow,
    Verdict,
    VerdictDocument,
)
from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    MqttDelivery,
    build_top_target_discovery,
    discovery_topic,
    top_target_attributes_topic,
    top_target_state_topic,
    verdict_state_topic,
)

from .conftest import FakeMqttClient, make_mqtt_config

BASE = "pierpressure"


def _target(id_: str, name: str | None, score: int) -> Target:
    return Target(
        id=id_,
        name=name,
        type="G",
        score=score,
        window=TargetWindow(
            start=datetime(2026, 9, 8, 21, 0, tzinfo=UTC),
            end=datetime(2026, 9, 9, 2, 0, tzinfo=UTC),
        ),
        max_altitude=61.0,
        transit_time=datetime(2026, 9, 8, 23, 30, tzinfo=UTC),
        moon_separation=100.0,
    )


def _document(targets: list[Target]) -> VerdictDocument:
    return VerdictDocument(
        pier="backyard",
        generated_at=datetime(2026, 9, 8, 18, 0, tzinfo=UTC),
        verdict=Verdict.GO,
        score=80,
        confidence=Confidence(band=Band.HIGH, value=100),
        reasons=["Score 80/100."],
        targets=targets,
        dark_window=DarkWindow(
            start=datetime(2026, 9, 8, 20, 30, tzinfo=UTC),
            end=datetime(2026, 9, 9, 3, 25, tzinfo=UTC),
        ),
        moon=Moon(illumination=0.1, phase=MoonPhase.WANING_CRESCENT),
    )


def _connected() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    return delivery, client


# --------------------------------------------------------------------------- #
# Discovery payload shape and identity
# --------------------------------------------------------------------------- #


def test_top_target_discovery_matches_sensor_schema() -> None:
    payload = build_top_target_discovery("backyard", BASE)
    jsonschema.validate(payload, SENSOR_SCHEMA)


def test_top_target_identity_derives_from_pier_id() -> None:
    payload = build_top_target_discovery("backyard", BASE)
    assert payload["unique_id"] == "pierpressure_backyard_top_target"
    assert payload["state_topic"] == top_target_state_topic(BASE, "backyard")
    assert payload["json_attributes_topic"] == top_target_attributes_topic(BASE, "backyard")


def test_top_target_availability_goes_unavailable_on_empty_list() -> None:
    payload = build_top_target_discovery("backyard", BASE)
    # An availability entry keyed on the attributes topic renders unavailable when
    # the list is empty (mirrors the score sensor's null handling).
    assert payload["availability_mode"] == "all"
    templates = [entry.get("value_template") for entry in payload["availability"]]
    assert any(t and "count" in t for t in templates)


# --------------------------------------------------------------------------- #
# State and attributes from the document
# --------------------------------------------------------------------------- #


def test_state_is_top_target_name() -> None:
    _, client = _connected()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.publish_verdict(
        _document([_target("NGC0224", "Andromeda Galaxy", 90), _target("NGC1976", None, 70)])
    )
    state = client.publishes_to(top_target_state_topic(BASE, "backyard"))
    assert state and state[-1].payload == "Andromeda Galaxy"
    assert state[-1].retain is True


def test_state_falls_back_to_id_when_no_common_name() -> None:
    _, client = _connected()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.publish_verdict(_document([_target("NGC7000", None, 88)]))
    state = client.publishes_to(top_target_state_topic(BASE, "backyard"))
    assert state and state[-1].payload == "NGC7000"


def test_attributes_carry_ordered_list_and_top_fields() -> None:
    _, client = _connected()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    top = _target("NGC0224", "Andromeda Galaxy", 90)
    second = _target("NGC1976", "Orion Nebula", 70)
    delivery.publish_verdict(_document([top, second]))

    attrs = client.publishes_to(top_target_attributes_topic(BASE, "backyard"))
    assert attrs and attrs[-1].retain is True
    payload = json.loads(attrs[-1].payload)
    assert payload["count"] == 2
    assert [t["id"] for t in payload["targets"]] == ["NGC0224", "NGC1976"]
    assert payload["top"]["id"] == "NGC0224"
    assert payload["top"]["score"] == 90
    assert payload["top"]["max_altitude"] == 61.0


def test_empty_target_list_publishes_zero_count() -> None:
    _, client = _connected()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.publish_verdict(_document([]))
    attrs = client.publishes_to(top_target_attributes_topic(BASE, "backyard"))
    payload = json.loads(attrs[-1].payload)
    assert payload["count"] == 0
    assert payload["targets"] == []
    assert payload["top"] is None


# --------------------------------------------------------------------------- #
# Additive: existing entities unchanged, identity stable across republish
# --------------------------------------------------------------------------- #


def test_top_target_discovery_is_published_retained() -> None:
    _, client = _connected()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.publish_verdict(_document([_target("NGC0224", "Andromeda Galaxy", 90)]))
    topic = discovery_topic("homeassistant", "sensor", "backyard", "top_target")
    published = client.publishes_to(topic)
    assert published and all(p.retain for p in published)


def test_existing_entities_are_unchanged() -> None:
    _, client = _connected()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.publish_verdict(_document([_target("NGC0224", "Andromeda Galaxy", 90)]))
    # The verdict/score/refresh discovery and the verdict state are still present.
    for topic in (
        discovery_topic("homeassistant", "sensor", "backyard", "verdict"),
        discovery_topic("homeassistant", "sensor", "backyard", "score"),
        discovery_topic("homeassistant", "button", "backyard", "refresh"),
        verdict_state_topic(BASE, "backyard"),
    ):
        assert client.publishes_to(topic)


def test_republish_introduces_no_new_top_target_identity() -> None:
    _, client = _connected()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    doc = _document([_target("NGC0224", "Andromeda Galaxy", 90)])
    delivery.publish_verdict(doc)
    delivery.publish_verdict(doc)
    topic = discovery_topic("homeassistant", "sensor", "backyard", "top_target")
    unique_ids = {json.loads(p.payload)["unique_id"] for p in client.publishes_to(topic)}
    assert unique_ids == {"pierpressure_backyard_top_target"}
