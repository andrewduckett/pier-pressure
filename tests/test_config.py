"""Tasks 3.1 and 3.2: YAML config loading, env override, per-pier isolation."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from pierpressure.core.config import (
    DEFAULT_GO_THRESHOLD,
    BrokerSettings,
    ConfigError,
    PierConfig,
    build_config,
    load_config,
    read_config,
    validate_piers,
)

VALID_CONFIG = """
mqtt:
  host: 192.168.1.10
  port: 1883
  username: pierpressure
  password: ${PIERPRESSURE_MQTT_PASSWORD}
recompute:
  interval_seconds: 900
piers:
  - id: backyard
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_single_pier_config_is_accepted(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, VALID_CONFIG))
    assert len(config.piers) == 1
    assert config.piers[0].id == "backyard"
    assert config.recompute.interval_seconds == 900


def test_env_override_expands_password(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PIERPRESSURE_MQTT_PASSWORD", "s3cr3t")
    config = load_config(_write(tmp_path, VALID_CONFIG))
    assert config.mqtt.password == "s3cr3t"


def test_missing_field_is_rejected_and_yields_no_verdict(tmp_path: Path) -> None:
    text = """
mqtt:
  host: 192.168.1.10
recompute:
  interval_seconds: 900
piers:
  - id: backyard
    latitude: 51.50
    elevation_m: 30
"""  # longitude missing -> only pier invalid -> no valid pier
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


def test_out_of_range_latitude_is_rejected(tmp_path: Path) -> None:
    text = VALID_CONFIG.replace("latitude: 51.50", "latitude: 120.0")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


def test_one_invalid_pier_does_not_disable_valid_piers(tmp_path: Path) -> None:
    text = """
mqtt:
  host: 192.168.1.10
recompute:
  interval_seconds: 900
piers:
  - id: good
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
  - id: bad
    latitude: 200.0
    longitude: -0.12
    elevation_m: 30
"""
    config = load_config(_write(tmp_path, text))
    assert [pier.id for pier in config.piers] == ["good"]


def test_no_valid_pier_is_a_hard_failure(tmp_path: Path) -> None:
    text = """
mqtt:
  host: 192.168.1.10
recompute:
  interval_seconds: 900
piers:
  - id: bad
    latitude: 200.0
    longitude: -0.12
    elevation_m: 30
"""
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


def test_omitted_go_threshold_uses_the_global_default() -> None:
    pier = PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0)
    assert pier.go_threshold == DEFAULT_GO_THRESHOLD


def test_explicit_go_threshold_overrides_the_default() -> None:
    pier = PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0, go_threshold=80)
    assert pier.go_threshold == 80


@pytest.mark.parametrize("bad", [-1, 101, 150])
def test_go_threshold_out_of_range_is_rejected(bad: int) -> None:
    with pytest.raises(ValidationError):
        PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0, go_threshold=bad)


def test_omitted_max_gust_disables_the_wind_gate() -> None:
    pier = PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0)
    assert pier.max_gust is None


def test_max_gust_is_stored_when_set() -> None:
    pier = PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0, max_gust=40.0)
    assert pier.max_gust == 40.0


@pytest.mark.parametrize("bad", [0.0, -5.0])
def test_non_positive_max_gust_is_rejected(bad: float) -> None:
    with pytest.raises(ValidationError):
        PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0, max_gust=bad)


def test_go_threshold_and_max_gust_load_from_yaml(tmp_path: Path) -> None:
    text = """
mqtt:
  host: 192.168.1.10
recompute:
  interval_seconds: 900
piers:
  - id: backyard
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
    go_threshold: 70
    max_gust: 45
"""
    config = load_config(_write(tmp_path, text))
    assert config.piers[0].go_threshold == 70
    assert config.piers[0].max_gust == 45.0


def test_validate_piers_isolates_each_entry() -> None:
    raw = [
        {"id": "good", "latitude": 51.5, "longitude": -0.12, "elevation_m": 30},
        {"id": "bad", "latitude": 999, "longitude": -0.12, "elevation_m": 30},
    ]
    valid = validate_piers(raw)
    assert [pier.id for pier in valid] == ["good"]


# --------------------------------------------------------------------------- #
# ha-addon-mqtt-service: read_config / build_config (design D2)
# --------------------------------------------------------------------------- #

NO_MQTT_CONFIG = """
recompute:
  interval_seconds: 900
piers:
  - id: backyard
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
"""

SUPERVISOR_BROKER = BrokerSettings(
    host="core-mosquitto", port=1883, username="addons", password="supervisor-secret"
)


def test_read_config_returns_the_raw_config(tmp_path: Path) -> None:
    read = read_config(_write(tmp_path, VALID_CONFIG))
    assert read.raw["recompute"] == {"interval_seconds": 900}


