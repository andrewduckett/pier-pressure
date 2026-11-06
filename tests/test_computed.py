"""Computed transparency and seeing in the core (ADR-0032, ADR-0033)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pierpressure.core.computed import (
    MissingColumn,
    MissingInputs,
    NoSharedHour,
    bad_layers,
    computed_seeing,
    computed_transparency,
)
from pierpressure.core.conditions import SEEING_COLUMN, SEEING_LEVELS, Series, Variable

_AT = datetime(2026, 11, 5, 22, 0, tzinfo=UTC)


def _value(aerosol: float, water_vapour: float) -> float:
    """The computed transparency for one hour with both inputs."""
    result = computed_transparency(
        Series(provider="open_meteo", issued_at=None, values={_AT: water_vapour}),
        Series(provider="open_meteo_air_quality", issued_at=None, values={_AT: aerosol}),
    )
    assert isinstance(result, Series)
    value = result.values[_AT]
    assert value is not None
    return value


@pytest.mark.parametrize(
    ("aerosol", "water_vapour", "expected"),
    [(0.05, 10.0, 1.0), (0.15, 30.0, 0.6959), (0.60, 20.0, 0.0834)],
)
def test_the_value_matches_the_adr_worked_examples(
    aerosol: float, water_vapour: float, expected: float
) -> None:
    assert _value(aerosol, water_vapour) == pytest.approx(expected, abs=5e-5)


_AEROSOLS = (0.0, 0.05, 0.1, 0.2, 0.4, 0.6, 1.0, 3.0)
_WATER_VAPOURS = (0.0, 5.0, 10.0, 20.0, 35.0, 60.0, 120.0)


def test_every_value_lies_in_zero_to_one() -> None:
    for aerosol in _AEROSOLS:
        for water_vapour in _WATER_VAPOURS:
            value = _value(aerosol, water_vapour)
            assert 0.0 <= value <= 1.0, (aerosol, water_vapour)


def test_more_aerosol_never_gives_a_better_value() -> None:
    for water_vapour in _WATER_VAPOURS:
        values = [_value(aerosol, water_vapour) for aerosol in _AEROSOLS]
        assert values == sorted(values, reverse=True), water_vapour


def test_more_water_vapour_never_gives_a_better_value() -> None:
    for aerosol in _AEROSOLS:
        values = [_value(aerosol, water_vapour) for water_vapour in _WATER_VAPOURS]
        assert values == sorted(values, reverse=True), aerosol


def test_the_spec_value_scenarios_hold() -> None:
    assert _value(0.60, 20.0) <= _value(0.05, 20.0)
    assert _value(0.15, 35.0) <= _value(0.15, 5.0)


def _hour(day: int, h: int) -> datetime:
    return datetime(2026, 11, day, h, 0, tzinfo=UTC)


def _night(first: int, last: int) -> list[datetime]:
    """Every hour from ``first`` on the 5th to ``last``, which may run into the 6th."""
    return [_hour(5, h) if h < 24 else _hour(6, h - 24) for h in range(first, last + 1)]


def _series(
    provider: str, values: dict[datetime, float | None], issued_at: datetime | None = None
) -> Series:
    return Series(provider=provider, issued_at=issued_at, values=values)


def test_the_computed_series_is_keyed_computed() -> None:
    result = computed_transparency(
        _series("open_meteo", {_AT: 10.0}), _series("open_meteo_air_quality", {_AT: 0.1})
    )
    assert isinstance(result, Series)
    assert result.provider == "computed"


def test_the_series_covers_only_hours_both_inputs_cover() -> None:
    water_vapour = _series("open_meteo", dict.fromkeys(_night(18, 23), 10.0))
    aerosol = _series("open_meteo_air_quality", dict.fromkeys(_night(20, 27), 0.1))
    result = computed_transparency(water_vapour, aerosol)
    assert isinstance(result, Series)
    assert list(result.values) == _night(20, 23)


def test_the_series_covers_an_hour_blank_in_one_input_as_none() -> None:
    water_vapour = _series("open_meteo", {_hour(5, 21): 10.0, _hour(5, 22): 10.0})
    aerosol = _series("open_meteo_air_quality", {_hour(5, 21): 0.1, _hour(5, 22): None})
    result = computed_transparency(water_vapour, aerosol)
    assert isinstance(result, Series)
    assert result.values[_hour(5, 22)] is None
    assert result.values[_hour(5, 21)] is not None


@pytest.mark.parametrize(
    ("vapour_issued", "aerosol_issued", "expected"),
    [
        (
            _hour(5, 21).replace(minute=5),
            _hour(5, 20).replace(minute=40),
            _hour(5, 20).replace(minute=40),
        ),
        (
            _hour(5, 20).replace(minute=40),
            _hour(5, 21).replace(minute=5),
            _hour(5, 20).replace(minute=40),
        ),
        (None, _hour(5, 21), _hour(5, 21)),
        (_hour(5, 19), None, _hour(5, 19)),
        (None, None, None),
    ],
)
def test_the_series_carries_the_earlier_input_issue_time(
    vapour_issued: datetime | None, aerosol_issued: datetime | None, expected: datetime | None
) -> None:
    result = computed_transparency(
        _series("open_meteo", {_AT: 10.0}, vapour_issued),
        _series("open_meteo_air_quality", {_AT: 0.1}, aerosol_issued),
    )
    assert isinstance(result, Series)
    assert result.issued_at == expected


_VAPOUR = _series("open_meteo", {_AT: 10.0})
_AEROSOL = _series("open_meteo_air_quality", {_AT: 0.1})


@pytest.mark.parametrize(
    ("water_vapour", "aerosol", "missing"),
    [
        (None, None, ("column_water_vapour", "aerosol_optical_depth")),
        (None, _AEROSOL, ("column_water_vapour",)),
        (_VAPOUR, None, ("aerosol_optical_depth",)),
    ],
)
def test_a_missing_input_is_the_reason_naming_its_keys_in_order(
    water_vapour: Series | None, aerosol: Series | None, missing: tuple[str, ...]
) -> None:
    assert computed_transparency(water_vapour, aerosol) == MissingInputs(missing)


def test_inputs_with_no_shared_hour_are_the_reason() -> None:
    water_vapour = _series("open_meteo", {_hour(5, 21): 10.0})
    aerosol = _series("open_meteo_air_quality", {_hour(5, 22): 0.1})
    assert computed_transparency(water_vapour, aerosol) == NoSharedHour()


def test_inputs_that_share_hours_but_never_a_value_are_the_reason() -> None:
    water_vapour = _series("open_meteo", {_hour(5, 21): 10.0, _hour(5, 22): None})
    aerosol = _series("open_meteo_air_quality", {_hour(5, 21): None, _hour(5, 22): 0.1})
    assert computed_transparency(water_vapour, aerosol) == NoSharedHour()


# --------------------------------------------------------------------------- #
# computed-seeing 2.1: bad layers between the pier's ground and the tropopause
# --------------------------------------------------------------------------- #

# Each level's height in a standard atmosphere, metres above sea level.
_HEIGHTS = dict(
    zip(
        SEEING_LEVELS,
        (110, 320, 540, 760, 990, 1460, 1950, 3010, 4210, 5570, 7190, 9160, 10360, 11790, 13610,
         16180, 20580),
        strict=True,
    )
)  # fmt: skip
_STANDARD_LAPSE = 0.0065  # K/m, never a bad layer


def _profile(
    lapse: dict[int, float] | None = None, top: int = 200
) -> tuple[dict[int, float], dict[int, float]]:
    """Heights and temperatures that cool at the standard rate up to ``top`` hPa, then hold.

    ``lapse`` overrides the cooling rate, in K/m, of the layer whose lower level it
    names. The isothermal air from ``top`` up makes ``top`` the tropopause.
    """
    rates = {level: (_STANDARD_LAPSE if level > top else 0.0) for level in SEEING_LEVELS[:-1]} | (
        lapse or {}
    )
    temperatures = {SEEING_LEVELS[0]: 15.0 - _STANDARD_LAPSE * _HEIGHTS[SEEING_LEVELS[0]]}
    for lower, upper in zip(SEEING_LEVELS, SEEING_LEVELS[1:], strict=False):
        temperatures[upper] = temperatures[lower] - rates[lower] * (
            _HEIGHTS[upper] - _HEIGHTS[lower]
        )
    return dict(_HEIGHTS), temperatures


def _bad(
    heights: dict[int, float], temperatures: dict[int, float], elevation_m: float = 0.0
) -> tuple[int, ...]:
    return bad_layers(
        [heights[level] for level in SEEING_LEVELS],
        [temperatures[level] for level in SEEING_LEVELS],
        elevation_m,
    )


def test_a_standard_column_has_no_bad_layer() -> None:
    assert _bad(*_profile()) == ()


def test_an_inversion_is_a_bad_layer() -> None:
    heights, temperatures = _profile()
    heights |= {850: 1500.0, 800: 2000.0}
    temperatures |= {850: 0.0, 800: 1.0}
    assert 850 in _bad(heights, temperatures, elevation_m=100.0)


def test_a_layer_cooling_at_the_standard_rate_is_not_a_bad_layer() -> None:
    heights, temperatures = _profile()
    heights |= {850: 1500.0, 800: 2000.0}
    temperatures |= {850: 0.0, 800: -3.25}
    assert 850 not in _bad(heights, temperatures)


def test_a_layer_high_up_cooling_at_the_standard_rate_is_not_a_bad_layer() -> None:
    heights, temperatures = _profile(top=150)
    heights |= {250: 10400.0, 200: 11800.0}
    temperatures |= {250: -45.0, 200: -54.1}
    assert 250 not in _bad(heights, temperatures)


def test_a_layer_cooling_slowly_is_a_bad_layer() -> None:
    heights, temperatures = _profile()
    heights |= {700: 3000.0, 600: 4200.0}
    temperatures |= {700: -5.0, 600: -9.8}
    assert 700 in _bad(heights, temperatures)


def test_a_bad_layer_is_one_cooling_by_less_than_0_476_k_per_100_m() -> None:
    assert _bad(*_profile({700: 0.00470})) == (700,)
    assert _bad(*_profile({700: 0.00480})) == ()
    assert _bad(*_profile({700: -0.002})) == (700,)


def test_a_bad_layer_below_the_piers_ground_is_not_counted() -> None:
    heights, temperatures = _profile({1000: 0.0})
    heights |= {1000: 120.0}
    assert _bad(heights, temperatures, elevation_m=0.0) == (1000,)
    assert _bad(heights, temperatures, elevation_m=400.0) == ()


def test_a_bad_layer_whose_lower_level_is_at_the_piers_elevation_is_counted() -> None:
    assert _bad(*_profile({975: 0.0}), elevation_m=320.0) == (975,)


def test_a_bad_layer_above_the_tropopause_is_not_counted() -> None:
    # Cooling by more than 2 K per km from 500 to 250 hPa, by 1 K per km from
    # 250 to 200, and a bad layer from 200 to 150.
    heights, temperatures = _profile({250: 0.001, 200: 0.0, 150: 0.0}, top=50)
    counted = _bad(heights, temperatures)
    assert 250 not in counted
    assert 200 not in counted


def test_bad_layer_count_finds_no_tropopause_below_500_hpa() -> None:
    # A layer from 600 to 500 hPa that cools by 1 K per km is bad, not the tropopause.
    assert _bad(*_profile({600: 0.001})) == (600,)


def test_bad_layer_count_without_a_tropopause_counts_every_layer_above_the_ground() -> None:
    # Cooling 3 K per km is bad, but too fast for a tropopause.
    lapse = dict.fromkeys(SEEING_LEVELS[9:-1], 0.003)
    assert _bad(*_profile(lapse, top=50)) == SEEING_LEVELS[9:-1]


def test_a_layer_whose_heights_do_not_increase_is_not_a_bad_layer() -> None:
    heights, temperatures = _profile()
    heights |= {600: heights[700]}
    temperatures |= {600: temperatures[700] + 1.0}
    assert 700 not in _bad(heights, temperatures)


def test_bad_layer_count_takes_no_layer_whose_heights_do_not_increase_as_the_tropopause() -> None:
    # The 400 hPa level sits at the 500 hPa level's height, warmer, so the layer
    # from 500 to 400 hPa is neither bad nor a tropopause, and the bad layer
    # from 300 to 250 hPa is still counted.
    heights, temperatures = _profile({300: 0.003})
    heights |= {400: heights[500]}
    temperatures |= {400: temperatures[500] + 1.0}
    assert _bad(heights, temperatures) == (300,)


# --------------------------------------------------------------------------- #
# computed-seeing 2.2: the seeing index (ADR-0033)
# --------------------------------------------------------------------------- #

# Layers below 500 hPa, so that none of them is read as the tropopause.
_BAD_LAYERS = (950, 900, 850, 800, 700, 600)


def _hour_values(bad: int, jet: float, boundary_layer: float) -> dict[Variable, float]:
    """One hour's seeing column with ``bad`` bad layers, a jet and a boundary layer."""
    heights, temperatures = _profile(dict.fromkeys(_BAD_LAYERS[:bad], 0.0))
    per_level = (
        value for level in SEEING_LEVELS for value in (temperatures[level], heights[level])
    )
    return dict(zip(SEEING_COLUMN, (*per_level, jet, boundary_layer), strict=True))


