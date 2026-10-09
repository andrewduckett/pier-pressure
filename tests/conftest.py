"""Shared test fakes and helpers.

The delivery layer is exercised against a fake MQTT client (no broker), per the
verification strategy in design D11.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.reasoncodes import ReasonCode

from pierpressure.conditions import FetchResult
from pierpressure.core.conditions import (
    BaseGroup,
    BaseHour,
    Conditions,
    GroupMeta,
    SecondaryGroup,
    SecondaryHour,
)
from pierpressure.core.config import MqttConfig, PierConfig
from pierpressure.core.model import (
    Band,
    Confidence,
    DarkWindow,
    Moon,
    MoonPhase,
    Verdict,
    VerdictDocument,
)
from pierpressure.health import ProviderHealth

_CONNECT_FLAGS = mqtt.ConnectFlags(session_present=False)
_NO_FLAGS = mqtt.DisconnectFlags(is_disconnect_packet_from_server=False)
# paho passes this reason for every disconnect it did not receive from the broker.
_UNSPECIFIED = ReasonCode(PacketTypes.DISCONNECT, "Unspecified error")


@dataclass
class Published:
    topic: str
    payload: Any
    qos: int
    retain: bool


# Attempt outcomes a ``FakeMqttClient`` script can play (design D5). A refusal is
# ``("refused", <reason name>)``, built with :func:`refused`.
SOCKET_FAILURE = "socket failure"
CLOSED_BEFORE_ANSWER = "closed before answer"
THREAD_ENDS = "thread ends"
ACCEPT = "accept"

Attempt = str | tuple[str, str]


def refused(reason: str) -> Attempt:
    """A CONNACK refusal, named as paho names it (for example "Not authorized")."""
    return ("refused", reason)


class _LiveThread:
    """Stands in for paho's network thread while the fake's loop runs."""


class FakeMqttClient:
    """Records everything the delivery adapter asks of the paho client.

    ``script`` lists the outcome of each connection attempt. ``loop_start`` plays
    it at once, on the calling thread, calling the handlers in paho's order. It
    stops after an acceptance, or when the thread ends. With no script, the first
    attempt is accepted. :meth:`drop` loses the connection after startup and plays
    a new script, as paho's thread does when it reconnects.

    Each ``subscribe`` queues the broker's answer (SUBACK). An acceptance delivers
    the queued answers after ``on_connect`` returns, as paho does;
    :meth:`ack_subscriptions` delivers them at any other time.
    """

    def __init__(
        self,
        *,
        script: Iterable[Attempt] = (ACCEPT,),
        publish_rc: int = 0,
    ) -> None:
        self.published: list[Published] = []
        self.will: Published | None = None
        self.subscriptions: list[str] = []
        self.on_message: Any = None
        self.on_pre_connect: Any = None
        self.on_connect: Any = None
        self.on_connect_fail: Any = None
        self.on_disconnect: Any = None
        self.on_subscribe: Any = None
        self.connected = False
        self.loop_started = False
        self.loop_start_calls = 0
        self.credentials: tuple[str, str | None] | None = None
        self.connected_to: tuple[str, int] | None = None
        self.reconnect_delays: tuple[int, int] | None = None
        self.calls: list[str] = []
        # paho's private network-thread attribute: set while its loop runs.
        self._thread: _LiveThread | None = None
        self._script = list(script)
        self._publish_rc = publish_rc
        # Subscriptions: the last message ID, the answers not yet delivered, the
        # topics the broker refuses (with paho's reason name), and the topics
        # whose ``subscribe`` call itself fails (with its result code).
        self._last_mid = 0
        self._pending_subacks: list[tuple[int, str]] = []
        self._refusals: dict[str, str] = {}
        self._subscribe_failures: dict[str, int] = {}
        # When set, ``subscribe`` answers a refusal from a second thread before it
        # returns its message ID (design D6's race). The threads are kept to join.
        self.answer_before_return = False
        self.answer_threads: list[threading.Thread] = []

    def reconnect_delay_set(self, min_delay: int = 1, max_delay: int = 120) -> None:
        self.calls.append("reconnect_delay_set")
        self.reconnect_delays = (min_delay, max_delay)

    def connect_async(self, host: str, port: int = 1883, keepalive: int = 60) -> None:
        self.calls.append("connect_async")
        self.connected_to = (host, port)

    def username_pw_set(self, username: str, password: str | None = None) -> None:
        self.credentials = (username, password)

    def will_set(self, topic: str, payload: Any = None, qos: int = 0, retain: bool = False) -> None:
        self.will = Published(topic, payload, qos, retain)

    def loop_start(self) -> None:
        self.calls.append("loop_start")
        self.loop_start_calls += 1
        if not self._script:
            raise AssertionError("loop_start called with no attempts left in the script")
        self.loop_started = True
        self._thread = _LiveThread()
        self._play_script()

    def drop(self, script: Iterable[Attempt]) -> None:
        """Lose the connection, then play ``script`` as paho's thread reconnects.

        paho reports a lost connection with the "Unspecified error" reason. The
        attempts play on the calling thread, as with ``loop_start``.
        """
        self.connected = False
        self._script = list(script)
        self._call(self.on_disconnect, self, None, _NO_FLAGS, _UNSPECIFIED, None)
        self._play_script()

    def _play_script(self) -> None:
        while self._script:
            attempt = self._script.pop(0)
            if attempt == THREAD_ENDS:
                self._thread = None
                return
            self._play(attempt)
            if attempt == ACCEPT:
                return
        # The script ran out with no outcome: end the thread, so the next
        # loop_start fails the test instead of the wait hanging forever.
        self._thread = None

    def loop_stop(self) -> None:
        self.calls.append("loop_stop")
        self.loop_started = False
        self._thread = None

    def _play(self, attempt: Attempt) -> None:
        """Call the handlers for one attempt, in the order paho 2.1 calls them."""
        self._call(self.on_pre_connect, self, None)
        if attempt == SOCKET_FAILURE:
            try:
                raise ConnectionRefusedError(111, "Connection refused")
            except OSError:
                # paho calls on_connect_fail inside its ``except OSError`` block.
                self._call(self.on_connect_fail, self, None)
            self._call(self.on_disconnect, self, None, _NO_FLAGS, _UNSPECIFIED, None)
        elif attempt == CLOSED_BEFORE_ANSWER:
            self._call(self.on_disconnect, self, None, _NO_FLAGS, _UNSPECIFIED, None)
        elif attempt == ACCEPT:
            self.connected = True
            success = ReasonCode(PacketTypes.CONNACK, "Success")
            self._call(self.on_connect, self, None, _CONNECT_FLAGS, success, None)
            self.ack_subscriptions()
        else:
            assert isinstance(attempt, tuple)
            reason = ReasonCode(PacketTypes.CONNACK, attempt[1])
            self._call(self.on_connect, self, None, _CONNECT_FLAGS, reason, None)
            self._call(self.on_disconnect, self, None, _NO_FLAGS, _UNSPECIFIED, None)

    @staticmethod
    def _call(handler: Any, *args: Any) -> None:
        if handler is not None:
            handler(*args)

    def refuse_subscription(self, topic: str, reason: str = "Not authorized") -> None:
        """Make the broker refuse ``topic`` with a SUBACK failure reason."""
        self._refusals[topic] = reason

    def fail_subscribe(self, topic: str, rc: int = mqtt.MQTT_ERR_NO_CONN) -> None:
        """Make ``subscribe(topic)`` return a failure code and send nothing."""
        self._subscribe_failures[topic] = rc

    def subscribe(self, topic: str, qos: int = 0) -> tuple[int, int | None]:
        if topic in self._subscribe_failures:
            return self._subscribe_failures[topic], None
        self.subscriptions.append(topic)
        self._last_mid += 1
        mid = self._last_mid
        reason = self._refusals.get(topic, "Granted QoS 0")
        if self.answer_before_return:
            answer = threading.Thread(target=self._answer, args=(mid, reason), daemon=True)
            self.answer_threads.append(answer)
            answer.start()
            answer.join(0.1)
        else:
            self._pending_subacks.append((mid, reason))
        return mqtt.MQTT_ERR_SUCCESS, mid

    def ack_subscriptions(self) -> None:
        """Deliver the broker's queued answers to ``on_subscribe``."""
        pending, self._pending_subacks = self._pending_subacks, []
        for mid, reason in pending:
            self._answer(mid, reason)

    def _answer(self, mid: int, reason: str) -> None:
        codes = [ReasonCode(PacketTypes.SUBACK, reason)]
        self._call(self.on_subscribe, self, None, mid, codes, None)

    def publish(self, topic: str, payload: Any = None, qos: int = 0, retain: bool = False) -> Any:
        self.published.append(Published(topic, payload, qos, retain))

        class _Info:
            rc = self._publish_rc

        return _Info()

    def disconnect(self) -> None:
        self.connected = False

    def publishes_to(self, topic: str) -> list[Published]:
        return [p for p in self.published if p.topic == topic]


