"""What each conditions provider supplies (provider-order design D2, ADR-0027).

A :class:`ProviderSpec` declares a provider's stable key, its display name,
whether it needs an API key, the variables it supplies and which of them travel
together as a bundle. The declarations are plain data in the core, so
configuration can check a provider list without importing the network-facing
provider layer (ADR-0022). The fetchers in ``pierpressure.conditions`` each point
at their spec here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from .conditions import Variable


@dataclass(frozen=True)
class ProviderSpec:
    """One provider's fixed declaration. It never changes with what a fetch returned."""

    key: str
    name: str
    needs_key: bool
    variables: tuple[Variable, ...]
    bundles: tuple[frozenset[Variable], ...] = ()

    def bundle_of(self, variable: Variable) -> frozenset[Variable]:
        """The bundle ``variable`` belongs to, or the variable alone."""
        for bundle in self.bundles:
            if variable in bundle:
                return bundle
        return frozenset({variable})


OPEN_METEO = ProviderSpec(
    key="open_meteo",
    name="Open-Meteo",
    needs_key=False,
    variables=(
        "cloud_cover",
        "cloud_low",
        "cloud_mid",
        "cloud_high",
        "wind_gust",
        "temperature",
        "dew_point",
        "humidity",
        "wind_speed",
        "wind_direction",
        "precipitation_probability",
    ),
    bundles=(frozenset({"cloud_cover", "cloud_low", "cloud_mid", "cloud_high"}),),
)

# Each named Open-Meteo model is its own provider (ADR-0028). HRDPS and RDPS
# never send a precipitation probability, so they don't declare one.
_OPEN_METEO_NO_PRECIPITATION = tuple(
    variable for variable in OPEN_METEO.variables if variable != "precipitation_probability"
)
OPEN_METEO_HRRR = replace(OPEN_METEO, key="open_meteo_hrrr", name="Open-Meteo HRRR")
OPEN_METEO_HRDPS = replace(
    OPEN_METEO,
    key="open_meteo_hrdps",
    name="Open-Meteo HRDPS",
    variables=_OPEN_METEO_NO_PRECIPITATION,
)
OPEN_METEO_RDPS = replace(
    OPEN_METEO,
    key="open_meteo_rdps",
    name="Open-Meteo RDPS",
    variables=_OPEN_METEO_NO_PRECIPITATION,
)
OPEN_METEO_ICON = replace(OPEN_METEO, key="open_meteo_icon", name="Open-Meteo ICON")
OPEN_METEO_GFS = replace(OPEN_METEO, key="open_meteo_gfs", name="Open-Meteo GFS")

# The air-quality forecast is a different Open-Meteo endpoint. Nothing reads its
# variables yet, and the timeline does not show them.
OPEN_METEO_AIR_QUALITY = ProviderSpec(
    key="open_meteo_air_quality",
    name="Open-Meteo air quality",
    needs_key=False,
    variables=("aerosol_optical_depth", "pm2_5"),
)

# NWS gives total cloud only, so it declares no bundle and fills no layer.
NWS = ProviderSpec(
    key="nws",
    name="NWS",
    needs_key=False,
    variables=(
        "cloud_cover",
        "wind_gust",
        "wind_speed",
        "wind_direction",
        "temperature",
        "dew_point",
        "humidity",
        "precipitation_probability",
    ),
)

SEVEN_TIMER = ProviderSpec(
    key="seven_timer",
    name="7Timer!",
    needs_key=False,
    variables=("seeing", "transparency"),
)

CATALOG: Mapping[str, ProviderSpec] = {
    spec.key: spec
    for spec in (
        OPEN_METEO,
        OPEN_METEO_HRRR,
        OPEN_METEO_HRDPS,
        OPEN_METEO_RDPS,
        OPEN_METEO_ICON,
        OPEN_METEO_GFS,
        OPEN_METEO_AIR_QUALITY,
        NWS,
        SEVEN_TIMER,
    )
}
