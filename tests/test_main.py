"""Task 7.1: the entry point wires config -> broker -> startup publish."""

from __future__ import annotations

import inspect
import json
import logging
import os
import signal
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

import httpx
import pytest

import pierpressure
from pierpressure import __main__ as entry
from pierpressure.conditions.provider import SourceForecast, assemble_snapshot
from pierpressure.core.clock import FixedClock
from pierpressure.core.config import (
    AppConfig,
    BrokerSettings,
    ConfigError,
    MqttConfig,
    RecomputeConfig,
)
from pierpressure.core.horizon import parse_horizon_text
from pierpressure.core.model import Verdict
from pierpressure.core.producer import produce_verdict
from pierpressure.delivery.mqtt import (
    DeliveryError,
    LoginRejected,
    MqttDelivery,
    availability_topic,
    verdict_state_topic,
)
from pierpressure.service import Service
from pierpressure.supervisor import SupervisorError, fetch_mqtt_broker

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
    ``supervisor`` is the broker to return, an error to raise, or a Supervisor
    reply that the real lookup turns into its error (addon-form-broker D5).
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

        def fake_fetch(token: str, **kwargs: Any) -> BrokerSettings:
            stub.supervisor_calls.append(token)
            if isinstance(supervisor, Exception):
                raise supervisor
            if isinstance(supervisor, httpx.Response):
                return _replay_supervisor(supervisor, token, **kwargs)
            assert isinstance(supervisor, BrokerSettings)
            return supervisor

        monkeypatch.setattr(entry, "MqttDelivery", FakeDelivery)
        monkeypatch.setattr(entry, "fetch_mqtt_broker", fake_fetch)


def _replay_supervisor(reply: httpx.Response, token: str, **kwargs: Any) -> BrokerSettings:
    """Run the real lookup against a Supervisor that always gives ``reply``, with no wait."""
    now = [0.0]

    def sleep(seconds: float) -> None:
        now[0] += seconds

    client = httpx.Client(transport=httpx.MockTransport(lambda _request: reply))
    return fetch_mqtt_broker(token, client=client, sleep=sleep, monotonic=lambda: now[0], **kwargs)


def _config(tmp_path: Path, text: str) -> str:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return str(path)


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
NINA_FIXTURE = Path(__file__).parent / "fixtures" / "nina_horizon.hrz"
SECRET = "pw-8c41f2"


def _form(path: Path, *piers: Any, interval_seconds: int = 600) -> None:
    path.write_text(
        json.dumps({"interval_seconds": interval_seconds, "piers": list(piers)}), encoding="utf-8"
    )


def _addon(monkeypatch: pytest.MonkeyPatch, options_file: Path, *piers: Any) -> None:
    """Run inside an add-on whose form lists ``piers``."""
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form(options_file, *piers)


def _load(config_path: str) -> AppConfig:
    return entry.load_app_config(config_path).config


def _errors(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]


def _no_file(tmp_path: Path) -> str:
    return str(tmp_path / "config.yaml")


def test_in_an_addon_main_uses_the_supervisor_broker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    stub = StartupStub(monkeypatch)
    entry.main([_no_file(tmp_path)])
    assert stub.supervisor_calls == ["token-1"]
    assert [(m.host, m.username) for m in stub.connected_to] == [("core-mosquitto", "addons")]


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
    [error] = _errors(caplog)
    assert error == "Configuration error: Invalid mqtt configuration: the mqtt block is missing"


def test_a_supervisor_failure_is_a_configuration_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    stub = StartupStub(monkeypatch, supervisor=SupervisorError("No MQTT broker was found."))
    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_no_file(tmp_path)]) == 1
    assert _errors(caplog) == ["Configuration error: No MQTT broker was found."]
    assert stub.connected_to == []


