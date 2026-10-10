"""reconnect-restores-delivery: the adapter publishes each pier's last state again.

``MqttDelivery`` records each retained message it publishes for a pier.
``replay()`` publishes them again, so a broker that lost its retained messages gets
them back after a reconnect, with no new verdict (design D4).
"""

from __future__ import annotations

from datetime import UTC, datetime

from pierpressure.core.model import Verdict
from pierpressure.delivery.mqtt import MqttDelivery, availability_topic, verdict_state_topic
from pierpressure.health import ProviderHealth

from .conftest import FakeMqttClient, Published, make_document, make_mqtt_config

BASE = "pierpressure"


def _health() -> ProviderHealth:
    return ProviderHealth.empty(
        key="open_meteo",
        name="Open-Meteo",
        role="base",
        tracking_since=datetime(2026, 10, 5, 9, 0, tzinfo=UTC),
    )


def _delivery() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    return MqttDelivery(make_mqtt_config(), client=client, manage_narrative=True), client


def _published_twice(delivery: MqttDelivery) -> None:
    """Publish health and a verdict for two piers, then a newer verdict for one."""
    for pier in ("backyard", "frontyard"):
        delivery.publish_health(pier, [_health()])
        delivery.publish_verdict(make_document(pier=pier), narrative="First night.")
    delivery.publish_verdict(
        make_document(pier="backyard", verdict=Verdict.GO, score=90), narrative=None
    )


def _last_payload_by_first_order(published: list[Published]) -> list[tuple[str, object]]:
    last: dict[str, object] = {}
    for message in published:
        last[message.topic] = message.payload
    return list(last.items())


def _replayed(delivery: MqttDelivery, client: FakeMqttClient) -> list[Published]:
    before = len(client.published)
    delivery.replay()
    return client.published[before:]


def test_replay_publishes_each_topic_again_with_its_last_payload() -> None:
    delivery, client = _delivery()
    _published_twice(delivery)
    expected = _last_payload_by_first_order(client.published)
    replayed = _replayed(delivery, client)
    assert [(m.topic, m.payload) for m in replayed] == expected


def test_replay_publishes_every_message_retained_at_qos_1() -> None:
    delivery, client = _delivery()
    _published_twice(delivery)
    replayed = _replayed(delivery, client)
    assert {(m.retain, m.qos) for m in replayed} == {(True, 1)}


def test_replay_leaves_out_the_availability_topic() -> None:
    delivery, client = _delivery()
    delivery.go_online()
    _published_twice(delivery)
    replayed = _replayed(delivery, client)
    assert availability_topic(BASE) not in {m.topic for m in replayed}


def test_replay_with_nothing_published_publishes_nothing() -> None:
    delivery, client = _delivery()
    delivery.replay()
    assert client.published == []


def test_replay_of_a_pier_with_only_health_publishes_only_its_health() -> None:
    delivery, client = _delivery()
    delivery.publish_health("backyard", [_health()])
    expected = [(m.topic, m.payload) for m in client.published]
    replayed = _replayed(delivery, client)
    assert [(m.topic, m.payload) for m in replayed] == expected


# --------------------------------------------------------------------------- #
# Recording whatever paho says (publish-failure-resilience D2)
# --------------------------------------------------------------------------- #


def test_a_refused_message_is_still_replayed() -> None:
    delivery, client = _delivery()
    state = verdict_state_topic(BASE, "backyard")
    client.fail_publish(state)
    delivery.publish_verdict(make_document(pier="backyard", verdict=Verdict.GO, score=90))

    replayed = [p for p in _replayed(delivery, client) if p.topic == state]
    assert [p.payload for p in replayed] == ["GO"]


def test_a_later_refused_payload_replaces_the_earlier_one() -> None:
    delivery, client = _delivery()
    state = verdict_state_topic(BASE, "backyard")
    delivery.publish_verdict(make_document(pier="backyard"))
    client.fail_publish(state)
    delivery.publish_verdict(make_document(pier="backyard", verdict=Verdict.GO, score=90))

    replayed = [p for p in _replayed(delivery, client) if p.topic == state]
    assert [p.payload for p in replayed] == ["GO"]
