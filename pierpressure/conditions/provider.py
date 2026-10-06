"""Provider interface, group assembly, and graceful fallback (design D6).

A source provider parses one external forecast into a :class:`SourceForecast` — a
per-hour set of readings plus the data's issue time. :func:`assemble_snapshot`
promotes the base and secondary forecasts into the core's per-source
:class:`~pierpressure.core.conditions.Conditions`: one self-stamped
:class:`~pierpressure.core.conditions.BaseGroup` (cloud/wind) and
:class:`~pierpressure.core.conditions.SecondaryGroup` (seeing/transparency), each
present only when its source returned rows (design D1). :class:`CompositeProvider`
fetches the two sources independently so one failing never fails the other. A
failed or empty fetch leaves its source unavailable until the next good fetch; it
is never filled from an earlier one.

Each fetch also reports a :class:`~pierpressure.health.FetchOutcome` per source.
The outcomes travel beside the conditions in a :class:`FetchResult`, so they feed
provider health and never reach the verdict (provider-health-entities D1).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
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
from pierpressure.health import NO_READINGS, FetchOutcome, ProviderInfo, Role, describe_error

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceReading:
    """One source's readings for a single hour. Absent fields are ``None``.

    ``cloud_low``/``cloud_mid``/``cloud_high`` carry the low/mid/high split of the
    total cloud cover (percent), each independently present-or-absent: a source
    reporting only a total leaves all three ``None``.
    """

    cloud_cover: float | None = None
    wind_gust: float | None = None
    seeing: float | None = None
    transparency: float | None = None
    cloud_low: float | None = None
    cloud_mid: float | None = None
    cloud_high: float | None = None


@dataclass(frozen=True)
class SourceForecast:
    """A source's parsed hourly readings, keyed by top-of-hour UTC, plus issue time.

    ``issued_at`` is the time the source issued this data (not when it was
    fetched), so the data's own age stays visible (design's per-source issue-time
    rule).
    """

    issued_at: datetime | None = None
    readings: Mapping[datetime, SourceReading] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.readings


class Provider(Protocol):
    """Anything that can fetch one source's forecast for a pier.

    ``key`` is the provider's stable identifier, used in health topics and entity
    identities; ``name`` is its display name.
    """

    @property
    def key(self) -> str: ...

    @property
    def name(self) -> str: ...

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
        BaseHour(
            time=time,
            cloud_cover=reading.cloud_cover,
            wind_gust=reading.wind_gust,
            cloud_low=reading.cloud_low,
            cloud_mid=reading.cloud_mid,
            cloud_high=reading.cloud_high,
        )
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


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class FetchResult:
    """One pier's conditions, and the outcome of each source fetch behind them."""

    conditions: Conditions
    outcomes: tuple[FetchOutcome, ...] = ()


@dataclass
class CompositeProvider:
    """Fetch the base and secondary sources independently and merge them.

    Each fetch is guarded, so one source failing never fails the other: losing the
    secondary source still yields cloud and wind, and losing the base source still
    yields whatever the secondary provided. A partial snapshot is a valid result,
    not an error.

    ``now`` stamps each outcome's fetch time; tests pass a fixed clock.
    """

    base: Provider
    secondary: Provider
    now: Callable[[], datetime] = _utcnow

    @property
    def providers(self) -> tuple[ProviderInfo, ...]:
        """Each source's key, display name, and role, in fetch order."""
        return (
            ProviderInfo(key=self.base.key, name=self.base.name, role="base"),
            ProviderInfo(key=self.secondary.key, name=self.secondary.name, role="secondary"),
        )

    def get(self, pier: PierConfig) -> FetchResult:
        base, base_outcome = self._safe_fetch(self.base, pier, "base")
        secondary, secondary_outcome = self._safe_fetch(self.secondary, pier, "secondary")
        return FetchResult(
            conditions=assemble_snapshot(base, secondary),
            outcomes=(base_outcome, secondary_outcome),
        )

    def _safe_fetch(
        self, provider: Provider, pier: PierConfig, role: Role
    ) -> tuple[SourceForecast, FetchOutcome]:
        """Fetch one source; a failure or an empty forecast is a failed outcome.

        The full error text goes to the log only. The outcome carries the safe
        description from :func:`~pierpressure.health.describe_error`.
        """
        fetched_at = self.now()
        error: str | None = None
        try:
            forecast = provider.fetch(pier)
        except Exception as exc:  # noqa: BLE001 - a failed source degrades, never fails
            logger.warning("conditions %s source failed: %s", role, exc)
            forecast, error = SourceForecast(), describe_error(exc)
        else:
            if forecast.is_empty:
                error = NO_READINGS
        return forecast, FetchOutcome(
            key=provider.key,
            name=provider.name,
            role=role,
            fetched_at=fetched_at,
            ok=error is None,
            error=error,
            issued_at=forecast.issued_at if error is None else None,
        )


def build_provider(
    base: Provider | None = None,
    secondary: Provider | None = None,
    now: Callable[[], datetime] = _utcnow,
) -> CompositeProvider:
    """Assemble the production provider stack: both sources, composed.

    ``base`` and ``secondary`` default to the real sources; tests pass stubs to run
    the production stack without the network. ``now`` stamps each fetch outcome,
    and Open-Meteo's issue time, so the two always come from the same clock.
    """
    from .open_meteo import OpenMeteoProvider
    from .seven_timer import SevenTimerProvider

    return CompositeProvider(
        base=base if base is not None else OpenMeteoProvider(now=now),
        secondary=secondary if secondary is not None else SevenTimerProvider(),
        now=now,
    )