@pytest.mark.parametrize(
    ("text", "token", "expected"),
    [
        (None, "token-1", "MQTT broker from the Supervisor's mqtt service: core-mosquitto:1883"),
        (FILE_BROKER, "token-1", "MQTT broker from config.yaml: broker.lan:1883"),
        (FILE_BROKER + PIERS, None, "MQTT broker from config.yaml: broker.lan:1883"),
    ],
    ids=["supervisor", "addon-file", "outside-addon-file"],
)
def test_main_logs_the_broker_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    text: str | None,
    token: str | None,
    expected: str,
) -> None:
    _form(options_file, BACKYARD)
    if token is None:
        monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    else:
        monkeypatch.setenv("SUPERVISOR_TOKEN", token)
    StartupStub(monkeypatch)
    with caplog.at_level(logging.DEBUG):
        entry.main([_no_file(tmp_path) if text is None else _config(tmp_path, text)])
    assert expected in [r.getMessage() for r in caplog.records]
    assert SUPERVISOR_PASSWORD not in caplog.text
    assert "file-secret" not in caplog.text


def test_a_supervisor_broker_gets_the_mosquitto_login_advice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    stub = StartupStub(monkeypatch)
    entry.main([_no_file(tmp_path)])
    assert stub.login_advice == [entry.SUPERVISOR_LOGIN_ADVICE]


def test_a_file_broker_gets_the_default_login_advice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    stub = StartupStub(monkeypatch)
    entry.main([_config(tmp_path, FILE_BROKER)])
    assert stub.login_advice == [None]


def test_a_rejected_supervisor_login_points_to_the_mosquitto_addon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    StartupStub(monkeypatch, reject_login=True)
    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_no_file(tmp_path)]) == 1
    assert _errors(caplog) == [
        "Startup delivery failure: The MQTT broker at core-mosquitto:1883 rejected the "
        "login: not authorized. The username and password came from the Supervisor's "
        "mqtt service, so restart the Mosquitto broker add-on, or set mqtt.host on the "
        "Configuration tab or in config.yaml to use your own broker login."
    ]


def test_a_rejected_file_login_names_the_file_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    StartupStub(monkeypatch, reject_login=True)
    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, FILE_BROKER)]) == 1
    assert _errors(caplog) == [
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
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    stub = StartupStub(monkeypatch, connect_error=KeyboardInterrupt())
    assert entry.main([_config(tmp_path, FILE_BROKER + PIERS)]) == 0
    assert stub.closed


# --------------------------------------------------------------------------- #
# addon-form-horizon-file D4, D6-D8: the form combined with config.yaml
# --------------------------------------------------------------------------- #


def test_form_setup_gives_a_verdict_without_a_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    stub = StartupStub(monkeypatch)

    with caplog.at_level(logging.INFO, logger="pierpressure"):
        config = _load(_no_file(tmp_path))
        entry.main([_no_file(tmp_path)])

    assert [p.id for p in config.piers] == ["backyard"]
    assert config.recompute.interval_seconds == 600
    assert (config.mqtt.discovery_prefix, config.mqtt.base_topic) == (
        "homeassistant",
        "pierpressure",
    )
    assert stub.supervisor_calls == ["token-1", "token-1"]
    assert [m.host for m in stub.connected_to] == ["core-mosquitto"]
    messages = [r.getMessage() for r in caplog.records]
    assert "Settings from the Configuration tab" in messages
    assert not any("ignored" in m for m in messages)


def test_a_form_pier_takes_its_horizon_file_from_config_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    StartupStub(monkeypatch)
    (tmp_path / "backyard.hrz").write_bytes(NINA_FIXTURE.read_bytes())
    text = "piers:\n  - id: backyard\n    horizon:\n      file: backyard.hrz\n      format: nina\n"
    expected = parse_horizon_text("nina", NINA_FIXTURE.read_text(encoding="utf-8"))

    # A relative path is read from the config folder, not the working directory.
    monkeypatch.chdir(options_file.root)
    with caplog.at_level(logging.INFO, logger="pierpressure"):
        [pier] = _load(_config(tmp_path, text)).piers

    assert pier.id == "backyard"
    assert pier.horizon_mask == expected
    assert "Settings from the Configuration tab and config.yaml" in [
        r.getMessage() for r in caplog.records
    ]


def test_a_file_pier_with_only_an_id_adds_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.INFO, logger="pierpressure"):
        [pier] = _load(_config(tmp_path, "piers:\n  - id: backyard\n")).piers

    assert pier.id == "backyard"
    assert "Settings from the Configuration tab" in [r.getMessage() for r in caplog.records]