def _column(
    hours: dict[datetime, dict[Variable, float | None]],
    issued_at: datetime | None = None,
) -> dict[Variable, Series | None]:
    return {
        variable: Series(
            provider="open_meteo",
            issued_at=issued_at,
            values={time: values.get(variable) for time, values in hours.items()},
        )
        for variable in SEEING_COLUMN
    }


def _seeing(bad: int, jet: float, boundary_layer: float) -> float:
    result = computed_seeing(_column({_AT: _hour_values(bad, jet, boundary_layer)}), 0.0)
    assert isinstance(result, Series)
    value = result.values[_AT]
    assert value is not None
    return value


def test_the_built_column_has_the_bad_layers_it_names() -> None:
    for bad in range(len(_BAD_LAYERS) + 1):
        heights, temperatures = _profile(dict.fromkeys(_BAD_LAYERS[:bad], 0.0))
        assert _bad(heights, temperatures) == _BAD_LAYERS[:bad]


@pytest.mark.parametrize(
    ("bad", "jet", "boundary_layer", "expected"),
    [(0, 80.0, 150.0, 1.0), (2, 150.0, 500.0, 0.6261), (3, 250.0, 900.0, 0.1117)],
)
def test_the_seeing_value_matches_the_adr_worked_examples(
    bad: int, jet: float, boundary_layer: float, expected: float
) -> None:
    assert _seeing(bad, jet, boundary_layer) == pytest.approx(expected, abs=5e-5)


