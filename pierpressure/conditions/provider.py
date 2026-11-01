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
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, get_args

from pierpressure.core.conditions import Conditions, Series, Variable
from pierpressure.core.config import PierConfig
from pierpressure.core.providers import OPEN_METEO, SEVEN_TIMER, ProviderSpec
from pierpressure.health import NO_READINGS, FetchOutcome, ProviderInfo, describe_error

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceReading:
    """One source's readings for a single hour. Absent fields are ``None``.

    ``cloud_low``/``cloud_mid``/``cloud_high`` carry the low/mid/high split of the
    total cloud cover (percent), each independently present-or-absent: a source
    reporting only a total leaves all three ``None``.

    The weather fields carry the source's values unrounded: temperature and dew
    point in °C, humidity and precipitation probability in %, wind speed in km/h
    and wind direction in degrees.
    """

    cloud_cover: float | None = None
    wind_gust: float | None = None
    seeing: float | None = None
    transparency: float | None = None
    cloud_low: float | None = None
    cloud_mid: float | None = None
    cloud_high: float | None = None
    temperature: float | None = None
    dew_point: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    wind_direction: float | None = None
    precipitation_probability: float | None = None


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


def _returned(forecast: SourceForecast, variables: Iterable[Variable]) -> bool:
    """Whether any hour of ``forecast`` carries a value for any of ``variables``."""
    return any(
        getattr(reading, variable) is not None
        for reading in forecast.readings.values()
        for variable in variables
    )


def _series(spec: ProviderSpec, forecast: SourceForecast, variable: Variable) -> Series:
    """``variable``'s series over every hour ``forecast`` returned, blanks as ``None``."""
    return Series(
        provider=spec.key,
        issued_at=forecast.issued_at,
        values={
            time: getattr(reading, variable) for time, reading in sorted(forecast.readings.items())
        },
    )


def assemble_snapshot(fills: Sequence[tuple[ProviderSpec, SourceForecast]]) -> Conditions:
    """Fill each variable from the first provider in order that returned it (provider-order D3).

    ``fills`` pairs each provider's declaration with its forecast, in the
    configured order. A provider returned a variable when at least one hour
    carries a value for it or for another member of its bundle. A bundle is
    decided once, so every member comes from the same provider, a member with no
    values included. A series is whole: hours its provider did not cover stay
    absent and are never taken from another provider. A failed fetch is an empty
    forecast, so it is passed over like any provider that returned nothing.

    Variables are walked in the fixed :data:`Variable` order and providers in
    ``fills`` order, so the result depends on nothing but the inputs.
    """
    series: dict[Variable, Series] = {}
    for variable in get_args(Variable):
        if variable in series:
            continue
        for spec, forecast in fills:
            if variable not in spec.variables:
                continue
            bundle = [member for member in spec.variables if member in spec.bundle_of(variable)]
            if _returned(forecast, bundle):
                for member in bundle:
                    series[member] = _series(spec, forecast, member)
                break
    return Conditions(series=series)


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
        """Each source's key, display name, and declared variables, in fetch order."""
        return (
            ProviderInfo(key=self.base.key, name=self.base.name, variables=OPEN_METEO.variables),
            ProviderInfo(
                key=self.secondary.key, name=self.secondary.name, variables=SEVEN_TIMER.variables
            ),
        )

    def get(self, pier: PierConfig) -> FetchResult:
        base, base_outcome = self._safe_fetch(self.base, pier, OPEN_METEO.variables)
        secondary, secondary_outcome = self._safe_fetch(self.secondary, pier, SEVEN_TIMER.variables)
        return FetchResult(
            conditions=assemble_snapshot([(OPEN_METEO, base), (SEVEN_TIMER, secondary)]),
            outcomes=(base_outcome, secondary_outcome),
        )

    def _safe_fetch(
        self, provider: Provider, pier: PierConfig, variables: tuple[str, ...]
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
            logger.warning("conditions provider %s failed: %s", provider.key, exc)
            forecast, error = SourceForecast(), describe_error(exc)
        else:
            if forecast.is_empty:
                error = NO_READINGS
        return forecast, FetchOutcome(
            key=provider.key,
            name=provider.name,
            variables=variables,
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