def test_the_file_adds_pier_settings_the_form_does_not_show(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    StartupStub(monkeypatch)
    text = "piers:\n  - id: backyard\n    go_threshold: 75\n    max_gust: 40\n"

    [pier] = _load(_config(tmp_path, text)).piers

    assert (pier.go_threshold, pier.max_gust) == (75, 40)


def test_blank_number_fields_count_as_not_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    blank = {**BACKYARD, "min_altitude": "", **dict.fromkeys(EQUIPMENT_FORM, "  ")}
    _addon(monkeypatch, options_file, blank)
    StartupStub(monkeypatch)

    [pier] = _load(_no_file(tmp_path)).piers

    assert {pier.horizon_mask.alt_at(az) for az in range(0, 360, 15)} == {0.0}
    assert pier.equipment is None


def test_the_files_broker_wins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    stub = StartupStub(monkeypatch)

    with caplog.at_level(logging.INFO, logger="pierpressure"):
        entry.main([_config(tmp_path, FILE_BROKER)])

    assert stub.supervisor_calls == []
    assert _connections(stub) == [("broker.lan", 1883, "me", "file-secret")]
    assert "Settings from the Configuration tab and config.yaml" in [
        r.getMessage() for r in caplog.records
    ]


def test_the_file_sets_only_its_topics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    stub = StartupStub(monkeypatch)

    entry.main([_config(tmp_path, "mqtt:\n  base_topic: observatory\n")])

    assert stub.supervisor_calls == ["token-1"]
    assert [(m.host, m.base_topic) for m in stub.connected_to] == [
        ("core-mosquitto", "observatory")
    ]


def test_credentials_without_a_host_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    stub = StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, "mqtt:\n  username: me\n")]) == 1

    assert stub.supervisor_calls == []
    [error] = _errors(caplog)
    assert error.startswith("Configuration error: mqtt.username is set without mqtt.host")


def test_a_broker_connection_split_across_both_stops_the_addon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    options_file.write_text(
        json.dumps({"interval_seconds": 600, "piers": [BACKYARD], "mqtt": {"host": "broker.lan"}}),
        encoding="utf-8",
    )
    stub = StartupStub(monkeypatch)

    with caplog.at_level(logging.DEBUG):
        assert entry.main([_config(tmp_path, f"mqtt:\n  password: {SECRET}\n")]) == 1

    assert stub.connected_to == []
    [error] = _errors(caplog)
    assert "broker connection" in error
    assert "set without mqtt.host" not in error
    assert SECRET not in caplog.text


def test_one_error_lists_every_problem(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, {**BACKYARD, "min_altitude": 10})
    StartupStub(monkeypatch)
    text = "piers:\n  - id: backyard\n    horizon:\n      min_altitude: 5\n  - id: roof\n"

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, text)]) == 1

    [error] = _errors(caplog)
    assert error.startswith("Configuration error: ")
    assert "horizon of pier 'backyard'" in error
    assert "'roof'" in error


def test_an_empty_config_yaml_names_the_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    StartupStub(monkeypatch)
    path = _config(tmp_path, "# Extra settings go here.\n")

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([path]) == 1

    [error] = _errors(caplog)
    assert error == f"Configuration error: Configuration root must be a mapping in {path}"


def test_a_skipped_form_pier_still_counts_as_listed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    broken = {**BACKYARD, "horizon_points": "[[0, 10], [90"}
    _addon(monkeypatch, options_file, broken, ROOF_FORM)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR):
        config = _load(_config(tmp_path, "piers:\n  - id: backyard\n    go_threshold: 70\n"))

    assert [p.id for p in config.piers] == ["roof"]
    errors = _errors(caplog)
    assert any("'backyard'" in e and "horizon_points" in e for e in errors)
    assert not any("not on the Configuration tab" in e for e in errors)


