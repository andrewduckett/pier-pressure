"""addon-form-horizon-file D1-D3, D5: the form and config.yaml combine.

The spec requirement is "The add-on combines the Configuration form with
config.yaml". These tests cover its scenarios that need no running service.
"""

from __future__ import annotations

from typing import Any

import pytest

from pierpressure.addon_settings import combine_settings
from pierpressure.core.config import ConfigError

PIER = {"id": "backyard", "latitude": 51.5, "longitude": -0.12, "elevation_m": 30.0}
ROOF = {**PIER, "id": "roof"}
SENTINEL = "pw-8c41f2"


def _form(*piers: dict[str, Any], **options: Any) -> dict[str, Any]:
    return {"interval_seconds": 900, "piers": list(piers), **options}


def _error(form: dict[str, Any], file: dict[str, Any] | None) -> str:
    with pytest.raises(ConfigError) as error:
        combine_settings(form, file)
    return str(error.value)


# --------------------------------------------------------------------------- #
# The file adds the settings the form leaves unset
# --------------------------------------------------------------------------- #


def test_without_a_file_the_settings_are_the_form_only() -> None:
    combined = combine_settings(_form(PIER), None)

    assert combined.raw == {"recompute": {"interval_seconds": 900}, "piers": [PIER]}
    assert not combined.file_adds


def test_the_file_adds_a_horizon_file_and_pier_settings() -> None:
    file = {
        "piers": [
            {
                "id": "backyard",
                "horizon": {"file": "backyard.hrz", "format": "nina"},
                "go_threshold": 75,
                "max_gust": 40,
            }
        ]
    }

    combined = combine_settings(_form(PIER), file)

    assert combined.raw["piers"] == [
        {
            **PIER,
            "horizon": {"file": "backyard.hrz", "format": "nina"},
            "go_threshold": 75,
            "max_gust": 40,
        }
    ]
    assert combined.file_adds


def test_the_file_adds_horizon_points_when_the_form_sets_none() -> None:
    file = {"piers": [{"id": "backyard", "horizon": {"points": [[0, 10], [180, 20]]}}]}
    form_pier = {**PIER, "min_altitude": None, "horizon_points": "  "}

    combined = combine_settings(_form(form_pier), file)

    assert combined.raw["piers"] == [{**PIER, "horizon": {"points": [[0, 10], [180, 20]]}}]


def test_the_file_adds_the_explainer_and_topic_names() -> None:
    file = {
        "explainer": {"enabled": True},
        "mqtt": {"base_topic": "observatory", "discovery_prefix": "ha"},
    }
    form = _form(PIER, mqtt={"host": "broker.lan", "password": ""})

    combined = combine_settings(form, file)

    assert combined.raw["explainer"] == {"enabled": True}
    assert combined.raw["mqtt"] == {
        "host": "broker.lan",
        "base_topic": "observatory",
        "discovery_prefix": "ha",
    }


def test_the_file_sets_the_broker_when_the_form_sets_none() -> None:
    file = {"mqtt": {"host": "file.lan", "port": 1884, "password": SENTINEL}}

    combined = combine_settings(_form(PIER, mqtt={"host": "", "port": None}), file)

    assert combined.raw["mqtt"] == {"host": "file.lan", "port": 1884, "password": SENTINEL}


def test_a_file_pier_with_only_an_id_adds_nothing() -> None:
    combined = combine_settings(_form(PIER), {"piers": [{"id": "backyard"}]})

    assert combined.raw["piers"] == [PIER]
    assert not combined.file_adds


def test_an_empty_file_adds_nothing() -> None:
    combined = combine_settings(_form(PIER), {})

    assert combined.raw == {"recompute": {"interval_seconds": 900}, "piers": [PIER]}
    assert not combined.file_adds


def test_the_form_pier_order_is_kept() -> None:
    file = {"piers": [{"id": "roof", "max_gust": 30}, {"id": "backyard", "max_gust": 40}]}

    combined = combine_settings(_form(PIER, ROOF), file)

    assert [pier["id"] for pier in combined.raw["piers"]] == ["backyard", "roof"]
    assert [pier["max_gust"] for pier in combined.raw["piers"]] == [40, 30]


def test_a_file_entry_applies_to_each_form_pier_with_its_id() -> None:
    # Today's behaviour for duplicate form ids, until #86 decides the rule (D3).
    file = {"piers": [{"id": "backyard", "max_gust": 40}]}

    combined = combine_settings(_form(PIER, PIER), file)

    assert combined.raw["piers"] == [{**PIER, "max_gust": 40}, {**PIER, "max_gust": 40}]


def test_a_file_entry_for_a_skipped_form_pier_is_dropped() -> None:
    # The translation skips backyard for its unreadable points; its file entry
    # still matches, so no "not on the Configuration tab" error (D2).
    broken = {**PIER, "horizon_points": "[[0, 10], [90"}
    file = {"piers": [{"id": "backyard", "go_threshold": 70}]}

    combined = combine_settings(_form(broken, ROOF), file)

    assert combined.raw["piers"] == [ROOF]


