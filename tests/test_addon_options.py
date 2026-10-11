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


def test_a_form_without_an_interval_leaves_out_recompute(tmp_path: Path) -> None:
    # The Supervisor always writes the interval; without it, the core reports the
    # missing recompute settings as it does for a file.
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


def _read_piers(tmp_path: Path, piers: list[object]) -> list[object]:
    read = read_addon_options(_options(tmp_path, json.dumps({"piers": piers})))
    assert read is not None
    result: list[object] = read["piers"]
    return result


def test_a_horizon_floor_becomes_a_horizon_block(tmp_path: Path) -> None:
    # addon-form-horizon D1.
    assert _read_piers(tmp_path, [{**PIER, "min_altitude": 15}]) == [
        {**PIER, "horizon": {"min_altitude": 15}}
    ]


def test_horizon_points_text_becomes_points(tmp_path: Path) -> None:
    pier = {**PIER, "horizon_points": "[[0, 10], [90, 25], [180, 5]]"}

    assert _read_piers(tmp_path, [pier]) == [
        {**PIER, "horizon": {"points": [[0, 10], [90, 25], [180, 5]]}}
    ]


def test_a_pier_without_horizon_fields_has_no_horizon(tmp_path: Path) -> None:
    assert _read_piers(tmp_path, [PIER]) == [PIER]


@pytest.mark.parametrize("blank", ["", "   ", None], ids=["empty", "blank", "null"])
def test_blank_horizon_points_count_as_unset(tmp_path: Path, blank: str | None) -> None:
    # A cleared text field may be saved as "" (addon-form-horizon D3).
    pier = {**PIER, "min_altitude": 15, "horizon_points": blank}

    assert _read_piers(tmp_path, [pier]) == [{**PIER, "horizon": {"min_altitude": 15}}]


def test_both_horizon_fields_reach_the_core_together(tmp_path: Path) -> None:
    # The core's "exactly one source" rule rejects the pier (D1).
    pier = {**PIER, "min_altitude": 15, "horizon_points": "[[0, 10]]"}

    assert _read_piers(tmp_path, [pier]) == [
        {**PIER, "horizon": {"min_altitude": 15, "points": [[0, 10]]}}
    ]


@pytest.mark.parametrize(
    ("points", "message"),
    [
        ("[[0, 10], [90", "horizon_points is not valid YAML"),
        (5, "horizon_points must be text"),
    ],
    ids=["invalid-yaml", "not-text"],
)
def test_unusable_horizon_points_skip_only_their_pier(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, points: object, message: str
) -> None:
    other = {**PIER, "id": "roof"}

    piers = _read_piers(tmp_path, [{**PIER, "horizon_points": points}, other])

    assert piers == [other]
    assert "Skipping invalid pier 'backyard'" in caplog.text
    assert message in caplog.text


def test_a_pier_that_is_not_a_mapping_passes_through(tmp_path: Path) -> None:
    # The core's per-pier check skips it (D3).
    assert _read_piers(tmp_path, ["backyard", PIER]) == ["backyard", PIER]


def test_a_form_whose_every_pier_is_skipped_keeps_an_empty_list(tmp_path: Path) -> None:
    # The form did list piers, so config.yaml is not read; the core reports
    # "No valid pier" (D2).
    assert _read_piers(tmp_path, [{**PIER, "horizon_points": "[[0"}]) == []
