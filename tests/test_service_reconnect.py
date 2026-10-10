"""reconnect-restores-delivery: the main thread restores delivery after a reconnect.

paho's thread puts a ``Reconnected`` marker on the work queue. The main thread
publishes each pier's last state again, then ``online``. It computes no verdict
and fetches no conditions for a reconnect (design D3).
"""

from __future__ import annotations

import json
import queue
from typing import Any

from pierpressure.conditions import FetchResult
from pierpressure.core.config import AppConfig, PierConfig, RecomputeConfig
from pierpressure.delivery.mqtt import (
    PAYLOAD_ONLINE,
    MqttDelivery,
    attributes_topic,
    availability_topic,
    health_state_topic,
)
from pierpressure.health import ProviderInfo
from pierpressure.service import RECONNECTED, Service

from .conftest import (
    ACCEPT,
    SOCKET_FAILURE,
    FakeMqttClient,
    RecordingDelivery,
    ScriptedMonotonic,
    ScriptedQueue,
    StepClock,
    make_conditions,
    make_mqtt_config,
    make_pier,
)

PIERS = ("a", "b")
PROVIDERS = (ProviderInfo(key="open_meteo", name="Open-Meteo", role="base"),)


def _app_config(interval: int = 10) -> AppConfig:
    return AppConfig(
        mqtt=make_mqtt_config(),
        recompute=RecomputeConfig(interval_seconds=interval),
        piers=[make_pier(pier) for pier in PIERS],
    )


