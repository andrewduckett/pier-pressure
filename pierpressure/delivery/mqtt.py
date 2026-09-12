"""MQTT-discovery delivery adapter (design D5, D6, D9).

Builds per-pier discovery payloads (verdict sensor, score sensor, refresh
button), publishes verdict state/attributes/availability, and subscribes to each
pier's refresh command topic. The MQTT client is injectable so tests can drive a
fake client with no broker.

Topic scheme (design D5), for base topic ``B`` and discovery prefix ``P``:

===========================  ==================================================  ======
Purpose                      Topic                                               Retain
===========================  ==================================================  ======
Verdict discovery cfg        ``P/sensor/pierpressure_<pier>/verdict/config``     yes
Score discovery cfg          ``P/sensor/pierpressure_<pier>/score/config``       yes
Refresh discovery cfg        ``P/button/pierpressure_<pier>/refresh/config``     yes
Verdict state                ``B/<pier>/verdict/state``                          yes
Document attributes (JSON)   ``B/<pier>/verdict/attributes``                     yes
Refresh command              ``B/<pier>/refresh/command``                        no
Availability (LWT)           ``B/status``                                        yes
===========================  ==================================================  ======
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from typing import Any, Protocol

import paho.mqtt.client as mqtt

from pierpressure.core.config import MqttConfig
from pierpressure.core.model import VerdictDocument

logger = logging.getLogger(__name__)

PAYLOAD_ONLINE = "online"
PAYLOAD_OFFLINE = "offline"


class DeliveryError(Exception):
    """The broker was unreachable or a publish failed. Never reported as success."""


# --------------------------------------------------------------------------- #
# Topic helpers
# --------------------------------------------------------------------------- #


def node_id(pier_id: str) -> str:
    """The discovery node id shared by a pier's entities."""
    return f"pierpressure_{pier_id}"


def availability_topic(base_topic: str) -> str:
    return f"{base_topic}/status"


def verdict_state_topic(base_topic: str, pier_id: str) -> str:
    return f"{base_topic}/{pier_id}/verdict/state"


def attributes_topic(base_topic: str, pier_id: str) -> str:
    return f"{base_topic}/{pier_id}/verdict/attributes"


def refresh_command_topic(base_topic: str, pier_id: str) -> str:
    return f"{base_topic}/{pier_id}/refresh/command"


def top_target_state_topic(base_topic: str, pier_id: str) -> str:
    return f"{base_topic}/{pier_id}/top_target/state"


def top_target_attributes_topic(base_topic: str, pier_id: str) -> str:
    return f"{base_topic}/{pier_id}/top_target/attributes"


def discovery_topic(discovery_prefix: str, component: str, pier_id: str, object_id: str) -> str:
    return f"{discovery_prefix}/{component}/{node_id(pier_id)}/{object_id}/config"


def _device_block(pier_id: str) -> dict[str, Any]:
    """The shared device block so a pier's entities group under one HA device."""
    return {
        "identifiers": [node_id(pier_id)],
        "name": f"PierPressure {pier_id}",
        "manufacturer": "PierPressure",
        "model": "night-verdict",
    }


# --------------------------------------------------------------------------- #
# Discovery payload builders (design D5, D6)
# --------------------------------------------------------------------------- #


def build_verdict_discovery(pier_id: str, base_topic: str) -> dict[str, Any]:
    return {
        "name": "Verdict",
        "has_entity_name": True,
        "unique_id": f"{node_id(pier_id)}_verdict",
        "state_topic": verdict_state_topic(base_topic, pier_id),
        "json_attributes_topic": attributes_topic(base_topic, pier_id),
        "availability_topic": availability_topic(base_topic),
        "payload_available": PAYLOAD_ONLINE,
        "payload_not_available": PAYLOAD_OFFLINE,
        "icon": "mdi:telescope",
        "device": _device_block(pier_id),
    }


