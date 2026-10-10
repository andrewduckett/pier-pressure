"""MQTT-discovery delivery adapter (design D5, D6, D9).

Builds per-pier discovery payloads (verdict sensor, score sensor, refresh
button), publishes verdict state/attributes/availability, and subscribes to each
pier's refresh command topic. The MQTT client is injectable so tests can drive a
fake client with no broker.

After a broker outage, paho reconnects in the background. The adapter then
subscribes to the refresh topics again and tells the service, which publishes
each pier's last retained messages again (:meth:`MqttDelivery.replay`), then
``online`` (reconnect-restores-delivery).

A publish never raises. While the connection is down, the adapter records each
retained message but holds it from paho; the replay sends it after the reconnect.
A message paho refuses is logged (publish-failure-resilience).

A clean disconnect skips the last-will, so :meth:`MqttDelivery.close` publishes
the retained ``offline`` itself while connected (stop-goes-offline).

Topic scheme (design D5), for base topic ``B`` and discovery prefix ``P``:

===========================  ====================================================  ======
Purpose                      Topic                                                 Retain
===========================  ====================================================  ======
Verdict discovery cfg        ``P/sensor/pierpressure_<pier>/verdict/config``       yes
Score discovery cfg          ``P/sensor/pierpressure_<pier>/score/config``         yes
Refresh discovery cfg        ``P/button/pierpressure_<pier>/refresh/config``       yes
Rank n discovery cfg         ``P/sensor/pierpressure_<pier>/target_<n>/config``    yes
Health discovery cfg         ``P/sensor/pierpressure_<pier>/<key>_health/config``  yes
Verdict state                ``B/<pier>/verdict/state``                            yes
Document attributes (JSON)   ``B/<pier>/verdict/attributes``                       yes
Rank n state                 ``B/<pier>/target_<n>/state``                         yes
Rank n attributes (JSON)     ``B/<pier>/target_<n>/attributes``                    yes
Health state                 ``B/<pier>/health/<key>/state``                       yes
Health attributes (JSON)     ``B/<pier>/health/<key>/attributes``                  yes
Refresh command              ``B/<pier>/refresh/command``                          no
Availability (LWT)           ``B/status``                                          yes
===========================  ====================================================  ======
"""

from __future__ import annotations

import logging
import sys
import threading
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol

import paho.mqtt.client as mqtt

from pierpressure.core.config import MqttConfig
from pierpressure.core.model import Target, VerdictDocument
from pierpressure.core.ranking import TOP_N
from pierpressure.health import ProviderHealth

logger = logging.getLogger(__name__)

# The rank sensors, Target 1 to Target TOP_N: one per place the ranking can emit.
RANKS = range(1, TOP_N + 1)

PAYLOAD_ONLINE = "online"
PAYLOAD_OFFLINE = "offline"

# How long a stop waits for the broker to confirm ``offline`` (stop-goes-offline D2).
OFFLINE_WAIT_SECONDS = 2.0


class DeliveryError(Exception):
    """The delivery adapter could not start: a bad broker address, or a rejected login."""


class LoginRejected(DeliveryError):
    """The broker refused the first connection because of the login (retry-broker-connection D3).

    Retrying cannot fix a wrong password or a missing permission, so the process
    stops. A login rejected during a later reconnect is only logged, with the same
    message (reconnect-restores-delivery D5).
    """

    def __init__(self, broker: str, reason: str, advice: str | None = None) -> None:
        self.broker = broker
        self.reason = reason
        super().__init__(login_rejected_message(broker, reason, advice))


def login_rejected_message(broker: str, reason: str, advice: str | None = None) -> str:
    """Name the broker and its reason, then give ``advice``: by default, check the file's login.

    The delivery adapter passes other advice when the login came from somewhere else.
    """
    rejected = f"The MQTT broker at {broker} rejected the login"
    return f"{rejected}: {reason.lower()}. {advice or _LOGIN_ADVICE}"


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


def rank_target_state_topic(base_topic: str, pier_id: str, rank: int) -> str:
    return f"{base_topic}/{pier_id}/target_{rank}/state"


def rank_target_attributes_topic(base_topic: str, pier_id: str, rank: int) -> str:
    return f"{base_topic}/{pier_id}/target_{rank}/attributes"


