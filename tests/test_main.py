"""Task 7.1: the entry point wires config -> broker -> startup publish."""

from __future__ import annotations

from datetime import UTC, datetime

from pierpressure.core.clock import FixedClock
from pierpressure.core.config import AppConfig, RecomputeConfig
from pierpressure.delivery.mqtt import MqttDelivery, verdict_state_topic
from pierpressure.service import Service

from .conftest import FakeMqttClient, make_mqtt_config, make_pier


def test_startup_publishes_a_verdict_against_a_fake_broker() -> None:
    client = FakeMqttClient()
    config = AppConfig(
        mqtt=make_mqtt_config(),
        recompute=RecomputeConfig(interval_seconds=900),
        piers=[make_pier("backyard")],
    )
    delivery = MqttDelivery(config.mqtt, client=client)
    delivery.connect()

    service = Service(config, delivery, FixedClock(datetime(2026, 9, 7, 21, 30, tzinfo=UTC)))
    delivery.subscribe_refresh([p.id for p in config.piers], service.enqueue_refresh)

    # max_iterations=0 -> just the startup publish, no blocking loop.
    service.run(max_iterations=0)

    state = client.publishes_to(verdict_state_topic("pierpressure", "backyard"))
    assert state and state[0].payload == "MAYBE"
    assert client.will is not None  # LWT registered on connect


def test_main_exits_nonzero_on_bad_config(tmp_path: object) -> None:
    from pierpressure.__main__ import main

    assert main(["/nonexistent/config.yaml"]) == 1
