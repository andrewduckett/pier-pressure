"""Tasks 3.1-3.5: provider parsing, assembly, resampling, and fallback."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from pierpressure.conditions.nws import NwsProvider, parse_nws
from pierpressure.conditions.open_meteo import COLUMNS, OpenMeteoProvider, parse_open_meteo
from pierpressure.conditions.provider import (
    CompositeProvider,
    SourceForecast,
    SourceReading,
    assemble_snapshot,
    build_provider,
)
from pierpressure.conditions.seven_timer import SevenTimerProvider, parse_seven_timer
from pierpressure.core.conditions import Conditions
from pierpressure.core.config import PierConfig
from pierpressure.core.providers import (
    CATALOG,
    NWS,
    OPEN_METEO,
    OPEN_METEO_HRDPS,
    SEVEN_TIMER,
    ProviderSpec,
)
from pierpressure.health import FetchOutcome, ProviderInfo, describe_error

from .conftest import make_pier

_FIXTURES = Path(__file__).parent / "fixtures"
_ISSUED = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _hour(h: int) -> datetime:
    return datetime(2026, 9, 8, h, 0, tzinfo=UTC)


# --------------------------------------------------------------------------- #
# 3.2 base provider parsing (Open-Meteo)
# --------------------------------------------------------------------------- #


def test_open_meteo_parses_hourly_cloud_and_gust() -> None:
    forecast = parse_open_meteo(_load("open_meteo.json"), issued_at=_ISSUED)
    assert forecast.issued_at == _ISSUED
    reading = forecast.readings[_hour(20)]
    assert reading.cloud_cover == 10.0
    assert reading.wind_gust == 15.0
    # seeing/transparency are not this source's business.
    assert reading.seeing is None
    assert reading.transparency is None


def test_open_meteo_leaves_null_hour_values_absent() -> None:
    forecast = parse_open_meteo(_load("open_meteo.json"), issued_at=_ISSUED)
    # cloud_cover is null at 22:00 in the fixture; gust is present.
    assert forecast.readings[_hour(22)].cloud_cover is None
    assert forecast.readings[_hour(22)].wind_gust == 22.0


def test_open_meteo_parses_the_cloud_component_split() -> None:
    forecast = parse_open_meteo(_load("open_meteo.json"), issued_at=_ISSUED)
    reading = forecast.readings[_hour(20)]
    assert reading.cloud_low == 5.0
    assert reading.cloud_mid == 3.0
    assert reading.cloud_high == 2.0


def test_open_meteo_leaves_a_null_component_absent() -> None:
    forecast = parse_open_meteo(_load("open_meteo.json"), issued_at=_ISSUED)
    # cloud_cover_high is null at 22:00; low and mid are present there.
    reading = forecast.readings[_hour(22)]
    assert reading.cloud_high is None
    assert reading.cloud_low == 5.0
    assert reading.cloud_mid == 8.0


def test_open_meteo_parses_the_weather_variables_unrounded() -> None:
    forecast = parse_open_meteo(_load("open_meteo.json"), issued_at=_ISSUED)
    reading = forecast.readings[_hour(20)]
    assert reading.temperature == 12.34
    assert reading.dew_point == 9.8
    assert reading.humidity == 85.0
    assert reading.wind_speed == 14.25
    assert reading.wind_direction == 230.0
    assert reading.precipitation_probability == 35.0


def test_open_meteo_leaves_a_null_weather_value_absent() -> None:
    forecast = parse_open_meteo(_load("open_meteo.json"), issued_at=_ISSUED)
    # dew_point_2m is null at 22:00; the other weather values are present there.
    reading = forecast.readings[_hour(22)]
    assert reading.dew_point is None
    assert reading.temperature == 11.2
    assert reading.humidity == 90.0
    assert reading.wind_speed == 10.4
    assert reading.wind_direction == 240.0
    assert reading.precipitation_probability == 10.0


def test_open_meteo_absent_weather_array_leaves_that_field_none_every_hour() -> None:
    payload = _load("open_meteo.json")
    del payload["hourly"]["precipitation_probability"]
    forecast = parse_open_meteo(payload, issued_at=_ISSUED)
    assert all(r.precipitation_probability is None for r in forecast.readings.values())
    assert forecast.readings[_hour(20)].temperature == 12.34
    assert forecast.readings[_hour(23)].wind_direction == 250.0


def test_open_meteo_fetch_requests_the_weather_variables_in_kmh() -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_load("open_meteo.json"))

    client = httpx.Client(transport=httpx.MockTransport(handle))
    OpenMeteoProvider(client=client, now=lambda: _ISSUED).fetch(make_pier())
    (request,) = requests
    hourly = request.url.params["hourly"].split(",")
    for variable in (
        "temperature_2m",
        "dew_point_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "wind_direction_10m",
        "precipitation_probability",
    ):
        assert variable in hourly
    assert request.url.params["wind_speed_unit"] == "kmh"


def _requests_of(
    provider_for: Callable[[httpx.Client], OpenMeteoProvider], payload: dict
) -> list[httpx.Request]:
    """Fetch once through a mock transport and return the requests it sent."""
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handle))
    provider_for(client).fetch(make_pier())
    return requests


def test_open_meteo_request_is_pinned_and_names_no_model() -> None:
    (request,) = _requests_of(
        lambda client: OpenMeteoProvider(client=client, now=lambda: _ISSUED),
        _load("open_meteo.json"),
    )
    params = request.url.params
    assert params["hourly"] == (
        "cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_gusts_10m,"
        "temperature_2m,dew_point_2m,relative_humidity_2m,wind_speed_10m,"
        "wind_direction_10m,precipitation_probability"
    )
    assert params["forecast_days"] == "2"
    assert params["wind_speed_unit"] == "kmh"
    assert params["timezone"] == "UTC"
    assert "models" not in params


def test_every_variable_an_open_meteo_spec_declares_has_a_column() -> None:
    open_meteo_specs = [spec for key, spec in CATALOG.items() if key.startswith("open_meteo")]
    assert len(open_meteo_specs) == 6
    for spec in open_meteo_specs:
        assert set(spec.variables) <= COLUMNS.keys(), spec.key


def test_a_model_provider_asks_for_its_model_and_its_declared_variables_only() -> None:
    (request,) = _requests_of(
        lambda client: OpenMeteoProvider(
            spec=OPEN_METEO_HRDPS,
            model="gem_hrdps_continental",
            client=client,
            now=lambda: _ISSUED,
        ),
        _load("open_meteo.json"),
    )
    params = request.url.params
    assert params.get_list("models") == ["gem_hrdps_continental"]
    assert params["forecast_days"] == "2"
    assert params["wind_speed_unit"] == "kmh"
    hourly = params["hourly"].split(",")
    assert "precipitation_probability" not in hourly
    assert hourly == [COLUMNS[variable] for variable in OPEN_METEO_HRDPS.variables]


def test_the_open_meteo_class_still_points_at_the_best_match_spec() -> None:
    assert OpenMeteoProvider.spec is OPEN_METEO
    assert OpenMeteoProvider().spec is OPEN_METEO
    assert OpenMeteoProvider().model is None


# --------------------------------------------------------------------------- #
# 3.3 secondary provider parsing + resample to hourly (7Timer!)
# --------------------------------------------------------------------------- #


def test_seven_timer_resamples_three_hourly_onto_the_hourly_grid() -> None:
    forecast = parse_seven_timer(_load("seven_timer.json"))
    # init 2026-09-08 18:00; timepoint 3 -> 21:00 block, timepoint 6 -> 00:00 block.
    assert forecast.issued_at == _hour(18)
    # Two 3-hourly entries expand to six hourly slots.
    assert len(forecast.readings) == 6
    for h in (21, 22, 23):
        assert forecast.readings[_hour(h)].seeing is not None
    # The 21:00 block holds the first entry's seeing index (2 -> quality > 0.5).
    assert (
        forecast.readings[_hour(21)].seeing is not None
        and forecast.readings[_hour(21)].seeing > 0.5
    )


def test_seven_timer_maps_best_and_worst_indices_to_quality() -> None:
    payload = {
        "init": "2026090818",
        "dataseries": [{"timepoint": 3, "seeing": 1, "transparency": 8}],
    }
    forecast = parse_seven_timer(payload)
    reading = forecast.readings[_hour(21)]
    assert reading.seeing == 1.0  # best index -> full quality
    assert reading.transparency == 0.0  # worst index -> zero quality


def test_seven_timer_follows_the_redirect_to_its_astro_endpoint() -> None:
    # 7Timer! answers api.pl with a 302 to astro.php, which serves the same JSON.
    astro_url = "https://www.7timer.info/bin/astro.php?lon=-87.9&lat=42.2&output=json"

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/bin/api.pl":
            return httpx.Response(302, headers={"Location": astro_url})
        return httpx.Response(200, json=_load("seven_timer.json"))

    client = httpx.Client(transport=httpx.MockTransport(handle))
    forecast = SevenTimerProvider(client=client).fetch(make_pier())
    assert forecast.issued_at == _hour(18)
    assert len(forecast.readings) == 6


# --------------------------------------------------------------------------- #
# The fill: each variable from the first provider in order that returned it
# (provider-order D3)
# --------------------------------------------------------------------------- #

_FIRST = ProviderSpec(
    key="first",
    name="First",
    needs_key=False,
    variables=("cloud_cover", "cloud_low", "cloud_mid", "cloud_high", "wind_gust"),
    bundles=(frozenset({"cloud_cover", "cloud_low", "cloud_mid", "cloud_high"}),),
)
_SECOND = replace(_FIRST, key="second", name="Second")


def _forecast(issued: int, **columns: dict[int, float | None]) -> SourceForecast:
    """A forecast whose readings hold each named variable at the given hours."""
    hours = sorted({h for column in columns.values() for h in column})
    return SourceForecast(
        issued_at=_hour(issued),
        readings={
            _hour(h): SourceReading(**{name: column.get(h) for name, column in columns.items()})
            for h in hours
        },
    )


def test_assemble_the_default_order_gives_cloud_to_open_meteo_and_seeing_to_seven_timer() -> None:
    base = _forecast(18, cloud_cover={21: 20.0}, wind_gust={21: 15.0})
    secondary = _forecast(17, seeing={21: 0.8}, transparency={21: 0.7})
    conditions = assemble_snapshot([(OPEN_METEO, base), (SEVEN_TIMER, secondary)])
    for variable in ("cloud_cover", "wind_gust"):
        assert conditions.series[variable].provider == "open_meteo"
        assert conditions.issued_at(variable) == _hour(18)
    for variable in ("seeing", "transparency"):
        assert conditions.series[variable].provider == "seven_timer"
        assert conditions.issued_at(variable) == _hour(17)
    assert conditions.value_at("cloud_cover", _hour(21)) == 20.0
    assert conditions.value_at("wind_gust", _hour(21)) == 15.0
    assert conditions.value_at("seeing", _hour(21)) == 0.8
    assert conditions.value_at("transparency", _hour(21)) == 0.7


def test_assemble_an_earlier_provider_wins_a_variable_both_returned() -> None:
    conditions = assemble_snapshot(
        [
            (_FIRST, _forecast(18, cloud_cover={21: 40.0})),
            (_SECOND, _forecast(17, cloud_cover={21: 70.0})),
        ]
    )
    assert conditions.series["cloud_cover"].provider == "first"
    assert conditions.value_at("cloud_cover", _hour(21)) == 40.0


def test_assemble_an_empty_column_falls_through_to_the_next_provider() -> None:
    conditions = assemble_snapshot(
        [
            (_FIRST, _forecast(18, cloud_cover={21: None, 22: None}, wind_gust={21: 9.0})),
            (_SECOND, _forecast(17, cloud_cover={21: 70.0, 22: 60.0})),
        ]
    )
    assert conditions.series["cloud_cover"].provider == "second"
    assert conditions.series["cloud_cover"].values == {_hour(21): 70.0, _hour(22): 60.0}
    assert conditions.series["wind_gust"].provider == "first"


def test_assemble_a_bundle_travels_together() -> None:
    four = {
        "cloud_cover": {21: 70.0},
        "cloud_low": {21: 1.0},
        "cloud_mid": {21: 2.0},
        "cloud_high": {21: 3.0},
    }
    conditions = assemble_snapshot(
        [(_FIRST, _forecast(18, cloud_cover={21: 40.0})), (_SECOND, _forecast(17, **four))]
    )
    assert conditions.series["cloud_cover"].provider == "first"
    for layer in ("cloud_low", "cloud_mid", "cloud_high"):
        series = conditions.series[layer]
        assert series.provider == "first"
        assert series.issued_at == _hour(18)
        assert series.values == {_hour(21): None}


def test_assemble_a_later_bundle_never_takes_a_variable_an_earlier_provider_won() -> None:
    total_only = ProviderSpec(
        key="total", name="Total", needs_key=False, variables=("cloud_cover",)
    )
    four = {
        "cloud_cover": {21: 70.0},
        "cloud_low": {21: 1.0},
        "cloud_mid": {21: 2.0},
        "cloud_high": {21: 3.0},
    }
    conditions = assemble_snapshot(
        [(total_only, _forecast(16, cloud_cover={21: 40.0})), (_SECOND, _forecast(17, **four))]
    )
    assert conditions.series["cloud_cover"].provider == "total"
    assert conditions.value_at("cloud_cover", _hour(21)) == 40.0
    assert conditions.issued_at("cloud_cover") == _hour(16)


def test_assemble_a_series_is_whole_never_merged_per_hour() -> None:
    conditions = assemble_snapshot(
        [
            (_FIRST, _forecast(18, cloud_cover={h: 10.0 for h in range(20, 24)})),
            (_SECOND, _forecast(17, cloud_cover={h: 90.0 for h in range(18, 24)})),
        ]
    )
    series = conditions.series["cloud_cover"]
    assert series.provider == "first"
    assert series.values == {_hour(h): 10.0 for h in range(20, 24)}
    assert conditions.value_at("cloud_cover", _hour(19)) is None


def test_assemble_a_failed_or_empty_forecast_is_passed_over() -> None:
    conditions = assemble_snapshot(
        [(_FIRST, SourceForecast()), (_SECOND, _forecast(17, cloud_cover={21: 70.0}))]
    )
    assert conditions.series["cloud_cover"].provider == "second"
    assert "wind_gust" not in conditions.series


def test_assemble_a_variable_no_provider_returned_has_no_series() -> None:
    conditions = assemble_snapshot([(OPEN_METEO, _forecast(18, cloud_cover={21: 20.0}))])
    assert "seeing" not in conditions.series
    assert "wind_gust" not in conditions.series
    assert assemble_snapshot([]) == Conditions()


def test_assemble_a_series_keeps_every_hour_its_provider_returned() -> None:
    base = _forecast(18, cloud_cover={21: 20.0, 22: None}, wind_gust={21: None, 22: 15.0})
    conditions = assemble_snapshot([(OPEN_METEO, base)])
    assert conditions.series["cloud_cover"].values == {_hour(21): 20.0, _hour(22): None}
    assert conditions.series["wind_gust"].values == {_hour(21): None, _hour(22): 15.0}


def test_assemble_a_total_only_provider_leaves_the_components_without_values() -> None:
    conditions = assemble_snapshot([(OPEN_METEO, _forecast(18, cloud_cover={21: 40.0}))])
    assert conditions.value_at("cloud_cover", _hour(21)) == 40.0
    for layer in ("cloud_low", "cloud_mid", "cloud_high"):
        assert conditions.value_at(layer, _hour(21)) is None


def test_assemble_carries_the_weather_variables_and_a_missing_one_alone_is_null() -> None:
    weather = {
        "temperature": {21: 12.34, 22: 11.0},
        "dew_point": {21: 9.8, 22: None},
        "humidity": {21: 85.0, 22: 86.0},
        "wind_speed": {21: 14.25, 22: 13.0},
        "wind_direction": {21: 230.0, 22: 231.0},
        "precipitation_probability": {21: 35.0, 22: 30.0},
    }
    conditions = assemble_snapshot([(OPEN_METEO, _forecast(18, **weather))])
    for variable, column in weather.items():
        for h, value in column.items():
            assert conditions.value_at(variable, _hour(h)) == value  # type: ignore[arg-type]


def test_assemble_a_provider_without_weather_leaves_the_weather_variables_unfilled() -> None:
    conditions = assemble_snapshot(
        [(OPEN_METEO, _forecast(18, cloud_cover={21: 40.0}, wind_gust={21: 15.0}))]
    )
    assert conditions.value_at("cloud_cover", _hour(21)) == 40.0
    for variable in ("temperature", "dew_point", "humidity", "wind_speed", "wind_direction"):
        assert variable not in conditions.series
    assert "precipitation_probability" not in conditions.series


def test_assemble_a_later_bundle_is_not_split_around_an_earlier_winner() -> None:
    four = {
        "cloud_cover": {21: 70.0},
        "cloud_low": {21: 1.0},
        "cloud_mid": {21: 2.0},
        "cloud_high": {21: 3.0},
    }
    conditions = assemble_snapshot(
        [(NWS, _forecast(16, cloud_cover={21: 40.0})), (OPEN_METEO, _forecast(17, **four))]
    )
    assert conditions.series["cloud_cover"].provider == "nws"
    assert [s.provider for s in conditions.alternates["cloud_cover"]] == ["open_meteo"]
    for layer in ("cloud_low", "cloud_mid", "cloud_high"):
        assert layer not in conditions.series
        assert layer not in conditions.alternates


# --------------------------------------------------------------------------- #
# Alternates: the series that lost the fill (cloud-agreement DD2)
# --------------------------------------------------------------------------- #

_THIRD = replace(_FIRST, key="third", name="Third")


def test_assemble_a_later_providers_cloud_becomes_an_alternate() -> None:
    conditions = assemble_snapshot(
        [
            (_FIRST, _forecast(18, cloud_cover={21: 40.0})),
            (_SECOND, _forecast(17, cloud_cover={21: 70.0})),
        ]
    )
    assert conditions.series["cloud_cover"].provider == "first"
    assert conditions.value_at("cloud_cover", _hour(21)) == 40.0
    (alternate,) = conditions.alternates["cloud_cover"]
    assert alternate.provider == "second"
    assert alternate.issued_at == _hour(17)
    assert alternate.values == {_hour(21): 70.0}


def test_assemble_alternates_keep_the_configured_order() -> None:
    conditions = assemble_snapshot(
        [
            (_FIRST, _forecast(18, cloud_cover={21: 40.0})),
            (_SECOND, _forecast(17, cloud_cover={21: 70.0})),
            (_THIRD, _forecast(16, cloud_cover={21: 10.0})),
        ]
    )
    assert [s.provider for s in conditions.alternates["cloud_cover"]] == ["second", "third"]


def test_assemble_an_alternate_never_fills_an_hour_the_filled_series_lacks() -> None:
    conditions = assemble_snapshot(
        [
            (_FIRST, _forecast(18, cloud_cover={h: 10.0 for h in range(20, 24)})),
            (_SECOND, _forecast(17, cloud_cover={h: 90.0 for h in range(18, 24)})),
        ]
    )
    assert conditions.value_at("cloud_cover", _hour(19)) is None
    (alternate,) = conditions.alternates["cloud_cover"]
    assert alternate.values == {_hour(h): 90.0 for h in range(18, 24)}


def test_assemble_a_provider_that_returned_nothing_leaves_no_alternate() -> None:
    conditions = assemble_snapshot(
        [
            (_FIRST, _forecast(18, cloud_cover={21: 40.0})),
            (_SECOND, _forecast(17, cloud_cover={21: None, 22: None}, wind_gust={21: 9.0})),
        ]
    )
    assert "cloud_cover" not in conditions.alternates


def test_assemble_a_failed_provider_leaves_the_snapshot_as_if_unlisted() -> None:
    first = _forecast(18, cloud_cover={21: 40.0}, wind_gust={21: 9.0})
    alone = assemble_snapshot([(_FIRST, first)])
    with_failed = assemble_snapshot([(_FIRST, first), (_SECOND, SourceForecast())])
    assert with_failed.alternates == {}
    assert with_failed == alone


def test_assemble_a_losing_bundle_becomes_alternates_member_by_member() -> None:
    four = {
        "cloud_cover": {21: 70.0},
        "cloud_low": {21: 1.0},
        "cloud_mid": {21: 2.0},
        "cloud_high": {21: 3.0},
    }
    conditions = assemble_snapshot(
        [(_FIRST, _forecast(18, cloud_cover={21: 40.0})), (_SECOND, _forecast(17, **four))]
    )
    for variable in ("cloud_cover", "cloud_low", "cloud_mid", "cloud_high"):
        assert [s.provider for s in conditions.alternates[variable]] == ["second"]
    for layer in ("cloud_low", "cloud_mid", "cloud_high"):
        assert conditions.series[layer].provider == "first"
        assert conditions.series[layer].values == {_hour(21): None}


def test_assemble_a_series_has_no_alternate_from_its_own_provider() -> None:
    total_only = ProviderSpec(
        key="total", name="Total", needs_key=False, variables=("cloud_cover",)
    )
    four = {
        "cloud_cover": {21: 70.0},
        "cloud_low": {21: 1.0},
        "cloud_mid": {21: 2.0},
        "cloud_high": {21: 3.0},
    }
    conditions = assemble_snapshot(
        [(total_only, _forecast(16, cloud_cover={21: 40.0})), (_SECOND, _forecast(17, **four))]
    )
    assert [s.provider for s in conditions.alternates["cloud_cover"]] == ["second"]
    assert "cloud_low" not in conditions.alternates


# --------------------------------------------------------------------------- #
# Every listed provider is fetched, in order; none is load-bearing
# (provider-order D4)
# --------------------------------------------------------------------------- #


class _StubProvider:
    def __init__(
        self,
        forecast: SourceForecast | None = None,
        *,
        fail: bool = False,
        spec: ProviderSpec = OPEN_METEO,
        calls: list[str] | None = None,
    ) -> None:
        self._forecast = forecast or SourceForecast()
        self._fail = fail
        self.spec = spec
        self._calls = calls if calls is not None else []

    def fetch(self, pier: object) -> SourceForecast:
        self._calls.append(self.spec.key)
        if self._fail:
            raise RuntimeError("source down")
        return self._forecast


_FETCHED = datetime(2026, 10, 5, 18, 0, tzinfo=UTC)
_BASE_FORECAST = SourceForecast(
    issued_at=_hour(18), readings={_hour(21): SourceReading(cloud_cover=30.0, wind_gust=10.0)}
)
_SECONDARY_FORECAST = SourceForecast(
    issued_at=_hour(17), readings={_hour(21): SourceReading(seeing=0.9, transparency=0.8)}
)


def _composite(*fetchers: _StubProvider) -> CompositeProvider:
    return CompositeProvider(fetchers=fetchers, now=lambda: _FETCHED)


def test_a_failed_later_provider_leaves_the_earlier_providers_data_intact() -> None:
    composite = _composite(
        _StubProvider(_BASE_FORECAST), _StubProvider(fail=True, spec=SEVEN_TIMER)
    )
    conditions = composite.get(make_pier()).conditions
    assert conditions.value_at("cloud_cover", _hour(21)) == 30.0
    assert conditions.value_at("wind_gust", _hour(21)) == 10.0
    assert "seeing" not in conditions.series
    assert "transparency" not in conditions.series


def test_a_failed_earlier_provider_does_not_fail_the_whole_snapshot() -> None:
    composite = _composite(
        _StubProvider(fail=True), _StubProvider(_SECONDARY_FORECAST, spec=SEVEN_TIMER)
    )
    conditions = composite.get(make_pier()).conditions
    assert "cloud_cover" not in conditions.series
    assert "wind_gust" not in conditions.series
    assert conditions.value_at("seeing", _hour(21)) == 0.9


def test_a_failed_provider_is_passed_over_for_a_variable_the_next_returned() -> None:
    second = replace(OPEN_METEO, key="second", name="Second")
    composite = _composite(_StubProvider(fail=True), _StubProvider(_BASE_FORECAST, spec=second))
    conditions = composite.get(make_pier()).conditions
    assert conditions.series["cloud_cover"].provider == "second"
    assert conditions.value_at("cloud_cover", _hour(21)) == 30.0


def test_every_listed_provider_is_fetched_in_order_with_one_outcome_each() -> None:
    calls: list[str] = []
    later = (replace(SEVEN_TIMER, key="later"), replace(SEVEN_TIMER, key="last"))
    full = SourceForecast(
        issued_at=_hour(18),
        readings={_hour(21): SourceReading(cloud_cover=30.0, seeing=0.9, transparency=0.8)},
    )
    first = replace(OPEN_METEO, variables=(*OPEN_METEO.variables, "seeing", "transparency"))
    composite = _composite(
        _StubProvider(full, spec=first, calls=calls),
        *(_StubProvider(_SECONDARY_FORECAST, spec=spec, calls=calls) for spec in later),
    )
    result = composite.get(make_pier())
    assert calls == ["open_meteo", "later", "last"]
    assert [outcome.key for outcome in result.outcomes] == ["open_meteo", "later", "last"]


# --------------------------------------------------------------------------- #
# A failed fetch is never filled from an earlier fetch (issue #37, design D1)
# --------------------------------------------------------------------------- #


class _ScriptedProvider:
    """Answer each fetch with the next scripted outcome: a forecast or a failure."""

    def __init__(self, *outcomes: SourceForecast | Exception, spec: ProviderSpec) -> None:
        self._outcomes = list(outcomes)
        self.spec = spec

    def fetch(self, pier: object) -> SourceForecast:
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _good_then(failure: SourceForecast | Exception) -> CompositeProvider:
    """A production stack whose two providers each succeed once, then fail.

    The data is issued at the real current time, not a pinned one, so it is fresh
    by any measure: reuse bounded by a staleness limit would still be caught.
    """
    now = datetime.now(UTC)
    base = SourceForecast(issued_at=now, readings={_hour(21): SourceReading(cloud_cover=25.0)})
    secondary = SourceForecast(
        issued_at=now, readings={_hour(21): SourceReading(seeing=0.8, transparency=0.7)}
    )
    return build_provider(
        ["open_meteo", "seven_timer"],
        fetchers={
            "open_meteo": _ScriptedProvider(base, failure, spec=OPEN_METEO),
            "seven_timer": _ScriptedProvider(secondary, failure, spec=SEVEN_TIMER),
        },
    )


@pytest.mark.parametrize("failure", [RuntimeError("source down"), SourceForecast()])
def test_a_failed_fetch_is_not_filled_from_the_same_piers_earlier_fetch(
    failure: SourceForecast | Exception,
) -> None:
    stack = _good_then(failure)
    pier = make_pier()
    first = stack.get(pier).conditions
    assert {"cloud_cover", "seeing"} <= first.series.keys()

    # No values or issue time carry over from the earlier fetch, for either provider.
    assert stack.get(pier).conditions == Conditions()


@pytest.mark.parametrize("failure", [RuntimeError("source down"), SourceForecast()])
def test_a_failed_fetch_is_not_filled_from_another_piers_fetch(
    failure: SourceForecast | Exception,
) -> None:
    stack = _good_then(failure)
    first = stack.get(make_pier("pier-a")).conditions
    assert {"cloud_cover", "seeing"} <= first.series.keys()

    assert stack.get(make_pier("pier-b")).conditions == Conditions()


# --------------------------------------------------------------------------- #
# Provider identity and per-fetch outcomes (provider-health-entities D1, D3)
# --------------------------------------------------------------------------- #


def test_build_provider_exposes_each_providers_key_name_and_variables_in_order() -> None:
    assert build_provider(["seven_timer", "open_meteo"]).providers == (
        ProviderInfo(key="seven_timer", name="7Timer!", variables=("seeing", "transparency")),
        ProviderInfo(key="open_meteo", name="Open-Meteo", variables=OPEN_METEO.variables),
    )


def test_each_fetcher_points_at_its_catalog_spec() -> None:
    assert OpenMeteoProvider.spec is CATALOG["open_meteo"]
    assert SevenTimerProvider.spec is CATALOG["seven_timer"]
    for key in CATALOG:
        if key == "nws":  # wired in nws-provider task 3.3
            continue
        [fetcher] = build_provider([key]).fetchers
        assert fetcher.spec is CATALOG[key]


def test_get_returns_the_fill_and_one_outcome_per_provider() -> None:
    composite = _composite(
        _StubProvider(_BASE_FORECAST), _StubProvider(_SECONDARY_FORECAST, spec=SEVEN_TIMER)
    )
    result = composite.get(make_pier())
    assert result.conditions == assemble_snapshot(
        [(OPEN_METEO, _BASE_FORECAST), (SEVEN_TIMER, _SECONDARY_FORECAST)]
    )
    assert result.outcomes == (
        FetchOutcome(
            key="open_meteo",
            name="Open-Meteo",
            variables=OPEN_METEO.variables,
            fetched_at=_FETCHED,
            ok=True,
            issued_at=_hour(18),
        ),
        FetchOutcome(
            key="seven_timer",
            name="7Timer!",
            variables=("seeing", "transparency"),
            fetched_at=_FETCHED,
            ok=True,
            issued_at=_hour(17),
        ),
    )


def test_a_provider_the_fill_passed_over_still_reports_success() -> None:
    second = replace(OPEN_METEO, key="second", name="Second")
    composite = _composite(
        _StubProvider(_BASE_FORECAST), _StubProvider(_BASE_FORECAST, spec=second)
    )
    result = composite.get(make_pier())
    assert {series.provider for series in result.conditions.series.values()} == {"open_meteo"}
    assert result.outcomes[1].ok is True


def test_a_raising_source_gives_a_failed_outcome_with_safe_error_text() -> None:
    composite = _composite(
        _StubProvider(fail=True), _StubProvider(_SECONDARY_FORECAST, spec=SEVEN_TIMER)
    )
    base_outcome = composite.get(make_pier()).outcomes[0]
    assert base_outcome.ok is False
    assert base_outcome.error == describe_error(RuntimeError("source down")) == "RuntimeError"
    assert base_outcome.fetched_at == _FETCHED
    assert base_outcome.issued_at is None


def test_an_empty_forecast_gives_a_failed_outcome() -> None:
    composite = _composite(
        _StubProvider(_BASE_FORECAST), _StubProvider(SourceForecast(), spec=SEVEN_TIMER)
    )
    secondary_outcome = composite.get(make_pier()).outcomes[1]
    assert secondary_outcome.ok is False
    assert secondary_outcome.error == "no readings returned"
    assert secondary_outcome.issued_at is None


def test_readings_with_blank_fields_give_a_successful_outcome() -> None:
    blank = SourceForecast(issued_at=_hour(18), readings={_hour(21): SourceReading()})
    composite = _composite(_StubProvider(blank), _StubProvider(fail=True, spec=SEVEN_TIMER))
    base_outcome = composite.get(make_pier()).outcomes[0]
    assert base_outcome.ok is True
    assert base_outcome.error is None
    assert base_outcome.issued_at == _hour(18)


def test_a_failed_fetch_logs_the_full_error_text(caplog: pytest.LogCaptureFixture) -> None:
    composite = _composite(
        _StubProvider(fail=True), _StubProvider(_SECONDARY_FORECAST, spec=SEVEN_TIMER)
    )
    composite.get(make_pier())
    assert "source down" in caplog.text


# --------------------------------------------------------------------------- #
# 3.4 forecast horizon
# --------------------------------------------------------------------------- #


def test_forecast_horizon_beyond_the_data_is_unavailable() -> None:
    # A forecast that only reaches 21:00-22:00 leaves later hours with no slot, so
    # the core reads them as unavailable rather than served (design D6 horizon).
    base = SourceForecast(
        issued_at=_hour(18),
        readings={
            _hour(21): SourceReading(cloud_cover=20.0),
            _hour(22): SourceReading(cloud_cover=25.0),
        },
    )
    conditions = assemble_snapshot([(OPEN_METEO, base)])
    assert _hour(21) in conditions.series["cloud_cover"].values
    assert _hour(23) not in conditions.series["cloud_cover"].values  # beyond the forecast horizon


def test_build_provider_passes_its_clock_to_open_meteo() -> None:
    # Open-Meteo stamps its issue time at fetch, so it must use the same clock as
    # the fetch outcomes, or its issue time could look later than its last success.
    def clock() -> datetime:
        return _FETCHED

    stack = build_provider(["open_meteo"], now=clock)
    assert stack.now is clock
    [open_meteo] = stack.fetchers
    assert isinstance(open_meteo, OpenMeteoProvider)
    assert open_meteo.now is clock


# --------------------------------------------------------------------------- #
# open-meteo-models 2.5: build_provider builds each model provider
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("key", "model"),
    [
        ("open_meteo_hrrr", "ncep_hrrr_conus"),
        ("open_meteo_hrdps", "gem_hrdps_continental"),
        ("open_meteo_rdps", "gem_regional"),
        ("open_meteo_icon", "icon_seamless"),
        ("open_meteo_gfs", "gfs_global"),
    ],
)
def test_each_model_provider_names_exactly_its_own_model(key: str, model: str) -> None:
    [fetcher] = build_provider([key]).fetchers
    assert isinstance(fetcher, OpenMeteoProvider)
    (request,) = _requests_of(
        lambda client: replace(fetcher, client=client), _load("open_meteo.json")
    )
    params = request.url.params
    assert params.get_list("models") == [model]
    assert params["forecast_days"] == "2"
    assert params["wind_speed_unit"] == "kmh"
    assert params["hourly"].split(",") == [COLUMNS[v] for v in CATALOG[key].variables]


def test_a_model_provider_stamps_its_fetch_time_as_the_issue_time() -> None:
    fetched_at = datetime(2026, 9, 8, 21, 5, tzinfo=UTC)

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_load("open_meteo.json"))

    stack = build_provider(["open_meteo_rdps"], now=lambda: fetched_at)
    [fetcher] = stack.fetchers
    assert isinstance(fetcher, OpenMeteoProvider)
    fetcher.client = httpx.Client(transport=httpx.MockTransport(handle))
    conditions = stack.get(make_pier()).conditions
    assert conditions.series
    for series in conditions.series.values():
        assert series.provider == "open_meteo_rdps"
        assert series.issued_at == fetched_at


# --------------------------------------------------------------------------- #
# open-meteo-models 3.1: each model's real response parses (design D6)
# Trimmed live recordings at Toronto (43.65, -79.38), fetched 2026-11-02 UTC.
# --------------------------------------------------------------------------- #


def _recording(model: str) -> SourceForecast:
    return parse_open_meteo(_load(f"open_meteo_{model}.json"), issued_at=_ISSUED)


@pytest.mark.parametrize("model", ["hrrr", "hrdps", "rdps", "icon", "gfs"])
def test_each_models_recording_parses_into_four_hours_of_readings(model: str) -> None:
    forecast = _recording(model)
    assert len(forecast.readings) == 4
    first = forecast.readings[min(forecast.readings)]
    for variable in ("cloud_cover", "cloud_low", "wind_gust", "temperature", "wind_direction"):
        assert getattr(first, variable) is not None, variable


@pytest.mark.parametrize("model", ["hrdps", "rdps"])
def test_hrdps_and_rdps_recordings_carry_no_precipitation_probability(model: str) -> None:
    readings = _recording(model).readings.values()
    assert all(reading.precipitation_probability is None for reading in readings)


def test_the_hrrr_recording_carries_precipitation_probability() -> None:
    readings = _recording("hrrr").readings
    assert readings[datetime(2026, 11, 2, 0, tzinfo=UTC)].precipitation_probability == 1.0


def test_hours_past_hrdps_reach_stay_absent() -> None:
    readings = _recording("hrdps").readings
    assert readings[datetime(2026, 11, 3, 18, tzinfo=UTC)].cloud_cover == 80.0
    past_reach = readings[datetime(2026, 11, 3, 19, tzinfo=UTC)]
    assert past_reach.cloud_cover is None
    assert past_reach.temperature is None


# --------------------------------------------------------------------------- #
# open-meteo-models 3.2: a model provider fills and fails like any provider
# --------------------------------------------------------------------------- #


def _open_meteo_stack(
    keys: list[str], answers: dict[str | None, httpx.Response]
) -> CompositeProvider:
    """The production stack, with Open-Meteo answering by the request's model."""

    def handle(request: httpx.Request) -> httpx.Response:
        return answers[request.url.params.get("models")]

    client = httpx.Client(transport=httpx.MockTransport(handle))
    stack = build_provider(keys, now=lambda: _FETCHED)
    for fetcher in stack.fetchers:
        assert isinstance(fetcher, OpenMeteoProvider)
        fetcher.client = client
    return stack