def narrative_state_topic(base_topic: str, pier_id: str) -> str:
    return f"{base_topic}/{pier_id}/narrative/state"


def narrative_attributes_topic(base_topic: str, pier_id: str) -> str:
    return f"{base_topic}/{pier_id}/narrative/attributes"


def health_state_topic(base_topic: str, pier_id: str, provider_key: str) -> str:
    return f"{base_topic}/{pier_id}/health/{provider_key}/state"


def health_attributes_topic(base_topic: str, pier_id: str, provider_key: str) -> str:
    return f"{base_topic}/{pier_id}/health/{provider_key}/attributes"


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


def target_display_name(target: Target) -> str:
    """A target's display name: its common name, or its id when unnamed (design D4).

    The top-target and rank sensors share this rule so the two can't drift apart.
    """
    return target.name if target.name else target.id


def top_target_state(document: VerdictDocument) -> str:
    """The top target's display name for the sensor state (id when unnamed)."""
    if not document.targets:
        return ""
    return target_display_name(document.targets[0])


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


def build_rank_target_discovery(pier_id: str, base_topic: str, rank: int) -> dict[str, Any]:
    """The sensor for one rank of the target list, Target 1 to Target TOP_N.

    Its state is the display name of the target at that rank; the rank and the
    target's fields ride along as JSON attributes. Availability is a two-entry list
    with ``availability_mode: all`` — the shared LWT topic AND a template requiring
    the attributes' ``available`` flag — so a rank with no target tonight renders
    ``unavailable`` rather than a placeholder, like the narrative sensor (design D2).
    """
    attrs = rank_target_attributes_topic(base_topic, pier_id, rank)
    return {
        "name": f"Target {rank}",
        "has_entity_name": True,
        "unique_id": f"{node_id(pier_id)}_target_{rank}",
        "state_topic": rank_target_state_topic(base_topic, pier_id, rank),
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
                "value_template": ("{{ 'online' if value_json.available else 'offline' }}"),
            },
        ],
        "icon": "mdi:telescope",
        "device": _device_block(pier_id),
    }


def rank_target_state(document: VerdictDocument, rank: int) -> str:
    """The display name of the target at ``rank`` (1-based), id when unnamed.

    An empty rank publishes an empty string; its availability makes it unavailable.
    """
    if rank > len(document.targets):
        return ""
    return target_display_name(document.targets[rank - 1])


def rank_target_attributes(document: VerdictDocument, rank: int) -> dict[str, Any]:
    """The JSON attributes payload for one rank: the flag, the rank, then its target.

    The target's fields sit at the top level so a card can read each one directly;
    a field that is an object in the document (``window``) stays an object. An
    empty rank carries only ``available: false`` and its rank.
    """
    import json

    if rank > len(document.targets):
        return {"available": False, "rank": rank}
    target = json.loads(document.targets[rank - 1].model_dump_json())
    payload = {"available": True, "rank": rank, **target}
    # Re-assert the adapter's keys so a future target field of the same name can't
    # replace them; ``update`` keeps them first in the payload.
    payload.update(available=True, rank=rank)
    return payload


def build_narrative_discovery(pier_id: str, base_topic: str) -> dict[str, Any]:
    """The optional narrative sensor (spec ha-delivery; ADR-0011; design D2).

    It carries the LLM-generated prose that explains an already-computed verdict.
    Home Assistant limits entity state values in length, so the state topic carries
    only a short marker while the full prose rides along in the JSON attributes for
    a dashboard card. Availability is a two-entry list with ``availability_mode:
    all`` — the shared LWT topic AND a template requiring the attributes'
    ``available`` flag — so a recompute with no narrative (provider failed or
    disabled mid-run) renders the sensor ``unavailable`` rather than showing an
    empty, placeholder, or stale value, mirroring the score and top-target sensors.
    """
    attrs = narrative_attributes_topic(base_topic, pier_id)
    return {
        "name": "Narrative",
        "has_entity_name": True,
        "unique_id": f"{node_id(pier_id)}_narrative",
        "state_topic": narrative_state_topic(base_topic, pier_id),
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
                "value_template": ("{{ 'online' if value_json.available else 'offline' }}"),
            },
        ],
        "icon": "mdi:text-long",
        "device": _device_block(pier_id),
    }