def test_an_unreadable_horizon_file_skips_only_its_pier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD, ROOF_FORM)
    StartupStub(monkeypatch)
    text = "piers:\n  - id: backyard\n    horizon:\n      file: missing.hrz\n      format: nina\n"

    with caplog.at_level(logging.ERROR):
        config = _load(_config(tmp_path, text))

    assert [p.id for p in config.piers] == ["roof"]
    assert any("Skipping invalid pier 'backyard'" in e for e in _errors(caplog))


@pytest.mark.parametrize("value", [f"[{SECRET}", f"*{SECRET}"], ids=["unclosed", "alias"])
def test_a_config_yaml_that_is_not_valid_yaml_stops_the_addon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    value: str,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    StartupStub(monkeypatch)
    path = _config(tmp_path, f"mqtt:\n  host: broker.lan\n  password: {value}\n")

    with caplog.at_level(logging.DEBUG):
        assert entry.main([path]) == 1

    [error] = _errors(caplog)
    assert error.startswith(f"Configuration error: {path} is not valid YAML at line ")
    assert "line 3, column 13" in error
    assert SECRET not in caplog.text


def test_a_bad_pier_in_the_saved_form_is_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, {**BACKYARD, "id": "north", "latitude": 95.0}, BACKYARD)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR):
        config = _load(_no_file(tmp_path))

    assert [p.id for p in config.piers] == ["backyard"]
    assert any("Skipping invalid pier 'north'" in error for error in _errors(caplog))


@pytest.mark.parametrize(
    "file_text",
    [None, "mqtt:\n  host: broker.lan\n", "piers: [unclosed\n", "piers:\n  - id: [roof]\n"],
    ids=["no-file", "no-piers", "broken-file", "no-text-ids"],
)
def test_nothing_is_set_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    file_text: str | None,
) -> None:
    _addon(monkeypatch, options_file)
    stub = StartupStub(monkeypatch)
    path = _no_file(tmp_path) if file_text is None else _config(tmp_path, file_text)

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([path]) == 1

    [error] = _errors(caplog)
    assert error.startswith("Configuration error: Nothing is set up")
    assert "Add a pier on the add-on's Configuration tab" in error
    assert "cannot list piers on its own" not in error
    assert "not valid YAML" not in error
    assert stub.supervisor_calls == []


def test_a_missing_options_file_counts_as_an_empty_form(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, PIERS)]) == 1

    [error] = _errors(caplog)
    assert error.startswith("Configuration error: Nothing is set up")


def test_an_empty_form_names_the_files_piers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file)
    stub = StartupStub(monkeypatch)
    text = "piers:\n  - id: roof\n    latitude: 1\n  - id: shed\n  - 7\n"

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, text)]) == 1

    [error] = _errors(caplog)
    assert error.startswith("Configuration error: Nothing is set up")
    assert "'roof', 'shed'" in error
    assert "config.yaml cannot list piers on its own" in error
    assert "same id" in error
    assert "keep only the extra settings in config.yaml" in error
    assert stub.connected_to == []


def test_an_empty_forms_broker_is_not_used(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    options_file.write_text(
        json.dumps({"interval_seconds": 600, "piers": [], "mqtt": {"host": "broker.lan"}}),
        encoding="utf-8",
    )
    stub = StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([_config(tmp_path, PIERS)]) == 1

    assert stub.supervisor_calls == []
    assert stub.connected_to == []
    assert _errors(caplog)[0].startswith("Configuration error: Nothing is set up")


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


def test_outside_an_addon_the_settings_come_from_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.INFO, logger="pierpressure"):
        entry.main([_config(tmp_path, FILE_BROKER + PIERS)])

    assert "Settings from config.yaml" in [r.getMessage() for r in caplog.records]


def test_load_app_config_reads_the_supervisors_options_file_by_default() -> None:
    # The autouse fixture swaps in a temporary path, so pin the real default here.
    original = entry.load_app_config.func  # type: ignore[attr-defined]
    default = inspect.signature(original).parameters["options_path"].default
    assert default == "/data/options.json"


