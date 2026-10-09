"""Task 7.1: the entry point wires config -> broker -> startup publish."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import pierpressure
from pierpressure import __main__ as entry
from pierpressure.core.clock import FixedClock
from pierpressure.core.config import AppConfig, BrokerSettings, MqttConfig, RecomputeConfig
from pierpressure.delivery.mqtt import (
    DeliveryError,
    LoginRejected,
    MqttDelivery,
    availability_topic,
    verdict_state_topic,
)
from pierpressure.service import Service
from pierpressure.supervisor import SupervisorError

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
    # run() publishes the retained online availability; connect() no longer does.
    online = client.publishes_to(availability_topic("pierpressure"))
    assert [(p.payload, p.retain) for p in online] == [("online", True)]


def test_main_exits_nonzero_on_bad_config(tmp_path: object) -> None:
    from pierpressure.__main__ import main

    assert main(["/nonexistent/config.yaml"]) == 1


def test_main_logs_version_before_config_error(caplog: pytest.LogCaptureFixture) -> None:
    from pierpressure.__main__ import main

    with caplog.at_level(logging.INFO, logger="pierpressure"):
        main(["/nonexistent/config.yaml"])

    messages = [record.getMessage() for record in caplog.records]
    assert messages[0] == f"PierPressure {pierpressure.__version__}"
    assert messages[1].startswith("Configuration error")


# --------------------------------------------------------------------------- #
# ha-addon-mqtt-service: the broker's source (design D1, D2, D6)
# --------------------------------------------------------------------------- #

PIERS = """
recompute:
  interval_seconds: 900