def build_score_discovery(pier_id: str, base_topic: str) -> dict[str, Any]:
    """The score sensor.

    Its state reads the number from the attributes JSON; its availability is a
    two-entry list with ``availability_mode: all`` — the shared LWT topic AND an
    ``availability_template`` requiring a non-null score — so a gated NO-GO (null
    score) renders as ``unavailable`` rather than ``0`` (design D6).
    """
    attrs = attributes_topic(base_topic, pier_id)
    return {
        "name": "Score",
        "has_entity_name": True,
        "unique_id": f"{node_id(pier_id)}_score",
        "state_topic": attrs,
        "value_template": "{{ value_json.score }}",
        "availability_mode": "all",
        "availability": [
            {
                "topic": availability_topic(base_topic),
                "payload_available": PAYLOAD_ONLINE,
                "payload_not_available": PAYLOAD_OFFLINE,
            },
            {
                "topic": attrs,
                "value_template": ("{{ 'online' if value_json.score is not none else 'offline' }}"),
            },
        ],
        "device": _device_block(pier_id),
    }


def build_top_target_discovery(pier_id: str, base_topic: str) -> dict[str, Any]:
    """The top-target sensor (spec ha-delivery; design D6).

    Its state is the top-ranked target's name (its designation when the catalog
    records no common name); the full ordered list and the top target's fields ride
    along as JSON attributes. Availability is a two-entry list with
    ``availability_mode: all`` — the shared LWT topic AND a template requiring a
    non-empty list — so an empty target list renders the sensor ``unavailable``
    rather than a placeholder, mirroring how the score sensor handles a null score.
    """
    attrs = top_target_attributes_topic(base_topic, pier_id)
    return {
        "name": "Top target",
        "has_entity_name": True,
        "unique_id": f"{node_id(pier_id)}_top_target",
        "state_topic": top_target_state_topic(base_topic, pier_id),
        "json_attributes_topic": attrs,
        "availability_mode": "all",
        "availability": [
            {
                "topic": availability_topic(base_topic),
                "payload_available": PAYLOAD_ONLINE,
                "payload_not_available": PAYLOAD_OFFLINE,
            },
            {
                "topic": attrs,
                "value_template": ("{{ 'online' if value_json.count | int > 0 else 'offline' }}"),
            },
        ],
        "icon": "mdi:telescope",
        "device": _device_block(pier_id),
    }


def top_target_state(document: VerdictDocument) -> str:
    """The top target's display name for the sensor state (id when unnamed)."""
    if not document.targets:
        return ""
    top = document.targets[0]
    return top.name if top.name else top.id


def top_target_attributes(document: VerdictDocument) -> dict[str, Any]:
    """The JSON attributes payload: the ordered list, the top target, and a count.

    ``count`` drives the availability template, so a dashboard card sees the full
    ordered ranking while the entity itself goes unavailable when nothing ranks.
    """
    import json

    targets = [json.loads(target.model_dump_json()) for target in document.targets]
    return {
        "count": len(targets),
        "top": targets[0] if targets else None,
        "targets": targets,
    }


def build_refresh_discovery(pier_id: str, base_topic: str) -> dict[str, Any]:
    return {
        "name": "Refresh",
        "has_entity_name": True,
        "unique_id": f"{node_id(pier_id)}_refresh",
        "command_topic": refresh_command_topic(base_topic, pier_id),
        "availability_topic": availability_topic(base_topic),
        "payload_available": PAYLOAD_ONLINE,
        "payload_not_available": PAYLOAD_OFFLINE,
        "icon": "mdi:refresh",
        "device": _device_block(pier_id),
    }


# --------------------------------------------------------------------------- #
# The MQTT client protocol (satisfied by paho and by the test fake)
# --------------------------------------------------------------------------- #


class MqttClient(Protocol):
    """The subset of the paho client API this adapter uses."""

    on_message: Any

    def will_set(
        self, topic: str, payload: Any = ..., qos: int = ..., retain: bool = ...
    ) -> Any: ...

    def connect(self, host: str, port: int = ..., keepalive: int = ...) -> Any: ...

    def loop_start(self) -> Any: ...

    def loop_stop(self) -> Any: ...

    def subscribe(self, topic: str, qos: int = ...) -> Any: ...

    def publish(
        self, topic: str, payload: Any = ..., qos: int = ..., retain: bool = ...
    ) -> Any: ...

    def disconnect(self) -> Any: ...


def _new_paho_client() -> MqttClient:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# The delivery adapter
# --------------------------------------------------------------------------- #


