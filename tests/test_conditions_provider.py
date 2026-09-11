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
# 3.1 assembly builds one self-stamped group per source (design D1, D2)
# --------------------------------------------------------------------------- #


def test_assemble_builds_both_groups_with_their_own_issue_times() -> None:
    base = SourceForecast(
        issued_at=_hour(18),
        readings={_hour(21): SourceReading(cloud_cover=20.0, wind_gust=15.0)},
    )
    secondary = SourceForecast(
        issued_at=_hour(17),
        readings={_hour(21): SourceReading(seeing=0.8, transparency=0.7)},
    )
    conditions = assemble_snapshot(base, secondary)
    assert conditions.base is not None and conditions.secondary is not None
    base_hour = conditions.base.at(_hour(21))
    assert base_hour is not None and (base_hour.cloud_cover, base_hour.wind_gust) == (20.0, 15.0)
    secondary_hour = conditions.secondary.at(_hour(21))
    assert secondary_hour is not None
    assert (secondary_hour.seeing, secondary_hour.transparency) == (0.8, 0.7)
    # Each source's issue time now travels on its own group's meta, mirroring
    # today's base_issued_at / secondary_issued_at.
    assert conditions.base.meta.issued_at == _hour(18)
    assert conditions.secondary.meta.issued_at == _hour(17)


def test_assemble_absent_secondary_yields_a_none_group_but_keeps_base() -> None:
    base = SourceForecast(
        issued_at=_hour(18),
        readings={_hour(21): SourceReading(cloud_cover=20.0, wind_gust=15.0)},
    )
    conditions = assemble_snapshot(base, SourceForecast())  # secondary empty
    assert conditions.secondary is None  # no rows -> no group, no issue time
    assert conditions.base is not None
    base_hour = conditions.base.at(_hour(21))
    assert base_hour is not None and base_hour.cloud_cover == 20.0


def test_assemble_copies_the_cloud_component_split_onto_the_base_hour() -> None:
    base = SourceForecast(
        issued_at=_hour(18),
        readings={
            _hour(21): SourceReading(
                cloud_cover=40.0, cloud_low=10.0, cloud_mid=20.0, cloud_high=30.0
            )
        },
    )
    conditions = assemble_snapshot(base, SourceForecast())
    assert conditions.base is not None
    base_hour = conditions.base.at(_hour(21))
    assert base_hour is not None
    assert (base_hour.cloud_low, base_hour.cloud_mid, base_hour.cloud_high) == (10.0, 20.0, 30.0)


def test_assemble_total_only_source_leaves_the_components_none() -> None:
    # A source that reports a total but no split yields a present group whose
    # component fields are all None (design D1).
    base = SourceForecast(
        issued_at=_hour(18),
        readings={_hour(21): SourceReading(cloud_cover=40.0)},
    )
    conditions = assemble_snapshot(base, SourceForecast())
    assert conditions.base is not None
    base_hour = conditions.base.at(_hour(21))
    assert base_hour is not None
    assert base_hour.cloud_cover == 40.0
    assert base_hour.cloud_low is None
    assert base_hour.cloud_mid is None
    assert base_hour.cloud_high is None


def test_assemble_base_wind_without_cloud_keeps_the_base_group_and_its_issue_time() -> None:
    # The round-2 Critical case: base returns wind rows but no cloud. The base
    # group is still present (rows exist), so its issue time survives — exactly as
    # today's base_issued_at was retained on any base reading (design D1, D2).
    base = SourceForecast(
        issued_at=_hour(18),
        readings={_hour(21): SourceReading(cloud_cover=None, wind_gust=15.0)},
    )
    conditions = assemble_snapshot(base, SourceForecast())
    assert conditions.base is not None
    assert conditions.base.meta.issued_at == _hour(18)
    base_hour = conditions.base.at(_hour(21))
    assert base_hour is not None
    assert base_hour.cloud_cover is None and base_hour.wind_gust == 15.0


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
    conditions = composite.get(make_pier())
    assert conditions.secondary is None  # the failed source contributes no group
    assert conditions.base is not None
    base_hour = conditions.base.at(_hour(21))
    assert base_hour is not None and base_hour.cloud_cover == 30.0


def test_base_failure_still_yields_the_secondary_group() -> None:
    secondary = _StubProvider(
        SourceForecast(
            issued_at=_hour(18),
            readings={_hour(21): SourceReading(seeing=0.9, transparency=0.8)},
        )
    )
    composite = CompositeProvider(base=_StubProvider(fail=True), secondary=secondary)
    conditions = composite.get(make_pier())
    assert conditions.base is None  # the failed base source contributes no group
    assert conditions.secondary is not None
    secondary_hour = conditions.secondary.at(_hour(21))
    assert secondary_hour is not None and secondary_hour.seeing == 0.9


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
    conditions = assemble_snapshot(base, SourceForecast())
    assert conditions.base is not None
    assert conditions.base.at(_hour(21)) is not None
    assert conditions.base.at(_hour(23)) is None  # beyond the forecast horizon


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
    conditions = composite.get(make_pier())
    assert conditions.secondary is None
    assert conditions.base is not None
    base_hour = conditions.base.at(_hour(21))
    assert base_hour is not None and base_hour.cloud_cover == 15.0
