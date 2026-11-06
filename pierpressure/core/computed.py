"""Variables the core derives from other variables' filled series (ADR-0031).

The provider layer hands each function here the filled input series, and puts
the result into the fill as the computed source's series. Nothing here fetches,
and nothing reads an alternate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from .conditions import SEEING_COLUMN, SEEING_LEVELS, Series, Variable
from .providers import COMPUTED

# ADR-0032. Uncalibrated: change a constant only in a new record, so nights
# before and after the change stay comparable.
_RAYLEIGH_AND_OZONE = 0.17  # mag per airmass, fixed at sea level
_MAG_PER_OPTICAL_DEPTH = 1.086
_MAG_PER_WATER_VAPOUR = 0.006  # mag per kg/m², a haze proxy rather than absorption
# 7Timer!'s index 1 and index 8 extinction bounds, mag per airmass.
_BEST_EXTINCTION = 0.3
_WORST_EXTINCTION = 1.0

# ADR-0033, under the same rule. A potential-temperature rise of 0.5 K per
# 100 m at 1000 hPa, less the dry adiabatic 0.976 K per 100 m (design DD4).
_BAD_LAYER_LAPSE = 0.00476  # K/m: a layer cooling more slowly than this is bad
_TROPOPAUSE_LAPSE = 0.002  # K/m: the WMO tropopause's cooling rate
_TROPOPAUSE_SEARCH_FROM = SEEING_LEVELS.index(500)
# The column alternates temperature and height per level, then the wind and the
# boundary layer (computed-seeing DD1).
_TEMPERATURES = SEEING_COLUMN[0:-2:2]
_HEIGHTS = SEEING_COLUMN[1:-2:2]
_PER_BAD_LAYER = 0.12
# The 300 hPa wind costs nothing from 18 to 126 km/h (5 to 35 m/s).
_JET_FAST = 126.0  # km/h
_JET_FAST_COST = 0.4
_JET_SLOW = 18.0  # km/h
_JET_SLOW_COST = 0.15
_BOUNDARY_LAYER_FREE = 200.0  # m
_BOUNDARY_LAYER_SPAN = 1300.0  # m, from free to full cost
_BOUNDARY_LAYER_COST = 0.25


@dataclass(frozen=True)
class MissingInputs:
    """No series was filled for these inputs, in the derivation's argument order."""

    variables: tuple[Variable, ...]


@dataclass(frozen=True)
class NoSharedHour:
    """Every input has a series, but no hour carries a value in all of them."""


@dataclass(frozen=True)
class MissingColumn:
    """At least one seeing-column variable has no filled series."""


Derivation = Series | MissingInputs | NoSharedHour
"""A computed series with at least one value, or the reason there is none. The
provider layer words the reason; the core never formats an error."""

SeeingDerivation = Series | MissingColumn | NoSharedHour
"""Computed seeing with at least one value, or the reason there is none."""


def _transparency(water_vapour: float, aerosol: float) -> float:
    extinction = (
        _RAYLEIGH_AND_OZONE
        + _MAG_PER_OPTICAL_DEPTH * aerosol
        + _MAG_PER_WATER_VAPOUR * water_vapour
    )
    quality = (_WORST_EXTINCTION - extinction) / (_WORST_EXTINCTION - _BEST_EXTINCTION)
    return min(1.0, max(0.0, quality))


def _earliest(*times: datetime | None) -> datetime | None:
    known = [time for time in times if time is not None]
    return min(known) if known else None


def computed_transparency(water_vapour: Series | None, aerosol: Series | None) -> Derivation:
    """Hourly transparency in ``[0, 1]`` from column water vapour and aerosol optical depth.

    The series covers only the hours both inputs cover, blank where either input
    is, and carries the older input's issue time. Without a value in any hour, the
    result is the reason instead.
    """
    if water_vapour is None or aerosol is None:
        missing: tuple[Variable, ...] = ()
        if water_vapour is None:
            missing += ("column_water_vapour",)
        if aerosol is None:
            missing += ("aerosol_optical_depth",)
        return MissingInputs(missing)
    values: dict[datetime, float | None] = {}
    for time in sorted(water_vapour.values.keys() & aerosol.values.keys()):
        vapour, optical_depth = water_vapour.values[time], aerosol.values[time]
        values[time] = (
            None
            if vapour is None or optical_depth is None
            else _transparency(vapour, optical_depth)
        )
    if all(value is None for value in values.values()):
        return NoSharedHour()
    return Series(
        provider=COMPUTED.key,
        issued_at=_earliest(water_vapour.issued_at, aerosol.issued_at),
        values=values,
    )


