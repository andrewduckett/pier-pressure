"""Task 2.1: the pure parts of the night dashboard's Docker check (design DD8).

Bringing Home Assistant up is checked by running ``mise run dashboard-check``;
these tests cover the files it writes and how it answers the MQTT config flow.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from dashboard_check import HttpError, mqtt_flow_input, wait_for, write_config

_PAGE = "# Night\n\n```yaml\nviews:\n  - title: Tonight\n```\n"


def test_write_config_loads_the_page_yaml_as_a_yaml_mode_dashboard(tmp_path: Path) -> None:
    write_config(tmp_path, _PAGE)
    config = (tmp_path / "config" / "configuration.yaml").read_text(encoding="utf-8")
    parsed = yaml.safe_load(config)
    lovelace = parsed["lovelace"]
    dashboard = next(iter(lovelace["dashboards"].values()))
    assert dashboard["mode"] == "yaml"
    assert (tmp_path / "config" / dashboard["filename"]).read_text(encoding="utf-8") == (
        "views:\n  - title: Tonight\n"
    )


def test_write_config_registers_the_plotly_graph_card_resource(tmp_path: Path) -> None:
    write_config(tmp_path, _PAGE)
    parsed = yaml.safe_load((tmp_path / "config" / "configuration.yaml").read_text("utf-8"))
    assert {"url": "/local/plotly-graph-card/plotly-graph-card.js", "type": "module"} in parsed[
        "lovelace"
    ]["resources"]


def test_write_config_points_pierpressure_at_the_compose_broker(tmp_path: Path) -> None:
    write_config(tmp_path, _PAGE)
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
