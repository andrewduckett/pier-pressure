"""addon-options-form D1, D3: the Configuration form's saved values become config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pierpressure.addon_options import read_addon_options

from pierpressure.core.config import ConfigError

PIER = {"id": "backyard", "latitude": 51.5, "longitude": -0.12, "elevation_m": 30.0}


def _options(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "options.json"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_form_with_piers_becomes_the_config_files_shape(tmp_path: Path) -> None:
    path = _options(tmp_path, json.dumps({"interval_seconds": 600, "piers": [PIER]}))

    assert read_addon_options(path) == {
        "recompute": {"interval_seconds": 600},
        "piers": [PIER],
    }


def test_pier_entries_pass_through_unchanged(tmp_path: Path) -> None:
    # An unknown key reaches PierConfig, which rejects the pier, rather than
    # being dropped here (design D1).
    odd = {**PIER, "colour": "red"}
    path = _options(tmp_path, json.dumps({"interval_seconds": 900, "piers": [odd]}))

    read = read_addon_options(path)

    assert read is not None
    assert read["piers"] == [odd]


def test_a_form_without_an_interval_leaves_the_default_to_the_config(tmp_path: Path) -> None:
    path = _options(tmp_path, json.dumps({"piers": [PIER]}))

    assert read_addon_options(path) == {"piers": [PIER]}


@pytest.mark.parametrize(
    "options",
    [{"interval_seconds": 900, "piers": []}, {"interval_seconds": 900}],
    ids=["empty-list", "no-key"],
)
def test_a_form_with_no_piers_gives_none(tmp_path: Path, options: dict[str, object]) -> None:
    assert read_addon_options(_options(tmp_path, json.dumps(options))) is None


def test_a_missing_file_gives_none(tmp_path: Path) -> None:
    assert read_addon_options(tmp_path / "options.json") is None


@pytest.mark.parametrize(
    "text",
    ["{not json", "[]", '{"piers": {"id": "backyard"}}'],
    ids=["invalid-json", "list-root", "piers-not-a-list"],
)
def test_a_broken_form_names_the_file(tmp_path: Path, text: str) -> None:
    path = _options(tmp_path, text)

    with pytest.raises(ConfigError, match=str(path)):
        read_addon_options(path)