def _tropopause(heights: Sequence[float], temperatures: Sequence[float]) -> int:
    """The index of the tropopause level, or the top level's when no level qualifies."""
    for index in range(_TROPOPAUSE_SEARCH_FROM, len(heights) - 1):
        rise = heights[index + 1] - heights[index]
        fall = temperatures[index] - temperatures[index + 1]
        if rise > 0 and fall <= _TROPOPAUSE_LAPSE * rise:
            return index
    return len(heights) - 1


def bad_layers(
    heights: Sequence[float], temperatures: Sequence[float], elevation_m: float
) -> tuple[int, ...]:
    """The lower level, in hPa, of each bad layer between the pier's ground and the tropopause.

    ``heights`` (metres above sea level) and ``temperatures`` (°C) hold one value per
    :data:`~pierpressure.core.conditions.SEEING_LEVELS` level, from the ground up. A
    layer whose heights don't increase upward is neither bad nor a tropopause, so
    bad data never divides by zero and never stops the count.
    """
    return tuple(
        SEEING_LEVELS[index]
        for index in range(_tropopause(heights, temperatures))
        if heights[index] >= elevation_m
        and (rise := heights[index + 1] - heights[index]) > 0
        and temperatures[index] - temperatures[index + 1] < _BAD_LAYER_LAPSE * rise
    )


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _seeing(bad: int, jet: float, boundary_layer: float) -> float:
    jet_cost = _JET_FAST_COST * _clamp((jet - _JET_FAST) / _JET_FAST) + _JET_SLOW_COST * _clamp(
        (_JET_SLOW - jet) / _JET_SLOW
    )
    boundary_layer_cost = _BOUNDARY_LAYER_COST * _clamp(
        (boundary_layer - _BOUNDARY_LAYER_FREE) / _BOUNDARY_LAYER_SPAN
    )
    return _clamp(1.0 - _PER_BAD_LAYER * bad - jet_cost - boundary_layer_cost)


def _seeing_at(hour: Mapping[Variable, float], elevation_m: float) -> float:
    bad = bad_layers(
        [hour[variable] for variable in _HEIGHTS],
        [hour[variable] for variable in _TEMPERATURES],
        elevation_m,
    )
    return _seeing(len(bad), hour["wind_speed_300hpa"], hour["boundary_layer_height"])


def computed_seeing(
    column: Mapping[Variable, Series | None], elevation_m: float
) -> SeeingDerivation:
    """Hourly seeing in ``[0, 1]`` from the filled seeing column (ADR-0033).

    ``column`` maps each :data:`~pierpressure.core.conditions.SEEING_COLUMN`
    variable to its filled series, and ``elevation_m`` is the pier's height above
    sea level. The series covers only the hours every member covers, blank where
    any member is, and carries the column's issue time. Without a value in any
    hour, the result is the reason instead.
    """
    members = [column.get(variable) for variable in SEEING_COLUMN]
    filled = [series for series in members if series is not None]
    if len(filled) < len(members):
        return MissingColumn()
    shared = set.intersection(*(set(series.values) for series in filled))
    values: dict[datetime, float | None] = {}
    for time in sorted(shared):
        hour = {
            variable: series.values[time]
            for variable, series in zip(SEEING_COLUMN, filled, strict=True)
        }
        known = {variable: value for variable, value in hour.items() if value is not None}
        values[time] = _seeing_at(known, elevation_m) if len(known) == len(hour) else None
    if all(value is None for value in values.values()):
        return NoSharedHour()
    return Series(
        provider=COMPUTED.key,
        issued_at=_earliest(*(series.issued_at for series in filled)),
        values=values,
    )