class MqttDelivery:
    """Publishes verdict documents to Home Assistant over MQTT discovery.

    Delivery consumes an already-produced document; it never computes one.
    """

    def __init__(self, config: MqttConfig, client: MqttClient | None = None) -> None:
        self._config = config
        self._client: MqttClient = client if client is not None else _new_paho_client()
        self._refresh_callback: Callable[[str], None] | None = None
        self._topic_to_pier: dict[str, str] = {}

    @property
    def base_topic(self) -> str:
        return self._config.base_topic

    @property
    def discovery_prefix(self) -> str:
        return self._config.discovery_prefix

    def connect(self) -> None:
        """Register the retained offline LWT, connect, and publish retained online.

        Any failure to reach the broker is raised as :class:`DeliveryError` — it
        is never reported as success (design D9).
        """
        status = availability_topic(self._config.base_topic)
        try:
            if self._config.username is not None:
                # paho accepts username/password before connect.
                set_creds = getattr(self._client, "username_pw_set", None)
                if callable(set_creds):
                    set_creds(self._config.username, self._config.password)
            self._client.will_set(status, PAYLOAD_OFFLINE, qos=1, retain=True)
            self._client.connect(self._config.host, self._config.port)
            self._client.loop_start()
        except (OSError, ValueError) as exc:
            raise DeliveryError(f"Could not connect to MQTT broker: {exc}") from exc
        self._publish(status, PAYLOAD_ONLINE, retain=True)

    def _publish(self, topic: str, payload: str, *, retain: bool) -> None:
        info = self._client.publish(topic, payload, qos=1, retain=retain)
        rc = getattr(info, "rc", mqtt.MQTT_ERR_SUCCESS)
        if rc != mqtt.MQTT_ERR_SUCCESS:
            raise DeliveryError(f"Publish to {topic!r} failed with rc={rc}")

    def publish_verdict(self, document: VerdictDocument) -> None:
        """Publish discovery, state, and attributes for the document's pier.

        Discovery config, verdict state, and the JSON attributes are all
        published retained so a Home Assistant restart re-reads the last verdict
        and re-creates the entities. ``unique_id``/topics derive from the pier id,
        so re-publishing updates the same entities rather than creating duplicates.
        """
        import json

        pier = document.pier
        base = self._config.base_topic
        prefix = self._config.discovery_prefix

        self._publish(
            discovery_topic(prefix, "sensor", pier, "verdict"),
            json.dumps(build_verdict_discovery(pier, base)),
            retain=True,
        )
        self._publish(
            discovery_topic(prefix, "sensor", pier, "score"),
            json.dumps(build_score_discovery(pier, base)),
            retain=True,
        )
        self._publish(
            discovery_topic(prefix, "button", pier, "refresh"),
            json.dumps(build_refresh_discovery(pier, base)),
            retain=True,
        )
        self._publish(
            discovery_topic(prefix, "sensor", pier, "top_target"),
            json.dumps(build_top_target_discovery(pier, base)),
            retain=True,
        )
        self._publish(verdict_state_topic(base, pier), document.verdict.value, retain=True)
        self._publish(attributes_topic(base, pier), document.to_json(), retain=True)
        self._publish(top_target_state_topic(base, pier), top_target_state(document), retain=True)
        self._publish(
            top_target_attributes_topic(base, pier),
            json.dumps(top_target_attributes(document)),
            retain=True,
        )

    def subscribe_refresh(self, pier_ids: Iterable[str], callback: Callable[[str], None]) -> None:
        """Subscribe to each pier's refresh command topic.

        The callback (invoked from paho's network thread) receives the pier id
        parsed from the command topic. It must not publish directly; per design
        D7 it enqueues the pier id for the main thread.
        """
        self._refresh_callback = callback
        base = self._config.base_topic
        for pier_id in pier_ids:
            topic = refresh_command_topic(base, pier_id)
            self._topic_to_pier[topic] = pier_id
            self._client.subscribe(topic)
        self._client.on_message = self._on_message

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        pier_id = self._topic_to_pier.get(message.topic)
        if pier_id is not None and self._refresh_callback is not None:
            self._refresh_callback(pier_id)

    def close(self) -> None:
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except (OSError, ValueError):  # pragma: no cover - best-effort shutdown
            logger.warning("Error during MQTT shutdown", exc_info=True)