# A Supervisor that provides no broker, and one whose broker requires TLS.
NO_BROKER_REPLY = httpx.Response(400, json={"result": "error", "message": "Service not enabled"})
TLS_REPLY = httpx.Response(
    200, json={"result": "ok", "data": {"host": "core-mosquitto", "port": 8883, "ssl": True}}
)


@pytest.mark.parametrize(
    ("reply", "opening"),
    [(NO_BROKER_REPLY, "No MQTT broker was found"), (TLS_REPLY, "The Supervisor's MQTT broker")],
    ids=["no-broker", "tls"],
)
@pytest.mark.parametrize(
    "file_text", [None, "mqtt:\n  base_topic: observatory\n"], ids=["no-file", "topics-file"]
)
def test_supervisor_errors_name_the_configuration_tab_and_config_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    reply: httpx.Response,
    opening: str,
    file_text: str | None,
) -> None:
    _addon(monkeypatch, options_file, BACKYARD)
    StartupStub(monkeypatch, supervisor=reply)
    path = _no_file(tmp_path) if file_text is None else _config(tmp_path, file_text)

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([path]) == 1

    [error] = _errors(caplog)
    assert error.startswith(f"Configuration error: {opening}")
    assert "on the Configuration tab or in config.yaml" in error
    assert "not read" not in error


def test_the_supervisor_login_advice_names_the_configuration_tab_and_config_yaml() -> None:
    advice = entry.SUPERVISOR_LOGIN_ADVICE
    assert "restart the Mosquitto broker add-on" in advice
    assert "set mqtt.host on the Configuration tab or in config.yaml" in advice
    assert "not read" not in advice


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
    [file_pier] = _load(_config(tmp_path / "docker", file_text)).piers

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
    [file_pier] = _load(_config(tmp_path / "docker", _equipment_file(EQUIPMENT))).piers

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
    [file_pier] = _load(_config(tmp_path / "docker", file_text)).piers
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


# --------------------------------------------------------------------------- #
# addon-form-gates: the form sets each pier's GO threshold and wind-gust limit
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fields",
    [{}, {"go_threshold": None, "max_gust": None}, {"go_threshold": "  ", "max_gust": "  "}],
    ids=["absent", "null", "blank"],
)
def test_empty_gate_fields_use_the_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path, fields: dict[str, Any]
) -> None:
    [pier] = _form_piers(tmp_path, monkeypatch, options_file, {**BACKYARD, **fields}).piers

    assert (pier.go_threshold, pier.max_gust) == (65, None)


def test_config_yaml_fills_a_gate_field_the_form_left_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, {**BACKYARD, "max_gust": None})
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR):
        [pier] = _load(_config(tmp_path, "piers:\n  - id: backyard\n    max_gust: 40\n")).piers

    assert pier.max_gust == 40
    assert _errors(caplog) == []


def test_a_go_threshold_on_the_form_and_in_config_yaml_stops_the_addon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _addon(monkeypatch, options_file, {**BACKYARD, "go_threshold": 70})
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert (
            entry.main([_config(tmp_path, "piers:\n  - id: backyard\n    go_threshold: 75\n")]) == 1
        )

    [error] = _errors(caplog)
    assert error.startswith("Configuration error: ")
    assert "go_threshold" in error
    assert "'backyard'" in error
    assert "is set on the Configuration tab and in config.yaml" in error


@pytest.mark.parametrize(
    "field_value", [("max_gust", 0), ("go_threshold", 101)], ids=["gust-zero", "threshold-101"]
)
def test_a_bad_gate_value_skips_only_its_pier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    field_value: tuple[str, int],
) -> None:
    # The Supervisor refuses a threshold over 100 on save; the service does not
    # rely on it.
    field, value = field_value

    with caplog.at_level(logging.ERROR):
        config = _form_piers(
            tmp_path, monkeypatch, options_file, {**BACKYARD, field: value}, ROOF_FORM
        )

    assert [p.id for p in config.piers] == ["roof"]
    assert field in _skip_error(caplog, "backyard")