_BADS = tuple(range(len(_BAD_LAYERS) + 1))
_JETS = (0.0, 5.0, 15.0, 18.0, 60.0, 126.0, 130.0, 180.0, 252.0, 400.0)
_BOUNDARY_LAYERS = (0.0, 150.0, 200.0, 500.0, 1200.0, 1500.0, 3000.0)


def test_every_seeing_value_lies_in_zero_to_one() -> None:
    for bad in _BADS:
        for jet in _JETS:
            for boundary_layer in _BOUNDARY_LAYERS:
                assert 0.0 <= _seeing(bad, jet, boundary_layer) <= 1.0, (bad, jet, boundary_layer)


def test_a_bad_layer_more_never_gives_a_better_seeing_value() -> None:
    for jet in _JETS:
        for boundary_layer in _BOUNDARY_LAYERS:
            values = [_seeing(bad, jet, boundary_layer) for bad in _BADS]
            assert values == sorted(values, reverse=True), (jet, boundary_layer)


def test_a_jet_further_outside_the_good_range_never_gives_a_better_seeing_value() -> None:
    above = tuple(jet for jet in _JETS if jet >= 126.0)
    below = tuple(jet for jet in reversed(_JETS) if jet <= 18.0)
    for bad in _BADS:
        for boundary_layer in _BOUNDARY_LAYERS:
            for jets in (above, below):
                values = [_seeing(bad, jet, boundary_layer) for jet in jets]
                assert values == sorted(values, reverse=True), (bad, boundary_layer, jets)