@dataclass
class FakeMessage:
    topic: str
    payload: bytes = b""


class RecordingDelivery:
    """A delivery stand-in that records the documents (and narratives) it is asked
    to publish, the provider health it publishes, and the order of every call.

    ``events`` holds one entry per call: ``("verdict", pier)``,
    ``("health", pier)``, or ``("online",)``. ``health_error`` makes every
    ``publish_health`` call raise it.
    """

    def __init__(self, *, health_error: Exception | None = None) -> None:
        self.documents: list[VerdictDocument] = []
        self.narratives: list[str | None] = []
        self.healths: list[tuple[str, tuple[ProviderHealth, ...]]] = []
        self.events: list[tuple[str, ...]] = []
        self._health_error = health_error

    def publish_verdict(self, document: VerdictDocument, narrative: str | None = None) -> None:
        self.events.append(("verdict", document.pier))
        self.documents.append(document)
        self.narratives.append(narrative)

    def publish_health(self, pier_id: str, healths: Iterable[ProviderHealth]) -> None:
        if self._health_error is not None:
            raise self._health_error
        self.events.append(("health", pier_id))
        self.healths.append((pier_id, tuple(healths)))

    def go_online(self) -> None:
        self.events.append(("online",))


class StepClock:
    """A clock that advances one second every time it is read."""

    def __init__(
        self, start: datetime | None = None, step: timedelta = timedelta(seconds=1)
    ) -> None:
        self._now = start or datetime(2026, 9, 7, 21, 30, tzinfo=UTC)
        self._step = step

    def now(self) -> datetime:
        current = self._now
        self._now = self._now + self._step
        return current


