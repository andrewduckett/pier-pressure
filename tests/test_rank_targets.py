"""The per-rank target sensors, Target 1 to Target TOP_N (spec ha-delivery).

Each rank of the target list gets its own sensor on the pier's device. A filled
rank's state is the target's display name, and its attributes carry the rank and
the target's fields. An empty rank publishes an ``available: false`` marker that
its discovery availability turns into ``unavailable``. Every publish writes every
rank, so a shrinking list never leaves an earlier target retained.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import jsonschema
import pytest

from pierpressure.core.model import Target, TargetWindow, VerdictDocument
from pierpressure.core.ranking import TOP_N
from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    MqttDelivery,
    attributes_topic,
    availability_topic,
    build_rank_target_discovery,
    build_refresh_discovery,
    build_score_discovery,
    build_top_target_discovery,
    build_verdict_discovery,
    discovery_topic,
    rank_target_attributes,
    rank_target_attributes_topic,
    rank_target_state,
    rank_target_state_topic,
    top_target_attributes,
    top_target_attributes_topic,
    top_target_state,
    top_target_state_topic,
    verdict_state_topic,
)

from .conftest import FakeMqttClient, make_document, make_mqtt_config

BASE = "pierpressure"
PREFIX = "homeassistant"
RANKS = range(1, TOP_N + 1)


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
        size_arcmin=178.0,
        magnitude=3.4,
        surface_brightness=13.5,
    )


def _targets(count: int) -> list[Target]:
    return [_target(f"NGC{n:04d}", f"Object {n}", 100 - n) for n in range(1, count + 1)]


def _document(targets: list[Target]) -> VerdictDocument:
    return make_document().model_copy(update={"targets": targets})


# --------------------------------------------------------------------------- #
# Topics (design D1)
# --------------------------------------------------------------------------- #


def test_rank_topics_derive_from_pier_and_rank() -> None:
    assert rank_target_state_topic(BASE, "backyard", 3) == "pierpressure/backyard/target_3/state"
    assert (
        rank_target_attributes_topic(BASE, "backyard", 3)
        == "pierpressure/backyard/target_3/attributes"
    )


# --------------------------------------------------------------------------- #
# Discovery payload shape and identity
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("rank", RANKS)
def test_rank_discovery_matches_sensor_schema(rank: int) -> None:
    jsonschema.validate(build_rank_target_discovery("backyard", BASE, rank), SENSOR_SCHEMA)


@pytest.mark.parametrize("rank", RANKS)
def test_rank_discovery_identity_derives_from_pier_and_rank(rank: int) -> None:
    payload = build_rank_target_discovery("backyard", BASE, rank)
    assert payload["name"] == f"Target {rank}"
    assert payload["unique_id"] == f"pierpressure_backyard_target_{rank}"
    assert payload["state_topic"] == rank_target_state_topic(BASE, "backyard", rank)
    assert payload["json_attributes_topic"] == rank_target_attributes_topic(BASE, "backyard", rank)


@pytest.mark.parametrize("rank", RANKS)
def test_rank_discovery_availability_reads_the_available_flag(rank: int) -> None:
    payload = build_rank_target_discovery("backyard", BASE, rank)
    assert payload["availability_mode"] == "all"
    assert payload["availability"] == [
        {
            "topic": availability_topic(BASE),
            "payload_available": "online",
            "payload_not_available": "offline",
        },
        {
            "topic": rank_target_attributes_topic(BASE, "backyard", rank),
            "value_template": "{{ 'online' if value_json.available else 'offline' }}",
        },
    ]


@pytest.mark.parametrize("rank", RANKS)
def test_rank_discovery_is_enabled_by_default(rank: int) -> None:
    payload = build_rank_target_discovery("backyard", BASE, rank)
    assert payload.get("enabled_by_default", True) is True


# --------------------------------------------------------------------------- #
# State and attributes of a filled rank (design D2)
# --------------------------------------------------------------------------- #


def test_filled_rank_state_is_the_target_name() -> None:
    document = _document(_targets(5))
    assert rank_target_state(document, 3) == "Object 3"


def test_filled_rank_attributes_carry_rank_and_target_fields() -> None:
    targets = _targets(5)
    document = _document(targets)
    attributes = rank_target_attributes(document, 3)
    assert attributes == {
        "available": True,
        "rank": 3,
        **json.loads(targets[2].model_dump_json()),
    }
    assert list(attributes)[:2] == ["available", "rank"]
    assert attributes["id"] == "NGC0003"
    assert attributes["window"] == {"start": "2026-09-08T21:00:00Z", "end": "2026-09-09T02:00:00Z"}


def test_filled_rank_without_common_name_shows_the_catalog_id() -> None:
    document = _document([_target("NGC0224", "Andromeda Galaxy", 90), _target("NGC7000", None, 80)])
    assert rank_target_state(document, 2) == "NGC7000"


# --------------------------------------------------------------------------- #
# An empty rank (design D2)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("rank", [3, TOP_N])
def test_empty_rank_state_is_an_empty_string(rank: int) -> None:
    assert rank_target_state(_document(_targets(2)), rank) == ""


@pytest.mark.parametrize("rank", [3, TOP_N])
def test_empty_rank_attributes_mark_no_target(rank: int) -> None:
    assert rank_target_attributes(_document(_targets(2)), rank) == {
        "available": False,
        "rank": rank,
    }


def test_every_rank_is_empty_when_no_target_ranks() -> None:
    document = _document([])
    for rank in RANKS:
        assert rank_target_state(document, rank) == ""
        assert rank_target_attributes(document, rank) == {"available": False, "rank": rank}


# --------------------------------------------------------------------------- #
# Publishing every rank (design D3, D6)
# --------------------------------------------------------------------------- #


def _connected() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    return delivery, client


def _rank_topics(rank: int) -> tuple[str, str, str]:
    return (
        discovery_topic(PREFIX, "sensor", "backyard", f"target_{rank}"),
        rank_target_state_topic(BASE, "backyard", rank),
        rank_target_attributes_topic(BASE, "backyard", rank),
    )


@pytest.mark.parametrize("count", [TOP_N, 3, 0])
def test_publish_writes_every_rank_retained(count: int) -> None:
    delivery, client = _connected()
    document = _document(_targets(count))
    delivery.publish_verdict(document)

    for rank in RANKS:
        config, state, attributes = (client.publishes_to(t) for t in _rank_topics(rank))
        assert len(config) == len(state) == len(attributes) == 1
        assert all(p.retain for p in (*config, *state, *attributes))
        assert json.loads(config[0].payload) == build_rank_target_discovery(
            "backyard", BASE, rank
        )
        assert state[0].payload == rank_target_state(document, rank)
        assert json.loads(attributes[0].payload) == rank_target_attributes(document, rank)


def test_rank_sensors_publish_in_design_order() -> None:
    delivery, client = _connected()
    delivery.publish_verdict(_document(_targets(2)))
    topics = [p.topic for p in client.published]

    configs = [topics.index(_rank_topics(rank)[0]) for rank in RANKS]
    states = [topics.index(_rank_topics(rank)[1]) for rank in RANKS]
    top_target_config = topics.index(discovery_topic(PREFIX, "sensor", "backyard", "top_target"))
    top_target_attributes = topics.index(f"{BASE}/backyard/top_target/attributes")

    # Rank configs follow the other discovery configs and precede every state.
    assert configs == sorted(configs)
    assert top_target_config < configs[0]
    assert configs[-1] < topics.index(f"{BASE}/backyard/verdict/state")
    # Rank states and attributes follow the top target's, rank by rank.
    assert top_target_attributes < states[0]
    assert states == sorted(states)
    for rank in RANKS:
        assert topics.index(_rank_topics(rank)[2]) == states[rank - 1] + 1


def _last_retained(client: FakeMqttClient, topic: str) -> str:
    published = client.publishes_to(topic)
    assert published and published[-1].retain
    return str(published[-1].payload)


def test_shrinking_list_clears_the_old_ranks() -> None:
    delivery, client = _connected()
    earlier = _targets(5)
    delivery.publish_verdict(_document(earlier))
    delivery.publish_verdict(_document(_targets(2)))

    earlier_names = {target.name for target in earlier}
    for rank in (3, 4, 5):
        _, state, attributes = _rank_topics(rank)
        assert json.loads(_last_retained(client, attributes)) == {"available": False, "rank": rank}
        assert _last_retained(client, state) not in earlier_names



# --------------------------------------------------------------------------- #
# Additive: existing entities unchanged, identity stable across republish
# --------------------------------------------------------------------------- #


def test_existing_entities_publish_the_same_topics_and_payloads() -> None:
    delivery, client = _connected()
    document = _document(_targets(3))
    delivery.publish_verdict(document)

    rank_topics = {topic for rank in RANKS for topic in _rank_topics(rank)}
    others = [(p.topic, p.payload, p.retain) for p in client.published if p.topic not in rank_topics]
    assert others == [
        (availability_topic(BASE), "online", True),
        (
            discovery_topic(PREFIX, "sensor", "backyard", "verdict"),
            json.dumps(build_verdict_discovery("backyard", BASE)),
            True,
        ),
        (
            discovery_topic(PREFIX, "sensor", "backyard", "score"),
            json.dumps(build_score_discovery("backyard", BASE)),
            True,
        ),
        (
            discovery_topic(PREFIX, "button", "backyard", "refresh"),
            json.dumps(build_refresh_discovery("backyard", BASE)),
            True,
        ),
        (
            discovery_topic(PREFIX, "sensor", "backyard", "top_target"),
            json.dumps(build_top_target_discovery("backyard", BASE)),
            True,
        ),
        (verdict_state_topic(BASE, "backyard"), document.verdict.value, True),
        (attributes_topic(BASE, "backyard"), document.to_json(), True),
        (top_target_state_topic(BASE, "backyard"), top_target_state(document), True),
        (
            top_target_attributes_topic(BASE, "backyard"),
            json.dumps(top_target_attributes(document)),
            True,
        ),
    ]


def test_republish_introduces_no_new_rank_identity() -> None:
    delivery, client = _connected()
    delivery.publish_verdict(_document(_targets(5)))
    delivery.publish_verdict(_document(_targets(2)))

    for rank in RANKS:
        config = client.publishes_to(_rank_topics(rank)[0])
        unique_ids = {json.loads(p.payload)["unique_id"] for p in config}
        assert unique_ids == {f"pierpressure_backyard_target_{rank}"}