def test_the_model_listed_first_fills_cloud_and_the_next_fills_precipitation() -> None:
    stack = _open_meteo_stack(
        ["open_meteo_hrdps", "open_meteo"],
        {
            "gem_hrdps_continental": httpx.Response(200, json=_load("open_meteo_hrdps.json")),
            None: httpx.Response(200, json=_load("open_meteo.json")),
        },
    )
    series = stack.get(make_pier()).conditions.series
    for variable in ("cloud_cover", "cloud_low", "cloud_mid", "cloud_high"):
        assert series[variable].provider == "open_meteo_hrdps"
    assert series["precipitation_probability"].provider == "open_meteo"


def test_hrrr_outside_its_area_fails_and_is_passed_over() -> None:
    stack = _open_meteo_stack(
        ["open_meteo_hrrr", "open_meteo"],
        {
            "ncep_hrrr_conus": httpx.Response(400, json={"error": True, "reason": "No data"}),
            None: httpx.Response(200, json=_load("open_meteo.json")),
        },
    )
    result = stack.get(make_pier())
    hrrr, best_match = result.outcomes
    assert hrrr.key == "open_meteo_hrrr"
    assert not hrrr.ok
    assert hrrr.error == "HTTPStatusError: 400 Bad Request"
    assert best_match.ok
    assert result.conditions.series["cloud_cover"].provider == "open_meteo"


