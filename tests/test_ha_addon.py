"""ha-addon: the add-on files stay valid and pinned to the release (design D1-D3, D7)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from next_version import RELEASE_TAG

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_FILE = ROOT / "repository.yaml"
ADDON_CONFIG = ROOT / "ha-addon" / "config.yaml"
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


def test_addon_offers_no_options(addon: dict[str, Any]) -> None:
    assert "options" not in addon
    assert "schema" not in addon


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
