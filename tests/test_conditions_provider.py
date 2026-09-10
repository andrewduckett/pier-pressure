"""Tasks 3.1-3.5: provider parsing, assembly, resampling, caching, and fallback."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pierpressure.conditions.open_meteo import parse_open_meteo
from pierpressure.conditions.provider import (
    CachingProvider,
    CompositeProvider,
    SourceForecast,
    SourceReading,
    assemble_snapshot,
)
from pierpressure.conditions.seven_timer import parse_seven_timer

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


# --------------------------------------------------------------------------- #
# 3.1 assembly merges sources with per-field availability and per-source times
# --------------------------------------------------------------------------- #


def test_assemble_merges_base_and_secondary_by_hour() -> None:
    base = SourceForecast(
        issued_at=_hour(18),
        readings={_hour(21): SourceReading(cloud_cover=20.0, wind_gust=15.0)},
    )
    secondary = SourceForecast(
        issued_at=_hour(17),
        readings={_hour(21): SourceReading(seeing=0.8, transparency=0.7)},
    )
    snap = assemble_snapshot(base, secondary)
    hour = snap.at(_hour(21))
    assert hour is not None
    assert (hour.cloud_cover, hour.wind_gust) == (20.0, 15.0)
    assert (hour.seeing, hour.transparency) == (0.8, 0.7)
    assert snap.base_issued_at == _hour(18)
    assert snap.secondary_issued_at == _hour(17)


def test_assemble_marks_absent_sources_unavailable() -> None:
    base = SourceForecast(
        issued_at=_hour(18),
        readings={_hour(21): SourceReading(cloud_cover=20.0, wind_gust=15.0)},
    )
    snap = assemble_snapshot(base, SourceForecast())  # secondary empty
    hour = snap.at(_hour(21))
    assert hour is not None
    assert hour.cloud_cover == 20.0
    assert hour.seeing is None
    assert snap.secondary_issued_at is None  # no data -> no issue time


# --------------------------------------------------------------------------- #
# 3.5 independent fetch + graceful fallback
# --------------------------------------------------------------------------- #


class _StubProvider:
    def __init__(self, forecast: SourceForecast | None = None, *, fail: bool = False) -> None:
        self._forecast = forecast or SourceForecast()
        self._fail = fail

    def fetch(self, pier: object) -> SourceForecast:
        if self._fail:
            raise RuntimeError("source down")
        return self._forecast


def test_secondary_failure_leaves_base_data_intact() -> None:
    base = _StubProvider(
        SourceForecast(
            issued_at=_hour(18),
            readings={_hour(21): SourceReading(cloud_cover=30.0, wind_gust=10.0)},
        )
    )
    composite = CompositeProvider(base=base, secondary=_StubProvider(fail=True))
    snap = composite.get(make_pier())
    hour = snap.at(_hour(21))
    assert hour is not None
    assert hour.cloud_cover == 30.0
    assert hour.seeing is None


def test_base_failure_still_yields_a_snapshot() -> None:
    secondary = _StubProvider(
        SourceForecast(
            issued_at=_hour(18),
            readings={_hour(21): SourceReading(seeing=0.9, transparency=0.8)},
        )
    )
    composite = CompositeProvider(base=_StubProvider(fail=True), secondary=secondary)
    snap = composite.get(make_pier())
    hour = snap.at(_hour(21))
    assert hour is not None
    assert hour.cloud_cover is None
    assert hour.wind_gust is None
    assert hour.seeing == 0.9


# --------------------------------------------------------------------------- #
# 3.4 caching: reuse within staleness, drop when over-stale
# --------------------------------------------------------------------------- #


def test_cache_reuses_recent_data_after_a_failed_fetch() -> None:
    good = SourceForecast(
        issued_at=_hour(18), readings={_hour(21): SourceReading(cloud_cover=25.0)}
    )
    provider = _StubProvider(good)
    now = _hour(19)
    caching = CachingProvider(inner=provider, now=lambda: now)
    assert caching.fetch(make_pier()).readings  # primes the cache

    # Next fetch fails; the cache (1h old) is within staleness and reused.
    provider._fail = True  # type: ignore[attr-defined]
    reused = caching.fetch(make_pier())
    assert reused.readings[_hour(21)].cloud_cover == 25.0
    assert reused.issued_at == _hour(18)  # original issue time preserved


def test_cache_drops_over_stale_data() -> None:
    good = SourceForecast(issued_at=_hour(0), readings={_hour(21): SourceReading(cloud_cover=25.0)})
    provider = _StubProvider(good)
    now = _hour(0) + timedelta(hours=20)  # far past MAX_STALENESS (12h)
    caching = CachingProvider(inner=provider, now=lambda: now)
    caching.fetch(make_pier())  # prime

    provider._fail = True  # type: ignore[attr-defined]
    reused = caching.fetch(make_pier())
    assert reused.is_empty  # too old to serve


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
    snap = assemble_snapshot(base, SourceForecast())
    assert snap.at(_hour(21)) is not None
    assert snap.at(_hour(23)) is None  # beyond the forecast horizon


def test_cache_is_per_source_so_base_survives_secondary_outage() -> None:
    # Two independent caches: base fresh, secondary failing -> base still usable.
    base_cache = CachingProvider(
        inner=_StubProvider(
            SourceForecast(
                issued_at=_hour(18), readings={_hour(21): SourceReading(cloud_cover=15.0)}
            )
        ),
        now=lambda: _hour(19),
    )
    secondary_cache = CachingProvider(inner=_StubProvider(fail=True), now=lambda: _hour(19))
    composite = CompositeProvider(base=base_cache, secondary=secondary_cache)
    snap = composite.get(make_pier())
    hour = snap.at(_hour(21))
    assert hour is not None and hour.cloud_cover == 15.0
    assert hour.seeing is None
