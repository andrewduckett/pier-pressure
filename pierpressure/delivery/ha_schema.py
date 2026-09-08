"""JSON schemas for Home Assistant MQTT-discovery payloads (design D11).

Home Assistant does not ship a single machine-readable discovery schema, so
these hand-authored JSON Schemas capture the fields PierPressure relies on for
each entity type. They are deliberately permissive about *extra* keys (Home
Assistant accepts many optional fields) but strict about the shape and types of
the fields we emit, so a malformed discovery config (a missing topic, a wrong
type) fails the test suite rather than only failing silently in production.
"""

from __future__ import annotations

from typing import Any

_DEVICE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "identifiers": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "name": {"type": "string"},
        "manufacturer": {"type": "string"},
        "model": {"type": "string"},
    },
    "required": ["identifiers"],
}

_AVAILABILITY_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "payload_available": {"type": "string"},
        "payload_not_available": {"type": "string"},
        "value_template": {"type": "string"},
    },
    "required": ["topic"],
}

SENSOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "unique_id": {"type": "string", "minLength": 1},
        "has_entity_name": {"type": "boolean"},
        "state_topic": {"type": "string", "minLength": 1},
        "json_attributes_topic": {"type": "string"},
        "value_template": {"type": "string"},
        "icon": {"type": "string"},
        "availability_topic": {"type": "string"},
        "payload_available": {"type": "string"},
        "payload_not_available": {"type": "string"},
        "availability_mode": {"enum": ["all", "any", "latest"]},
        "availability": {
            "type": "array",
            "items": _AVAILABILITY_ITEM_SCHEMA,
            "minItems": 1,
        },
        "device": _DEVICE_SCHEMA,
    },
    "required": ["unique_id", "state_topic", "device"],
}

BUTTON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "unique_id": {"type": "string", "minLength": 1},
        "has_entity_name": {"type": "boolean"},
        "command_topic": {"type": "string", "minLength": 1},
        "icon": {"type": "string"},
        "availability_topic": {"type": "string"},
        "payload_available": {"type": "string"},
        "payload_not_available": {"type": "string"},
        "device": _DEVICE_SCHEMA,
    },
    "required": ["unique_id", "command_topic", "device"],
}
