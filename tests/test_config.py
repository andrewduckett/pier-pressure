"""Tasks 3.1 and 3.2: YAML config loading, env override, per-pier isolation."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from pierpressure.core.config import (
    DEFAULT_GO_THRESHOLD,
    ConfigError,
    PierConfig,
    load_config,
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