@pytest.mark.parametrize(
    "fields", [{"max_gust": 0}, {"go_threshold": 101}], ids=["gust-zero", "threshold-101"]
)
def test_a_bad_gate_value_on_the_only_pier_stops_the_addon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    fields: dict[str, int],
) -> None:
    _addon(monkeypatch, options_file, {**BACKYARD, **fields})
    StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR):
        assert entry.main([_no_file(tmp_path)]) == 1

    errors = _errors(caplog)
    assert any("Skipping invalid pier 'backyard'" in e for e in errors)
    assert errors[-1].startswith("Configuration error: No valid pier")


def test_form_gates_give_the_same_verdict_as_file_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    # The instant and conditions of tests/test_golden_verdict.py.
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    file_text = FILE_BROKER + PIERS + "    go_threshold: 75\n    max_gust: 40\n"
    [file_pier] = _load(_config(tmp_path / "docker", file_text)).piers
    form = {**BACKYARD, "go_threshold": 75, "max_gust": 40}
    [form_pier] = _form_piers(tmp_path, monkeypatch, options_file, form).piers
    conditions = assemble_snapshot(_base_full(), _secondary_full())

    with no_network():
        from_file = produce_verdict(file_pier, FixedClock(_INSTANT), conditions)
        from_form = produce_verdict(form_pier, FixedClock(_INSTANT), conditions)

    assert (form_pier.go_threshold, form_pier.max_gust) == (75, 40)
    assert (file_pier.go_threshold, file_pier.max_gust) == (75, 40)
    assert from_form.to_json() == from_file.to_json()


def _with_gusts(forecast: SourceForecast, gust: float) -> SourceForecast:
    """``forecast`` with every hour's gust set to ``gust``, its cloud unchanged."""
    readings = {
        time: replace(reading, wind_gust=gust) for time, reading in forecast.readings.items()
    }
    return SourceForecast(issued_at=forecast.issued_at, readings=readings)


def test_a_gust_over_the_forms_limit_is_a_no_go(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    [gated] = _form_piers(tmp_path, monkeypatch, options_file, {**BACKYARD, "max_gust": 30}).piers
    [open_pier] = _form_piers(tmp_path, monkeypatch, options_file, BACKYARD).piers
    conditions = assemble_snapshot(_with_gusts(_base_full(), 45.0), _secondary_full())

    with no_network():
        document = produce_verdict(gated, FixedClock(_INSTANT), conditions)
        without_gate = produce_verdict(open_pier, FixedClock(_INSTANT), conditions)

    # Without the wind gate, no other gate fails.
    assert without_gate.verdict is not Verdict.NO_GO
    assert document.verdict is Verdict.NO_GO
    assert document.score is None
    assert any("30 km/h limit" in r for r in document.reasons), document.reasons


# --------------------------------------------------------------------------- #
# addon-form-broker: the form sets the broker (design D2, D4-D6)
# --------------------------------------------------------------------------- #

FORM_PASSWORD = "pw-8c41f2"
FORM_BROKER = {"host": "broker.lan", "port": 1884, "username": "pier", "password": FORM_PASSWORD}


def _form_with_broker(path: Path, mqtt: dict[str, Any], *piers: Any) -> None:
    path.write_text(
        json.dumps({"interval_seconds": 600, "piers": list(piers), "mqtt": mqtt}),
        encoding="utf-8",
    )


def _connections(stub: StartupStub) -> list[tuple[str, int, str | None, str | None]]:
    return [
        (m.host, m.port, m.username, m.password and m.password.get_secret_value())
        for m in stub.connected_to
    ]


def test_the_forms_broker_is_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form_with_broker(options_file, FORM_BROKER, BACKYARD)
    stub = StartupStub(monkeypatch)

    entry.main([str(tmp_path / "config.yaml")])

    assert stub.supervisor_calls == []
    assert _connections(stub) == [("broker.lan", 1884, "pier", FORM_PASSWORD)]


def test_the_forms_broker_uses_port_1883_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form_with_broker(options_file, {"host": "broker.lan"}, BACKYARD)
    stub = StartupStub(monkeypatch)

    entry.main([str(tmp_path / "config.yaml")])

    assert _connections(stub) == [("broker.lan", 1883, None, None)]


def test_blank_broker_fields_on_the_form_count_as_not_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options_file: Path
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form_with_broker(
        options_file, {"host": "broker.lan", "username": "", "password": ""}, BACKYARD
    )
    stub = StartupStub(monkeypatch)

    entry.main([str(tmp_path / "config.yaml")])

    assert _connections(stub) == [("broker.lan", 1883, None, None)]


def test_a_username_on_the_form_without_a_host_stops_before_asking_the_supervisor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form_with_broker(options_file, {"username": "pier"}, BACKYARD)
    stub = StartupStub(monkeypatch)

    with caplog.at_level(logging.ERROR, logger="pierpressure"):
        assert entry.main([str(tmp_path / "config.yaml")]) == 1

    assert stub.supervisor_calls == []
    [error] = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert error.startswith("Configuration error: mqtt.username is set without mqtt.host")


def test_a_rejected_login_from_the_form_gets_the_default_advice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form_with_broker(options_file, FORM_BROKER, BACKYARD)
    stub = StartupStub(monkeypatch, reject_login=True)

    with caplog.at_level(logging.DEBUG):
        assert entry.main([str(tmp_path / "config.yaml")]) == 1

    assert stub.login_advice == [None]
    [error] = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert "Check mqtt.username and mqtt.password" in error
    assert "Mosquitto" not in error
    assert FORM_PASSWORD not in caplog.text


def test_the_log_names_the_form_as_the_brokers_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form_with_broker(options_file, {"host": "broker.lan", "password": FORM_PASSWORD}, BACKYARD)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.DEBUG):
        entry.main([str(tmp_path / "config.yaml")])

    messages = [r.getMessage() for r in caplog.records]
    assert "MQTT broker from the Configuration tab: broker.lan:1883" in messages
    assert FORM_PASSWORD not in caplog.text


