"""The observing-conditions provider layer (design D1, D6; ADR-0005).

All network access, caching, and graceful fallback live here, outside the pure
core. The layer fetches cloud and wind (base source) and seeing and transparency
(secondary source) from independent external forecasts and merges them into an
immutable :class:`~pierpressure.core.conditions.ConditionsSnapshot`. No single
source is load-bearing: one source failing degrades the snapshot to a partial
result rather than failing it, and a transient outage is bridged by cache.

The core imports nothing from this package — the dependency runs one way, so the
core stays offline and deterministic while conditions are fetched live.
"""

from __future__ import annotations

from .provider import (
    CachingProvider,
    CompositeProvider,
    Provider,
    SourceForecast,
    SourceReading,
    assemble_snapshot,
    build_provider,
)

__all__ = [
    "CachingProvider",
    "CompositeProvider",
    "Provider",
    "SourceForecast",
    "SourceReading",
    "assemble_snapshot",
    "build_provider",
]
