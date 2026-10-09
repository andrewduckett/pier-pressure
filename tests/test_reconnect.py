"""reconnect-restores-delivery: the process restores delivery after each reconnect.

After the first connection, paho's thread reconnects on its own (ADR-0018). The
adapter tracks a phase (design D1), subscribes again on each accept and tells the
service (D2), and logs the outage. The fake client's ``drop`` plays a lost
connection and the attempts that follow (D6).
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Iterator

import paho.mqtt.client as mqtt
import pytest

from pierpressure.delivery import mqtt as delivery_mqtt
from pierpressure.delivery.mqtt import MqttDelivery, refresh_command_topic

from .conftest import (
    ACCEPT,
    SOCKET_FAILURE,
    THREAD_ENDS,
    FakeMqttClient,
    make_mqtt_config,
    refused,
)

BROKER = "192.168.1.10:1883"
PASSWORD = "secret"
PIERS = ["backyard", "frontyard"]
BASE = "pierpressure"
TOPICS = [refresh_command_topic(BASE, pier) for pier in PIERS]


class Started:
    """A delivery that has connected once and subscribed to the refresh topics.

    ``prepare`` runs on the client before the first subscriptions, for example to
    make the broker refuse one.
    """

    def __init__(self, prepare: Callable[[FakeMqttClient], None] | None = None) -> None:
        self.client = FakeMqttClient()
        self.delivery = MqttDelivery(make_mqtt_config(), client=self.client)
        self.delivery.connect()
        if prepare is not None:
            prepare(self.client)
        self.refreshed: list[str] = []
        self.reconnects = 0
        self.delivery.subscribe_refresh(PIERS, self.refreshed.append)
        self.delivery.on_reconnect(self._count_reconnect)
        self.client.ack_subscriptions()

    def _count_reconnect(self) -> None:
        self.reconnects += 1


@pytest.fixture(autouse=True)
def fast_watcher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check paho's thread every 10 ms, so no test waits a full second (design D7)."""
    monkeypatch.setattr(delivery_mqtt, "_WAIT_SLICE_SECONDS", 0.01)


@pytest.fixture
def started() -> Iterator[Started]:
    fixture = Started()
    yield fixture
    fixture.delivery.close()


def _wait_until(condition: Callable[[], bool]) -> bool:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.005)
    return False


def _watchers() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name == "pierpressure-mqtt-watcher"]


def _messages(caplog: pytest.LogCaptureFixture, level: int) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == level]


# --------------------------------------------------------------------------- #
# Subscribing again (spec "Refresh works again after a reconnect"; design D2)
# --------------------------------------------------------------------------- #


def test_a_reconnect_subscribes_to_every_refresh_topic_again(started: Started) -> None:
    started.client.drop([ACCEPT])
    assert started.client.active_subscriptions == set(TOPICS)


def test_a_refresh_after_a_reconnect_reaches_the_refresh_callback(started: Started) -> None:
    started.client.drop([ACCEPT])
    started.client.deliver(TOPICS[1])
    assert started.refreshed == ["frontyard"]


def test_a_reconnect_tells_the_reconnect_listener(started: Started) -> None:
    started.client.drop([ACCEPT])
    assert started.reconnects == 1


def test_the_first_connection_is_not_a_reconnect(started: Started) -> None:
    assert started.reconnects == 0


def test_failed_attempts_do_not_tell_the_reconnect_listener(started: Started) -> None:
    started.client.drop([SOCKET_FAILURE, refused("Server unavailable"), ACCEPT])
    assert started.reconnects == 1


# --------------------------------------------------------------------------- #
# Logging the outage (spec "The outage is logged"; design D1)
# --------------------------------------------------------------------------- #