# --------------------------------------------------------------------------- #
# A setting given in both is an error that names it and its pier
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("form_pier", "file_pier", "setting"),
    [
        ({"min_altitude": 10}, {"horizon": {"file": "a.hrz", "format": "nina"}}, "horizon"),
        ({"min_altitude": 0}, {"horizon": {"min_altitude": 5}}, "horizon"),
        ({"horizon_points": "[[0, 10]]"}, {"horizon": {"points": [[0, 5]]}}, "horizon"),
        ({"equipment_focal_length_mm": 400}, {"equipment": {"focal_length_mm": 500}}, "equipment"),
        ({}, {"latitude": 10.0}, "latitude"),
    ],
    ids=["horizon", "horizon-floor-0", "horizon-points", "equipment", "latitude"],
)
def test_a_pier_setting_in_both_names_the_setting_and_pier(
    form_pier: dict[str, Any], file_pier: dict[str, Any], setting: str
) -> None:
    message = _error(_form({**PIER, **form_pier}), {"piers": [{"id": "backyard", **file_pier}]})

    assert setting in message
    assert "'backyard'" in message
    assert "Configuration tab" in message


@pytest.mark.parametrize(
    ("form_mqtt", "file_mqtt"),
    [
        ({"host": "broker.lan"}, {"password": SENTINEL}),
        ({"host": "broker.lan", "password": SENTINEL}, {"host": "file.lan"}),
        ({"username": "pier"}, {"port": 1884}),
    ],
    ids=["host-and-password", "host-and-host", "username-and-port"],
)
def test_a_broker_connection_in_both_names_the_broker_connection(
    form_mqtt: dict[str, Any], file_mqtt: dict[str, Any]
) -> None:
    message = _error(_form(PIER, mqtt=form_mqtt), {"mqtt": file_mqtt})

    assert "broker connection" in message
    assert SENTINEL not in message


def test_an_interval_in_the_file_names_the_recompute_interval() -> None:
    message = _error(_form(PIER), {"recompute": {"interval_seconds": 600}})

    assert "recompute interval" in message


# --------------------------------------------------------------------------- #
# The file's piers must match the form's piers
# --------------------------------------------------------------------------- #


def test_a_file_pier_the_form_does_not_list_is_named() -> None:
    message = _error(_form(PIER), {"piers": [{"id": "roof", "max_gust": 30}]})

    assert "'roof'" in message
    assert "not on the Configuration tab" in message


def test_a_pier_listed_twice_in_the_file_is_named() -> None:
    file = {"piers": [{"id": "backyard"}, {"id": "backyard", "max_gust": 30}]}

    message = _error(_form(PIER), file)

    assert "'backyard'" in message
    assert "more than once" in message


@pytest.mark.parametrize(
    "entry",
    ["backyard", 5, None, ["backyard"]],
    ids=["text", "number", "null", "list"],
)
def test_a_file_pier_that_is_not_a_mapping_names_its_position(entry: object) -> None:
    message = _error(_form(PIER), {"piers": [{"id": "backyard"}, entry]})

    assert "entry 2" in message
    assert "piers" in message


@pytest.mark.parametrize(
    "entry",
    [
        {"max_gust": 30},
        {"id": None},
        {"id": 5},
        {"id": ["backyard"]},
        {"id": {"name": "backyard"}},
    ],
    ids=["missing", "null", "number", "list", "mapping"],
)
def test_a_file_pier_id_that_is_not_text_names_its_position(entry: dict[str, Any]) -> None:
    message = _error(_form(PIER), {"piers": [entry]})

    assert "entry 1" in message
    assert "id" in message


@pytest.mark.parametrize("piers", ["backyard", {"id": "backyard"}, 5, None])
def test_a_file_piers_that_is_not_a_list_is_an_error(piers: object) -> None:
    message = _error(_form(PIER), {"piers": piers})

    assert "piers" in message
    assert "list" in message


def test_a_file_mqtt_that_is_not_a_mapping_is_an_error() -> None:
    message = _error(_form(PIER), {"mqtt": "broker.lan"})

    assert "mqtt" in message
    assert "broker.lan" not in message


# --------------------------------------------------------------------------- #
# One error, on one line, that names every problem and no value
# --------------------------------------------------------------------------- #


def test_one_error_names_every_problem_on_one_line() -> None:
    form = _form({**PIER, "min_altitude": 10})
    file = {
        "recompute": {"interval_seconds": 600},
        "piers": [{"id": "backyard", "horizon": {"min_altitude": 5}}, {"id": "roof"}, 7],
    }

    message = _error(form, file)

    assert "horizon" in message
    assert "'roof'" in message
    assert "recompute interval" in message
    assert "entry 3" in message
    assert "\n" not in message


def test_an_id_with_a_line_break_is_shown_escaped() -> None:
    message = _error(_form(PIER), {"piers": [{"id": "roof\nERROR forged"}]})

    assert "\n" not in message
    assert "'roof\\nERROR forged'" in message


def test_a_key_name_with_a_line_break_is_shown_escaped() -> None:
    form = _form({**PIER, "odd\nkey": 1})

    message = _error(form, {"piers": [{"id": "backyard", "odd\nkey": 2}]})

    assert "\n" not in message
    assert "odd\\nkey" in message


def test_no_error_contains_a_setting_value() -> None:
    form = _form(
        {**PIER, "max_gust": SENTINEL},
        mqtt={"host": "broker.lan", "password": SENTINEL},
    )
    file = {
        "mqtt": {"host": SENTINEL, "password": SENTINEL},
        "explainer": {"api_key": SENTINEL},
        "piers": [{"id": "backyard", "max_gust": SENTINEL, "latitude": SENTINEL}],
    }

    message = _error(form, file)

    assert "broker connection" in message
    assert "max_gust" in message
    assert SENTINEL not in message


def test_each_form_pier_with_a_repeated_id_is_checked_once() -> None:
    form = _form(PIER, {**PIER, "min_altitude": 10}, {**PIER, "min_altitude": 20})

    message = _error(form, {"piers": [{"id": "backyard", "horizon": {"min_altitude": 5}}]})

    assert message.count("horizon of pier 'backyard'") == 1
