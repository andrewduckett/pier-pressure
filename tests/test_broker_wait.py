"""retry-broker-connection: the process waits for the broker at startup.

``MqttDelivery.connect`` lets paho retry, and returns only once the broker accepts
(design D1, D2). It stops only on a rejected login (D3). Each failed attempt logs
one warning (D4). The fake client plays paho's callbacks from a script (D5).
"""

from __future__ import annotations

import logging

import pytest

from pierpressure.delivery.mqtt import DeliveryError, LoginRejected, MqttDelivery

from .conftest import (
    ACCEPT,
    CLOSED_BEFORE_ANSWER,
    SOCKET_FAILURE,
    THREAD_ENDS,
    Attempt,
    FakeMqttClient,
    make_mqtt_config,
    refused,
)

BROKER = "192.168.1.10:1883"
PASSWORD = "secret"


def _connect(*script: Attempt) -> FakeMqttClient:
    client = FakeMqttClient(script=script)
    MqttDelivery(make_mqtt_config(), client=client).connect()
    return client


def _rejection(reason: str) -> tuple[FakeMqttClient, DeliveryError]:
    client = FakeMqttClient(script=[refused(reason)])
    with pytest.raises(DeliveryError) as raised:
        MqttDelivery(make_mqtt_config(), client=client).connect()
    return client, raised.value


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]


# --------------------------------------------------------------------------- #
# Starting the connection (design D1)
# --------------------------------------------------------------------------- #


def test_connect_starts_the_connection_in_the_background() -> None:
    client = _connect(ACCEPT)
    assert client.calls[:3] == ["reconnect_delay_set", "connect_async", "loop_start"]


def test_connect_registers_the_will_before_it_connects() -> None:
    client = _connect(ACCEPT)
    assert client.will is not None


def test_connect_sets_pauses_from_1_to_120_seconds() -> None:
    client = _connect(ACCEPT)
    assert client.reconnect_delays == (1, 120)


def test_connect_targets_the_configured_broker() -> None:
    client = _connect(ACCEPT)
    assert client.connected_to == ("192.168.1.10", 1883)


# --------------------------------------------------------------------------- #
# Waiting through temporary failures (spec "The broker starts after the process")
# --------------------------------------------------------------------------- #


def test_connect_returns_once_the_broker_accepts_after_failed_attempts() -> None:
    client = _connect(SOCKET_FAILURE, SOCKET_FAILURE, SOCKET_FAILURE, ACCEPT)
    assert client.connected


def test_connect_publishes_nothing_while_it_waits() -> None:
    client = _connect(SOCKET_FAILURE, SOCKET_FAILURE, SOCKET_FAILURE, ACCEPT)
    assert client.published == []


@pytest.mark.parametrize(
    "failure",
    [refused("Server unavailable"), CLOSED_BEFORE_ANSWER],
    ids=["broker-not-ready", "closed-before-answer"],
)
def test_a_temporary_failure_is_tried_again(failure: Attempt) -> None:
    client = _connect(failure, ACCEPT)
    assert client.connected


def test_an_ended_network_thread_is_started_again() -> None:
    client = _connect(THREAD_ENDS, ACCEPT)
    assert client.loop_start_calls == 2


def test_connect_returns_after_the_restarted_thread_is_accepted() -> None:
    client = _connect(THREAD_ENDS, ACCEPT)
    assert client.connected


# --------------------------------------------------------------------------- #
# Rejected logins (design D3)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("reason", ["Bad user name or password", "Not authorized"])
def test_a_rejected_login_raises_login_rejected(reason: str) -> None:
    _, error = _rejection(reason)
    assert isinstance(error, LoginRejected)


@pytest.mark.parametrize("reason", ["Bad user name or password", "Not authorized"])
def test_a_rejected_login_stops_the_network_loop(reason: str) -> None:
    client, _ = _rejection(reason)
    assert client.calls[-1] == "loop_stop"


# Mosquitto answers a wrong password with "Not authorized", so both reasons get
# the same advice (found in the manual check of task 5.2).
@pytest.mark.parametrize("reason", ["Bad user name or password", "Not authorized"])
def test_a_rejected_login_names_the_broker_reason_and_fix(reason: str) -> None:
    _, error = _rejection(reason)
    assert str(error) == (
        f"The MQTT broker at {BROKER} rejected the login: {reason.lower()}. "
        "Check mqtt.username and mqtt.password, and the user's permissions on the broker."
    )


def test_a_rejected_login_gives_the_configured_advice() -> None:
    client = FakeMqttClient(script=[refused("Not authorized")])
    delivery = MqttDelivery(make_mqtt_config(), client=client, login_advice="Ask the admin.")
    with pytest.raises(LoginRejected) as raised:
        delivery.connect()
    assert str(raised.value) == (
        f"The MQTT broker at {BROKER} rejected the login: not authorized. Ask the admin."
    )


@pytest.mark.parametrize("reason", ["Bad user name or password", "Not authorized"])
def test_a_rejected_login_message_leaves_out_the_password(reason: str) -> None:
    _, error = _rejection(reason)
    assert PASSWORD not in str(error)


def test_a_rejected_login_logs_no_retry_warning(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    _rejection("Not authorized")
    assert _warnings(caplog) == []


# --------------------------------------------------------------------------- #
# One log line per failed attempt (design D4)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("failure", "reason"),
    [
        (SOCKET_FAILURE, "ConnectionRefusedError"),
        (refused("Server unavailable"), "Server unavailable"),
        (CLOSED_BEFORE_ANSWER, "connection closed before the broker answered"),
        (THREAD_ENDS, "network thread stopped"),
    ],
    ids=["socket-failure", "refusal", "closed-before-answer", "thread-ended"],
)
def test_each_failed_attempt_logs_one_warning(
    caplog: pytest.LogCaptureFixture, failure: Attempt, reason: str
) -> None:
    caplog.set_level(logging.WARNING)
    _connect(failure, ACCEPT)
    assert _warnings(caplog) == [
        f"Could not connect to the MQTT broker at {BROKER} ({reason}); trying again"
    ]


def test_every_failed_attempt_gets_its_own_warning(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    _connect(SOCKET_FAILURE, CLOSED_BEFORE_ANSWER, refused("Server unavailable"), ACCEPT)
    assert len(_warnings(caplog)) == 3


def test_failed_attempt_warnings_leave_out_the_password(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    _connect(SOCKET_FAILURE, CLOSED_BEFORE_ANSWER, refused("Server unavailable"), ACCEPT)
    assert all(PASSWORD not in record.getMessage() for record in caplog.records)


def test_a_script_with_no_outcome_fails_instead_of_hanging() -> None:
    # Guards the fake itself: a script that runs out must end the test, not hang it.
    with pytest.raises(AssertionError, match="no attempts left"):
        _connect(SOCKET_FAILURE)
