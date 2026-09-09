"""Tasks 6.1-6.4: the persistent loop, no-starvation, dedupe, on-demand refresh."""

from __future__ import annotations

import queue
from datetime import UTC, datetime

from pierpressure.core.clock import FixedClock
from pierpressure.core.config import AppConfig, RecomputeConfig
from pierpressure.delivery.mqtt import MqttDelivery, refresh_command_topic
from pierpressure.service import Service

from .conftest import (
    FakeMessage,
    FakeMqttClient,
    RecordingDelivery,
    ScriptedMonotonic,
    ScriptedQueue,
    StepClock,
    make_mqtt_config,
    make_pier,
)


def _app_config(interval: int = 10, pier_ids: tuple[str, ...] = ("backyard",)) -> AppConfig:
    return AppConfig(
        mqtt=make_mqtt_config(),
        recompute=RecomputeConfig(interval_seconds=interval),
        piers=[make_pier(pid) for pid in pier_ids],
    )


def test_startup_publishes_all_piers() -> None:
    delivery = RecordingDelivery()
    service = Service(_app_config(pier_ids=("a", "b")), delivery, StepClock())  # type: ignore[arg-type]
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)
    assert {doc.pier for doc in delivery.documents} == {"a", "b"}


def test_frequent_refreshes_do_not_starve_the_interval_recompute() -> None:
    # Two refreshes are dequeued while now < deadline (deadline untouched); then
    # monotonic passes the deadline and the periodic all-pier recompute fires.
    calls: list[str | tuple[str, str]] = []
    service = Service(
        _app_config(interval=10),
        RecordingDelivery(),  # type: ignore[arg-type]
        FixedClock(datetime(2026, 9, 7, 21, 30, tzinfo=UTC)),
        refresh_queue=ScriptedQueue(["backyard", "backyard"]),  # type: ignore[arg-type]
    )
    service.publish_all = lambda: calls.append("all")  # type: ignore[method-assign]
    service.publish_pier = lambda pid: calls.append(("pier", pid))  # type: ignore[method-assign]

    # readings: startup deadline(0), iter1 now(1), iter2 now(2), iter3 now(11), reset(12)
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0, 2.0, 11.0, 12.0]), max_iterations=3)

    assert calls.count("all") == 2  # startup + periodic (not starved)
    assert calls.count(("pier", "backyard")) == 2


def test_interval_recompute_republishes_all_with_later_generated_at() -> None:
    delivery = RecordingDelivery()
    service = Service(_app_config(interval=10, pier_ids=("a", "b")), delivery, StepClock())  # type: ignore[arg-type]
    # startup deadline(0); iter1 now(20) -> deadline passed -> publish_all; reset(30)
    service.run(monotonic=ScriptedMonotonic([0.0, 20.0, 30.0]), max_iterations=1)

    a_docs = [doc for doc in delivery.documents if doc.pier == "a"]
    assert len(a_docs) == 2  # startup + interval
    assert a_docs[1].generated_at > a_docs[0].generated_at


def test_refresh_republishes_exactly_the_target_pier() -> None:
    delivery = RecordingDelivery()
    service = Service(
        _app_config(interval=10, pier_ids=("a", "b")),
        delivery,  # type: ignore[arg-type]
        StepClock(),
        refresh_queue=ScriptedQueue(["a"]),  # type: ignore[arg-type]
    )
    # startup deadline(0); iter1 now(1) < deadline -> dequeue "a" -> publish pier a
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)

    published_after_startup = delivery.documents[2:]  # first two are startup a,b
    assert [doc.pier for doc in published_after_startup] == ["a"]


def test_duplicate_refreshes_collapse_to_one_recompute() -> None:
    delivery = RecordingDelivery()
    real_queue: queue.Queue[str] = queue.Queue()
    for _ in range(5):
        real_queue.put("backyard")
    service = Service(_app_config(interval=10), delivery, StepClock(), refresh_queue=real_queue)  # type: ignore[arg-type]
    # startup deadline(0); iter1 now(1) -> dequeue one + drain the other 4 into a set
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)

    after_startup = delivery.documents[1:]  # first is startup
    assert [doc.pier for doc in after_startup] == ["backyard"]  # one, not five


def test_command_on_refresh_topic_republishes_with_current_timestamp() -> None:
    from pierpressure.core.clock import SystemClock

    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    config = _app_config(interval=10)
    service = Service(config, delivery, SystemClock())
    delivery.subscribe_refresh(["backyard"], service.enqueue_refresh)

    # Document timestamps are floored to whole seconds (design D3), so compare
    # against a likewise-floored capture of the command instant.
    command_time = datetime.now(UTC).replace(microsecond=0)
    # Simulate the broker delivering a refresh command to the callback.
    client.on_message(client, None, FakeMessage(refresh_command_topic("pierpressure", "backyard")))

    # Process the queued refresh (now < deadline so it is dequeued as a refresh).
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)

    import json

    from pierpressure.delivery.mqtt import attributes_topic

    attrs = client.publishes_to(attributes_topic("pierpressure", "backyard"))
    generated_at = datetime.fromisoformat(json.loads(attrs[-1].payload)["generated_at"])
    assert generated_at >= command_time
