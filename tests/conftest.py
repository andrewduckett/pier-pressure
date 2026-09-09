"""Shared test fakes and helpers.

The delivery layer is exercised against a fake MQTT client (no broker), per the
verification strategy in design D11.
"""

from __future__ import annotations

import queue
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

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


@dataclass
class Published:
    topic: str
    payload: Any
    qos: int
    retain: bool


class FakeMqttClient:
    """Records everything the delivery adapter asks of the paho client."""

    def __init__(self, *, connect_error: Exception | None = None, publish_rc: int = 0) -> None:
        self.published: list[Published] = []
        self.will: Published | None = None
        self.subscriptions: list[str] = []
        self.on_message: Any = None
        self.connected = False
        self.loop_started = False
        self.credentials: tuple[str, str | None] | None = None
        self._connect_error = connect_error
        self._publish_rc = publish_rc

    def username_pw_set(self, username: str, password: str | None = None) -> None:
        self.credentials = (username, password)

    def will_set(self, topic: str, payload: Any = None, qos: int = 0, retain: bool = False) -> None:
        self.will = Published(topic, payload, qos, retain)

    def connect(self, host: str, port: int = 1883, keepalive: int = 60) -> None:
        if self._connect_error is not None:
            raise self._connect_error
        self.connected = True

    def loop_start(self) -> None:
        self.loop_started = True

    def loop_stop(self) -> None:
        self.loop_started = False

    def subscribe(self, topic: str, qos: int = 0) -> None:
        self.subscriptions.append(topic)

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
    """A delivery stand-in that records the documents it is asked to publish."""

    def __init__(self) -> None:
        self.documents: list[VerdictDocument] = []

    def publish_verdict(self, document: VerdictDocument) -> None:
        self.documents.append(document)


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
