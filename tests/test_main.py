"""Task 7.1: the entry point wires config -> broker -> startup publish."""

from __future__ import annotations

import inspect
import json
import logging
import os
import signal
from collections.abc import Iterator
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

import pytest

import pierpressure
from pierpressure import __main__ as entry
from pierpressure.conditions.provider import assemble_snapshot
from pierpressure.core.clock import FixedClock
from pierpressure.core.config import AppConfig, BrokerSettings, MqttConfig, RecomputeConfig
from pierpressure.core.producer import produce_verdict
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
from .offline_guard import no_network
from .test_golden_verdict import _INSTANT, _base_full, _secondary_full


@pytest.fixture(autouse=True)
def restore_sigterm() -> Iterator[None]:
    """``main`` installs a SIGTERM handler; put the test process's own back after."""
    previous = signal.getsignal(signal.SIGTERM)
    yield
    signal.signal(signal.SIGTERM, previous)


@pytest.fixture(autouse=True)
def options_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``load_app_config`` at a temporary ``options.json``, absent at first.

    No test reads the real ``/data/options.json``; a test writes this path to
    give the add-on's Configuration form values (addon-options-form D2).
    """
    path = tmp_path / "options.json"
    monkeypatch.setattr(entry, "load_app_config", partial(entry.load_app_config, options_path=path))
    return path


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


# --------------------------------------------------------------------------- #
# addon-options-form D2, D4: the Configuration form before the config file
# --------------------------------------------------------------------------- #

BACKYARD = {"id": "backyard", "latitude": 51.5, "longitude": -0.12, "elevation_m": 30.0}
ROOF = """
recompute:
  interval_seconds: 900
piers:
  - id: roof
    latitude: 48.85
    longitude: 2.35
    elevation_m: 35