class ScriptedQueue:
    """A queue whose ``get`` returns a scripted sequence (``None`` -> Empty).

    ``get_nowait`` always raises Empty, so drain/dedupe pulls nothing extra;
    this isolates the deadline logic under test.
    """

    _EMPTY = object()

    def __init__(self, script: list[str | None]) -> None:
        self._script = [self._EMPTY if item is None else item for item in script]
        self.extra: list[str] = []

    def get(self, timeout: float | None = None) -> str:
        if not self._script:
            raise queue.Empty
        item = self._script.pop(0)
        if item is self._EMPTY:
            raise queue.Empty
        assert isinstance(item, str)
        return item

    def get_nowait(self) -> str:
        raise queue.Empty

    def put(self, item: str) -> None:
        self.extra.append(item)


class ScriptedMonotonic:
    """Returns a scripted sequence of monotonic readings (last value repeats)."""

    def __init__(self, readings: list[float]) -> None:
        self._readings = readings
        self._index = 0

    def __call__(self) -> float:
        value = self._readings[min(self._index, len(self._readings) - 1)]
        self._index += 1
        return value


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #


def make_pier(pier_id: str = "backyard") -> PierConfig:
    return PierConfig(id=pier_id, latitude=51.5, longitude=-0.12, elevation_m=30.0)


def make_conditions(
    *,
    cloud: float | None = 20.0,
    wind: float | None = 15.0,
    seeing: float | None = 0.7,
    transparency: float | None = 0.7,
    issued_at: datetime | None = None,
) -> Conditions:
    """Fixed per-source conditions spanning an evening-to-morning horizon.

    The horizon (18:00 -> next 06:00 UTC) comfortably brackets a London night, so
    the core finds real overlap with the dark window. Both the base (cloud/wind)
    and secondary (seeing/transparency) groups share the same issue time. Being
    fixed, it pins the conditions input for byte-identity determinism tests.
    """
    issued = issued_at or datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    start = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)
    slots = [start + timedelta(hours=h) for h in range(13)]
    base = BaseGroup.of(
        GroupMeta(source="base", issued_at=issued),
        tuple(BaseHour(time=t, cloud_cover=cloud, wind_gust=wind) for t in slots),
    )
    secondary = SecondaryGroup.of(
        GroupMeta(source="secondary", issued_at=issued),
        tuple(SecondaryHour(time=t, seeing=seeing, transparency=transparency) for t in slots),
    )
    return Conditions(base=base, secondary=secondary)


def make_mqtt_config(**overrides: Any) -> MqttConfig:
    base: dict[str, Any] = {
        "host": "192.168.1.10",
        "port": 1883,
        "username": "pierpressure",
        "password": "secret",
    }
    base.update(overrides)
    return MqttConfig(**base)


def make_document(
    *,
    pier: str = "backyard",
    verdict: Verdict = Verdict.MAYBE,
    score: int | None = 50,
    generated_at: datetime | None = None,
) -> VerdictDocument:
    return VerdictDocument(
        pier=pier,
        generated_at=generated_at or datetime(2026, 9, 7, 21, 30, tzinfo=UTC),
        verdict=verdict,
        score=score,
        confidence=Confidence(band=Band.LOW, value=0),
        reasons=["test reason"],
        targets=[],
        dark_window=DarkWindow(start=None, end=None),
        moon=Moon(illumination=0.0, phase=MoonPhase.NEW),
    )


def fixed_conditions(conditions: Conditions) -> Callable[[PierConfig], FetchResult]:
    """A conditions provider that returns ``conditions`` with no fetch outcomes."""
    return lambda _pier: FetchResult(conditions)
