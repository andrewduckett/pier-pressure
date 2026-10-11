"""addon-options-form D1, D3: the Configuration form's saved values become config.

The horizon fields follow addon-form-horizon D1-D3, and the equipment fields
addon-form-equipment D1-D3.
"""

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


def test_a_yaml_error_logs_on_one_line(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    # The parser's message spans several lines; the Log tab shows one per record.
    _read_piers(tmp_path, [{**PIER, "horizon_points": "[[0, 10], [90"}])

    [record] = caplog.records
    assert "\n" not in record.getMessage()


EQUIPMENT_FIELDS = {
    "equipment_focal_length_mm": 400,
    "equipment_sensor_width_mm": 23.5,
    "equipment_sensor_height_mm": 15.7,
    "equipment_reducer": 0.8,
}


def test_equipment_fields_become_an_equipment_block(tmp_path: Path) -> None:
    # addon-form-equipment D1.
    assert _read_piers(tmp_path, [{**PIER, **EQUIPMENT_FIELDS}]) == [
        {
            **PIER,
            "equipment": {
                "focal_length_mm": 400,
                "sensor_width_mm": 23.5,
                "sensor_height_mm": 15.7,
                "reducer": 0.8,
            },
        }
    ]


def test_equipment_without_a_reducer_has_no_reducer_key(tmp_path: Path) -> None:
    # The core's default of 1.0 applies (D1).
    fields = {key: value for key, value in EQUIPMENT_FIELDS.items() if key != "equipment_reducer"}

    assert _read_piers(tmp_path, [{**PIER, **fields}]) == [
        {
            **PIER,
            "equipment": {
                "focal_length_mm": 400,
                "sensor_width_mm": 23.5,
                "sensor_height_mm": 15.7,
            },
        }
    ]


def test_some_equipment_fields_give_a_block_of_just_those(tmp_path: Path) -> None:
    # The core rejects the incomplete block and skips the pier (D2).
    pier = {**PIER, "equipment_focal_length_mm": 400, "equipment_sensor_width_mm": 23.5}

    assert _read_piers(tmp_path, [pier]) == [
        {**PIER, "equipment": {"focal_length_mm": 400, "sensor_width_mm": 23.5}}
    ]


def test_a_pier_without_equipment_fields_has_no_equipment(tmp_path: Path) -> None:
    assert _read_piers(tmp_path, [PIER]) == [PIER]


def test_null_equipment_fields_count_as_unset(tmp_path: Path) -> None:
    # D3: a cleared field may be saved as null.
    all_null = {**PIER, **dict.fromkeys(EQUIPMENT_FIELDS)}
    one_null = {**PIER, "id": "roof", **EQUIPMENT_FIELDS, "equipment_reducer": None}

    assert _read_piers(tmp_path, [all_null, one_null]) == [
        PIER,
        {
            **PIER,
            "id": "roof",
            "equipment": {
                "focal_length_mm": 400,
                "sensor_width_mm": 23.5,
                "sensor_height_mm": 15.7,
            },
        },
    ]


def test_an_equipment_block_beside_equipment_fields_skips_only_its_pier(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # D1: the edge does not merge the two.
    both = {**PIER, "equipment": {"focal_length_mm": 400}, "equipment_focal_length_mm": 400}
    other = {**PIER, "id": "roof"}

    assert _read_piers(tmp_path, [both, other]) == [other]
    assert "Skipping invalid pier 'backyard'" in caplog.text
    assert "equipment and the equipment_* fields cannot both be set" in caplog.text


def test_an_equipment_block_alone_passes_through(tmp_path: Path) -> None:
    # The core checks it as it checks a file's block (D1).
    pier = {**PIER, "equipment": {"focal_length_mm": 400}}

    assert _read_piers(tmp_path, [pier]) == [pier]


def test_horizon_and_equipment_blocks_sit_side_by_side(tmp_path: Path) -> None:
    pier = {**PIER, "min_altitude": 15, "equipment_focal_length_mm": 400}

    assert _read_piers(tmp_path, [pier]) == [
        {**PIER, "horizon": {"min_altitude": 15}, "equipment": {"focal_length_mm": 400}}
    ]