def test_a_jet_inside_the_good_range_costs_nothing_in_the_seeing_value() -> None:
    assert {_seeing(0, jet, 150.0) for jet in (18.0, 60.0, 126.0)} == {1.0}


def test_the_spec_seeing_value_scenarios_hold() -> None:
    assert _seeing(1, 60.0, 300.0) <= _seeing(0, 60.0, 300.0)
    assert _seeing(1, 180.0, 300.0) <= _seeing(1, 130.0, 300.0)
    assert _seeing(1, 5.0, 300.0) <= _seeing(1, 15.0, 300.0)
    assert _seeing(1, 60.0, 1200.0) <= _seeing(1, 60.0, 200.0)


def test_a_deeper_boundary_layer_never_gives_a_better_seeing_value() -> None:
    for bad in _BADS:
        for jet in _JETS:
            values = [_seeing(bad, jet, boundary_layer) for boundary_layer in _BOUNDARY_LAYERS]
            assert values == sorted(values, reverse=True), (bad, jet)


def test_the_seeing_value_counts_only_bad_layers_above_the_piers_ground() -> None:
    column = _column({_AT: _hour_values(1, 80.0, 150.0)})
    low, high = computed_seeing(column, 0.0), computed_seeing(column, 1000.0)
    assert isinstance(low, Series)
    assert isinstance(high, Series)
    assert (low.values[_AT], high.values[_AT]) == (pytest.approx(0.88), 1.0)