def narrative_state(narrative: str | None) -> str:
    """The short state marker for the narrative sensor (the prose rides in attrs)."""
    return "ready" if narrative else "unavailable"


def narrative_attributes(narrative: str | None) -> dict[str, Any]:
    """The JSON attributes payload: the availability flag and the full prose.

    ``available`` drives the sensor's availability template, so a ``None`` narrative
    publishes an explicit unavailable marker rather than leaving an earlier retained
    narrative shown as current (spec ha-delivery).
    """
    return {"available": narrative is not None, "narrative": narrative}


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


def build_health_discovery(
    pier_id: str, base_topic: str, provider_key: str, provider_name: str
) -> dict[str, Any]:
    """A provider's health sensor (spec ha-delivery; provider-health-entities D5).

    A diagnostic timestamp sensor whose state is the provider's last successful
    fetch. Availability is the shared last-will topic only, with no template, so a
    failing provider keeps showing its last success: the age of that time is the
    signal.
    """
    return {
        "name": f"{provider_name} health",
        "has_entity_name": True,
        "unique_id": f"{node_id(pier_id)}_{provider_key}_health",
        "state_topic": health_state_topic(base_topic, pier_id, provider_key),
        "json_attributes_topic": health_attributes_topic(base_topic, pier_id, provider_key),
        "device_class": "timestamp",
        "entity_category": "diagnostic",
        "availability_topic": availability_topic(base_topic),
        "payload_available": PAYLOAD_ONLINE,
        "payload_not_available": PAYLOAD_OFFLINE,
        "device": _device_block(pier_id),
    }


def _iso(moment: datetime | None) -> str | None:
    """UTC ISO 8601 with its ``+00:00`` offset, to the whole second; ``None`` stays null.

    A time with no time zone is rejected: Home Assistant's timestamp sensor needs
    an offset, and guessing one would misreport the time.
    """
    if moment is None:
        return None
    if moment.tzinfo is None:
        raise ValueError(f"health time {moment!r} has no time zone")
    return moment.astimezone(UTC).isoformat(timespec="seconds")


def health_state(health: ProviderHealth) -> str:
    """The last successful fetch, or the literal ``None``, which reads as unknown.

    Publishing ``None`` actively replaces any retained time from before a restart.
    """
    return _iso(health.last_success) or "None"


def health_attributes(health: ProviderHealth) -> dict[str, Any]:
    """The JSON attributes: the provider, its role, and the latest fetch."""
    return {
        "provider": health.name,
        "role": health.role,
        "tracking_since": _iso(health.tracking_since),
        "status": health.status,
        "last_fetch": _iso(health.last_fetch),
        "last_error": health.last_error,
        "issued_at": _iso(health.issued_at),
    }


# --------------------------------------------------------------------------- #
# The MQTT client protocol (satisfied by paho and by the test fake)
# --------------------------------------------------------------------------- #


class MqttClient(Protocol):
    """The subset of the paho client API this adapter uses."""

    on_message: Any
    on_pre_connect: Any
    on_connect: Any
    on_connect_fail: Any
    on_disconnect: Any
    on_subscribe: Any

    def will_set(
        self, topic: str, payload: Any = ..., qos: int = ..., retain: bool = ...
    ) -> Any: ...

    def reconnect_delay_set(self, min_delay: int = ..., max_delay: int = ...) -> Any: ...

    def connect_async(self, host: str, port: int = ..., keepalive: int = ...) -> Any: ...

    def loop_start(self) -> Any: ...

    def loop_stop(self) -> Any: ...

    def subscribe(self, topic: str, qos: int = ...) -> tuple[int, int | None]:
        """Return the result code and the message ID (``None`` when nothing was sent)."""
        ...

    def publish(
        self, topic: str, payload: Any = ..., qos: int = ..., retain: bool = ...
    ) -> Any: ...

    def disconnect(self) -> Any: ...


def _new_paho_client() -> MqttClient:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # type: ignore[attr-defined]


def _network_thread_running(client: MqttClient) -> bool:
    """Whether paho's network thread is running (retry-broker-connection D2).

    paho exposes the thread only as the private ``_thread``, and sets it back to
    ``None`` when the thread ends. ``tests/test_paho_contract.py`` pins this.
    """
    return getattr(client, "_thread", None) is not None


