"""Variables the core derives from other variables' filled series (ADR-0031).

The provider layer hands each function here the filled input series, and puts
the result into the fill as the computed source's series. Nothing here fetches,
and nothing reads an alternate.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from .conditions import SEEING_LEVELS, Series, Variable
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


@dataclass(frozen=True)
class MissingInputs:
    """No series was filled for these inputs, in the derivation's argument order."""

    variables: tuple[Variable, ...]


@dataclass(frozen=True)
class NoSharedHour:
    """Every input has a series, but no hour carries a value in all of them."""


Derivation = Series | MissingInputs | NoSharedHour
"""A computed series with at least one value, or the reason there is none. The
provider layer words the reason; the core never formats an error."""


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
