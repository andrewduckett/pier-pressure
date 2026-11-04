"""Tasks 3.1 and 3.2: YAML config loading, env override, per-pier isolation."""

from __future__ import annotations

import logging
import traceback
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from pierpressure.core.config import (
    DEFAULT_GO_THRESHOLD,
    DEFAULT_PROVIDERS,
    BrokerSettings,
    ConfigError,
    ConfigFile,
    PierConfig,
    build_config,
    load_config,
    read_config,
    read_config_mapping,
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
    assert config.mqtt.password == SecretStr("s3cr3t")


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


def test_omitted_dew_margin_is_4_degrees() -> None:
    pier = PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0)
    assert pier.dew_margin == 4.0


@pytest.mark.parametrize("value", [0.0, 2.5])
def test_dew_margin_is_stored_when_set(value: float) -> None:
    pier = PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0, dew_margin=value)
    assert pier.dew_margin == value


@pytest.mark.parametrize("bad", [-1.0, float("inf"), float("nan")])
def test_a_negative_or_non_finite_dew_margin_is_rejected(bad: float) -> None:
    with pytest.raises(ValidationError, match="dew_margin"):
        PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0, dew_margin=bad)


def test_dew_margin_loads_from_yaml(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, VALID_CONFIG + "    dew_margin: 3\n"))
    assert config.piers[0].dew_margin == 3.0


@pytest.mark.parametrize("bad", ["-1", ".inf", ".nan"])
def test_a_bad_dew_margin_in_yaml_skips_the_pier_naming_the_field(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, bad: str
) -> None:
    with caplog.at_level(logging.ERROR), pytest.raises(ConfigError):
        load_config(_write(tmp_path, VALID_CONFIG + f"    dew_margin: {bad}\n"))
    assert "dew_margin" in caplog.text


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
        SecretStr("file-secret"),
    )