# --------------------------------------------------------------------------- #
# computed-seeing 2.3: the computed seeing series
# --------------------------------------------------------------------------- #

_GOOD_HOUR = _hour_values(0, 80.0, 150.0)


def test_the_computed_seeing_series_is_keyed_computed_and_covers_the_columns_hours() -> None:
    result = computed_seeing(_column(dict.fromkeys(_night(20, 27), _GOOD_HOUR)), 0.0)
    assert isinstance(result, Series)
    assert result.provider == "computed"
    assert list(result.values) == _night(20, 27)


@pytest.mark.parametrize("blank", ["temperature_300hpa", "boundary_layer_height"])
def test_the_computed_seeing_series_is_blank_where_any_member_is(blank: Variable) -> None:
    hours: dict[datetime, dict[Variable, float | None]] = {
        _hour(5, 22): {**_GOOD_HOUR, blank: None},
        _hour(5, 23): dict(_GOOD_HOUR),
    }
    result = computed_seeing(_column(hours), 0.0)
    assert isinstance(result, Series)
    assert result.values == {_hour(5, 22): None, _hour(5, 23): 1.0}


def test_the_computed_seeing_series_carries_the_columns_issue_time() -> None:
    issued = _hour(5, 21).replace(minute=5)
    result = computed_seeing(_column({_AT: dict(_GOOD_HOUR)}, issued_at=issued), 0.0)
    assert isinstance(result, Series)
    assert result.issued_at == issued


def test_the_computed_seeing_series_covers_only_hours_every_member_covers() -> None:
    column = _column(dict.fromkeys(_night(20, 23), _GOOD_HOUR))
    short = column["boundary_layer_height"]
    assert short is not None
    column["boundary_layer_height"] = Series(
        provider=short.provider,
        issued_at=short.issued_at,
        values={time: value for time, value in short.values.items() if time != _hour(5, 20)},
    )
    result = computed_seeing(column, 0.0)
    assert isinstance(result, Series)
    assert list(result.values) == _night(21, 23)


@pytest.mark.parametrize("missing", ["geopotential_height_500hpa", "wind_speed_300hpa"])
def test_a_missing_seeing_column_member_is_the_reason(missing: Variable) -> None:
    column = _column({_AT: dict(_GOOD_HOUR)})
    assert computed_seeing({**column, missing: None}, 0.0) == MissingColumn()
    del column[missing]
    assert computed_seeing(column, 0.0) == MissingColumn()


def test_a_seeing_column_with_a_blank_in_every_hour_is_the_reason() -> None:
    hours: dict[datetime, dict[Variable, float | None]] = {
        _hour(5, 22): {**_GOOD_HOUR, "temperature_850hpa": None},
        _hour(5, 23): {**_GOOD_HOUR, "boundary_layer_height": None},
    }
    assert computed_seeing(_column(hours), 0.0) == NoSharedHour()