# --------------------------------------------------------------------------- #
# nws-provider: the National Weather Service raw gridpoint forecast
# --------------------------------------------------------------------------- #


def test_the_nws_fixture_pair_names_a_grid_cell_and_an_update_time() -> None:
    point = _load("nws_points.json")["properties"]
    grid = _load("nws_gridpoints.json")["properties"]
    assert (point["gridId"], point["gridX"], point["gridY"]) == ("MKX", 88, 65)
    assert grid["updateTime"] == "2026-11-03T14:31:48+00:00"


_NWS_UNITS = {
    "skyCover": "wmoUnit:percent",
    "windSpeed": "wmoUnit:km_h-1",
    "windGust": "wmoUnit:km_h-1",
    "windDirection": "wmoUnit:degree_(angle)",
    "temperature": "wmoUnit:degC",
    "dewpoint": "wmoUnit:degC",
    "relativeHumidity": "wmoUnit:percent",
    "probabilityOfPrecipitation": "wmoUnit:percent",
}


def _nws(**periods: list[tuple[str, float | None]]) -> dict:
    """A gridpoint payload holding each named NWS property's ``(validTime, value)`` periods."""
    properties: dict = {"updateTime": "2026-09-08T20:35:00+00:00"}
    for name, values in periods.items():
        properties[name] = {
            "uom": _NWS_UNITS[name],
            "values": [{"validTime": when, "value": value} for when, value in values],
        }
    return {"properties": properties}


