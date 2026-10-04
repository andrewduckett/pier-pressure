"""ha-addon: the add-on files stay valid and pinned to the release (design D1-D3, D7)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_FILE = ROOT / "repository.yaml"
ADDON_CONFIG = ROOT / "ha-addon" / "config.yaml"

REPOSITORY_URL = "https://github.com/andrewduckett/pier-pressure"
IMAGE = "ghcr.io/andrewduckett/pier-pressure"

# Exactly YYYY.M.N with no prefix and no leading zeros, as scripts/next_version.py.
RELEASE_VERSION = re.compile(r"[1-9]\d{3}\.[1-9]\d?\.(0|[1-9]\d*)")


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture
def addon() -> dict[str, Any]:
    config = _load(ADDON_CONFIG)
    assert isinstance(config, dict)
    return config


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
    assert RELEASE_VERSION.fullmatch(addon["version"])


def test_addon_runs_the_release_image_without_tag_or_arch(addon: dict[str, Any]) -> None:
    assert addon["image"] == IMAGE
    assert "{arch}" not in addon["image"]


def test_addon_reads_config_from_its_own_folder(addon: dict[str, Any]) -> None:
    mapped = [entry if isinstance(entry, str) else entry["type"] for entry in addon["map"]]
    assert "addon_config" in mapped
    assert addon["environment"]["PIERPRESSURE_CONFIG"] == "/config/config.yaml"


def test_addon_offers_no_options(addon: dict[str, Any]) -> None:
    assert "options" not in addon
    assert "schema" not in addon
