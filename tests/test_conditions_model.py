"""The conditions snapshot in the pure core: one series per variable (provider-order D1)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import get_args

import pytest

from pierpressure.core import conditions as conditions_module
from pierpressure.core.conditions import TIMELINE_VARIABLES, Conditions, Series, Variable
from pierpressure.core.model import TimelineEntry


def _t(h: int) -> datetime:
    return datetime(2026, 9, 8, h, 0, tzinfo=UTC)


def test_a_series_carries_its_provider_issue_time_and_hourly_values() -> None:
    series = Series(provider="open_meteo", issued_at=_t(11), values={_t(21): 40.0, _t(22): None})
    assert series.provider == "open_meteo"
    assert series.issued_at == _t(11)
    assert series.values == {_t(21): 40.0, _t(22): None}


def test_value_at_reads_the_variables_series_for_the_hour() -> None:
    conditions = Conditions(
        series={
            "cloud_cover": Series(provider="open_meteo", issued_at=_t(11), values={_t(21): 40.0})
        }
    )
    assert conditions.value_at("cloud_cover", _t(21)) == 40.0


def test_value_at_is_none_for_a_blank_hour_a_missing_hour_or_a_missing_series() -> None:
    conditions = Conditions(
        series={
            "cloud_cover": Series(provider="open_meteo", issued_at=_t(11), values={_t(21): None})
        }
    )
    assert conditions.value_at("cloud_cover", _t(21)) is None
    assert conditions.value_at("cloud_cover", _t(22)) is None
    assert conditions.value_at("seeing", _t(21)) is None


def test_issued_at_reads_each_series_own_issue_time() -> None:
    conditions = Conditions(
        series={
            "cloud_cover": Series(provider="open_meteo", issued_at=_t(11), values={_t(21): 1.0}),
            "seeing": Series(provider="seven_timer", issued_at=_t(6), values={_t(21): 0.5}),
        }
    )
    assert conditions.issued_at("cloud_cover") == _t(11)
    assert conditions.issued_at("seeing") == _t(6)
    assert conditions.issued_at("wind_gust") is None


def test_hours_is_the_sorted_union_of_every_series_hours() -> None:
    conditions = Conditions(
        series={
            "cloud_cover": Series(provider="a", issued_at=None, values={_t(22): 1.0, _t(20): None}),
            "seeing": Series(provider="b", issued_at=None, values={_t(21): 0.5, _t(22): 0.5}),
        }
    )
    assert conditions.hours(("cloud_cover", "seeing")) == (_t(20), _t(21), _t(22))


def test_hours_counts_only_the_given_variables_series() -> None:
    conditions = Conditions(
        series={
            "cloud_cover": Series(provider="a", issued_at=None, values={_t(21): 1.0}),
            "seeing": Series(provider="b", issued_at=None, values={_t(22): 0.5, _t(23): 0.5}),
        }
    )
    assert conditions.hours(("cloud_cover",)) == (_t(21),)


def test_the_empty_value_has_no_series_and_no_hours() -> None:
    empty = Conditions()
    assert empty.series == {}
    assert empty.hours(("cloud_cover",)) == ()
    assert empty.value_at("cloud_cover", _t(21)) is None
    assert empty.issued_at("cloud_cover") is None


def test_the_group_types_are_gone() -> None:
    for name in ("BaseGroup", "SecondaryGroup", "GroupMeta", "BaseHour", "SecondaryHour"):
        assert not hasattr(conditions_module, name)


def test_series_and_conditions_are_immutable() -> None:
    series = Series(provider="a", issued_at=None, values={})
    with pytest.raises(dataclasses.FrozenInstanceError):
        series.provider = "b"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        Conditions().series = {}  # type: ignore[misc]


def test_conditions_default_to_no_alternates() -> None:
    assert Conditions().alternates == {}


def test_readings_at_lists_the_filled_value_then_each_alternate_in_order() -> None:
    conditions = Conditions(
        series={"cloud_cover": Series(provider="a", issued_at=None, values={_t(21): 40.0})},
        alternates={
            "cloud_cover": (
                Series(provider="b", issued_at=None, values={_t(21): 70.0}),
                Series(provider="c", issued_at=None, values={_t(21): 10.0}),
            )
        },
    )
    assert conditions.readings_at("cloud_cover", _t(21)) == (("a", 40.0), ("b", 70.0), ("c", 10.0))


def test_readings_at_leaves_out_blank_and_missing_hours() -> None:
    conditions = Conditions(
        series={"cloud_cover": Series(provider="a", issued_at=None, values={_t(21): None})},
        alternates={
            "cloud_cover": (
                Series(provider="b", issued_at=None, values={_t(21): 70.0}),
                Series(provider="c", issued_at=None, values={_t(22): 10.0}),
            )
        },
    )
    assert conditions.readings_at("cloud_cover", _t(21)) == (("b", 70.0),)
    assert conditions.readings_at("seeing", _t(21)) == ()


def test_hours_ignores_hours_only_an_alternate_covers() -> None:
    conditions = Conditions(
        series={"cloud_cover": Series(provider="a", issued_at=None, values={_t(21): 40.0})},
        alternates={
            "cloud_cover": (
                Series(provider="b", issued_at=None, values={_t(21): 1.0, _t(23): 1.0}),
            )
        },
    )
    assert conditions.hours(("cloud_cover",)) == (_t(21),)


def test_the_air_quality_variables_come_before_water_vapour() -> None:
    assert get_args(Variable)[-3:-1] == ("aerosol_optical_depth", "pm2_5")


def test_column_water_vapour_comes_last_and_the_timeline_does_not_show_it() -> None:
    assert get_args(Variable)[-1] == "column_water_vapour"
    assert "column_water_vapour" not in TIMELINE_VARIABLES


def test_timeline_variables_are_the_timeline_entry_fields_that_hold_a_variable() -> None:
    not_a_variable = {"time", "sun_altitude", "moon_altitude", "cloud_cover_min", "cloud_cover_max"}
    shown = tuple(name for name in TimelineEntry.model_fields if name not in not_a_variable)
    assert shown == TIMELINE_VARIABLES
