"""The observing-conditions provider layer (ADR-0005, ADR-0027).

All network access and graceful fallback live here, outside the pure core. The
layer fetches every configured provider, in order, and fills the core's immutable
:class:`~pierpressure.core.conditions.Conditions` one series per variable: each
variable comes from the first provider in order that returned it. No single
provider is load-bearing: a provider that fails is passed over, and the variables
only it returned show as missing data until its next good fetch.

The core imports nothing from this package — the dependency runs one way, so the
core stays offline and deterministic while conditions are fetched live.
"""

from __future__ import annotations

from .provider import (
    CompositeProvider,
    FetchResult,
    Provider,
    SourceForecast,
    SourceReading,
    assemble_snapshot,
    build_provider,
)

__all__ = [
    "CompositeProvider",
    "FetchResult",
    "Provider",
    "SourceForecast",
    "SourceReading",
    "assemble_snapshot",
    "build_provider",
]
