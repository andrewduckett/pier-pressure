"""Provider health sensors on the MQTT delivery surface (provider-health-entities).

One diagnostic timestamp sensor per pier per conditions provider. Its state is the
last successful fetch, or ``None`` (unknown) when there is none since the process
started; its attributes describe the latest fetch. Availability is the shared
last-will topic only, so a failing provider keeps showing its last success.
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
    build_health_discovery,
    discovery_topic,
    health_attributes,
    health_attributes_topic,
    health_state,
    health_state_topic,
)
from pierpressure.health import ProviderHealth

from .conftest import FakeMqttClient, make_document, make_mqtt_config

BASE = "pierpressure"
PREFIX = "homeassistant"

_START = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
_SUCCESS = datetime(2026, 10, 5, 12, 0, 30, 123456, tzinfo=UTC)
_FAILED = datetime(2026, 10, 5, 18, 0, tzinfo=UTC)
_ISSUED = datetime(2026, 10, 5, 11, 0, tzinfo=UTC)


def _empty(key: str = "open_meteo", name: str = "Open-Meteo") -> ProviderHealth:
    return ProviderHealth.empty(key=key, name=name, role="base", tracking_since=_START)


def _failing_after_success() -> ProviderHealth:
    return ProviderHealth(
        key="open_meteo",
        name="Open-Meteo",
        role="base",
        tracking_since=_START,
        status="failed",
        last_fetch=_FAILED,
        last_error="ConnectError",
        last_success=_SUCCESS,
        issued_at=_ISSUED,
    )


# --------------------------------------------------------------------------- #
# 3.2 discovery
# --------------------------------------------------------------------------- #


def test_health_discovery_validates_and_is_a_diagnostic_timestamp() -> None:
    payload = build_health_discovery("backyard", BASE, "open_meteo", "Open-Meteo")
    jsonschema.validate(payload, SENSOR_SCHEMA)
    assert payload["name"] == "Open-Meteo health"
    assert payload["has_entity_name"] is True
    assert payload["unique_id"] == "pierpressure_backyard_open_meteo_health"
    assert payload["device_class"] == "timestamp"
    assert payload["entity_category"] == "diagnostic"
    assert payload["state_topic"] == "pierpressure/backyard/health/open_meteo/state"
    assert payload["json_attributes_topic"] == "pierpressure/backyard/health/open_meteo/attributes"
    assert payload["device"]["identifiers"] == ["pierpressure_backyard"]


def test_health_availability_is_the_last_will_topic_only() -> None:
    payload = build_health_discovery("backyard", BASE, "seven_timer", "7Timer!")
    assert payload["availability_topic"] == availability_topic(BASE)
    assert payload["payload_available"] == PAYLOAD_ONLINE
    assert payload["payload_not_available"] == PAYLOAD_OFFLINE
    assert "availability" not in payload
    assert "availability_mode" not in payload


def test_health_discovery_topic_derives_from_pier_and_provider() -> None:
    assert (
        discovery_topic(PREFIX, "sensor", "backyard", "open_meteo_health")
        == "homeassistant/sensor/pierpressure_backyard/open_meteo_health/config"
    )


# --------------------------------------------------------------------------- #
# 3.3 state and attributes
# --------------------------------------------------------------------------- #


def test_state_is_the_last_success_in_iso_8601_with_offset() -> None:
    assert health_state(_failing_after_success()) == "2026-10-05T12:00:30+00:00"


def test_state_with_no_success_is_the_literal_none() -> None:
    assert health_state(_empty()) == "None"


def test_attributes_with_no_history_are_null() -> None:
    assert health_attributes(_empty()) == {
        "provider": "Open-Meteo",
        "role": "base",
        "tracking_since": "2026-10-05T09:00:00+00:00",
        "status": None,
        "last_fetch": None,
        "last_error": None,
        "issued_at": None,
    }


def test_attributes_after_a_failure_keep_the_earlier_issue_time() -> None:
    assert health_attributes(_failing_after_success()) == {
        "provider": "Open-Meteo",
        "role": "base",
        "tracking_since": "2026-10-05T09:00:00+00:00",
        "status": "failed",
        "last_fetch": "2026-10-05T18:00:00+00:00",
        "last_error": "ConnectError",
        "issued_at": "2026-10-05T11:00:00+00:00",
    }


# --------------------------------------------------------------------------- #
# 3.4 publish_health
# --------------------------------------------------------------------------- #


def _delivery() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    return MqttDelivery(make_mqtt_config(), client=client), client


def test_publish_health_publishes_each_record_retained() -> None:
    delivery, client = _delivery()
    healths = [_failing_after_success(), _empty("seven_timer", "7Timer!")]
    delivery.publish_health("backyard", healths)

    expected = []
    for health in healths:
        expected += [
            (
                discovery_topic(PREFIX, "sensor", "backyard", f"{health.key}_health"),
                json.dumps(build_health_discovery("backyard", BASE, health.key, health.name)),
            ),
            (health_state_topic(BASE, "backyard", health.key), health_state(health)),
            (
                health_attributes_topic(BASE, "backyard", health.key),
                json.dumps(health_attributes(health)),
            ),
        ]
    assert [(p.topic, p.payload) for p in client.published] == expected
    assert all(p.retain for p in client.published)


def test_publish_verdict_output_is_unchanged_by_health() -> None:
    document = make_document()
    plain, plain_client = _delivery()
    plain.publish_verdict(document)

    with_health, health_client = _delivery()
    with_health.publish_health("backyard", [_failing_after_success()])
    health_client.published.clear()
    with_health.publish_verdict(document)

    assert health_client.published == plain_client.published
    attributes = json.loads(
        next(p.payload for p in plain_client.published if p.topic.endswith("verdict/attributes"))
    )
    assert not any("health" in key for key in attributes)
