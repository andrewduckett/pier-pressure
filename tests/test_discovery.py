"""Task 5.1: discovery payload builders validated against the HA schema."""

from __future__ import annotations

import jsonschema

from pierpressure.delivery.ha_schema import BUTTON_SCHEMA, SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    build_refresh_discovery,
    build_score_discovery,
    build_verdict_discovery,
)

BASE = "pierpressure"


def test_verdict_discovery_matches_sensor_schema() -> None:
    jsonschema.validate(build_verdict_discovery("backyard", BASE), SENSOR_SCHEMA)


def test_score_discovery_matches_sensor_schema() -> None:
    payload = build_score_discovery("backyard", BASE)
    jsonschema.validate(payload, SENSOR_SCHEMA)
    # The score availability requires a non-null score (design D6).
    assert payload["availability_mode"] == "all"
    templates = [entry.get("value_template") for entry in payload["availability"]]
    assert any(t and "value_json.score is not none" in t for t in templates)


def test_refresh_discovery_matches_button_schema() -> None:
    jsonschema.validate(build_refresh_discovery("backyard", BASE), BUTTON_SCHEMA)


def test_all_entities_share_one_device() -> None:
    device_ids = {
        tuple(builder("backyard", BASE)["device"]["identifiers"])
        for builder in (build_verdict_discovery, build_score_discovery, build_refresh_discovery)
    }
    assert device_ids == {("pierpressure_backyard",)}


def test_unique_ids_and_topics_are_stable_across_rebuilds() -> None:
    for builder, topic_key in (
        (build_verdict_discovery, "state_topic"),
        (build_score_discovery, "state_topic"),
        (build_refresh_discovery, "command_topic"),
    ):
        first = builder("backyard", BASE)
        second = builder("backyard", BASE)
        assert first["unique_id"] == second["unique_id"]
        assert first[topic_key] == second[topic_key]


def test_unique_ids_are_distinct_per_entity() -> None:
    ids = {
        builder("backyard", BASE)["unique_id"]
        for builder in (build_verdict_discovery, build_score_discovery, build_refresh_discovery)
    }
    assert len(ids) == 3
