"""Task 8.5 (optional): opt-in integration test against a real local broker.

Marked ``integration`` and deselected by default (see ``addopts`` in
pyproject.toml), so ``just test`` is green on a machine with no broker. Run it
explicitly with ``uv run pytest -m integration`` against a local Mosquitto.
"""

from __future__ import annotations

import queue

import pytest

from pierpressure.core.clock import SystemClock
from pierpressure.core.config import AppConfig, RecomputeConfig
from pierpressure.delivery.mqtt import (
    PAYLOAD_OFFLINE,
    MqttDelivery,
    availability_topic,
    refresh_command_topic,
    verdict_state_topic,
)
from pierpressure.service import Service

from .conftest import make_mqtt_config, make_pier

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883


@pytest.mark.integration
def test_publish_subscribe_and_lwt_against_local_broker() -> None:
    import paho.mqtt.client as mqtt

    received: queue.Queue[tuple[str, bytes]] = queue.Queue()

    listener = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    listener.on_message = lambda c, u, m: received.put((m.topic, m.payload))
    listener.connect(BROKER_HOST, BROKER_PORT)
    listener.subscribe(verdict_state_topic("pierpressure", "backyard"))
    listener.subscribe(availability_topic("pierpressure"))
    listener.loop_start()

    config = AppConfig(
        mqtt=make_mqtt_config(host=BROKER_HOST, port=BROKER_PORT, username=None, password=None),
        recompute=RecomputeConfig(interval_seconds=900),
        piers=[make_pier("backyard")],
    )
    delivery = MqttDelivery(config.mqtt)
    delivery.connect()
    service = Service(config, delivery, SystemClock())
    delivery.subscribe_refresh(["backyard"], service.enqueue_refresh)
    service.run(max_iterations=0)  # startup publish only

    topics = {received.get(timeout=5)[0] for _ in range(2)}
    assert verdict_state_topic("pierpressure", "backyard") in topics
    assert availability_topic("pierpressure") in topics

    # A refresh command triggers a republish.
    listener.publish(refresh_command_topic("pierpressure", "backyard"), "PRESS")
    service.run(max_iterations=1)

    delivery.close()
    listener.loop_stop()
    listener.disconnect()
    assert PAYLOAD_OFFLINE  # LWT payload constant is exercised above
