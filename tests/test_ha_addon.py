"""ha-addon: the add-on files stay valid and pinned to the release (design D1-D3, D7).

The Configuration form's options, schema and labels follow addon-options-form D5, D6,
and its horizon fields addon-form-horizon D4, D5.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from next_version import RELEASE_TAG

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_FILE = ROOT / "repository.yaml"
ADDON_CONFIG = ROOT / "ha-addon" / "config.yaml"
ADDON_TRANSLATIONS = ROOT / "ha-addon" / "translations" / "en.yaml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"

REPOSITORY_URL = "https://github.com/andrewduckett/pier-pressure"
IMAGE = "ghcr.io/andrewduckett/pier-pressure"

# Docker platform the release builds -> Home Assistant add-on architecture.
PLATFORM_TO_ARCH = {"linux/amd64": "amd64", "linux/arm64": "aarch64"}


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture
def addon() -> dict[str, Any]:
    config = _load(ADDON_CONFIG)
    assert isinstance(config, dict)
    return config


def _release_step(uses_prefix: str) -> dict[str, Any]:
    """The one step of the release job that uses the action ``uses_prefix``."""
    steps = _load(RELEASE_WORKFLOW)["jobs"]["release"]["steps"]
    matches = [step for step in steps if str(step.get("uses", "")).startswith(uses_prefix)]
    assert len(matches) == 1, f"expected one {uses_prefix} step in the release job"
    step: dict[str, Any] = matches[0]
    return step


def test_repository_file_names_this_repository() -> None:
    repository = _load(REPOSITORY_FILE)

    assert isinstance(repository, dict)
    assert repository["name"]
    assert repository["url"] == REPOSITORY_URL
    assert repository["maintainer"]


def test_addon_config_sets_the_required_fields(addon: dict[str, Any]) -> None:
    for field in ("name", "version", "slug", "description", "arch", "image"):
        assert addon.get(field), f"add-on config is missing {field}"
    assert addon["slug"] == "pierpressure"


def test_addon_version_is_a_release_version(addon: dict[str, Any]) -> None:
    # Quoted in the file, so YAML keeps it a string rather than a float.
    assert isinstance(addon["version"], str)
    assert RELEASE_TAG.fullmatch(addon["version"])


def test_addon_runs_the_release_image_without_tag_or_arch(addon: dict[str, Any]) -> None:
    assert addon["image"] == IMAGE
    assert "{arch}" not in addon["image"]


def test_addon_reads_config_from_its_own_folder(addon: dict[str, Any]) -> None:
    mapped = [entry if isinstance(entry, str) else entry["type"] for entry in addon["map"]]
    assert "addon_config" in mapped
    assert addon["environment"]["PIERPRESSURE_CONFIG"] == "/config/config.yaml"


PIER_FIELDS = {
    "id": "str",
    "latitude": "float(-90,90)",
    "longitude": "float(-180,180)",
    "elevation_m": "float",
    "min_altitude": "float(0,90)?",
}


def test_addon_form_defaults_to_the_interval_and_no_piers(addon: dict[str, Any]) -> None:
    assert addon["options"] == {"interval_seconds": 900, "piers": []}


def test_addon_form_schema_declares_the_interval_and_piers(addon: dict[str, Any]) -> None:
    schema = addon["schema"]
    assert schema["interval_seconds"] == "int(1,)"
    # A list of one mapping: the Supervisor shows it as a list of piers, each with
    # its own fields. The horizon fields are optional, as in PierConfig; the
    # others are required.
    (pier,) = schema["piers"]
    assert {key: value for key, value in pier.items() if key != "horizon_points"} == PIER_FIELDS
    assert re.fullmatch(r"match\(.*\)\?", pier["horizon_points"])
    assert set(schema) == set(addon["options"])


def _horizon_points_pattern(addon: dict[str, Any]) -> str:
    match = re.fullmatch(r"match\((.*)\)\?", addon["schema"]["piers"][0]["horizon_points"])
    assert match is not None
    return match.group(1)


@pytest.mark.parametrize("text", ["[[0, 10], [90, 25]]", "", "   "])
def test_the_horizon_points_check_accepts_brackets_or_blank(
    addon: dict[str, Any], text: str
) -> None:
    # The Supervisor runs vol.Match, which uses re.match (addon-form-horizon D4).
    assert re.match(_horizon_points_pattern(addon), text)


@pytest.mark.parametrize("text", ["[0, 10], [90, 25]", "[[0, 10]] extra"])
def test_the_horizon_points_check_rejects_other_text(addon: dict[str, Any], text: str) -> None:
    assert not re.match(_horizon_points_pattern(addon), text)


def test_every_form_field_has_a_label(addon: dict[str, Any]) -> None:
    labels = _load(ADDON_TRANSLATIONS)["configuration"]
    schema = addon["schema"]

    for key in schema:
        assert labels[key]["name"], f"{key} has no name"
        assert labels[key]["description"], f"{key} has no description"
    for field in schema["piers"][0]:
        entry = labels["piers"]["fields"][field]
        assert entry["name"], f"piers.{field} has no name"
        assert entry["description"], f"piers.{field} has no description"


@pytest.mark.parametrize(
    ("path", "unit"),
    [
        (("interval_seconds",), "seconds"),
        (("piers", "fields", "latitude"), "degrees"),
        (("piers", "fields", "longitude"), "degrees"),
        (("piers", "fields", "elevation_m"), "metres"),
        (("piers", "fields", "min_altitude"), "degrees"),
        (("piers", "fields", "horizon_points"), "degrees"),
    ],
)
def test_every_number_label_names_its_unit(path: tuple[str, ...], unit: str) -> None:
    entry: Any = _load(ADDON_TRANSLATIONS)["configuration"]
    for key in path:
        entry = entry[key]
    assert unit in entry["description"]


def test_addon_architectures_match_the_release_platforms(addon: dict[str, Any]) -> None:
    build = _release_step("docker/build-push-action@")
    platforms = [p.strip() for p in build["with"]["platforms"].split(",")]

    assert set(platforms) <= PLATFORM_TO_ARCH.keys(), f"unmapped release platform in {platforms}"
    assert sorted(addon["arch"]) == sorted(PLATFORM_TO_ARCH[p] for p in platforms)


def test_addon_image_matches_the_release_image(addon: dict[str, Any]) -> None:
    meta = _release_step("docker/metadata-action@")
    repository = REPOSITORY_URL.removeprefix("https://github.com/")
    released = meta["with"]["images"].replace("${{ github.repository }}", repository)

    assert released == addon["image"]


def test_addon_wants_the_mqtt_service(addon: dict[str, Any]) -> None:
    # "want", not "need": the add-on still installs without a broker add-on
    # (ha-addon-mqtt-service spec "Add-on config declares the service").
    assert "mqtt:want" in addon.get("services", [])