def test_an_outage_logs_one_warning_per_event(
    started: Started, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    started.client.drop([SOCKET_FAILURE, refused("Server unavailable"), ACCEPT])
    assert _messages(caplog, logging.WARNING) == [
        f"Lost the connection to the MQTT broker at {BROKER}; trying again",
        f"Could not connect to the MQTT broker at {BROKER} (ConnectionRefusedError); trying again",
        f"Could not connect to the MQTT broker at {BROKER} (Server unavailable); trying again",
    ]


def test_a_reconnect_logs_one_info_line(started: Started, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    started.client.drop([SOCKET_FAILURE, ACCEPT])
    assert _messages(caplog, logging.INFO) == [f"Reconnected to the MQTT broker at {BROKER}"]


def test_outage_log_lines_leave_out_the_password(
    started: Started, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    started.client.drop([SOCKET_FAILURE, refused("Not authorized"), ACCEPT])
    assert all(PASSWORD not in record.getMessage() for record in caplog.records)


# --------------------------------------------------------------------------- #
# A login rejected during a reconnect (spec "... does not stop the process")
# --------------------------------------------------------------------------- #


def test_a_rejected_login_during_a_reconnect_logs_an_error_with_the_advice(
    started: Started, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    started.client.drop([refused("Not authorized"), ACCEPT])
    assert _messages(caplog, logging.ERROR) == [
        f"The MQTT broker at {BROKER} rejected the login: not authorized. "
        "Check mqtt.username and mqtt.password, and the user's permissions on the broker. "
        "Trying again."
    ]


def test_a_rejected_login_during_a_reconnect_logs_no_retry_warning(
    started: Started, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    started.client.drop([refused("Not authorized"), ACCEPT])
    assert _messages(caplog, logging.WARNING) == [
        f"Lost the connection to the MQTT broker at {BROKER}; trying again"
    ]


def test_a_rejected_login_during_a_reconnect_keeps_the_loop_running(started: Started) -> None:
    started.client.drop([refused("Not authorized"), ACCEPT])
    assert "loop_stop" not in started.client.calls


def test_a_rejected_login_during_a_reconnect_is_tried_again(started: Started) -> None:
    started.client.drop([refused("Bad user name or password"), ACCEPT])
    assert started.reconnects == 1


# --------------------------------------------------------------------------- #
# Checking each subscription (spec "A refused subscription is logged"; D2)
# --------------------------------------------------------------------------- #


def _refused_warning(topic: str, reason: str = "Not authorized") -> str:
    return f"The MQTT broker at {BROKER} refused the subscription to {topic} ({reason})"


def test_a_subscription_refused_at_startup_logs_a_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    fixture = Started(lambda client: client.refuse_subscription(TOPICS[1]))
    fixture.delivery.close()
    assert _messages(caplog, logging.WARNING) == [_refused_warning(TOPICS[1])]


def test_a_subscription_refused_after_a_reconnect_logs_a_warning(
    started: Started, caplog: pytest.LogCaptureFixture
) -> None:
    started.client.refuse_subscription(TOPICS[0], "Unspecified error")
    caplog.set_level(logging.WARNING)
    started.client.drop([ACCEPT])
    assert _messages(caplog, logging.WARNING)[1:] == [
        _refused_warning(TOPICS[0], "Unspecified error")
    ]


def test_a_failed_subscribe_call_logs_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    fixture = Started(lambda client: client.fail_subscribe(TOPICS[0]))
    fixture.delivery.close()
    assert _messages(caplog, logging.WARNING) == [
        f"Could not subscribe to {TOPICS[0]} on the MQTT broker at {BROKER} "
        f"({mqtt.error_string(mqtt.MQTT_ERR_NO_CONN)})"
    ]


def test_a_refused_subscription_still_subscribes_to_the_other_topics() -> None:
    fixture = Started(lambda client: client.refuse_subscription(TOPICS[0]))
    fixture.delivery.close()
    assert fixture.client.subscriptions == TOPICS


def test_a_refusal_answered_before_subscribe_returns_names_its_topic(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # paho queues SUBSCRIBE before it returns the message ID, so the broker's
    # answer can reach paho's thread first (design D6).
    def race(client: FakeMqttClient) -> None:
        client.answer_before_return = True
        client.refuse_subscription(TOPICS[0])

    caplog.set_level(logging.WARNING)
    fixture = Started(race)
    for answer in fixture.client.answer_threads:
        answer.join(5)
    fixture.delivery.close()
    assert _messages(caplog, logging.WARNING) == [_refused_warning(TOPICS[0])]


# --------------------------------------------------------------------------- #
# Keeping paho's thread running (spec "A failed immediate try during a
# reconnect is tried again"; design D7)
# --------------------------------------------------------------------------- #


def test_an_ended_thread_after_startup_is_started_again(started: Started) -> None:
    started.client.drop([THREAD_ENDS, ACCEPT])
    assert _wait_until(lambda: started.client.loop_start_calls == 2)


def test_an_ended_thread_after_startup_logs_one_failed_attempt(
    started: Started, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    started.client.drop([THREAD_ENDS, ACCEPT])
    assert _wait_until(lambda: started.reconnects == 1)
    assert _messages(caplog, logging.WARNING) == [
        f"Lost the connection to the MQTT broker at {BROKER}; trying again",
        f"Could not connect to the MQTT broker at {BROKER} (network thread stopped); trying again",
    ]


def test_a_restarted_thread_restores_refresh(started: Started) -> None:
    started.client.drop([THREAD_ENDS, ACCEPT])
    assert _wait_until(lambda: started.reconnects == 1)
    started.client.deliver(TOPICS[0])
    assert started.refreshed == ["backyard"]


def test_close_stops_the_watcher_before_the_loop(started: Started) -> None:
    watchers_at_loop_stop: list[int] = []
    loop_stop = started.client.loop_stop

    def record_then_stop() -> None:
        watchers_at_loop_stop.append(len(_watchers()))
        loop_stop()

    started.client.loop_stop = record_then_stop  # type: ignore[method-assign]
    started.delivery.close()
    assert watchers_at_loop_stop == [0]


def test_close_leaves_no_watcher_running() -> None:
    fixture = Started()
    assert _watchers()
    fixture.delivery.close()
    assert _watchers() == []
