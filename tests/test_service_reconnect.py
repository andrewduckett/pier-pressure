"""reconnect-restores-delivery: the main thread restores delivery after a reconnect.

paho's thread puts a ``Reconnected`` marker on the work queue. The main thread
publishes each pier's last state again, then ``online``. It computes no verdict
and fetches no conditions for a reconnect (design D3).
"""

from __future__ import annotations

import queue
from typing import Any

from pierpressure.conditions import FetchResult
from pierpressure.core.config import AppConfig, PierConfig, RecomputeConfig
from pierpressure.delivery.mqtt import PAYLOAD_ONLINE, MqttDelivery, availability_topic
from pierpressure.health import ProviderInfo
from pierpressure.service import RECONNECTED, Service

from .conftest import (
    ACCEPT,
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
    service.publish_pier = lambda pier: calls.append(pier)  # type: ignore[method-assign]
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
