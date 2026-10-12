"""addon-options-form D1, D3: the Configuration form's saved values become config.

The horizon fields follow addon-form-horizon D1-D3, the equipment fields
addon-form-equipment D1-D3, and the broker fields addon-form-broker D2.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from pierpressure.addon_options import (
    EQUIPMENT_FIELDS,
    HORIZON_FIELDS,
    is_set,
    pier_settings,
    read_form_values,
    translate_form,
)
from pierpressure.core.config import ConfigError

ADDON_CONFIG = Path(__file__).resolve().parent.parent / "ha-addon" / "config.yaml"


def read_addon_options(path: Path) -> dict[str, Any] | None:
    """The saved form values at ``path``, translated as the add-on's startup does."""
    options = read_form_values(path)
    return None if options is None else translate_form(options)


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


EQUIPMENT_FORM_VALUES = {
    "equipment_focal_length_mm": 400,
    "equipment_sensor_width_mm": 23.5,
    "equipment_sensor_height_mm": 15.7,
    "equipment_reducer": 0.8,
}


def test_equipment_fields_become_an_equipment_block(tmp_path: Path) -> None:
    # addon-form-equipment D1.
    assert _read_piers(tmp_path, [{**PIER, **EQUIPMENT_FORM_VALUES}]) == [
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
    fields = {
        key: value for key, value in EQUIPMENT_FORM_VALUES.items() if key != "equipment_reducer"
    }

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
    all_null = {**PIER, **dict.fromkeys(EQUIPMENT_FORM_VALUES)}
    one_null = {**PIER, "id": "roof", **EQUIPMENT_FORM_VALUES, "equipment_reducer": None}

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


def test_a_null_equipment_key_beside_equipment_fields_counts_as_unset(tmp_path: Path) -> None:
    # Only an equipment mapping clashes with the fields (D1, D3).
    pier = {**PIER, "equipment": None, "equipment_focal_length_mm": 400}

    assert _read_piers(tmp_path, [pier]) == [{**PIER, "equipment": {"focal_length_mm": 400}}]


# --------------------------------------------------------------------------- #
# addon-form-broker D2: the form's broker block, without empty fields
# --------------------------------------------------------------------------- #

BROKER = {"host": "broker.lan", "port": 1884, "username": "pier", "password": "pw-8c41f2"}


def _read_with_broker(tmp_path: Path, mqtt: object) -> dict[str, object]:
    options = {"interval_seconds": 900, "piers": [PIER], "mqtt": mqtt}
    read = read_addon_options(_options(tmp_path, json.dumps(options)))
    assert read is not None
    return read


def test_the_form_broker_becomes_the_mqtt_block(tmp_path: Path) -> None:
    assert _read_with_broker(tmp_path, BROKER)["mqtt"] == BROKER


@pytest.mark.parametrize("empty", [None, "", "   "], ids=["null", "empty", "blank"])
def test_empty_broker_fields_are_left_out(tmp_path: Path, empty: str | None) -> None:
    mqtt = {"host": "broker.lan", "username": empty, "password": empty}

    assert _read_with_broker(tmp_path, mqtt)["mqtt"] == {"host": "broker.lan"}


@pytest.mark.parametrize(
    "mqtt",
    [{}, {"host": None, "port": None, "username": "", "password": "  "}],
    ids=["empty-block", "every-field-empty"],
)
def test_a_broker_block_with_nothing_set_gives_no_mqtt_key(
    tmp_path: Path, mqtt: dict[str, object]
) -> None:
    assert "mqtt" not in _read_with_broker(tmp_path, mqtt)


def test_a_form_without_piers_ignores_its_broker(tmp_path: Path) -> None:
    options = {"interval_seconds": 900, "piers": [], "mqtt": BROKER}

    assert read_addon_options(_options(tmp_path, json.dumps(options))) is None


@pytest.mark.parametrize("mqtt", [[], "", 0, False], ids=["list", "text", "zero", "false"])
def test_a_broker_value_that_is_not_a_mapping_reaches_the_core(
    tmp_path: Path, mqtt: object
) -> None:
    # The core rejects it; dropping it would silently use the Supervisor's broker.
    assert _read_with_broker(tmp_path, mqtt)["mqtt"] == mqtt


# --------------------------------------------------------------------------- #
# addon-form-horizon-file D2: one "set" rule, and the settings a form pier sets
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("blank", ["", "   "], ids=["empty", "blank"])
def test_blank_min_altitude_counts_as_unset(tmp_path: Path, blank: str) -> None:
    assert _read_piers(tmp_path, [{**PIER, "min_altitude": blank}]) == [PIER]


@pytest.mark.parametrize("blank", ["", "   "], ids=["empty", "blank"])
@pytest.mark.parametrize("field", list(EQUIPMENT_FORM_VALUES))
def test_blank_equipment_fields_count_as_unset(tmp_path: Path, field: str, blank: str) -> None:
    assert _read_piers(tmp_path, [{**PIER, field: blank}]) == [PIER]


def test_a_min_altitude_of_zero_counts_as_set(tmp_path: Path) -> None:
    assert _read_piers(tmp_path, [{**PIER, "min_altitude": 0}]) == [
        {**PIER, "horizon": {"min_altitude": 0}}
    ]


@pytest.mark.parametrize("value", [0, 0.0, 15, "text", False, [], {}])
def test_is_set_counts_any_value_but_none_and_blank_text(value: object) -> None:
    assert is_set(value)


@pytest.mark.parametrize("value", [None, "", "   ", "\t\n"])
def test_is_set_rejects_none_and_blank_text(value: object) -> None:
    assert not is_set(value)


@pytest.mark.parametrize(
    ("pier", "settings"),
    [
        ({"min_altitude": 10}, {"horizon"}),
        ({"min_altitude": 0}, {"horizon"}),
        ({"horizon_points": "[[0, 10]]"}, {"horizon"}),
        ({"horizon": {"file": "a.hrz"}}, {"horizon"}),
        ({"equipment_focal_length_mm": 400}, {"equipment"}),
        ({"equipment_reducer": 0.8}, {"equipment"}),
        ({"equipment": {"focal_length_mm": 400}}, {"equipment"}),
        ({"id": "backyard"}, set()),
        ({"latitude": 51.5, "go_threshold": 70}, {"latitude", "go_threshold"}),
        ({"min_altitude": "", "horizon_points": "  ", "equipment_reducer": None}, set()),
        ({"latitude": None, "max_gust": ""}, set()),
    ],
)
def test_pier_settings_names_what_a_raw_pier_sets(
    pier: dict[str, object], settings: set[str]
) -> None:
    assert pier_settings(pier) == settings


def test_every_form_pier_field_has_a_known_setting() -> None:
    # A flattened field the conflict check does not know would be compared under
    # its own name, and miss its block in config.yaml (design D2).
    addon = yaml.safe_load(ADDON_CONFIG.read_text(encoding="utf-8"))
    fields = addon["schema"]["piers"][0]
    for field in fields:
        settings = pier_settings({field: 1})
        if field in HORIZON_FIELDS:
            assert settings == {"horizon"}, field
        elif field in EQUIPMENT_FIELDS:
            assert settings == {"equipment"}, field
        elif field == "id":
            assert settings == set()
        else:
            assert settings == {field}, field
    # The flattened fields that build a block are all on the form.
    assert set(HORIZON_FIELDS) | set(EQUIPMENT_FIELDS) <= set(fields)