piers:
  - id: backyard
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
"""
FILE_BROKER = "mqtt:\n  host: broker.lan\n  username: me\n  password: file-secret\n"
SUPERVISOR_PASSWORD = "supervisor-secret"
SUPERVISOR_BROKER = BrokerSettings(
    host="core-mosquitto", port=1883, username="addons", password=SUPERVISOR_PASSWORD
)


class StartupStub:
    """Stands in for the broker connection and the Supervisor lookup.

    ``connected_to`` records the MQTT config the delivery was built with; its
    ``connect`` then fails, so ``main`` stops right after config loading.
    ``supervisor_calls`` records each token the Supervisor was asked with.
    """

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        supervisor: Any = SUPERVISOR_BROKER,
        connect_error: BaseException | None = None,
        reject_login: bool = False,
    ):
        self.connected_to: list[MqttConfig] = []
        self.calls: list[str] = []
        self.login_advice: list[str | None] = []
        self.closed = False
        self.supervisor_calls: list[str] = []
        stub = self

        class FakeDelivery:
            def __init__(
                self, mqtt: MqttConfig, *, login_advice: str | None = None, **_kwargs: Any
            ) -> None:
                stub.connected_to.append(mqtt)
                stub.login_advice.append(login_advice)
                self._advice = login_advice

            def on_reconnect(self, _callback: Any) -> None:
                stub.calls.append("on_reconnect")

            def connect(self) -> None:
                stub.calls.append("connect")
                if reject_login:
                    # As MqttDelivery does: its own advice, or the default.
                    raise LoginRejected("core-mosquitto:1883", "Not authorized", self._advice)
                raise connect_error or DeliveryError("stopped by test")

            def close(self) -> None:
                stub.closed = True

        def fake_fetch(token: str) -> BrokerSettings:
            stub.supervisor_calls.append(token)
            if isinstance(supervisor, Exception):
                raise supervisor
            assert isinstance(supervisor, BrokerSettings)
            return supervisor

        monkeypatch.setattr(entry, "MqttDelivery", FakeDelivery)
        monkeypatch.setattr(entry, "fetch_mqtt_broker", fake_fetch)


def _config(tmp_path: Path, text: str) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_in_an_addon_main_uses_the_supervisor_broker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    stub = StartupStub(monkeypatch)
    entry.main([_config(tmp_path, PIERS)])
    assert stub.supervisor_calls == ["token-1"]
    assert [(m.host, m.username) for m in stub.connected_to] == [("core-mosquitto", "addons")]


def test_a_file_host_means_main_never_asks_the_supervisor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    stub = StartupStub(monkeypatch)
    entry.main([_config(tmp_path, FILE_BROKER + PIERS)])
    assert stub.supervisor_calls == []
    assert [m.host for m in stub.connected_to] == ["broker.lan"]


@pytest.mark.parametrize("token", [None, ""], ids=["unset", "empty"])
def test_outside_an_addon_main_never_asks_the_supervisor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, token: str | None
) -> None:
    if token is None:
        monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    else:
        monkeypatch.setenv("SUPERVISOR_TOKEN", token)
    stub = StartupStub(monkeypatch)
    assert entry.main([_config(tmp_path, PIERS)]) == 1
    assert stub.supervisor_calls == []


def test_outside_an_addon_the_missing_host_error_is_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    StartupStub(monkeypatch)
    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        entry.main([_config(tmp_path, PIERS)])
    [error] = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert error.startswith("Configuration error: Invalid mqtt/recompute configuration")


def test_a_supervisor_failure_is_a_configuration_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    stub = StartupStub(monkeypatch, supervisor=SupervisorError("No MQTT broker was found."))
    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, PIERS)]) == 1
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert errors == ["Configuration error: No MQTT broker was found."]
    assert stub.connected_to == []


def test_credentials_without_a_host_stop_before_asking_the_supervisor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    stub = StartupStub(monkeypatch)
    assert entry.main([_config(tmp_path, "mqtt:\n  username: me\n" + PIERS)]) == 1
    assert stub.supervisor_calls == []


@pytest.mark.parametrize(
    ("text", "token", "expected"),
    [
        (PIERS, "token-1", "MQTT broker from the Supervisor's mqtt service: core-mosquitto:1883"),
        (FILE_BROKER + PIERS, None, "MQTT broker from config.yaml: broker.lan:1883"),
    ],
    ids=["supervisor", "file"],
)
def test_main_logs_the_broker_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    text: str,
    token: str | None,
    expected: str,
) -> None:
    if token is None:
        monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    else:
        monkeypatch.setenv("SUPERVISOR_TOKEN", token)
    StartupStub(monkeypatch)
    with caplog.at_level(logging.DEBUG):
        entry.main([_config(tmp_path, text)])
    assert expected in [r.getMessage() for r in caplog.records]
    assert SUPERVISOR_PASSWORD not in caplog.text
    assert "file-secret" not in caplog.text


def test_a_supervisor_broker_gets_the_mosquitto_login_advice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    stub = StartupStub(monkeypatch)
    entry.main([_config(tmp_path, PIERS)])
    assert stub.login_advice == [entry.SUPERVISOR_LOGIN_ADVICE]


def test_a_file_broker_gets_the_default_login_advice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    stub = StartupStub(monkeypatch)
    entry.main([_config(tmp_path, FILE_BROKER + PIERS)])
    assert stub.login_advice == [None]


def test_a_rejected_supervisor_login_points_to_the_mosquitto_addon(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    StartupStub(monkeypatch, reject_login=True)
    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, PIERS)]) == 1
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert errors == [
        "Startup delivery failure: The MQTT broker at core-mosquitto:1883 rejected the "
        "login: not authorized. The username and password came from the Supervisor's "
        "mqtt service, so restart the Mosquitto broker add-on, or set mqtt.host to use "
        "your own broker login."
    ]


def test_a_rejected_file_login_names_the_file_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    StartupStub(monkeypatch, reject_login=True)
    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, FILE_BROKER + PIERS)]) == 1
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert errors == [
        "Startup delivery failure: The MQTT broker at core-mosquitto:1883 rejected the "
        "login: not authorized. Check mqtt.username and mqtt.password, and the user's "
        "permissions on the broker."
    ]


def test_main_listens_for_reconnects_before_it_connects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A reconnect just after connect() returns must still reach the service.
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    stub = StartupStub(monkeypatch)
    entry.main([_config(tmp_path, FILE_BROKER + PIERS)])
    assert stub.calls == ["on_reconnect", "connect"]


def test_ctrl_c_while_waiting_for_the_broker_shuts_down_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub = StartupStub(monkeypatch, connect_error=KeyboardInterrupt())
    assert entry.main([_config(tmp_path, FILE_BROKER + PIERS)]) == 0
    assert stub.closed