# --------------------------------------------------------------------------- #
# Waiting for the broker at startup (retry-broker-connection)
# --------------------------------------------------------------------------- #

# paho pauses between attempts, doubling from the first pause up to the limit.
FIRST_PAUSE_SECONDS = 1
PAUSE_LIMIT_SECONDS = 120

# How often ``connect``, then the watcher, checks that paho's network thread is
# still running.
_WAIT_SLICE_SECONDS = 1.0

# paho's names for the refusals that retrying cannot fix. Both get the same advice,
# because Mosquitto answers a wrong password with "Not authorized".
_LOGIN_REJECTIONS = ("Bad user name or password", "Not authorized")
_LOGIN_ADVICE = "Check mqtt.username and mqtt.password, and the user's permissions on the broker."


class _Phase(Enum):
    """Where the connection is (reconnect-restores-delivery D1). Only paho's thread moves it."""

    STARTING = "starting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


# --------------------------------------------------------------------------- #
# The delivery adapter
# --------------------------------------------------------------------------- #


class MqttDelivery:
    """Publishes verdict documents to Home Assistant over MQTT discovery.

    Delivery consumes an already-produced document; it never computes one. It
    remembers each pier's last retained messages, so it can publish them again
    after a reconnect without a new verdict (reconnect-restores-delivery D4).
    """

    def __init__(
        self,
        config: MqttConfig,
        client: MqttClient | None = None,
        *,
        manage_narrative: bool = False,
        login_advice: str | None = None,
    ) -> None:
        self._config = config
        # What to check when the broker rejects the login, at startup or during a
        # reconnect (reconnect-restores-delivery D5). ``None`` gives the default.
        self._login_advice = login_advice
        self._client: MqttClient = client if client is not None else _new_paho_client()
        self._refresh_callback: Callable[[str], None] | None = None
        self._topic_to_pier: dict[str, str] = {}
        self._reconnect_listener: Callable[[], None] | None = None
        # The topic of each subscription the broker has not yet answered, by
        # message ID (reconnect-restores-delivery D2). The subscription lock guards
        # it and the topic map: the main thread and paho's thread both subscribe.
        self._unanswered: dict[int, str] = {}
        self._subscription_lock = threading.Lock()
        # Each pier's retained messages, from topic to the last payload, in the
        # order the topics were first published (reconnect-restores-delivery D4).
        self._retained: dict[str, dict[str, str]] = {}
        # Told once, from config, whether this delivery owns the narrative entity
        # (design D2/D7). When false, no narrative discovery or state is ever
        # published, so a default deployment is byte-identical to the pre-feature
        # output and gains no entity.
        self._manage_narrative = manage_narrative
        # Startup wait (retry-broker-connection D2): paho's handlers store one
        # outcome, then set the event. ``None`` means the broker accepted.
        self._outcome_ready = threading.Event()
        self._rejection: str | None = None
        # Whether the current attempt already has its warning (D4).
        self._attempt_logged = False
        self._phase = _Phase.STARTING
        # Keeps paho's thread running after startup (reconnect-restores-delivery D7).
        self._watcher: threading.Thread | None = None
        self._stop_watching = threading.Event()
        # Set by close(), so its own DISCONNECT is not logged as a lost connection.
        self._closing = False
        # Main thread only. Whether paho refused the last ``online``, which has no
        # replay record; and whether a refusal is logged since the last success.
        self._online_refused = False
        self._refusal_logged = False

    @property
    def base_topic(self) -> str:
        return self._config.base_topic

    @property
    def discovery_prefix(self) -> str:
        return self._config.discovery_prefix

    def connect(self) -> None:
        """Register the retained offline LWT, then wait until the broker accepts.

        paho tries in the background, pausing between attempts, and this method
        returns once the broker accepts (retry-broker-connection D1, D2). Nothing
        is published before then. The service publishes its startup health reset
        first, then calls :meth:`go_online` (provider-health-entities D4).

        Raises :class:`LoginRejected` when the broker rejects the login, which
        retrying cannot fix (D3). Once the broker accepts, a watcher thread keeps
        paho's thread running until :meth:`close` (reconnect-restores-delivery D7).
        """
        status = availability_topic(self._config.base_topic)
        if self._config.username is not None:
            # paho accepts username/password before connect.
            set_creds = getattr(self._client, "username_pw_set", None)
            if callable(set_creds):
                set_creds(self._config.username, self._config.password)
        self._client.will_set(status, PAYLOAD_OFFLINE, qos=1, retain=True)
        self._client.on_pre_connect = self._on_pre_connect
        self._client.on_connect = self._on_connect
        self._client.on_connect_fail = self._on_connect_fail
        self._client.on_disconnect = self._on_disconnect
        self._client.on_subscribe = self._on_subscribe
        self._client.reconnect_delay_set(FIRST_PAUSE_SECONDS, PAUSE_LIMIT_SECONDS)
        try:
            self._client.connect_async(self._config.host, self._config.port)
        except ValueError as exc:
            raise DeliveryError(f"Could not connect to MQTT broker: {exc}") from exc
        self._client.loop_start()
        self._wait_for_outcome()

        if self._rejection is not None:
            self._client.loop_stop()
            raise LoginRejected(self._broker, self._rejection, self._login_advice)
        self._watcher = threading.Thread(
            target=self._watch_network_thread, name="pierpressure-mqtt-watcher", daemon=True
        )
        self._watcher.start()

    def _wait_for_outcome(self) -> None:
        """Wait for the broker's answer, restarting paho's thread if it ends (D2).

        One of paho's immediate tries can end its thread with no callback. A new
        thread pauses, then tries again. A restart happens at most once a slice.
        """
        while not self._outcome_ready.is_set():
            self._restart_stopped_network_thread()
            self._outcome_ready.wait(_WAIT_SLICE_SECONDS)

    def _watch_network_thread(self) -> None:
        """Start paho's thread again whenever it ends, until :meth:`close` (D7).

        One of paho's immediate tries can end its thread with no callback during a
        reconnect, as at startup. If the thread is running, ``loop_start`` starts
        nothing, so a race between the check and the call is harmless.
        """
        while not self._stop_watching.wait(_WAIT_SLICE_SECONDS):
            self._restart_stopped_network_thread()

    def _restart_stopped_network_thread(self) -> None:
        """Log the ended attempt and start paho's thread again, if it has ended."""
        if not _network_thread_running(self._client):
            self._log_failed_attempt("network thread stopped")
            self._client.loop_start()

    @property
    def _broker(self) -> str:
        return f"{self._config.host}:{self._config.port}"

    # paho calls these handlers on its network thread, at startup and on every
    # reconnect (reconnect-restores-delivery D1). They log, store the startup
    # outcome, subscribe again and tell the service. They never publish: the main
    # thread does all publishing (ADR-0012).

    def _on_pre_connect(self, _client: Any, _userdata: Any) -> None:
        if self._phase is not _Phase.CONNECTED:
            self._attempt_logged = False

    def _on_connect(
        self, _client: Any, _userdata: Any, _flags: Any, reason: Any, _properties: Any
    ) -> None:
        # Every answer after the first is a reconnect, even when paho reconnected
        # without first reporting the lost connection.
        if self._phase is _Phase.STARTING:
            self._on_first_answer(reason)
        else:
            self._on_reconnect_answer(reason)

    def _on_first_answer(self, reason: Any) -> None:
        """Store the startup outcome for ``connect`` (retry-broker-connection D2, D3)."""
        if self._outcome_ready.is_set():
            return
        if not reason.is_failure:
            self._phase = _Phase.CONNECTED
            self._outcome_ready.set()
            return
        if reason.getName() in _LOGIN_REJECTIONS:
            self._rejection = reason.getName()
            self._outcome_ready.set()
            return
        self._log_failed_attempt(str(reason))

    def _on_reconnect_answer(self, reason: Any) -> None:
        """Restore delivery on an accept; otherwise log and let paho try again (D1, D2)."""
        if not reason.is_failure:
            logger.info("Reconnected to the MQTT broker at %s", self._broker)
            self._phase = _Phase.CONNECTED
            with self._subscription_lock:
                # The broker's answers to earlier subscriptions went with the old session.
                self._unanswered.clear()
            self._subscribe_all()
            if self._reconnect_listener is not None:
                self._reconnect_listener()
            return
        if reason.getName() in _LOGIN_REJECTIONS:
            # The same login worked before, so the cause may be temporary (D5).
            self._attempt_logged = True
            message = login_rejected_message(self._broker, reason.getName(), self._login_advice)
            logger.error("%s Trying again.", message)
            return
        self._log_failed_attempt(str(reason))

    def _on_connect_fail(self, _client: Any, _userdata: Any) -> None:
        if not self._awaiting_answer:
            return
        # paho calls this inside its ``except OSError`` block, so the error is
        # still being handled. Only its class name is logged.
        error = sys.exc_info()[0]
        self._log_failed_attempt(error.__name__ if error is not None else "connection failed")

    def _on_disconnect(
        self, _client: Any, _userdata: Any, _flags: Any, _reason: Any, _properties: Any
    ) -> None:
        if self._closing:
            return
        if self._phase is _Phase.CONNECTED:
            logger.warning(
                "Lost the connection to the MQTT broker at %s; trying again", self._broker
            )
            self._phase = _Phase.RECONNECTING
        elif self._awaiting_answer:
            self._log_failed_attempt("connection closed before the broker answered")

    @property
    def _awaiting_answer(self) -> bool:
        """Whether an attempt is under way whose failure needs a warning."""
        if self._phase is _Phase.STARTING:
            return not self._outcome_ready.is_set()
        return self._phase is _Phase.RECONNECTING

    def _log_failed_attempt(self, reason: str) -> None:
        """Log one warning per failed attempt, whichever handler sees it first (D4)."""
        if self._attempt_logged:
            return
        self._attempt_logged = True
        logger.warning(
            "Could not connect to the MQTT broker at %s (%s); trying again", self._broker, reason
        )

    def go_online(self) -> None:
        """Publish the retained ``online`` availability for every entity.

        If paho refuses it, the next :meth:`publish_verdict` publishes it again.
        """
        sent = self._send(availability_topic(self._config.base_topic), PAYLOAD_ONLINE, retain=True)
        self._online_refused = not sent

    def replay(self) -> None:
        """Publish each pier's last retained messages again, after a reconnect (D4).

        Each topic goes out with the payload it last had, in the order the topics
        were first published, so discovery configs precede states. The availability
        topic belongs to no pier and is not replayed; the service publishes it after.
        """
        for retained in list(self._retained.values()):
            for topic, payload in list(retained.items()):
                self._send(topic, payload, retain=True)

    def _publish(self, topic: str, payload: str, *, retain: bool, pier: str | None = None) -> None:
        """Record a pier's retained message for :meth:`replay` (D4), then send it.

        The record comes first, whatever paho then says, so the replay always has
        the latest payload (publish-failure-resilience D2). Only the main thread
        publishes and replays, so the record needs no lock.
        """
        if retain and pier is not None:
            self._retained.setdefault(pier, {})[topic] = payload
        self._send(topic, payload, retain=retain)

    def _send(self, topic: str, payload: str, *, retain: bool) -> bool:
        """Hand one message to paho, unless the connection is down. Never raises.

        Returns ``False`` only when paho refused the message.

        While the connection is down, the message is held: the replay after the
        reconnect sends the latest payload of each pier's topics, then the service
        publishes ``online`` (publish-failure-resilience D1). ``_phase`` is read
        without a lock; a stale read only hands paho a message it queues.

        paho returns ``MQTT_ERR_NO_CONN`` when it saw the drop first. It keeps the
        message and sends it after the reconnect, and the drop is logged already.
        Any other failure is logged, and the next replay or interval repairs the
        topic (publish-failure-resilience D3). Only the first refusal since the last
        success is a warning, so a lasting refusal does not flood the log.
        """
        if self._phase is _Phase.RECONNECTING:
            return True
        info = self._client.publish(topic, payload, qos=1, retain=retain)
        rc = getattr(info, "rc", mqtt.MQTT_ERR_SUCCESS)
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self._refusal_logged = False
            return True
        if rc == mqtt.MQTT_ERR_NO_CONN:
            logger.debug("paho queued the publish to %r until it reconnects", topic)
            return True
        level = logging.DEBUG if self._refusal_logged else logging.WARNING
        self._refusal_logged = True
        logger.log(
            level,
            "The MQTT client did not send the publish to %r (%s); "
            "the next update publishes it again",
            topic,
            mqtt.error_string(rc),
        )
        return False

    def publish_verdict(self, document: VerdictDocument, narrative: str | None = None) -> None:
        """Publish discovery, state, and attributes for the document's pier.

        Discovery config, verdict state, and the JSON attributes are all
        published retained so a Home Assistant restart re-reads the last verdict
        and re-creates the entities. ``unique_id``/topics derive from the pier id,
        so re-publishing updates the same entities rather than creating duplicates.

        ``narrative`` is the optional LLM prose for this recompute. It is published
        only when this delivery manages the narrative entity (from config); when it
        does, the entity is always published — with the prose when present, and with
        an explicit unavailable marker when absent — so an earlier retained narrative
        is never left shown as current (design D2, ADR-0011). The narrative's absence
        or disablement never blocks or alters the other entities.
        """
        import json

        pier = document.pier
        base = self._config.base_topic
        prefix = self._config.discovery_prefix

        self._publish(
            discovery_topic(prefix, "sensor", pier, "verdict"),
            json.dumps(build_verdict_discovery(pier, base)),
            retain=True,
            pier=pier,
        )
        self._publish(
            discovery_topic(prefix, "sensor", pier, "score"),
            json.dumps(build_score_discovery(pier, base)),
            retain=True,
            pier=pier,
        )
        self._publish(
            discovery_topic(prefix, "button", pier, "refresh"),
            json.dumps(build_refresh_discovery(pier, base)),
            retain=True,
            pier=pier,
        )
        self._publish(
            discovery_topic(prefix, "sensor", pier, "top_target"),
            json.dumps(build_top_target_discovery(pier, base)),
            retain=True,
            pier=pier,
        )
        for rank in RANKS:
            self._publish(
                discovery_topic(prefix, "sensor", pier, f"target_{rank}"),
                json.dumps(build_rank_target_discovery(pier, base, rank)),
                retain=True,
                pier=pier,
            )
        self._publish(
            verdict_state_topic(base, pier), document.verdict.value, retain=True, pier=pier
        )
        self._publish(attributes_topic(base, pier), document.to_json(), retain=True, pier=pier)
        self._publish(
            top_target_state_topic(base, pier), top_target_state(document), retain=True, pier=pier
        )
        self._publish(
            top_target_attributes_topic(base, pier),
            json.dumps(top_target_attributes(document)),
            retain=True,
            pier=pier,
        )
        # Every rank is written on every publish, filled or not, so a shrinking list
        # never leaves an earlier target retained (design D3).
        for rank in RANKS:
            self._publish(
                rank_target_state_topic(base, pier, rank),
                rank_target_state(document, rank),
                retain=True,
                pier=pier,
            )
            self._publish(
                rank_target_attributes_topic(base, pier, rank),
                json.dumps(rank_target_attributes(document, rank)),
                retain=True,
                pier=pier,
            )
        if self._manage_narrative:
            self._publish(
                discovery_topic(prefix, "sensor", pier, "narrative"),
                json.dumps(build_narrative_discovery(pier, base)),
                retain=True,
                pier=pier,
            )
            self._publish(
                narrative_state_topic(base, pier),
                narrative_state(narrative),
                retain=True,
                pier=pier,
            )
            self._publish(
                narrative_attributes_topic(base, pier),
                json.dumps(narrative_attributes(narrative)),
                retain=True,
                pier=pier,
            )
        if self._online_refused:
            # ``online`` has no replay record, so this update repairs it.
            self.go_online()

    def publish_health(self, pier_id: str, healths: Iterable[ProviderHealth]) -> None:
        """Publish discovery, state, and attributes for each provider's health.

        All retained, so a Home Assistant restart re-reads them. Health travels
        beside the verdict document and never inside it (ADR-0015).
        """
        import json

        base = self._config.base_topic
        prefix = self._config.discovery_prefix
        for health in healths:
            self._publish(
                discovery_topic(prefix, "sensor", pier_id, f"{health.key}_health"),
                json.dumps(build_health_discovery(pier_id, base, health.key, health.name)),
                retain=True,
                pier=pier_id,
            )
            self._publish(
                health_state_topic(base, pier_id, health.key),
                health_state(health),
                retain=True,
                pier=pier_id,
            )
            self._publish(
                health_attributes_topic(base, pier_id, health.key),
                json.dumps(health_attributes(health)),
                retain=True,
                pier=pier_id,
            )

    def subscribe_refresh(self, pier_ids: Iterable[str], callback: Callable[[str], None]) -> None:
        """Subscribe to each pier's refresh command topic.

        The callback (invoked from paho's network thread) receives the pier id
        parsed from the command topic. It must not publish directly; per design
        D7 it enqueues the pier id for the main thread.
        """
        self._refresh_callback = callback
        self._client.on_message = self._on_message
        base = self._config.base_topic
        for pier_id in pier_ids:
            topic = refresh_command_topic(base, pier_id)
            with self._subscription_lock:
                self._topic_to_pier[topic] = pier_id
            self._subscribe(topic)

    def _subscribe_all(self) -> None:
        """Subscribe again to every refresh topic, from paho's thread (D2)."""
        with self._subscription_lock:
            topics = list(self._topic_to_pier)
        for topic in topics:
            self._subscribe(topic)

    def _subscribe(self, topic: str) -> None:
        """Subscribe, logging a failed call, and note the topic for the broker's answer.

        paho queues the request before ``subscribe`` returns, so the answer can
        reach paho's thread first. Holding the lock until the message ID is noted
        makes :meth:`_on_subscribe` wait for it (D2).
        """
        with self._subscription_lock:
            rc, mid = self._client.subscribe(topic)
            if rc == mqtt.MQTT_ERR_SUCCESS and mid is not None:
                self._unanswered[mid] = topic
        if rc != mqtt.MQTT_ERR_SUCCESS:
            logger.warning(
                "Could not subscribe to %s on the MQTT broker at %s (%s)",
                topic,
                self._broker,
                mqtt.error_string(rc),
            )

    def _on_subscribe(
        self, _client: Any, _userdata: Any, mid: int, reason_codes: Any, _properties: Any
    ) -> None:
        """Log each subscription the broker refuses; retrying cannot fix one (D2)."""
        with self._subscription_lock:
            topic = self._unanswered.pop(mid, "a refresh topic")
        for reason in reason_codes:
            if reason.is_failure:
                logger.warning(
                    "The MQTT broker at %s refused the subscription to %s (%s)",
                    self._broker,
                    topic,
                    reason,
                )

    def on_reconnect(self, callback: Callable[[], None]) -> None:
        """Call ``callback`` on paho's thread after each reconnect (design D2).

        It must not publish; the service only queues a marker for the main thread.
        """
        self._reconnect_listener = callback

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        with self._subscription_lock:
            pier_id = self._topic_to_pier.get(message.topic)
        if pier_id is not None and self._refresh_callback is not None:
            self._refresh_callback(pier_id)

    def close(self) -> None:
        """Stop the watcher, publish ``offline`` if connected, disconnect, then stop paho.

        The watcher stops first, or it would start the thread ``loop_stop`` ends.
        A clean disconnect skips the last-will, so ``offline`` goes out first, while
        paho's thread still runs to send it (stop-goes-offline D1). While the
        connection is down, the broker sends the last-will instead. Never raises.
        """
        self._closing = True
        self._stop_watching.set()
        if self._watcher is not None:
            self._watcher.join()
        if self._phase is _Phase.CONNECTED:
            self._publish_offline()
        try:
            self._client.disconnect()
            self._client.loop_stop()
        except OSError, ValueError:  # pragma: no cover - best-effort shutdown
            logger.warning("Error during MQTT shutdown", exc_info=True)

    def _publish_offline(self) -> None:
        """Publish the retained ``offline`` and wait briefly for the broker (D2).

        A refused or unconfirmed message is logged, and the stop goes on.
        """
        status = availability_topic(self._config.base_topic)
        info = self._client.publish(status, PAYLOAD_OFFLINE, qos=1, retain=True)
        try:
            info.wait_for_publish(timeout=OFFLINE_WAIT_SECONDS)
            confirmed = info.is_published()
        except RuntimeError, ValueError:
            confirmed = False
        if not confirmed:
            logger.warning("The MQTT broker did not confirm the offline availability")
