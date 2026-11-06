"""Provider interface, the per-variable fill, and graceful fallback (ADR-0027).

A provider parses one external forecast into a :class:`SourceForecast` — a
per-hour set of readings plus the data's issue time — and points at its
:class:`~pierpressure.core.providers.ProviderSpec`, which declares the variables
it supplies and its bundles. :func:`assemble_snapshot` fills the core's
:class:`~pierpressure.core.conditions.Conditions` one series per variable, from
the first provider in the configured order that returned it, and keeps every
later provider's series for it as an alternate.
:class:`CompositeProvider` fetches every provider in that order, each guarded so
one failing never fails another, then runs the fill. A failed or empty fetch is
passed over; its variables are never filled from an earlier fetch.

Each fetch also reports a :class:`~pierpressure.health.FetchOutcome` per provider.
The outcomes travel beside the conditions in a :class:`FetchResult`, so they feed
provider health and never reach the verdict (provider-health-entities D1).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from typing import Protocol, get_args

from pierpressure.core.conditions import Conditions, Series, Variable
from pierpressure.core.config import PierConfig
from pierpressure.core.providers import CATALOG, ProviderSpec
from pierpressure.health import NO_READINGS, FetchOutcome, ProviderInfo, describe_error

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceReading:
    """One provider's readings for a single hour. Absent fields are ``None``.

    ``cloud_low``/``cloud_mid``/``cloud_high`` carry the low/mid/high split of the
    total cloud cover (percent), each independently present-or-absent: a provider
    reporting only a total leaves all three ``None``.

    The weather fields carry the provider's values unrounded: temperature and dew
    point in °C, humidity and precipitation probability in %, wind speed in km/h
    and wind direction in degrees. Aerosol optical depth (no unit) and PM2.5
    (µg/m³) are carried as reported, and so is column water vapour (kg/m²).
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
    aerosol_optical_depth: float | None = None
    pm2_5: float | None = None
    column_water_vapour: float | None = None


@dataclass(frozen=True)
class SourceForecast:
    """A provider's parsed hourly readings, keyed by top-of-hour UTC, plus issue time.

    ``issued_at`` is the time the provider issued this data (not when it was
    fetched), so the data's own age stays visible (the per-series issue-time
    rule).
    """

    issued_at: datetime | None = None
    readings: Mapping[datetime, SourceReading] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.readings


class Provider(Protocol):
    """Anything that can fetch one provider's forecast for a pier.

    ``spec`` is the provider's fixed declaration in the core: its stable key, used
    in health topics and entity identities, its display name, and its variables.
    """

    @property
    def spec(self) -> ProviderSpec: ...

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
    values included. A provider fills its bundle whole or not at all: when an
    earlier provider holds any member, it fills none of them. A series is whole:
    hours its provider did not cover stay absent and are never taken from
    another provider. A failed fetch is an empty
    forecast, so it is passed over like any provider that returned nothing.

    Every later provider that declares a variable and returned its bundle
    becomes one of that variable's alternates, in ``fills`` order
    (cloud-agreement DD2). Alternates are decided per variable, so a losing
    bundle yields one alternate per member, a member with no values included.

    Variables are walked in the fixed :data:`Variable` order and providers in
    ``fills`` order, so the result depends on nothing but the inputs.
    """
    series: dict[Variable, Series] = {}
    filled_by: dict[Variable, int] = {}
    alternates: dict[Variable, list[Series]] = {}
    for variable in get_args(Variable):
        for index, (spec, forecast) in enumerate(fills):
            if variable not in spec.variables:
                continue
            bundle = [member for member in spec.variables if member in spec.bundle_of(variable)]
            if not _returned(forecast, bundle):
                continue
            if variable not in series:
                # An earlier provider that won any member keeps it, and this
                # provider fills none of the rest, so a bundle is never split.
                if any(member in series for member in bundle):
                    continue
                for member in bundle:
                    series[member] = _series(spec, forecast, member)
                    filled_by[member] = index
            elif index > filled_by[variable]:
                alternates.setdefault(variable, []).append(_series(spec, forecast, variable))
    return Conditions(
        series=series,
        alternates={variable: tuple(found) for variable, found in alternates.items()},
    )


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class FetchResult:
    """One pier's conditions, and the outcome of each provider fetch behind them."""

    conditions: Conditions
    outcomes: tuple[FetchOutcome, ...] = ()