def _at(day: int, h: int) -> datetime:
    return datetime(2026, 9, day, h, 0, tzinfo=UTC)


def test_nws_period_holds_a_three_hour_sky_cover_across_its_hours() -> None:
    forecast = parse_nws(_nws(skyCover=[("2026-09-08T21:00:00+00:00/PT3H", 45)]))
    assert {time: r.cloud_cover for time, r in forecast.readings.items()} == {
        _hour(21): 45.0,
        _hour(22): 45.0,
        _hour(23): 45.0,
    }


def test_nws_period_spanning_days_holds_across_thirty_hours() -> None:
    forecast = parse_nws(_nws(windSpeed=[("2026-09-08T06:00:00+00:00/P1DT6H", 14.8)]))
    expected = {_at(8, 6) + timedelta(hours=n): 14.8 for n in range(30)}
    assert {time: r.wind_speed for time, r in forecast.readings.items()} == expected


def test_nws_periods_for_different_variables_stay_independent() -> None:
    forecast = parse_nws(
        _nws(
            skyCover=[("2026-09-08T21:00:00+00:00/PT3H", 45)],
            temperature=[("2026-09-08T21:00:00+00:00/PT1H", 12.5)],
        )
    )
    assert forecast.readings[_hour(21)].temperature == 12.5
    for h in (22, 23):
        assert forecast.readings[_hour(h)].cloud_cover == 45.0
        assert forecast.readings[_hour(h)].temperature is None


