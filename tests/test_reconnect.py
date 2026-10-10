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
from datetime import UTC, datetime

import paho.mqtt.client as mqtt
import pytest

from pierpressure.core.model import Verdict
from pierpressure.delivery import mqtt as delivery_mqtt
from pierpressure.delivery.mqtt import (
    MqttDelivery,
    health_state_topic,
    refresh_command_topic,
    verdict_state_topic,
)
from pierpressure.health import ProviderHealth

from .conftest import (
    ACCEPT,
    SOCKET_FAILURE,
    THREAD_ENDS,
    FakeMqttClient,
    Published,
    make_document,
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


def test_a_rejected_login_during_a_reconnect_gives_the_configured_advice(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client, login_advice="Ask the admin.")
    delivery.connect()
    caplog.set_level(logging.ERROR)
    client.drop([refused("Not authorized"), ACCEPT])
    delivery.close()
    assert _messages(caplog, logging.ERROR) == [
        f"The MQTT broker at {BROKER} rejected the login: not authorized. Ask the admin. "
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


def test_close_stops_the_watcher_before_the_loop() -> None:
    # Count only this delivery's watcher: other tests may leave theirs running.
    before = set(_watchers())
    fixture = Started()
    watchers_at_loop_stop: list[int] = []
    loop_stop = fixture.client.loop_stop

    def record_then_stop() -> None:
        watchers_at_loop_stop.append(len(set(_watchers()) - before))
        loop_stop()

    fixture.client.loop_stop = record_then_stop  # type: ignore[method-assign]
    fixture.delivery.close()
    assert watchers_at_loop_stop == [0]


def test_close_leaves_no_watcher_running() -> None:
    before = set(_watchers())
    fixture = Started()
    assert set(_watchers()) - before
    fixture.delivery.close()
    assert set(_watchers()) - before == set()


# --------------------------------------------------------------------------- #
# Review fixes: shutdown, unreported drops, unanswered subscriptions
# --------------------------------------------------------------------------- #


def test_a_clean_shutdown_logs_no_lost_connection(caplog: pytest.LogCaptureFixture) -> None:
    fixture = Started()
    caplog.set_level(logging.WARNING)
    fixture.delivery.close()
    assert _messages(caplog, logging.WARNING) == []


def test_an_accept_with_no_reported_drop_is_a_reconnect(started: Started) -> None:
    started.client.active_subscriptions.clear()  # the broker forgot the old session
    started.client.accept_again()
    assert (started.reconnects, started.client.active_subscriptions) == (1, set(TOPICS))


def test_a_lost_connection_forgets_unanswered_subscriptions() -> None:
    # The answers to the startup subscriptions are lost with the old session.
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    delivery.subscribe_refresh(PIERS, lambda _pier: None)
    client.drop([SOCKET_FAILURE, ACCEPT])
    delivery.close()
    # The reconnect's subscriptions were answered; none of the lost ones linger.
    assert delivery._unanswered == {}


# --------------------------------------------------------------------------- #
# Holding publishes while disconnected (publish-failure-resilience D1)
# --------------------------------------------------------------------------- #


def _health() -> ProviderHealth:
    return ProviderHealth.empty(
        key="open_meteo",
        name="Open-Meteo",
        role="base",
        tracking_since=datetime(2026, 10, 9, 9, 0, tzinfo=UTC),
    )


def test_nothing_is_handed_to_the_client_while_disconnected(started: Started) -> None:
    started.client.drop([SOCKET_FAILURE])
    before = len(started.client.published)

    started.delivery.publish_health("backyard", [_health()])
    started.delivery.publish_verdict(make_document(pier="backyard"))
    started.delivery.go_online()
    started.delivery.replay()

    assert started.client.published[before:] == []


def test_the_replay_after_the_reconnect_sends_the_held_payloads(started: Started) -> None:
    started.delivery.publish_verdict(make_document(pier="backyard"))
    started.client.drop([SOCKET_FAILURE])
    started.delivery.publish_health("backyard", [_health()])
    started.delivery.publish_verdict(make_document(pier="backyard", verdict=Verdict.GO, score=90))
    started.client.accept_again()
    before = len(started.client.published)

    started.delivery.replay()

    replayed = started.client.published[before:]
    state = verdict_state_topic(BASE, "backyard")
    assert [p.payload for p in replayed if p.topic == state] == ["GO"]
    assert any(p.topic == health_state_topic(BASE, "backyard", "open_meteo") for p in replayed)
    assert all(p.retain for p in replayed)


def test_a_publish_after_the_reconnect_goes_to_the_client(started: Started) -> None:
    started.client.drop([SOCKET_FAILURE])
    started.client.accept_again()
    before = len(started.client.published)

    started.delivery.go_online()

    assert [p.topic for p in started.client.published[before:]] == [
        delivery_mqtt.availability_topic(BASE)
    ]


# --------------------------------------------------------------------------- #
# stop-goes-offline: a planned stop publishes a retained offline first
# --------------------------------------------------------------------------- #

STATUS = delivery_mqtt.availability_topic(BASE)


def test_close_publishes_a_retained_offline_before_it_disconnects() -> None:
    fixture = Started()
    fixture.delivery.close()

    assert fixture.client.publishes_to(STATUS)[-1] == Published(STATUS, "offline", 1, True)
    calls = fixture.client.calls
    assert calls[-3:] == [f"publish {STATUS}", "disconnect", "loop_stop"]


def test_close_waits_two_seconds_at_most_for_the_offline() -> None:
    fixture = Started()
    fixture.delivery.close()
    assert fixture.client.wait_timeouts == [2.0]


def test_close_while_disconnected_publishes_nothing(started: Started) -> None:
    started.client.drop([SOCKET_FAILURE])
    before = len(started.client.published)

    started.delivery.close()

    assert started.client.published[before:] == []
    assert started.client.calls[-2:] == ["disconnect", "loop_stop"]


def test_an_unconfirmed_offline_still_lets_close_finish(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fixture = Started()
    fixture.client.leave_unconfirmed(STATUS)

    with caplog.at_level(logging.WARNING):
        fixture.delivery.close()

    assert fixture.client.calls[-2:] == ["disconnect", "loop_stop"]
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "offline" in warnings[0].getMessage()


def test_a_refused_offline_still_lets_close_finish(caplog: pytest.LogCaptureFixture) -> None:
    fixture = Started()
    fixture.client.fail_publish(STATUS, mqtt.MQTT_ERR_QUEUE_SIZE)

    with caplog.at_level(logging.WARNING):
        fixture.delivery.close()

    assert fixture.client.calls[-2:] == ["disconnect", "loop_stop"]
    assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 1


def test_a_second_close_publishes_nothing() -> None:
    fixture = Started()
    fixture.delivery.close()
    before = len(fixture.client.published)

    fixture.delivery.close()

    assert fixture.client.published[before:] == []
