"""Provider interface, group assembly, caching, and graceful fallback (design D6).

A source provider parses one external forecast into a :class:`SourceForecast` — a
per-hour set of readings plus the data's issue time. :func:`assemble_snapshot`
promotes the base and secondary forecasts into the core's per-source
:class:`~pierpressure.core.conditions.Conditions`: one self-stamped
:class:`~pierpressure.core.conditions.BaseGroup` (cloud/wind) and
:class:`~pierpressure.core.conditions.SecondaryGroup` (seeing/transparency), each
present only when its source returned rows (design D1). :class:`CachingProvider`
bridges a transient outage by reusing the last-good forecast within a staleness
bound, and :class:`CompositeProvider` fetches the two sources independently so one
failing never fails the other.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol

from pierpressure.core.conditions import (
    BaseGroup,
    BaseHour,
    Conditions,
    GroupMeta,
    SecondaryGroup,
    SecondaryHour,
)
from pierpressure.core.config import PierConfig

logger = logging.getLogger(__name__)

# The longest a cached forecast may be reused after a failed refresh before it is
# treated as unavailable (design D5/D6, task 5.1). It aligns with the freshness
# curve's stale point in the core, so confidence has already decayed toward its
# floor by the time cache is dropped entirely.
MAX_STALENESS = timedelta(hours=12)


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class SourceReading:
    """One source's readings for a single hour. Absent fields are ``None``."""

    cloud_cover: float | None = None
    wind_gust: float | None = None
    seeing: float | None = None
    transparency: float | None = None


@dataclass(frozen=True)
class SourceForecast:
    """A source's parsed hourly readings, keyed by top-of-hour UTC, plus issue time.

    ``issued_at`` is the time the source issued this data (not when it was
    fetched), so reusing a cached forecast keeps the original issue time and its
    staleness stays visible (design's per-source issue-time rule).
    """

    issued_at: datetime | None = None
    readings: Mapping[datetime, SourceReading] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.readings


class Provider(Protocol):
    """Anything that can fetch one source's forecast for a pier."""

    def fetch(self, pier: PierConfig) -> SourceForecast: ...


def assemble_snapshot(base: SourceForecast, secondary: SourceForecast) -> Conditions:
    """Promote the base and secondary forecasts into per-source :class:`Conditions`.

    Each source becomes its own self-stamped group, present only when that source
    returned rows (design D1): the base group carries the cloud/wind hours and the
    base source's issue time, the secondary group the seeing/transparency hours and
    the secondary source's issue time. A source that contributed nothing yields a
    ``None`` group — the exact condition that made today's ``base_issued_at``
    ``None`` — so per-source freshness travels with each source's own data.

    Every field stays independently present-or-absent within its group's hours, so
    a source that returned rows but left a field empty still yields a present group
    whose hours carry ``None`` for that field.
    """
    base_hours = tuple(
        BaseHour(time=time, cloud_cover=reading.cloud_cover, wind_gust=reading.wind_gust)
        for time, reading in sorted(base.readings.items())
    )
    secondary_hours = tuple(
        SecondaryHour(time=time, seeing=reading.seeing, transparency=reading.transparency)
        for time, reading in sorted(secondary.readings.items())
    )
    return Conditions(
        base=BaseGroup.of(GroupMeta(source="base", issued_at=base.issued_at), base_hours),
        secondary=SecondaryGroup.of(
            GroupMeta(source="secondary", issued_at=secondary.issued_at), secondary_hours
        ),
    )


@dataclass
class CachingProvider:
    """Wrap a provider so a failed or empty fetch reuses the last-good forecast.

    On a successful non-empty fetch the result is cached and returned. On a
    failure (or an empty result) the cache is reused if it is within
    ``max_staleness``; beyond that the forecast is treated as unavailable (an
    empty forecast). Reused data keeps its original issue time, so the caller can
    see how stale it is (design D6). Caching is per source, so a fresh base cache
    stays usable even while the secondary source is stale or absent.
    """

    inner: Provider
    max_staleness: timedelta = MAX_STALENESS
    now: Callable[[], datetime] = _utcnow
    _cached: SourceForecast | None = field(default=None, init=False, repr=False)

    def fetch(self, pier: PierConfig) -> SourceForecast:
        try:
            result = self.inner.fetch(pier)
        except Exception as exc:  # noqa: BLE001 - any fetch failure falls back to cache
            logger.warning("conditions source fetch failed, trying cache: %s", exc)
            return self._reuse()
        if not result.is_empty:
            self._cached = result
            return result
        return self._reuse()

    def _reuse(self) -> SourceForecast:
        if self._cached is None or self._cached.issued_at is None:
            return SourceForecast()
        if self.now() - self._cached.issued_at > self.max_staleness:
            return SourceForecast()
        return self._cached


@dataclass
class CompositeProvider:
    """Fetch the base and secondary sources independently and merge them.

    Each fetch is guarded, so one source failing never fails the other: losing the
    secondary source still yields cloud and wind, and losing the base source still
    yields whatever the secondary provided. A partial snapshot is a valid result,
    not an error.
    """

    base: Provider
    secondary: Provider

    def get(self, pier: PierConfig) -> Conditions:
        return assemble_snapshot(
            self._safe_fetch(self.base, pier, "base"),
            self._safe_fetch(self.secondary, pier, "secondary"),
        )

    @staticmethod
    def _safe_fetch(provider: Provider, pier: PierConfig, label: str) -> SourceForecast:
        try:
            return provider.fetch(pier)
        except Exception as exc:  # noqa: BLE001 - a failed source degrades, never fails
            logger.warning("conditions %s source failed: %s", label, exc)
            return SourceForecast()


def build_provider() -> CompositeProvider:
    """Assemble the production provider stack: each source cached, then composed."""
    from .open_meteo import OpenMeteoProvider
    from .seven_timer import SevenTimerProvider

    return CompositeProvider(
        base=CachingProvider(OpenMeteoProvider()),
        secondary=CachingProvider(SevenTimerProvider()),
    )
