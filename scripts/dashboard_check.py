"""Bring up a throwaway Home Assistant to check the night dashboard (design DD8).

``mise run dashboard-check`` runs this. It writes a fresh Home Assistant config
under ``.workspace/dashboard-check/``, installs the pinned plotly-graph-card
release, and starts Home Assistant beside mosquitto and PierPressure under the
``dashboard`` compose profile. Then it completes onboarding, adds the MQTT
integration, waits for PierPressure's Verdict entity, and prints the URL and
the login. The stack stays up so a person can open the dashboard and take the
screenshot; ``docker compose --profile dashboard down`` stops it.

It never touches a real Home Assistant: everything it starts and writes is local
and throwaway.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKDIR = ROOT / ".workspace" / "dashboard-check"
PAGE = ROOT / "docs" / "night-dashboard.md"

PLOTLY_GRAPH_CARD_VERSION = "v4.0.2"
HA_URL = "http://localhost:8123"
CLIENT_ID = f"{HA_URL}/"
USERNAME = "pier"
PASSWORD = "pressure-check"
DASHBOARD_PATH = "pierpressure-night"
DASHBOARD_FILE = "night-dashboard.yaml"
VERDICT_ENTITY = "sensor.pierpressure_backyard_verdict"

# A US pier, like the user's, so the check sees a real evening in local time (D9).
TIME_ZONE = "America/Denver"
LATITUDE = 39.74
LONGITUDE = -104.99
ELEVATION_M = 1600

_YAML_FENCE = re.compile(r"^```yaml\n(.*?)^```", re.MULTILINE | re.DOTALL)


# --------------------------------------------------------------------------- #
# Files
# --------------------------------------------------------------------------- #


def write_config(workdir: Path, page: str) -> None:
    """Write Home Assistant's config and PierPressure's config under ``workdir``.

    The dashboard file is the page's YAML block, unchanged.
    """
    blocks = _YAML_FENCE.findall(page)
    if len(blocks) != 1:
        raise RuntimeError(f"the docs page should hold one ```yaml block, found {len(blocks)}")
    config_dir = workdir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / DASHBOARD_FILE).write_text(blocks[0], encoding="utf-8")
    configuration = {
        "default_config": None,
        "homeassistant": {
            "name": "PierPressure dashboard check",
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "elevation": ELEVATION_M,
            "unit_system": "metric",
            "time_zone": TIME_ZONE,
            "currency": "USD",
            "country": "US",
        },
        "lovelace": {
            "resource_mode": "yaml",
            "resources": [
                {"url": "/local/plotly-graph-card/plotly-graph-card.js", "type": "module"}
            ],
            "dashboards": {
                DASHBOARD_PATH: {
                    "mode": "yaml",
                    "filename": DASHBOARD_FILE,
                    "title": "Night",
                    "icon": "mdi:telescope",
                    "show_in_sidebar": True,
                }
            },
        },
    }
    (config_dir / "configuration.yaml").write_text(
        yaml.safe_dump(configuration, sort_keys=False), encoding="utf-8"
    )
    pierpressure = {
        "mqtt": {"host": "mosquitto"},
        "recompute": {"interval_seconds": 900},
        "piers": [
            {
                "id": "backyard",
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
                "elevation_m": ELEVATION_M,
            }
        ],
    }
    (workdir / "pierpressure.yaml").write_text(
        yaml.safe_dump(pierpressure, sort_keys=False), encoding="utf-8"
    )


def install_plotly_graph_card(www: Path, version: str = PLOTLY_GRAPH_CARD_VERSION) -> None:
    """Download every ``.js`` file of the release, as the card's manual install says.

    The card loads its other files on demand, so the main file alone is not
    enough. A finished download is kept and reused on the next run.
    """
    marker = www / ".version"
    if marker.is_file() and marker.read_text(encoding="utf-8") == version:
        return
    www.mkdir(parents=True, exist_ok=True)
    release = _get_json(
        f"https://api.github.com/repos/dbuezas/lovelace-plotly-graph-card/releases/tags/{version}"
    )
    assets = [a for a in release["assets"] if str(a["name"]).endswith(".js")]
    if not any(a["name"] == "plotly-graph-card.js" for a in assets):
        raise RuntimeError(f"plotly-graph-card {version} has no plotly-graph-card.js")
    for asset in assets:
        with urllib.request.urlopen(asset["browser_download_url"], timeout=60) as response:
            (www / asset["name"]).write_bytes(response.read())
    marker.write_text(version, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Home Assistant's APIs
# --------------------------------------------------------------------------- #


def mqtt_flow_input(step: dict[str, Any]) -> dict[str, Any]:
    """What to send for one step of the MQTT config flow, or why to stop."""
    if step.get("type") == "menu" and "broker" in step.get("menu_options", []):
        return {"next_step_id": "broker"}
    if step.get("type") == "form" and step.get("step_id") == "broker" and not step.get("errors"):
        # Home Assistant 2026.10 requires the collapsed "other settings" section too.
        return {
            "broker": "mosquitto",
            "port": 1883,
            "protocol": "5",
            "other_settings": {"set_client_cert": False, "set_ca_cert": "off", "transport": "tcp"},
        }
    raise RuntimeError(f"unexpected MQTT config flow step: {json.dumps(step)}")


def _request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    form: dict[str, str] | None = None,
    token: str | None = None,
) -> Any:
    url = path if path.startswith("http") else f"{HA_URL}{path}"
    headers: dict[str, str] = {}
    data: bytes | None = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} failed: {error.code} {detail}") from error
    return json.loads(payload) if payload else None


def _get_json(url: str) -> Any:
    return _request("GET", url)


def _wait_for(what: str, check: Any, timeout: float, interval: float = 3.0) -> Any:
    deadline = time.monotonic() + timeout
    while True:
        try:
            result = check()
        except OSError, RuntimeError:
            result = None
        if result:
            return result
        if time.monotonic() > deadline:
            raise RuntimeError(f"timed out after {timeout:.0f} s waiting for {what}")
        time.sleep(interval)


def onboard() -> str:
    """Create the owner, finish the onboarding steps, and return an access token."""
    _wait_for("Home Assistant to answer", lambda: _get_json("/api/onboarding"), timeout=300)
    created = _request(
        "POST",
        "/api/onboarding/users",
        body={
            "client_id": CLIENT_ID,
            "name": "Dashboard check",
            "username": USERNAME,
            "password": PASSWORD,
            "language": "en",
        },
    )
    tokens = _request(
        "POST",
        "/auth/token",
        form={
            "grant_type": "authorization_code",
            "code": created["auth_code"],
            "client_id": CLIENT_ID,
        },
    )
    token = str(tokens["access_token"])
    _request("POST", "/api/onboarding/core_config", body={}, token=token)
    _request("POST", "/api/onboarding/analytics", body={}, token=token)
    _request(
        "POST",
        "/api/onboarding/integration",
        body={"client_id": CLIENT_ID, "redirect_uri": f"{HA_URL}/?auth_callback=1"},
        token=token,
    )
    return token


def add_mqtt_integration(token: str) -> None:
    step = _request(
        "POST",
        "/api/config/config_entries/flow",
        body={"handler": "mqtt", "show_advanced_options": False},
        token=token,
    )
    while step.get("type") != "create_entry":
        step = _request(
            "POST",
            f"/api/config/config_entries/flow/{step['flow_id']}",
            body=mqtt_flow_input(step),
            token=token,
        )


# --------------------------------------------------------------------------- #
# The check
# --------------------------------------------------------------------------- #


def _compose(*args: str) -> None:
    command = ["docker", "compose", "--profile", "dashboard", *args]
    env_config = {"PIERPRESSURE_CONFIG": str(WORKDIR / "pierpressure.yaml")}
    subprocess.run(command, cwd=ROOT, check=True, env={**os.environ, **env_config})


def _reset_home_assistant_state() -> None:
    """Remove everything Home Assistant wrote last time, keeping the card download.

    Home Assistant writes as root inside its container, so the files are removed
    from inside a container too.
    """
    config = WORKDIR / "config"
    if not config.is_dir():
        return
    _compose(
        "run", "--rm", "--no-deps", "--entrypoint", "sh", "homeassistant", "-c",
        "find /config -mindepth 1 -maxdepth 1 ! -name www -exec rm -rf {} +",
    )  # fmt: skip


def main() -> int:
    try:
        _compose("down")
        _reset_home_assistant_state()
        write_config(WORKDIR, PAGE.read_text(encoding="utf-8"))
        install_plotly_graph_card(WORKDIR / "config" / "www" / "plotly-graph-card")
        _compose("up", "-d", "--build", "--wait")
        token = onboard()
        add_mqtt_integration(token)
        _wait_for(
            f"{VERDICT_ENTITY} to have a state",
            lambda: (
                _request("GET", f"/api/states/{VERDICT_ENTITY}", token=token).get("state")
                not in (None, "unknown", "unavailable")
            ),
            timeout=300,
        )
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"dashboard-check failed: {error}", file=sys.stderr)
        return 1
    print(
        f"\nHome Assistant is up with the night dashboard.\n"
        f"  Dashboard: {HA_URL}/{DASHBOARD_PATH}\n"
        f"  Login:     {USERNAME} / {PASSWORD}\n"
        f"  Stop it:   docker compose --profile dashboard down\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
