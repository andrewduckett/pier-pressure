"""Computed transparency in the core (computed-transparency DD3, DD4, ADR-0032)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pierpressure.core.computed import computed_transparency
from pierpressure.core.conditions import Series

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