def test_build_config_takes_the_connection_from_the_broker(tmp_path: Path) -> None:
    text = "mqtt:\n  discovery_prefix: ha\n  base_topic: observatory\n" + NO_MQTT_CONFIG
    config = build_config(read_config(_write(tmp_path, text)), SUPERVISOR_BROKER)
    mqtt = config.mqtt
    assert (mqtt.host, mqtt.port, mqtt.username, mqtt.password) == (
        "core-mosquitto",
        1883,
        "addons",
        SecretStr("supervisor-secret"),
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
    with pytest.raises(
        ConfigError, match=r"^Invalid mqtt configuration: mqtt\.host: Field required$"
    ):
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


# --------------------------------------------------------------------------- #
# addon-form-broker: the connection rule holds for every ConfigFile (design D3)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("key", "value"), [("port", 1884), ("username", "me"), ("password", "pw")])
def test_config_file_rejects_broker_settings_without_a_host(
    tmp_path: Path, key: str, value: object
) -> None:
    with pytest.raises(ConfigError) as built:
        ConfigFile(raw={"mqtt": {key: value}}, base_dir=tmp_path)
    with pytest.raises(ConfigError) as read:
        read_config(_write(tmp_path, f"mqtt:\n  {key}: {value}\n" + NO_MQTT_CONFIG))
    assert str(built.value) == str(read.value)


@pytest.mark.parametrize("mqtt", ["broker.lan", ["broker.lan"]])
def test_config_file_rejects_an_mqtt_block_that_is_not_a_mapping(
    tmp_path: Path, mqtt: object
) -> None:
    with pytest.raises(ConfigError) as built:
        ConfigFile(raw={"mqtt": mqtt}, base_dir=tmp_path)
    with pytest.raises(ConfigError) as read:
        read_config(_write(tmp_path, "mqtt: broker.lan\n" + NO_MQTT_CONFIG))
    assert str(built.value) == str(read.value)


# --------------------------------------------------------------------------- #
# addon-form-horizon-file: read_config_mapping (design D4)
# --------------------------------------------------------------------------- #


def test_read_config_mapping_returns_the_expanded_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PIERPRESSURE_MQTT_PASSWORD", "s3cr3t")
    raw = read_config_mapping(_write(tmp_path, VALID_CONFIG))
    assert raw["mqtt"]["password"] == "s3cr3t"
    assert raw["piers"][0]["id"] == "backyard"


def test_read_config_mapping_skips_the_broker_rule(tmp_path: Path) -> None:
    raw = read_config_mapping(_write(tmp_path, "mqtt:\n  password: pw\n"))
    assert raw == {"mqtt": {"password": "pw"}}


@pytest.mark.parametrize("text", ["- a\n- b\n", "just text\n", ""])
def test_read_config_mapping_rejects_a_root_that_is_not_a_mapping(
    tmp_path: Path, text: str
) -> None:
    with pytest.raises(ConfigError, match="root must be a mapping"):
        read_config_mapping(_write(tmp_path, text))


SENTINEL = "pw-8c41f2"


@pytest.mark.parametrize(
    ("value", "tail", "where"),
    [
        (f"[{SENTINEL}", "", "line 4, column 1, in the part that starts at line 3, column 13"),
        (
            f"[{SENTINEL}",
            "recompute:\n  interval_seconds: 900\n",
            "line 4, column 10, in the part that starts at line 3, column 13",
        ),
        (f"*{SENTINEL}", "", "line 3, column 13"),
    ],
    ids=["unclosed-at-end", "unclosed-before-more", "undefined-alias"],
)
def test_a_yaml_error_names_only_the_file_line_and_column(
    tmp_path: Path, value: str, tail: str, where: str
) -> None:
    path = _write(tmp_path, f"mqtt:\n  host: broker.lan\n  password: {value}\n{tail}")
    with pytest.raises(ConfigError) as error:
        read_config_mapping(path)
    assert str(error.value) == f"{path} is not valid YAML at {where}"
    assert SENTINEL not in str(error.value)


def test_a_yaml_error_names_the_broken_line_first(tmp_path: Path) -> None:
    # The problem is on line 7; the mapping it breaks starts on line 5.
    text = "mqtt:\n  host: b\nrecompute:\npiers:\n  - id: a\n    latitude: 1\n   bad: 3\n"
    with pytest.raises(ConfigError) as error:
        read_config_mapping(_write(tmp_path, text))
    assert str(error.value).endswith(
        "is not valid YAML at line 7, column 4, in the part that starts at line 5, column 3"
    )


def test_a_root_that_is_not_a_mapping_names_the_file(tmp_path: Path) -> None:
    path = _write(tmp_path, "- a\n")
    with pytest.raises(ConfigError, match="root must be a mapping") as error:
        read_config_mapping(path)
    assert str(path) in str(error.value)


def test_read_config_reports_the_same_yaml_error(tmp_path: Path) -> None:
    path = _write(tmp_path, f"mqtt:\n  password: *{SENTINEL}\n")
    with pytest.raises(ConfigError) as error:
        read_config(path)
    assert str(error.value) == f"{path} is not valid YAML at line 2, column 13"


# --------------------------------------------------------------------------- #
# config-secrets-hidden-in-errors: an mqtt error shows none of the block's text (D1, D6)
# --------------------------------------------------------------------------- #

MARKER = "mk-5e3d91"
MQTT_SETTINGS = ("host", "port", "username", "password", "discovery_prefix", "base_topic")


def _hidden_error(tmp_path: Path, text: str, caplog: pytest.LogCaptureFixture, *hidden: str) -> str:
    """Load ``text``, and check that no ``hidden`` text is in the error, log or traceback."""
    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as error:
        load_config(_write(tmp_path, text))
    message = str(error.value)
    shown = "".join(traceback.format_exception(error.value))
    for text_ in hidden:
        assert text_ not in message
        assert text_ not in shown
        assert text_ not in caplog.text
    return message


def test_an_mqtt_password_that_is_a_number_is_named_without_its_value(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    text = "mqtt:\n  host: broker.lan\n  password: 98765\n" + NO_MQTT_CONFIG

    message = _hidden_error(tmp_path, text, caplog, "98765")

    assert "mqtt.password" in message


@pytest.mark.parametrize(
    ("line", "hidden"),
    [(f"pasword: {MARKER}", ("pasword", MARKER)), (f"{MARKER}:", (MARKER,))],
    ids=["misspelled-key", "bare-key"],
)
def test_an_unknown_mqtt_key_is_not_named(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, line: str, hidden: tuple[str, ...]
) -> None:
    text = f"mqtt:\n  host: broker.lan\n  {line}\n" + NO_MQTT_CONFIG

    message = _hidden_error(tmp_path, text, caplog, *hidden)

    assert "the mqtt block holds a setting it does not know" in message
    for setting in MQTT_SETTINGS:
        assert setting in message


@pytest.mark.parametrize("value", [f"[{MARKER}]", MARKER], ids=["list", "text"])
def test_an_mqtt_block_that_is_not_a_mapping_does_not_show_its_value(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, value: str
) -> None:
    text = f"mqtt: {value}\n" + NO_MQTT_CONFIG

    message = _hidden_error(tmp_path, text, caplog, MARKER)

    assert "mqtt block must be a mapping of settings" in message


def test_a_bad_recompute_interval_keeps_its_error_text(tmp_path: Path) -> None:
    text = VALID_CONFIG.replace("interval_seconds: 900", "interval_seconds: 0")

    with pytest.raises(ConfigError, match=r"(?s)^Invalid mqtt/recompute configuration: .*greater"):
        load_config(_write(tmp_path, text))


def test_valid_secrets_are_masked_when_printed(tmp_path: Path) -> None:
    from pierpressure.explain import NarrativeExplainer, build_explainer

    text = (
        f"mqtt:\n  host: broker.lan\n  username: pier\n  password: {MARKER}-pw\n"
        + NO_MQTT_CONFIG
        + f"explainer:\n  enabled: true\n  api_key: {MARKER}-key\n"
    )
    read = read_config(_write(tmp_path, text))
    config = build_config(read)
    explainer = build_explainer(config.explainer)
    assert isinstance(explainer, NarrativeExplainer)
    broker = BrokerSettings(host="core-mosquitto", port=1883, username="addons", password=MARKER)

    for shown in (read, config, config.model_dump(), broker, explainer.provider):
        assert MARKER not in repr(shown)


# --------------------------------------------------------------------------- #
# provider-order 1.5: the ordered provider list
# --------------------------------------------------------------------------- #


_DEFAULT_ORDER = ["open_meteo", "seven_timer", "open_meteo_air_quality"]


def test_the_default_order_is_one_constant() -> None:
    assert list(DEFAULT_PROVIDERS) == _DEFAULT_ORDER


def _with_conditions(tmp_path: Path, block: str) -> Path:
    return _write(tmp_path, VALID_CONFIG + block)


def test_an_absent_conditions_block_gives_the_default_order(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, VALID_CONFIG))
    assert config.conditions.providers == _DEFAULT_ORDER


def test_a_conditions_block_without_a_list_gives_the_default_order(tmp_path: Path) -> None:
    config = load_config(_with_conditions(tmp_path, "conditions: {}\n"))
    assert config.conditions.providers == _DEFAULT_ORDER


def test_a_configured_order_is_kept_as_written(tmp_path: Path) -> None:
    config = load_config(
        _with_conditions(tmp_path, "conditions:\n  providers: [seven_timer, open_meteo]\n")
    )
    assert config.conditions.providers == ["seven_timer", "open_meteo"]


@pytest.mark.parametrize(
    ("providers", "rule"),
    [
        ("[]", "the provider list must name at least one provider"),
        ("[open_meteo, weather_wizard]", "weather_wizard is not a known provider"),
        ("[open_meteo, seven_timer, open_meteo]", "open_meteo is listed more than once"),
        (
            "[seven_timer]",
            "the provider list must include a provider that needs no key and supplies cloud cover",
        ),
        (
            "[open_meteo_air_quality]",
            "the provider list must include a provider that needs no key and supplies cloud cover",
        ),
    ],
)
def test_an_invalid_provider_list_stops_startup_naming_the_rule(
    tmp_path: Path, providers: str, rule: str
) -> None:
    path = _with_conditions(tmp_path, f"conditions:\n  providers: {providers}\n")
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert str(excinfo.value) == f"Invalid conditions configuration: {rule}"


def test_a_provider_list_error_carries_no_other_configuration_value(tmp_path: Path) -> None:
    path = _with_conditions(tmp_path, "conditions:\n  providers: [seven_timer]\n")
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    message = str(excinfo.value)
    for value in ("192.168.1.10", "pierpressure", "backyard", "900", "seven_timer"):
        assert value not in message


def test_a_null_provider_list_gives_the_default_order(tmp_path: Path) -> None:
    config = load_config(_with_conditions(tmp_path, "conditions:\n  providers:\n"))
    assert config.conditions.providers == _DEFAULT_ORDER


# --------------------------------------------------------------------------- #
# open-meteo-models 1.2: each Open-Meteo model is a provider in the list
# --------------------------------------------------------------------------- #


def test_the_model_keys_are_kept_in_their_configured_order(tmp_path: Path) -> None:
    block = (
        "conditions:\n"
        "  providers: [open_meteo_hrrr, open_meteo_hrdps, open_meteo_rdps, seven_timer]\n"
    )
    config = load_config(_with_conditions(tmp_path, block))
    assert config.conditions.providers == [
        "open_meteo_hrrr",
        "open_meteo_hrdps",
        "open_meteo_rdps",
        "seven_timer",
    ]


def test_a_model_provider_alone_satisfies_the_cloud_rule(tmp_path: Path) -> None:
    config = load_config(
        _with_conditions(tmp_path, "conditions:\n  providers: [open_meteo_hrdps]\n")
    )
    assert config.conditions.providers == ["open_meteo_hrdps"]


def test_a_model_outside_its_area_does_not_stop_startup(tmp_path: Path) -> None:
    # The base pier sits at 51.5, -0.12 (London), outside HRRR's area.
    config = load_config(
        _with_conditions(tmp_path, "conditions:\n  providers: [open_meteo_hrrr, open_meteo]\n")
    )
    assert (config.piers[0].latitude, config.piers[0].longitude) == (51.5, -0.12)
    assert config.conditions.providers == ["open_meteo_hrrr", "open_meteo"]


# --------------------------------------------------------------------------- #
# nws-provider 1.1: the National Weather Service is a provider in the list
# --------------------------------------------------------------------------- #


def test_nws_is_kept_in_its_configured_order(tmp_path: Path) -> None:
    config = load_config(
        _with_conditions(
            tmp_path, "conditions:\n  providers: [nws, open_meteo_hrrr, seven_timer]\n"
        )
    )
    assert config.conditions.providers == ["nws", "open_meteo_hrrr", "seven_timer"]


def test_nws_alone_satisfies_the_cloud_rule(tmp_path: Path) -> None:
    config = load_config(_with_conditions(tmp_path, "conditions:\n  providers: [nws]\n"))
    assert config.conditions.providers == ["nws"]


def test_a_pier_outside_nws_coverage_does_not_stop_startup(tmp_path: Path) -> None:
    # The base pier sits at 51.5, -0.12 (London), outside NWS coverage.
    config = load_config(
        _with_conditions(tmp_path, "conditions:\n  providers: [nws, open_meteo]\n")
    )
    assert config.conditions.providers == ["nws", "open_meteo"]


def test_the_default_order_leaves_out_nws(tmp_path: Path) -> None:
    config = load_config(_with_conditions(tmp_path, ""))
    assert "nws" not in config.conditions.providers


# --------------------------------------------------------------------------- #
# air-quality-provider 3.1: the air-quality forecast is a provider in the list
# --------------------------------------------------------------------------- #


def test_the_air_quality_provider_is_kept_in_its_configured_order(tmp_path: Path) -> None:
    config = load_config(
        _with_conditions(
            tmp_path, "conditions:\n  providers: [open_meteo_hrrr, open_meteo_air_quality]\n"
        )
    )
    assert config.conditions.providers == ["open_meteo_hrrr", "open_meteo_air_quality"]