class CountingProvider:
    """A conditions provider that counts its calls."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _pier: PierConfig) -> FetchResult:
        self.calls += 1
        return FetchResult(make_conditions())


def _queue(*items: Any) -> queue.Queue[Any]:
    work: queue.Queue[Any] = queue.Queue()
    for item in items:
        work.put(item)
    return work


def _run_once(work: queue.Queue[Any], **kwargs: Any) -> RecordingDelivery:
    """Run startup, then one loop iteration before the interval deadline."""
    delivery = RecordingDelivery()
    service = Service(_app_config(), delivery, StepClock(), refresh_queue=work, **kwargs)  # type: ignore[arg-type]
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)
    return delivery


def _after_startup(delivery: RecordingDelivery) -> list[tuple[str, ...]]:
    # Startup publishes "online" once, then a verdict for each pier.
    start = delivery.events.index(("online",)) + 1 + len(PIERS)
    return delivery.events[start:]


# --------------------------------------------------------------------------- #
# Handling the marker (spec "Entities come back online after a reconnect")
# --------------------------------------------------------------------------- #


def test_a_reconnect_replays_the_last_state_then_goes_online() -> None:
    delivery = _run_once(_queue(RECONNECTED))
    assert _after_startup(delivery) == [("replay",), ("online",)]


def test_enqueue_reconnect_puts_the_marker_on_the_queue() -> None:
    work: queue.Queue[Any] = queue.Queue()
    service = Service(_app_config(), RecordingDelivery(), StepClock(), refresh_queue=work)  # type: ignore[arg-type]
    service.enqueue_reconnect()
    assert work.get_nowait() is RECONNECTED


def test_several_reconnects_drained_together_replay_once() -> None:
    delivery = _run_once(_queue(RECONNECTED, RECONNECTED, RECONNECTED))
    assert _after_startup(delivery) == [("replay",), ("online",)]


def test_a_reconnect_drained_with_refreshes_is_handled_first() -> None:
    delivery = _run_once(_queue("b", RECONNECTED))
    assert _after_startup(delivery) == [("replay",), ("online",), ("verdict", "b")]


# --------------------------------------------------------------------------- #
# No new verdict (spec "A reconnect computes no new verdict")
# --------------------------------------------------------------------------- #


def test_a_reconnect_fetches_no_conditions() -> None:
    provider = CountingProvider()
    _run_once(_queue(RECONNECTED), conditions_provider=provider)
    assert provider.calls == len(PIERS)  # startup only


def test_a_reconnect_calls_no_explainer() -> None:
    explained: list[str] = []
    _run_once(_queue(RECONNECTED), explainer=lambda doc: explained.append(doc.pier))
    assert explained == list(PIERS)  # startup only


def test_a_reconnect_does_not_move_the_interval_deadline() -> None:
    calls: list[str] = []
    service = Service(
        _app_config(interval=10),
        RecordingDelivery(),  # type: ignore[arg-type]
        StepClock(),
        refresh_queue=ScriptedQueue([RECONNECTED, "a"]),  # type: ignore[arg-type]
    )
    service.publish_all = lambda: calls.append("all")  # type: ignore[method-assign]
    service.publish_pier = lambda pier_id: calls.append(pier_id)  # type: ignore[method-assign]
    # deadline 10; iter1 now(1) takes the marker; iter2 now(10.5) is past the
    # deadline, so the interval recompute runs and the refresh still waits.
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0, 10.5, 11.0]), max_iterations=2)
    assert calls == ["all", "all"]


# --------------------------------------------------------------------------- #
# Startup order (spec "The first connection is not a reconnect", "A reconnect
# during startup keeps the startup order")
# --------------------------------------------------------------------------- #


def test_startup_with_no_reconnect_goes_online_once() -> None:
    delivery = _run_once(_queue())
    assert delivery.events.count(("online",)) == 1


def test_a_reconnect_during_startup_keeps_the_startup_order() -> None:
    delivery = _run_once(_queue(RECONNECTED), providers=PROVIDERS)
    assert delivery.events == [
        ("health", "a"),
        ("health", "b"),
        ("online",),
        ("verdict", "a"),
        ("health", "a"),
        ("verdict", "b"),
        ("health", "b"),
        ("replay",),
        ("online",),
    ]


# --------------------------------------------------------------------------- #
# A message still being sent at the drop (spec "... does not change the order")
# --------------------------------------------------------------------------- #


def test_a_drop_after_online_still_ends_with_state_then_online() -> None:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    work: queue.Queue[Any] = queue.Queue()
    service = Service(_app_config(), delivery, StepClock(), refresh_queue=work)
    delivery.on_reconnect(service.enqueue_reconnect)
    status = availability_topic("pierpressure")
    drops: list[int] = []

    def drop_after_online(_pier: PierConfig) -> FetchResult:
        # The connection drops after "online" and before the broker acks it.
        if not drops:
            drops.append(len(client.published))
            client.drop([ACCEPT])
        return FetchResult(make_conditions())

    service._conditions_provider = drop_after_online
    try:
        service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)
    finally:
        delivery.close()

    before_drop = client.published[: drops[0]]
    assert before_drop[-1].topic == status  # online went out before the drop
    last = client.published[-1]
    assert (last.topic, last.payload, last.retain) == (status, PAYLOAD_ONLINE, True)
    replayed_topics = {m.topic for m in client.published[drops[0] : -1]}
    assert replayed_topics >= {m.topic for m in client.published if m.topic != status}


# --------------------------------------------------------------------------- #
# Publishing during an outage (publish-failure-resilience D1, D4)
# --------------------------------------------------------------------------- #


class ReconnectOnWait(queue.Queue[Any]):
    """A work queue whose first ``get`` lets the broker accept again first.

    It plays paho's thread reconnecting while the main thread waits for work.
    """

    def __init__(self, client: FakeMqttClient) -> None:
        super().__init__()
        self._client = client
        self._accepted = False

    def get(self, block: bool = True, timeout: float | None = None) -> Any:
        if not self._accepted:
            self._accepted = True
            self._client.accept_again()
        return super().get(block, timeout)


def _real_delivery() -> tuple[MqttDelivery, FakeMqttClient, ReconnectOnWait]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    return delivery, client, ReconnectOnWait(client)


def test_an_interval_during_an_outage_is_published_after_the_reconnect() -> None:
    delivery, client, work = _real_delivery()
    service = Service(_app_config(), delivery, StepClock(), refresh_queue=work)
    delivery.on_reconnect(service.enqueue_reconnect)
    calls: list[int] = []

    def drop_at_the_interval(_pier: PierConfig) -> FetchResult:
        calls.append(len(client.published))
        if len(calls) == len(PIERS) + 1:  # the first fetch of the interval recompute
            client.drop([SOCKET_FAILURE])
        return FetchResult(make_conditions())

    service._conditions_provider = drop_at_the_interval
    try:
        # Startup at 0; the interval is due at 11; the main thread waits at 12.
        service.run(monotonic=ScriptedMonotonic([0.0, 11.0, 11.0, 12.0]), max_iterations=2)
    finally:
        delivery.close()

    dropped_at = calls[len(PIERS)]
    startup = client.published[:dropped_at]
    after = client.published[dropped_at:]
    status = availability_topic("pierpressure")
    assert (after[-1].topic, after[-1].payload, after[-1].retain) == (status, PAYLOAD_ONLINE, True)
    for pier in PIERS:
        sent_before = [
            m.payload for m in startup if m.topic == attributes_topic("pierpressure", pier)
        ]
        sent_after = [m.payload for m in after if m.topic == attributes_topic("pierpressure", pier)]
        # Only the replay sends it, with the verdict from the recompute in the outage.
        assert len(sent_after) == 1
        assert _generated_at(sent_after[0]) > _generated_at(sent_before[-1])
        assert all(m.retain for m in after if m.topic.startswith(f"pierpressure/{pier}/"))


def test_a_drop_before_the_startup_reset_sends_the_reset_before_online() -> None:
    delivery, client, work = _real_delivery()
    service = Service(_app_config(), delivery, StepClock(), refresh_queue=work, providers=PROVIDERS)
    delivery.on_reconnect(service.enqueue_reconnect)
    client.drop([SOCKET_FAILURE])
    try:
        service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)
    finally:
        delivery.close()

    topics = [m.topic for m in client.published]
    status = availability_topic("pierpressure")
    online_at = topics.index(status)
    for pier in PIERS:
        reset_at = topics.index(health_state_topic("pierpressure", pier, "open_meteo"))
        assert reset_at < online_at
    assert topics[-1] == status


def _generated_at(attributes: object) -> str:
    assert isinstance(attributes, str)
    value = json.loads(attributes)["generated_at"]
    assert isinstance(value, str)
    return value