def test_nws_horizon_cuts_a_period_that_straddles_it() -> None:
    forecast = parse_nws(
        _nws(
            temperature=[("2026-09-08T18:00:00+00:00/PT1H", 12.0)],
            skyCover=[("2026-09-11T16:00:00+00:00/PT3H", 60)],
        )
    )
    assert forecast.readings[_at(11, 16)].cloud_cover == 60.0
    assert forecast.readings[_at(11, 17)].cloud_cover == 60.0
    assert _at(11, 18) not in forecast.readings


def test_nws_horizon_drops_a_period_that_starts_past_it() -> None:
    forecast = parse_nws(
        _nws(
            temperature=[("2026-09-08T18:00:00+00:00/PT1H", 12.0)],
            skyCover=[("2026-09-11T19:00:00+00:00/PT1H", 60)],
        )
    )
    assert _at(11, 19) not in forecast.readings


def test_nws_horizon_is_measured_from_the_earliest_start_across_variables() -> None:
    forecast = parse_nws(
        _nws(
            skyCover=[("2026-09-08T20:00:00+00:00/PT1H", 30)],
            temperature=[("2026-09-08T18:00:00+00:00/P4D", 12.0)],
        )
    )
    assert max(forecast.readings) == _at(11, 17)


def test_nws_unit_expected_codes_are_carried_unrounded() -> None:
    forecast = parse_nws(
        _nws(
            temperature=[("2026-09-08T21:00:00+00:00/PT1H", 12.34)],
            windSpeed=[("2026-09-08T21:00:00+00:00/PT1H", 14.25)],
        )
    )
    assert forecast.readings[_hour(21)].temperature == 12.34
    assert forecast.readings[_hour(21)].wind_speed == 14.25


