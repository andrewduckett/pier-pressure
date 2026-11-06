"""Variables the core derives from other variables' filled series (ADR-0031).

The provider layer hands each function here the filled input series, and puts
the result into the fill as the computed source's series. Nothing here fetches,
and nothing reads an alternate.
"""

from __future__ import annotations

from datetime import datetime

from .conditions import Series
from .providers import COMPUTED

# ADR-0032. Uncalibrated: change a constant only in a new record, so nights
# before and after the change stay comparable.
_RAYLEIGH_AND_OZONE = 0.17  # mag per airmass, fixed at sea level
_MAG_PER_OPTICAL_DEPTH = 1.086
_MAG_PER_WATER_VAPOUR = 0.006  # mag per kg/m², a haze proxy rather than absorption
# 7Timer!'s index 1 and index 8 extinction bounds, mag per airmass.
_BEST_EXTINCTION = 0.3
_WORST_EXTINCTION = 1.0


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


def computed_transparency(water_vapour: Series, aerosol: Series) -> Series:
    """Hourly transparency in ``[0, 1]`` from column water vapour and aerosol optical depth.

    The series covers only the hours both inputs cover, blank where either input
    is, and carries the older input's issue time.
    """
    values: dict[datetime, float | None] = {}
    for time in sorted(water_vapour.values.keys() & aerosol.values.keys()):
        vapour, optical_depth = water_vapour.values[time], aerosol.values[time]
        values[time] = (
            None
            if vapour is None or optical_depth is None
            else _transparency(vapour, optical_depth)
        )
    return Series(
        provider=COMPUTED.key,
        issued_at=_earliest(water_vapour.issued_at, aerosol.issued_at),
        values=values,
    )