"""


def _form(path: Path, *piers: Any, interval_seconds: int = 600) -> None:
    path.write_text(
        json.dumps({"interval_seconds": interval_seconds, "piers": list(piers)}), encoding="utf-8"
    )


def _load(config_path: str) -> AppConfig:
    return entry.load_app_config(config_path).config


def test_a_form_setup_without_a_file_uses_the_form_and_the_supervisor_broker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, BACKYARD, interval_seconds=600)
    stub = StartupStub(monkeypatch)
    missing = str(tmp_path / "config.yaml")

    config = _load(missing)
    entry.main([missing])

    assert [p.id for p in config.piers] == ["backyard"]
    assert config.recompute.interval_seconds == 600
    assert (config.mqtt.discovery_prefix, config.mqtt.base_topic) == (
        "homeassistant",
        "pierpressure",
    )
    assert stub.supervisor_calls == ["token-1", "token-1"]
    assert [m.host for m in stub.connected_to] == ["core-mosquitto"]


def test_an_empty_form_falls_back_to_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, interval_seconds=60)
    StartupStub(monkeypatch)

    config = _load(_config(tmp_path, PIERS))

    assert [p.id for p in config.piers] == ["backyard"]
    # The form's interval is ignored along with its empty pier list.
    assert config.recompute.interval_seconds == 900


def test_the_form_wins_over_an_existing_file_and_warns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, BACKYARD)
    StartupStub(monkeypatch)
    config_path = _config(tmp_path, FILE_BROKER + ROOF)

    with caplog.at_level(logging.WARNING, logger="pierpressure"):
        config = _load(config_path)

    assert [p.id for p in config.piers] == ["backyard"]
    # The file's broker is ignored too: the form always uses the Supervisor's.
    assert config.mqtt.host == "core-mosquitto"
    [warning] = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert config_path in warning
    assert "ignored" in warning


def test_a_bad_pier_in_the_saved_form_is_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, {**BACKYARD, "id": "north", "latitude": 95.0}, BACKYARD)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR):
        config = _load(str(tmp_path / "config.yaml"))

    assert [p.id for p in config.piers] == ["backyard"]
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert any("Skipping invalid pier 'north'" in error for error in errors)


def test_with_nothing_set_up_the_error_names_the_file_and_the_configuration_tab(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file)
    stub = StartupStub(monkeypatch)
    missing = str(tmp_path / "config.yaml")

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([missing]) == 1

    [error] = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert error.startswith("Configuration error: ")
    assert missing in error
    assert "Configuration tab" in error
    assert stub.supervisor_calls == []


def test_outside_an_addon_the_form_is_never_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    _form(options_file, BACKYARD)
    StartupStub(monkeypatch)

    config = _load(_config(tmp_path, FILE_BROKER + ROOF))

    assert [p.id for p in config.piers] == ["roof"]


def test_outside_an_addon_a_broken_form_is_never_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    options_file.write_text("{not json", encoding="utf-8")
    StartupStub(monkeypatch)

    config = _load(_config(tmp_path, FILE_BROKER + ROOF))

    assert [p.id for p in config.piers] == ["roof"]


@pytest.mark.parametrize(
    ("form", "expected"),
    [
        ([BACKYARD], "Settings from the Configuration tab"),
        ([], "Settings from config.yaml"),
    ],
    ids=["form", "file"],
)
def test_main_logs_the_settings_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    form: list[dict[str, Any]],
    expected: str,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, *form)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.INFO, logger="pierpressure"):
        entry.main([_config(tmp_path, PIERS)])

    assert expected in [r.getMessage() for r in caplog.records]


def test_load_app_config_reads_the_supervisors_options_file_by_default() -> None:
    # The autouse fixture swaps in a temporary path, so pin the real default here.
    original = entry.load_app_config.func  # type: ignore[attr-defined]
    default = inspect.signature(original).parameters["options_path"].default
    assert default == "/data/options.json"


# A form user's broker errors must not point only to config.yaml, which is not
# read while the form lists piers (design "Risks / Trade-offs").
FORM_NOTE = "config.yaml is not read while the Configuration tab lists piers"


@pytest.mark.parametrize(
    ("form", "from_form"), [([BACKYARD], True), ([], False)], ids=["form", "file"]
)
def test_load_app_config_reports_whether_the_form_was_the_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    form: list[dict[str, Any]],
    from_form: bool,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, *form)
    StartupStub(monkeypatch)

    loaded = entry.load_app_config(_config(tmp_path, PIERS))

    assert loaded.from_form is from_form
    assert loaded.broker_from_supervisor


@pytest.mark.parametrize(
    "message",
    [
        "No MQTT broker was found. Install the Mosquitto broker add-on, or set mqtt.host "
        "in config.yaml.",
        "The Supervisor's MQTT broker requires TLS. Set mqtt.host and mqtt.port in config.yaml.",
    ],
    ids=["no-broker", "tls"],
)
def test_a_form_users_supervisor_error_says_the_file_is_not_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    message: str,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, BACKYARD)
    StartupStub(monkeypatch, supervisor=SupervisorError(message))

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([str(tmp_path / "config.yaml")]) == 1

    [error] = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert error.startswith(f"Configuration error: {message}")
    assert FORM_NOTE in error


def test_a_file_users_supervisor_error_keeps_its_wording(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file)
    StartupStub(monkeypatch, supervisor=SupervisorError("No MQTT broker was found."))

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, PIERS)]) == 1

    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert errors == ["Configuration error: No MQTT broker was found."]


def test_a_form_users_rejected_login_says_the_file_is_not_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, BACKYARD)
    stub = StartupStub(monkeypatch, reject_login=True)

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([str(tmp_path / "config.yaml")]) == 1

    # The adapter keeps this advice for a login rejected during a reconnect too.
    assert stub.login_advice == [entry.FORM_LOGIN_ADVICE]
    [error] = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert error.startswith("Startup delivery failure: The MQTT broker at core-mosquitto:1883")
    assert "restart the Mosquitto broker add-on" in error
    assert FORM_NOTE in error


def test_a_file_users_rejected_supervisor_login_keeps_its_advice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file)
    stub = StartupStub(monkeypatch, reject_login=True)

    entry.main([_config(tmp_path, PIERS)])

    assert stub.login_advice == [entry.SUPERVISOR_LOGIN_ADVICE]


# --------------------------------------------------------------------------- #
# stop-goes-offline D3: SIGTERM stops the process the same way as Ctrl-C
# --------------------------------------------------------------------------- #


class _UnhandledSigterm(Exception):
    """Raised by the guard handler: ``main`` left SIGTERM to its default action."""


@pytest.fixture
def sigterm_guard() -> None:
    """Fail the test, instead of killing pytest, if ``main`` handles no SIGTERM.

    ``restore_sigterm`` puts the test process's own handler back after.
    """

    def guard(_signum: int, _frame: Any) -> None:
        raise _UnhandledSigterm

    signal.signal(signal.SIGTERM, guard)


class RunningStub:
    """A delivery that connects, and a service whose ``run`` the test controls.

    ``events`` records ``subscribe_refresh``, ``run`` and ``close`` in order.
    """

    def __init__(self, monkeypatch: pytest.MonkeyPatch, terminate_in: str) -> None:
        self.events: list[str] = []
        stub = self

        def step(name: str) -> None:
            stub.events.append(name)
            if name == terminate_in:
                os.kill(os.getpid(), signal.SIGTERM)

        class FakeDelivery:
            def __init__(self, _mqtt: MqttConfig, **_kwargs: Any) -> None:
                pass

            def on_reconnect(self, _callback: Any) -> None:
                pass

            def connect(self) -> None:
                pass

            def subscribe_refresh(self, _pier_ids: Any, _callback: Any) -> None:
                step("subscribe_refresh")

            def close(self) -> None:
                stub.events.append("close")

        class FakeService:
            def __init__(self, *_args: Any, **_kwargs: Any) -> None:
                pass

            def enqueue_reconnect(self) -> None:
                pass

            def enqueue_refresh(self, _pier_id: str) -> None:
                pass

            def run(self) -> None:
                step("run")

        monkeypatch.setattr(entry, "MqttDelivery", FakeDelivery)
        monkeypatch.setattr(entry, "Service", FakeService)


@pytest.mark.usefixtures("sigterm_guard")
def test_sigterm_while_running_closes_the_delivery_and_exits_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    stub = RunningStub(monkeypatch, terminate_in="run")
    assert entry.main([_config(tmp_path, FILE_BROKER + PIERS)]) == 0
    assert stub.events == ["subscribe_refresh", "run", "close"]


@pytest.mark.usefixtures("sigterm_guard")
def test_sigterm_before_the_service_runs_still_closes_the_delivery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    stub = RunningStub(monkeypatch, terminate_in="subscribe_refresh")
    assert entry.main([_config(tmp_path, FILE_BROKER + PIERS)]) == 0
    assert stub.events == ["subscribe_refresh", "close"]


@pytest.mark.usefixtures("sigterm_guard")
def test_sigterm_while_loading_the_config_exits_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Inside an add-on, loading the config can wait on the Supervisor.
    def terminate(_path: str) -> Any:
        os.kill(os.getpid(), signal.SIGTERM)

    monkeypatch.setattr(entry, "load_app_config", terminate)
    assert entry.main([_config(tmp_path, FILE_BROKER + PIERS)]) == 0


# --------------------------------------------------------------------------- #
# addon-form-horizon: the form sets each pier's horizon (design D1-D3)
# --------------------------------------------------------------------------- #

ROOF_FORM = {**BACKYARD, "id": "roof"}
POINTS = [[0, 10], [90, 25], [180, 5]]


def _form_piers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path, *piers: Any
) -> AppConfig:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, *piers)
    StartupStub(monkeypatch)
    return _load(str(tmp_path / "config.yaml"))


@pytest.mark.parametrize(
    ("fields", "altitude"),
    [
        ({"min_altitude": 15}, 15.0),
        ({}, 0.0),
        ({"min_altitude": 15, "horizon_points": "  "}, 15.0),
    ],
    ids=["floor", "open-sky", "blank-points-beside-floor"],
)
def test_the_form_sets_a_flat_horizon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    fields: dict[str, Any],
    altitude: float,
) -> None:
    config = _form_piers(tmp_path, monkeypatch, options_file, {**BACKYARD, **fields})

    [pier] = config.piers
    assert {pier.horizon_mask.alt_at(az) for az in range(0, 360, 15)} == {altitude}


def test_form_points_match_the_same_points_in_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    file_text = FILE_BROKER + PIERS + f"    horizon:\n      points: {POINTS}\n"
    [file_pier] = _load(_config(tmp_path, file_text)).piers

    form = {**BACKYARD, "horizon_points": json.dumps(POINTS)}
    [form_pier] = _form_piers(tmp_path, monkeypatch, options_file, form).piers

    assert form_pier.horizon_mask == file_pier.horizon_mask
    assert form_pier.horizon_mask.alt_at(90) == 25.0


@pytest.mark.parametrize(
    ("fields", "names_field"),
    [
        ({"horizon_points": "[[0, 10], [90"}, True),
        ({"horizon_points": 5}, True),
        ({"horizon_points": "[[0, 95]]"}, False),
        ({"min_altitude": 15, "horizon_points": "[[0, 10]]"}, False),
    ],
    ids=["unreadable", "not-text", "out-of-range", "both-fields"],
)
def test_a_bad_form_horizon_skips_only_its_pier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    fields: dict[str, Any],
    names_field: bool,
) -> None:
    with caplog.at_level(logging.ERROR):
        config = _form_piers(tmp_path, monkeypatch, options_file, {**BACKYARD, **fields}, ROOF_FORM)

    assert [p.id for p in config.piers] == ["roof"]
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    [error] = [e for e in errors if "Skipping invalid pier 'backyard'" in e]
    assert ("horizon_points" in error) is names_field


def test_malformed_saved_values_skip_only_their_pier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The Supervisor normally refuses these; the service does not rely on it.
    with caplog.at_level(logging.ERROR):
        config = _form_piers(
            tmp_path,
            monkeypatch,
            options_file,
            {**BACKYARD, "horizon_points": 5},
            "not a pier",
            ROOF_FORM,
        )

    assert [p.id for p in config.piers] == ["roof"]
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    skips = [e for e in errors if e.startswith("Skipping invalid pier")]
    assert len(skips) == 2
    assert any("'backyard'" in e and "horizon_points" in e for e in skips)


def test_a_bad_horizon_on_the_only_pier_stops_the_addon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, {**BACKYARD, "horizon_points": "[[0, 10], [90"})
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR):
        assert entry.main([str(tmp_path / "config.yaml")]) == 1

    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert any("'backyard'" in e and "horizon_points" in e for e in errors)
    assert errors[-1].startswith("Configuration error: No valid pier")


# --------------------------------------------------------------------------- #
# addon-form-equipment: the form sets each pier's equipment (design D1-D3)
# --------------------------------------------------------------------------- #

EQUIPMENT = {
    "focal_length_mm": 400.0,
    "sensor_width_mm": 23.5,
    "sensor_height_mm": 15.7,
    "reducer": 0.8,
}
EQUIPMENT_FORM = {f"equipment_{key}": value for key, value in EQUIPMENT.items()}
REQUIRED_EQUIPMENT_FORM = {
    key: value for key, value in EQUIPMENT_FORM.items() if key != "equipment_reducer"
}


def _equipment_file(equipment: dict[str, float]) -> str:
    lines = "".join(f"      {key}: {value}\n" for key, value in equipment.items())
    return FILE_BROKER + PIERS + "    equipment:\n" + lines


def _skip_error(caplog: pytest.LogCaptureFixture, pier_id: str) -> str:
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    [error] = [e for e in errors if f"Skipping invalid pier {pier_id!r}" in e]
    return error


def test_form_equipment_matches_the_same_equipment_in_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    [file_pier] = _load(_config(tmp_path, _equipment_file(EQUIPMENT))).piers

    [form_pier] = _form_piers(
        tmp_path, monkeypatch, options_file, {**BACKYARD, **EQUIPMENT_FORM}
    ).piers

    assert form_pier.equipment is not None
    assert form_pier.equipment == file_pier.equipment


def test_form_equipment_without_a_reducer_has_a_reducer_of_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    [pier] = _form_piers(
        tmp_path, monkeypatch, options_file, {**BACKYARD, **REQUIRED_EQUIPMENT_FORM}
    ).piers

    assert pier.equipment is not None
    assert pier.equipment.reducer == 1.0


def test_a_form_pier_without_equipment_fields_has_no_equipment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    [pier] = _form_piers(tmp_path, monkeypatch, options_file, BACKYARD).piers

    assert pier.equipment is None


def test_saved_null_equipment_counts_as_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    all_null = {**BACKYARD, **dict.fromkeys(EQUIPMENT_FORM)}
    null_height = {**ROOF_FORM, **REQUIRED_EQUIPMENT_FORM, "equipment_sensor_height_mm": None}

    with caplog.at_level(logging.ERROR):
        config = _form_piers(tmp_path, monkeypatch, options_file, all_null, null_height)

    [pier] = config.piers
    assert (pier.id, pier.equipment) == ("backyard", None)
    assert "sensor_height_mm" in _skip_error(caplog, "roof")


@pytest.mark.parametrize(
    ("fields", "missing"),
    [
        (
            {"equipment_focal_length_mm": 400.0, "equipment_sensor_width_mm": 23.5},
            "sensor_height_mm",
        ),
        ({"equipment_reducer": 0.8}, "focal_length_mm"),
    ],
    ids=["no-sensor-height", "reducer-alone"],
)
def test_incomplete_form_equipment_skips_only_its_pier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    fields: dict[str, float],
    missing: str,
) -> None:
    # The core's equipment check rejects the block, as it would a file's (D2).
    with caplog.at_level(logging.ERROR):
        config = _form_piers(tmp_path, monkeypatch, options_file, {**BACKYARD, **fields}, ROOF_FORM)

    assert [p.id for p in config.piers] == ["roof"]
    assert missing in _skip_error(caplog, "backyard")


@pytest.mark.parametrize("value", [0.0, -1.0], ids=["zero", "negative"])
@pytest.mark.parametrize("key", list(EQUIPMENT))
def test_a_form_equipment_value_of_zero_or_less_skips_only_its_pier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    key: str,
    value: float,
) -> None:
    # The Supervisor refuses a negative value on save; the service does not rely on it.
    bad = {**BACKYARD, **REQUIRED_EQUIPMENT_FORM, f"equipment_{key}": value}
    good = {**ROOF_FORM, **REQUIRED_EQUIPMENT_FORM}

    with caplog.at_level(logging.ERROR):
        config = _form_piers(tmp_path, monkeypatch, options_file, bad, good)

    assert [p.id for p in config.piers] == ["roof"]
    assert key in _skip_error(caplog, "backyard")


def test_an_equipment_mapping_beside_equipment_fields_skips_only_its_pier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    both = {**BACKYARD, "equipment": EQUIPMENT, "equipment_focal_length_mm": 400.0}

    with caplog.at_level(logging.ERROR):
        config = _form_piers(tmp_path, monkeypatch, options_file, both, ROOF_FORM)

    assert [p.id for p in config.piers] == ["roof"]
    assert "equipment" in _skip_error(caplog, "backyard")


def test_incomplete_equipment_on_the_only_pier_stops_the_addon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, {**BACKYARD, "equipment_focal_length_mm": 400.0})
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR):
        assert entry.main([str(tmp_path / "config.yaml")]) == 1

    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert any("Skipping invalid pier 'backyard'" in e for e in errors)
    assert errors[-1].startswith("Configuration error: No valid pier")


def test_form_equipment_ranks_like_file_equipment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    # The instant, conditions and London pier of tests/test_producer_targets.py's
    # equipment test, plus a horizon. The asserts below check that the top pick
    # still has a known size.
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    file_text = _equipment_file(EQUIPMENT) + "    horizon:\n      min_altitude: 15\n"
    [file_pier] = _load(_config(tmp_path, file_text)).piers
    form = {**BACKYARD, **EQUIPMENT_FORM, "min_altitude": 15}
    [form_pier] = _form_piers(tmp_path, monkeypatch, options_file, form).piers
    conditions = assemble_snapshot(_base_full(), _secondary_full())

    with no_network():
        from_file = produce_verdict(file_pier, FixedClock(_INSTANT), conditions)
        from_form = produce_verdict(form_pier, FixedClock(_INSTANT), conditions)

    assert from_form.to_json() == from_file.to_json()
    top = from_form.targets[0]
    assert top.size_arcmin is not None
    top_pick = f"Top pick {top.name or top.id} "
    framing = [r for r in from_form.reasons if r.startswith(top_pick) and "field of view" in r]
    assert len(framing) == 1, from_form.reasons


def test_a_form_pier_without_equipment_has_no_field_of_view_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    [pier] = _form_piers(tmp_path, monkeypatch, options_file, BACKYARD).piers
    conditions = assemble_snapshot(_base_full(), _secondary_full())

    with no_network():
        document = produce_verdict(pier, FixedClock(_INSTANT), conditions)

    assert document.targets
    assert not any("field of view" in r for r in document.reasons), document.reasons
