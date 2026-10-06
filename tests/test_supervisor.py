"""ha-addon-mqtt-service: the Supervisor's mqtt service lookup (design D3-D5)."""

from __future__ import annotations

import json
import logging
import socket
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from pierpressure import supervisor
from pierpressure.core.config import BrokerSettings
from pierpressure.supervisor import SupervisorError, fetch_mqtt_broker

TOKEN = "supervisor-token-123"
PASSWORD = "broker-password-456"
SERVICE_URL = "http://supervisor/services/mqtt"

BROKER_DATA: dict[str, Any] = {
    "host": "core-mosquitto",
    "port": 1883,
    "ssl": False,
    "protocol": "3.1.1",
    "username": "addons",
    "password": PASSWORD,
    "addon": "core_mosquitto",
}


class FakeTime:
    """A monotonic clock that only moves when the code sleeps or a request runs."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


Reply = httpx.Response | Exception


def _ok(**overrides: Any) -> httpx.Response:
    data = {**BROKER_DATA, **overrides}
    return httpx.Response(200, json={"result": "ok", "data": data})


def _not_enabled() -> httpx.Response:
    return httpx.Response(400, json={"result": "error", "message": "Service not enabled"})


class Supervisor:
    """A scripted Supervisor behind ``httpx.MockTransport``.

    Each request takes the next reply; the last one repeats. ``request_seconds``
    is how long each request takes on the fake clock. ``starts`` records the
    fake-clock time at which each request began.
    """

    def __init__(self, time: FakeTime, replies: list[Reply], request_seconds: float = 0.0):
        self.time = time
        self.replies = replies
        self.request_seconds = request_seconds
        self.requests: list[httpx.Request] = []
        self.starts: list[float] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        self.starts.append(self.time.now)
        self.time.now += self.request_seconds
        reply = self.replies[min(len(self.requests), len(self.replies)) - 1]
        if isinstance(reply, Exception):
            raise reply
        return reply

    def fetch(self) -> BrokerSettings:
        client = httpx.Client(transport=httpx.MockTransport(self.handle))
        return fetch_mqtt_broker(
            TOKEN, client=client, sleep=self.time.sleep, monotonic=self.time.monotonic
        )


@pytest.fixture
def time() -> FakeTime:
    return FakeTime()


def _supervisor(time: FakeTime, *replies: Reply, request_seconds: float = 0.0) -> Supervisor:
    return Supervisor(time, list(replies), request_seconds)


# --------------------------------------------------------------------------- #
# 2.1 — a successful lookup
# --------------------------------------------------------------------------- #


def test_returns_the_broker_settings(time: FakeTime) -> None:
    broker = _supervisor(time, _ok()).fetch()
    assert broker == BrokerSettings(
        host="core-mosquitto", port=1883, username="addons", password=PASSWORD
    )


def test_sends_the_token_to_the_mqtt_service(time: FakeTime) -> None:
    fake = _supervisor(time, _ok())
    fake.fetch()
    [request] = fake.requests
    assert (request.method, str(request.url)) == ("GET", SERVICE_URL)
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"


def test_missing_credentials_come_back_as_none(time: FakeTime) -> None:
    data = {k: v for k, v in BROKER_DATA.items() if k not in ("username", "password")}
    reply = httpx.Response(200, json={"result": "ok", "data": data})
    broker = _supervisor(time, reply).fetch()
    assert (broker.username, broker.password) == (None, None)


# --------------------------------------------------------------------------- #
# 2.2 — the bounded wait
# --------------------------------------------------------------------------- #

_NOT_YET: list[Callable[[], Reply]] = [
    _not_enabled,
    lambda: httpx.Response(404),
    lambda: httpx.Response(500),
    lambda: httpx.Response(503),
    lambda: httpx.ConnectError("connection refused"),
    lambda: httpx.ReadTimeout("timed out"),
    lambda: httpx.Response(200, text="<html>not json</html>"),
    lambda: httpx.Response(200, json={"result": "ok", "data": {"port": 1883}}),
    lambda: httpx.Response(200, json={"result": "ok", "data": {"host": "core-mosquitto"}}),
    lambda: httpx.Response(200, json={"result": "ok"}),
]
_NOT_YET_IDS = [
    "400-not-enabled",
    "404",
    "500",
    "503",
    "connect-error",
    "timeout",
    "not-json",
    "no-host",
    "no-port",
    "no-data",
]


@pytest.mark.parametrize("not_yet", _NOT_YET, ids=_NOT_YET_IDS)
def test_a_missing_broker_is_retried_until_it_appears(
    time: FakeTime, not_yet: Callable[[], Reply]
) -> None:
    fake = _supervisor(time, not_yet(), not_yet(), _ok())
    assert fake.fetch().host == "core-mosquitto"
    assert len(fake.requests) == 3


def test_retries_pause_two_seconds(time: FakeTime) -> None:
    _supervisor(time, _not_enabled(), _not_enabled(), _ok()).fetch()
    assert time.sleeps == [2.0, 2.0]


def test_no_request_starts_later_than_sixty_seconds_after_the_first(time: FakeTime) -> None:
    fake = _supervisor(time, _not_enabled(), request_seconds=0.75)
    with pytest.raises(SupervisorError):
        fake.fetch()
    assert fake.starts[-1] - fake.starts[0] <= 60.0


def test_the_wait_uses_the_whole_sixty_seconds(time: FakeTime) -> None:
    fake = _supervisor(time, _not_enabled(), request_seconds=0.75)
    with pytest.raises(SupervisorError):
        fake.fetch()
    assert fake.starts[-1] - fake.starts[0] == pytest.approx(60.0)


def test_the_last_pause_is_shortened_to_end_at_the_deadline(time: FakeTime) -> None:
    fake = _supervisor(time, _not_enabled(), request_seconds=0.75)
    with pytest.raises(SupervisorError):
        fake.fetch()
    assert time.sleeps[-1] < 2.0
    assert fake.starts[0] + 60.0 == pytest.approx(fake.starts[-1])


def test_timeouts_end_the_wait_within_sixty_five_seconds(time: FakeTime) -> None:
    fake = _supervisor(time, httpx.ReadTimeout("timed out"), request_seconds=5.0)
    with pytest.raises(SupervisorError):
        fake.fetch()
    assert time.now - fake.starts[0] <= 65.0


def test_no_broker_error_names_both_fixes(time: FakeTime) -> None:
    with pytest.raises(SupervisorError) as caught:
        _supervisor(time, _not_enabled()).fetch()
    message = str(caught.value)
    assert "No MQTT broker was found" in message
    assert "Mosquitto broker add-on" in message
    assert "mqtt.host" in message


def test_the_first_miss_logs_one_line(time: FakeTime, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="pierpressure"):
        _supervisor(time, _not_enabled(), _not_enabled(), _not_enabled(), _ok()).fetch()
    waiting = [r for r in caplog.records if r.name == "pierpressure.supervisor"]
    assert len(waiting) == 1
    assert "mqtt service" in waiting[0].getMessage()


# --------------------------------------------------------------------------- #
# 2.3 — failures that end the lookup at once
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("status", [401, 403])
def test_access_refused_fails_at_once(time: FakeTime, status: int) -> None:
    fake = _supervisor(time, httpx.Response(status), _ok())
    with pytest.raises(SupervisorError, match="refused access to the mqtt service") as caught:
        fake.fetch()
    assert len(fake.requests) == 1
    assert "mqtt.host" in str(caught.value)
    assert "report" in str(caught.value)


def test_a_tls_broker_fails_at_once(time: FakeTime) -> None:
    fake = _supervisor(time, _ok(ssl=True))
    with pytest.raises(SupervisorError, match="requires TLS") as caught:
        fake.fetch()
    assert len(fake.requests) == 1
    assert "mqtt.port" in str(caught.value)


def test_another_mqtt_version_fails_at_once(time: FakeTime) -> None:
    fake = _supervisor(time, _ok(protocol="3.1"))
    with pytest.raises(SupervisorError, match="MQTT 3.1,") as caught:
        fake.fetch()
    assert len(fake.requests) == 1
    assert "only MQTT 3.1.1" in str(caught.value)


def test_a_missing_protocol_counts_as_3_1_1(time: FakeTime) -> None:
    data = {k: v for k, v in BROKER_DATA.items() if k != "protocol"}
    reply = httpx.Response(200, json={"result": "ok", "data": data})
    assert _supervisor(time, reply).fetch().host == "core-mosquitto"


# --------------------------------------------------------------------------- #
# Secrets stay out of errors and logs (task 2.5)
# --------------------------------------------------------------------------- #

_FAILURES: list[Callable[[], list[Reply]]] = [
    lambda: [_not_enabled()],
    lambda: [httpx.Response(401)],
    lambda: [_ok(ssl=True)],
    lambda: [_ok(protocol="3.1")],
    lambda: [httpx.ConnectError(f"refused with {TOKEN}")],
    lambda: [httpx.Response(200, text=json.dumps({"data": {"password": PASSWORD}}))],
]


@pytest.mark.parametrize("replies", _FAILURES)
def test_errors_and_logs_never_contain_secrets(
    time: FakeTime, caplog: pytest.LogCaptureFixture, replies: Callable[[], list[Reply]]
) -> None:
    with caplog.at_level(logging.DEBUG), pytest.raises(SupervisorError) as caught:
        _supervisor(time, *replies()).fetch()
    for text in [str(caught.value), caplog.text]:
        assert TOKEN not in text
        assert PASSWORD not in text


# --------------------------------------------------------------------------- #
# 2.4 — proxy settings never receive the token
# --------------------------------------------------------------------------- #


def test_the_request_bypasses_proxy_settings(
    time: FakeTime, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example:3128")
    monkeypatch.setenv("ALL_PROXY", "http://proxy.example:3128")
    reached: list[str] = []

    def record(address: tuple[str, int], *_args: Any, **_kwargs: Any) -> socket.socket:
        reached.append(address[0])
        raise OSError("blocked in test")

    monkeypatch.setattr(socket, "create_connection", record)
    with pytest.raises(SupervisorError):
        fetch_mqtt_broker(TOKEN, sleep=time.sleep, monotonic=_jump_past_deadline(time))
    assert reached
    assert set(reached) == {"supervisor"}


def _jump_past_deadline(time: FakeTime) -> Callable[[], float]:
    """A clock that reads past the deadline after the first request."""
    readings = iter([time.now])

    def monotonic() -> float:
        return next(readings, time.now + supervisor.WAIT_SECONDS + 1.0)

    return monotonic