def test_nws_unit_unexpected_code_leaves_the_variable_absent() -> None:
    payload = _nws(
        windSpeed=[("2026-09-08T21:00:00+00:00/PT2H", 8.0)],
        temperature=[("2026-09-08T21:00:00+00:00/PT2H", 12.0)],
    )
    payload["properties"]["windSpeed"]["uom"] = "wmoUnit:kn"
    forecast = parse_nws(payload)
    assert all(r.wind_speed is None for r in forecast.readings.values())
    assert forecast.readings[_hour(22)].temperature == 12.0


def test_nws_unit_null_value_is_absent_for_its_hours() -> None:
    forecast = parse_nws(
        _nws(
            dewpoint=[("2026-09-08T21:00:00+00:00/PT2H", None)],
            temperature=[("2026-09-08T21:00:00+00:00/PT2H", 12.0)],
        )
    )
    assert forecast.readings[_hour(21)].dew_point is None
    assert forecast.readings[_hour(22)].dew_point is None


def test_nws_issue_time_is_the_update_time() -> None:
    forecast = parse_nws(_nws(skyCover=[("2026-09-08T21:00:00+00:00/PT1H", 45)]))
    assert forecast.issued_at == datetime(2026, 9, 8, 20, 35, tzinfo=UTC)


def test_nws_issue_time_is_none_without_an_update_time() -> None:
    payload = _nws(skyCover=[("2026-09-08T21:00:00+00:00/PT1H", 45)])
    del payload["properties"]["updateTime"]
    assert parse_nws(payload).issued_at is None


