"""The per-rank target sensors, Target 1 to Target TOP_N (spec ha-delivery).

Each rank of the target list gets its own sensor on the pier's device. A filled
rank's state is the target's display name, and its attributes carry the rank and
the target's fields. An empty rank publishes an ``available: false`` marker that
its discovery availability turns into ``unavailable``. Every publish writes every
rank, so a shrinking list never leaves an earlier target retained.
"""

from __future__ import annotations

import json

import jsonschema
import pytest

from pierpressure.core.ranking import TOP_N
from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    availability_topic,
    build_rank_target_discovery,
    rank_target_attributes_topic,
    rank_target_state_topic,
)

BASE = "pierpressure"
PREFIX = "homeassistant"
RANKS = range(1, TOP_N + 1)


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
