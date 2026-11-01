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
from dataclasses import dataclass

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

SEVEN_TIMER = ProviderSpec(
    key="seven_timer",
    name="7Timer!",
    needs_key=False,
    variables=("seeing", "transparency"),
)

CATALOG: Mapping[str, ProviderSpec] = {spec.key: spec for spec in (OPEN_METEO, SEVEN_TIMER)}