_MILWAUKEE = PierConfig(id="milwaukee", latitude=43.0389, longitude=-87.9065, elevation_m=180.0)
_LUDINGTON = PierConfig(id="ludington", latitude=43.9553, longitude=-86.4526, elevation_m=180.0)


class _FakeNws:
    """Serves the recorded NWS pair by URL path and records every request.

    ``cells`` maps a point path to the office and cell it names; any other point
    is outside coverage and answers 404. ``redirects`` maps a point path to the
    one NWS redirects it to. ``failures`` answers a path once with a status.
    """

    def __init__(
        self,
        cells: dict[str, tuple[str, int, int]] | None = None,
        redirects: dict[str, str] | None = None,
        failures: dict[str, int] | None = None,
    ) -> None:
        self.cells = cells or {"/points/43.0389,-87.9065": ("MKX", 88, 65)}
        self.redirects = redirects or {}
        self.failures = failures or {}
        self.requests: list[httpx.Request] = []

    @property
    def paths(self) -> list[str]:
        return [request.url.path for request in self.requests]

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self._handle))

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path in self.failures:
            return httpx.Response(self.failures.pop(path))
        if path in self.redirects:
            return httpx.Response(
                301, headers={"Location": f"https://api.weather.gov{self.redirects[path]}"}
            )
        if path.startswith("/gridpoints/"):
            return httpx.Response(200, json=_load("nws_gridpoints.json"))
        if path not in self.cells:
            return httpx.Response(404)
        point = _load("nws_points.json")
        office, x, y = self.cells[path]
        point["properties"].update(gridId=office, gridX=x, gridY=y)
        return httpx.Response(200, json=point)


