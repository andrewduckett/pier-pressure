"""reconnect-restores-delivery: the process restores delivery after each reconnect.

After the first connection, paho's thread reconnects on its own (ADR-0018). The
adapter tracks a phase (design D1), subscribes again on each accept and tells the
service (D2), and logs the outage. The fake client's ``drop`` plays a lost
connection and the attempts that follow (D6).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from pierpressure.delivery.mqtt import MqttDelivery, refresh_command_topic

from .conftest import ACCEPT, SOCKET_FAILURE, FakeMqttClient, make_mqtt_config, refused

BROKER = "192.168.1.10:1883"
PASSWORD = "secret"
PIERS = ["backyard", "frontyard"]
BASE = "pierpressure"
TOPICS = [refresh_command_topic(BASE, pier) for pier in PIERS]


class Started:
    """A delivery that has connected once and subscribed to the refresh topics."""

    def __init__(self) -> None:
        self.client = FakeMqttClient()
        self.delivery = MqttDelivery(make_mqtt_config(), client=self.client)
        self.delivery.connect()
        self.refreshed: list[str] = []
        self.reconnects = 0
        self.delivery.subscribe_refresh(PIERS, self.refreshed.append)
        self.delivery.on_reconnect(self._count_reconnect)
        self.client.ack_subscriptions()

    def _count_reconnect(self) -> None:
        self.reconnects += 1


@pytest.fixture
def started() -> Iterator[Started]:
    fixture = Started()
    yield fixture
    fixture.delivery.close()


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