def test_read_config_returns_the_folder_that_holds_the_file(tmp_path: Path) -> None:
    read = read_config(_write(tmp_path, VALID_CONFIG))
    assert read.base_dir == tmp_path.resolve()


def test_read_config_reports_a_file_broker_host(tmp_path: Path) -> None:
    assert read_config(_write(tmp_path, VALID_CONFIG)).names_broker_host


@pytest.mark.parametrize(
    "mqtt_block",
    ["", "mqtt:\n  base_topic: observatory\n", "mqtt:\n"],
    ids=["no-mqtt-block", "no-host", "empty-mqtt-block"],
)
def test_read_config_reports_no_broker_host(tmp_path: Path, mqtt_block: str) -> None:
    read = read_config(_write(tmp_path, mqtt_block + NO_MQTT_CONFIG))
    assert not read.names_broker_host


@pytest.mark.parametrize("field", ["port: 1884", "username: me", "password: pw"])
def test_read_config_rejects_broker_settings_without_a_host(tmp_path: Path, field: str) -> None:
    text = f"mqtt:\n  {field}\n" + NO_MQTT_CONFIG
    with pytest.raises(ConfigError, match=r"mqtt\.host"):
        read_config(_write(tmp_path, text))


def test_build_config_ignores_the_broker_when_the_file_names_a_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PIERPRESSURE_MQTT_PASSWORD", "file-secret")
    config = build_config(read_config(_write(tmp_path, VALID_CONFIG)), SUPERVISOR_BROKER)
    mqtt = config.mqtt
    assert (mqtt.host, mqtt.port, mqtt.username, mqtt.password) == (
        "192.168.1.10",
        1883,
        "pierpressure",
        "file-secret",
    )


def test_build_config_takes_the_connection_from_the_broker(tmp_path: Path) -> None:
    text = "mqtt:\n  discovery_prefix: ha\n  base_topic: observatory\n" + NO_MQTT_CONFIG
    config = build_config(read_config(_write(tmp_path, text)), SUPERVISOR_BROKER)
    mqtt = config.mqtt
    assert (mqtt.host, mqtt.port, mqtt.username, mqtt.password) == (
        "core-mosquitto",
        1883,
        "addons",
        "supervisor-secret",
    )


def test_build_config_keeps_the_file_topics_with_a_broker(tmp_path: Path) -> None:
    text = "mqtt:\n  discovery_prefix: ha\n  base_topic: observatory\n" + NO_MQTT_CONFIG
    config = build_config(read_config(_write(tmp_path, text)), SUPERVISOR_BROKER)
    assert (config.mqtt.discovery_prefix, config.mqtt.base_topic) == ("ha", "observatory")


def test_build_config_accepts_a_file_without_an_mqtt_block(tmp_path: Path) -> None:
    config = build_config(read_config(_write(tmp_path, NO_MQTT_CONFIG)), SUPERVISOR_BROKER)
    assert config.mqtt.host == "core-mosquitto"
    assert (config.mqtt.discovery_prefix, config.mqtt.base_topic) == (
        "homeassistant",
        "pierpressure",
    )


def test_build_config_without_a_host_or_broker_keeps_the_missing_host_error(
    tmp_path: Path,
) -> None:
    text = "mqtt:\n  base_topic: observatory\n" + NO_MQTT_CONFIG
    with pytest.raises(ConfigError, match=r"(?s)^Invalid mqtt/recompute configuration: .*host"):
        build_config(read_config(_write(tmp_path, text)))


def test_read_config_reports_malformed_yaml_as_a_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not valid YAML"):
        read_config(_write(tmp_path, "mqtt: [unclosed\n" + NO_MQTT_CONFIG))


@pytest.mark.parametrize("block", ["mqtt: broker.lan\n", "mqtt: [broker.lan]\n"])
def test_read_config_rejects_an_mqtt_block_that_is_not_a_mapping(
    tmp_path: Path, block: str
) -> None:
    with pytest.raises(ConfigError, match="mqtt"):
        read_config(_write(tmp_path, block + NO_MQTT_CONFIG))


def test_read_config_ignores_blank_broker_settings(tmp_path: Path) -> None:
    text = "mqtt:\n  host:\n  port:\n  username:\n  password:\n" + NO_MQTT_CONFIG
    assert not read_config(_write(tmp_path, text)).names_broker_host


def test_read_config_treats_an_empty_host_as_unset(tmp_path: Path) -> None:
    text = 'mqtt:\n  host: ""\n' + NO_MQTT_CONFIG
    assert not read_config(_write(tmp_path, text)).names_broker_host