def test_nws_fetch_resolves_the_point_then_requests_its_gridpoint() -> None:
    server = _FakeNws()
    forecast = NwsProvider(client=server.client()).fetch(_MILWAUKEE)
    assert server.paths == ["/points/43.0389,-87.9065", "/gridpoints/MKX/88,65"]
    assert forecast.issued_at == datetime(2026, 11, 3, 14, 31, 48, tzinfo=UTC)
    assert forecast.readings


def test_nws_fetch_remembers_the_grid_cell_for_the_same_pier() -> None:
    server = _FakeNws()
    provider = NwsProvider(client=server.client())
    provider.fetch(_MILWAUKEE)
    server.requests.clear()
    provider.fetch(_MILWAUKEE)
    assert server.paths == ["/gridpoints/MKX/88,65"]


def test_nws_fetch_resolves_two_piers_separately() -> None:
    server = _FakeNws(
        cells={
            "/points/43.0389,-87.9065": ("MKX", 88, 65),
            "/points/43.9553,-86.4526": ("GRR", 21, 97),
        }
    )
    provider = NwsProvider(client=server.client())
    for pier in (_MILWAUKEE, _LUDINGTON, _MILWAUKEE, _LUDINGTON):
        provider.fetch(pier)
    assert server.paths == [
        "/points/43.0389,-87.9065",
        "/gridpoints/MKX/88,65",
        "/points/43.9553,-86.4526",
        "/gridpoints/GRR/21,97",
        "/gridpoints/MKX/88,65",
        "/gridpoints/GRR/21,97",
    ]


def test_nws_fetch_follows_a_redirect_from_the_point_request() -> None:
    pier = PierConfig(id="five", latitude=42.12345, longitude=-87.65432, elevation_m=180.0)
    server = _FakeNws(
        cells={"/points/42.1235,-87.6543": ("LOT", 75, 72)},
        redirects={"/points/42.12345,-87.65432": "/points/42.1235,-87.6543"},
    )
    forecast = NwsProvider(client=server.client()).fetch(pier)
    assert server.paths[-1] == "/gridpoints/LOT/75,72"
    assert forecast.readings


def test_nws_fail_point_503_is_not_remembered() -> None:
    server = _FakeNws(failures={"/points/43.0389,-87.9065": 503})
    provider = NwsProvider(client=server.client())
    with pytest.raises(httpx.HTTPStatusError):
        provider.fetch(_MILWAUKEE)
    server.requests.clear()
    provider.fetch(_MILWAUKEE)
    assert server.paths == ["/points/43.0389,-87.9065", "/gridpoints/MKX/88,65"]


def test_nws_fail_outside_coverage_is_passed_over_for_the_next_provider() -> None:
    # make_pier() sits in London, which the fake NWS answers with 404.
    nws = NwsProvider(client=_FakeNws().client())
    composite = CompositeProvider(
        fetchers=(nws, _StubProvider(_BASE_FORECAST)), now=lambda: _FETCHED
    )
    result = composite.get(make_pier())
    outcome, _ = result.outcomes
    assert outcome.key == "nws"
    assert not outcome.ok
    assert outcome.error == "HTTPStatusError: 404 Not Found"
    assert result.conditions.series["cloud_cover"].provider == "open_meteo"


def test_nws_fail_gridpoint_404_forgets_the_cell() -> None:
    server = _FakeNws()
    provider = NwsProvider(client=server.client())
    provider.fetch(_MILWAUKEE)
    server.failures["/gridpoints/MKX/88,65"] = 404
    with pytest.raises(httpx.HTTPStatusError):
        provider.fetch(_MILWAUKEE)
    server.requests.clear()
    provider.fetch(_MILWAUKEE)
    assert server.paths == ["/points/43.0389,-87.9065", "/gridpoints/MKX/88,65"]