@dataclass
class CompositeProvider:
    """Fetch every provider in order, then fill each variable (provider-order D4).

    Each fetch is guarded, so one provider failing never fails another: a failed
    provider is passed over for every variable, and the snapshot holds whatever
    the rest returned. A partial snapshot is a valid result, not an error.

    ``now`` stamps each outcome's fetch time; tests pass a fixed clock.
    """

    fetchers: Sequence[Provider]
    now: Callable[[], datetime] = _utcnow

    @property
    def providers(self) -> tuple[ProviderInfo, ...]:
        """Each provider's key, display name, and declared variables, in order."""
        return tuple(
            ProviderInfo(key=f.spec.key, name=f.spec.name, variables=f.spec.variables)
            for f in self.fetchers
        )

    def get(self, pier: PierConfig) -> FetchResult:
        fetched = [self._safe_fetch(fetcher, pier) for fetcher in self.fetchers]
        fills = [
            (fetcher.spec, forecast)
            for fetcher, (forecast, _) in zip(self.fetchers, fetched, strict=True)
        ]
        return FetchResult(
            conditions=assemble_snapshot(fills),
            outcomes=tuple(outcome for _, outcome in fetched),
        )

    def _safe_fetch(
        self, provider: Provider, pier: PierConfig
    ) -> tuple[SourceForecast, FetchOutcome]:
        """Fetch one provider; a failure or an empty forecast is a failed outcome.

        The full error text goes to the log only. The outcome carries the safe
        description from :func:`~pierpressure.health.describe_error`.
        """
        spec = provider.spec
        fetched_at = self.now()
        error: str | None = None
        try:
            forecast = provider.fetch(pier)
        except Exception as exc:  # noqa: BLE001 - a failed provider degrades, never fails
            logger.warning("conditions provider %s failed: %s", spec.key, exc)
            forecast, error = SourceForecast(), describe_error(exc)
        else:
            if forecast.is_empty:
                error = NO_READINGS
        return forecast, FetchOutcome(
            key=spec.key,
            name=spec.name,
            variables=spec.variables,
            fetched_at=fetched_at,
            ok=error is None,
            error=error,
            issued_at=forecast.issued_at if error is None else None,
        )


def build_provider(
    keys: Sequence[str],
    *,
    now: Callable[[], datetime] = _utcnow,
    fetchers: Mapping[str, Provider] | None = None,
) -> CompositeProvider:
    """Assemble the production provider stack from the configured provider order.

    ``keys`` are catalog keys, already checked by the configuration. ``fetchers``
    replaces the real fetcher for a key; tests pass stubs to run the production
    stack without the network. ``now`` stamps each fetch outcome, and
    Open-Meteo's issue time, so the two always come from the same clock.
    """
    from .nws import NwsProvider
    from .open_meteo import MODELS, OpenMeteoProvider
    from .seven_timer import SevenTimerProvider

    real: dict[str, Callable[[], Provider]] = {
        OpenMeteoProvider.spec.key: lambda: OpenMeteoProvider(now=now),
        SevenTimerProvider.spec.key: SevenTimerProvider,
        NwsProvider.spec.key: NwsProvider,
    }
    for key, model in MODELS.items():
        real[key] = partial(OpenMeteoProvider, spec=CATALOG[key], model=model, now=now)
    real["open_meteo_air_quality"] = partial(
        OpenMeteoProvider, spec=CATALOG["open_meteo_air_quality"], now=now
    )
    overrides = fetchers or {}
    return CompositeProvider(
        fetchers=tuple(overrides[key] if key in overrides else real[key]() for key in keys),
        now=now,
    )