# --------------------------------------------------------------------------- #
# config-secrets-hidden-in-errors: the add-on's combined path (D5, D6)
# --------------------------------------------------------------------------- #

UNKNOWN_KEY_VALUE = "hunter2-5e3d91"


@pytest.mark.parametrize(
    ("file_text", "expected", "hidden"),
    [
        (
            f"mqtt:\n  pasword: {UNKNOWN_KEY_VALUE}\n",
            "the mqtt block holds a setting it does not know",
            ("pasword", UNKNOWN_KEY_VALUE),
        ),
        ("mqtt:\n  host: file.lan\n", "the broker connection", ()),
    ],
    ids=["unknown-key", "broker-conflict"],
)
def test_an_addon_error_does_not_show_the_forms_password(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options_file: Path,
    caplog: pytest.LogCaptureFixture,
    file_text: str,
    expected: str,
    hidden: tuple[str, ...],
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "token-1")
    _form_with_broker(options_file, FORM_BROKER, BACKYARD)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as error:
        _load(_config(tmp_path, file_text))

    message = str(error.value)
    assert expected in message
    for text in (FORM_PASSWORD, *hidden):
        assert text not in message
        assert text not in caplog.text


@pytest.mark.parametrize(
    ("block", "named", "marker"),
    [
        ("mqtt:\n  host: broker.lan\n  password: 4815162342\n", "mqtt", "4815162342"),
        (
            "mqtt:\n  host: broker.lan\nexplainer:\n  enabled: true\n  sk-5e3d91: 1\n",
            "explainer",
            "sk-5e3d91",
        ),
    ],
    ids=["mqtt-password-number", "explainer-unknown-key"],
)
def test_main_logs_a_block_error_without_its_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    block: str,
    named: str,
    marker: str,
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    StartupStub(monkeypatch)

    with caplog.at_level(logging.DEBUG):
        assert entry.main([_config(tmp_path, block + PIERS)]) == 1

    [error] = _errors(caplog)
    assert error.startswith(f"Configuration error: Invalid {named} configuration: ")
    assert marker not in caplog.text
