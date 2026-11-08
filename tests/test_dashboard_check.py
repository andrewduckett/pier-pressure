"""The pure parts of the dashboard check, which runs the card in Docker.

Bringing Home Assistant up is checked by running ``mise run dashboard-check``;
these tests cover the files it writes and how it answers the MQTT config flow.
"""

from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

import pytest
import yaml
from dashboard_check import (
    CARD_DASHBOARD_PATH,
    PASSWORD,
    ROOT,
    USERNAME,
    HttpError,
    install_pierpressure_card,
    mqtt_flow_input,
    ready_message,
    wait_for,
    write_config,
)

_CARD_HASH = "0123456789ab"


def test_write_config_holds_only_the_card_dashboard(tmp_path: Path) -> None:
    write_config(tmp_path, _CARD_HASH)
    parsed = yaml.safe_load((tmp_path / "config" / "configuration.yaml").read_text("utf-8"))
    assert list(parsed["lovelace"]["dashboards"]) == [CARD_DASHBOARD_PATH]
    assert not (tmp_path / "config" / "night-dashboard.yaml").exists()


def test_write_config_registers_only_the_card_resource(tmp_path: Path) -> None:
    write_config(tmp_path, _CARD_HASH)
    parsed = yaml.safe_load((tmp_path / "config" / "configuration.yaml").read_text("utf-8"))
    assert parsed["lovelace"]["resources"] == [
        {"url": f"/local/pierpressure-card/pierpressure-card.js?v={_CARD_HASH}", "type": "module"}
    ]


def test_write_config_points_pierpressure_at_the_compose_broker(tmp_path: Path) -> None:
    write_config(tmp_path, _CARD_HASH)
    parsed = yaml.safe_load((tmp_path / "pierpressure.yaml").read_text(encoding="utf-8"))
    assert parsed["mqtt"]["host"] == "mosquitto"
    assert [pier["id"] for pier in parsed["piers"]] == ["backyard"]


def test_mqtt_flow_picks_the_broker_from_a_menu() -> None:
    step = {"type": "menu", "step_id": "user", "menu_options": ["addon", "broker"]}
    assert mqtt_flow_input(step) == {"next_step_id": "broker"}


def test_mqtt_flow_fills_the_broker_form() -> None:
    step = {"type": "form", "step_id": "broker", "errors": {}}
    assert mqtt_flow_input(step) == {
        "broker": "mosquitto",
        "port": 1883,
        "protocol": "5",
        "other_settings": {"set_client_cert": False, "set_ca_cert": "off", "transport": "tcp"},
    }


@pytest.mark.parametrize(
    "step",
    [
        {"type": "abort", "reason": "single_instance_allowed"},
        {"type": "form", "step_id": "broker", "errors": {"base": "cannot_connect"}},
        {"type": "form", "step_id": "something_new"},
    ],
)
def test_mqtt_flow_stops_on_anything_else(step: dict[str, object]) -> None:
    with pytest.raises(RuntimeError, match="MQTT"):
        mqtt_flow_input(step)


def test_wait_stops_at_once_on_a_client_error() -> None:
    def rejected() -> None:
        raise HttpError("GET /api/states/x", 401, "unauthorized")

    with pytest.raises(HttpError, match="401"):
        wait_for("the verdict", rejected, timeout=60, interval=0)


@pytest.mark.parametrize("code", [404, 502])
def test_wait_retries_not_found_and_server_errors(code: int) -> None:
    calls: list[int] = []

    def not_yet() -> bool:
        calls.append(code)
        if len(calls) < 3:
            raise HttpError("GET /api/states/x", code, "")
        return True

    assert wait_for("the verdict", not_yet, timeout=60, interval=0) is True
    assert len(calls) == 3


def test_ready_message_names_the_login_but_never_prints_the_password() -> None:
    message = ready_message()
    assert USERNAME in message
    assert PASSWORD not in message
    assert "scripts/dashboard_check.py" in message


def _built_card(tmp_path: Path) -> Path:
    built = tmp_path / "dist" / "pierpressure-card.js"
    built.parent.mkdir()
    built.write_text("console.info('PIERPRESSURE-CARD dev');\n", encoding="utf-8")
    return built


def test_install_card_copies_the_built_file_into_www(tmp_path: Path) -> None:
    built = _built_card(tmp_path)
    www = tmp_path / "www"

    install_pierpressure_card(www, built)

    assert (www / "pierpressure-card" / "pierpressure-card.js").read_bytes() == built.read_bytes()


def test_install_card_returns_a_hash_of_the_file(tmp_path: Path) -> None:
    built = _built_card(tmp_path)

    card_hash = install_pierpressure_card(tmp_path / "www", built)

    assert card_hash == hashlib.sha256(built.read_bytes()).hexdigest()[:12]


def test_install_card_says_to_build_it_when_the_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="mise run card"):
        install_pierpressure_card(tmp_path / "www", tmp_path / "dist" / "pierpressure-card.js")


def test_write_config_adds_a_dashboard_holding_the_card(tmp_path: Path) -> None:
    write_config(tmp_path, _CARD_HASH)
    parsed = yaml.safe_load((tmp_path / "config" / "configuration.yaml").read_text("utf-8"))
    dashboard = parsed["lovelace"]["dashboards"][CARD_DASHBOARD_PATH]
    views = yaml.safe_load((tmp_path / "config" / dashboard["filename"]).read_text("utf-8"))
    assert dashboard["mode"] == "yaml"
    assert views["views"][0]["cards"] == [{"type": "custom:pierpressure-card", "pier": "backyard"}]


def test_ready_message_names_the_card_dashboard() -> None:
    assert f"/{CARD_DASHBOARD_PATH}" in ready_message()


def test_dashboard_check_builds_the_card_first() -> None:
    tasks = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))["tasks"]
    assert "card" in tasks["dashboard-check"]["depends"]
