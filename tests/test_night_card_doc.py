"""The dashboard card's repository files: HACS, the release, and the docs page.

The card's own behaviour is tested in ``card/`` with Vitest (night-card design,
Test Seams). These tests read what HACS and the release workflow read.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_CARD_FILE = "pierpressure-card.js"


def test_hacs_json_names_the_card_file() -> None:
    hacs = json.loads((_ROOT / "hacs.json").read_text(encoding="utf-8"))

    assert hacs["name"]
    assert hacs["filename"] == _CARD_FILE


def test_hacs_json_leaves_the_add_on_repository_file_in_place() -> None:
    assert (_ROOT / "repository.yaml").is_file()


_WORKFLOWS = _ROOT / ".github" / "workflows"


def _steps(workflow: str, job: str) -> list[dict[str, Any]]:
    loaded = yaml.safe_load((_WORKFLOWS / workflow).read_text(encoding="utf-8"))
    steps: list[dict[str, Any]] = loaded["jobs"][job]["steps"]
    return steps


def _index(steps: list[dict[str, Any]], match: Callable[[dict[str, Any]], bool]) -> int:
    found = [n for n, step in enumerate(steps) if match(step)]
    assert len(found) == 1, f"expected one matching step, found {len(found)}"
    return found[0]


def _runs(text: str) -> Callable[[dict[str, Any]], bool]:
    return lambda step: text in str(step.get("run", ""))


def _uses(prefix: str) -> Callable[[dict[str, Any]], bool]:
    return lambda step: str(step.get("uses", "")).startswith(prefix)


def _caches(path: str) -> Callable[[dict[str, Any]], bool]:
    return lambda step: _uses("actions/cache@")(step) and step["with"]["path"] == path


def test_release_builds_the_card_with_the_release_version() -> None:
    steps = _steps("release.yml", "release")
    card = steps[_index(steps, _runs("mise run card"))]

    assert card["env"]["PIERPRESSURE_VERSION"] == "${{ steps.version.outputs.version }}"


def test_release_builds_the_card_after_it_computes_the_version() -> None:
    steps = _steps("release.yml", "release")

    assert _index(steps, lambda step: step.get("id") == "version") < _index(
        steps, _runs("mise run card")
    )


def test_release_builds_the_card_with_mise_tools_installed() -> None:
    steps = _steps("release.yml", "release")

    assert _index(steps, _uses("jdx/mise-action@")) < _index(steps, _runs("mise run card"))


def test_release_builds_the_card_before_the_image() -> None:
    steps = _steps("release.yml", "release")

    assert _index(steps, _runs("mise run card")) < _index(steps, _uses("docker/build-push-action@"))


def test_release_attaches_the_card_to_the_github_release() -> None:
    steps = _steps("release.yml", "release")
    create = steps[_index(steps, _runs("gh release create"))]

    assert f"card/dist/{_CARD_FILE}" in create["run"]


@pytest.mark.parametrize(
    ("workflow", "job"), [("ci.yml", "check"), ("release.yml", "check"), ("release.yml", "release")]
)
def test_release_and_ci_jobs_cache_the_npm_packages(workflow: str, job: str) -> None:
    steps = _steps(workflow, job)
    cache = steps[_index(steps, _caches("~/.npm"))]

    assert "hashFiles('card/package-lock.json')" in cache["with"]["key"]
