"""Tasks 1.1-1.2: golden-output regression suite (design D4).

Recorded raw Open-Meteo + 7Timer! payloads are driven through the *provider layer*
(``assemble_snapshot``) into ``produce_verdict`` at a pinned instant, and the whole
verdict document is asserted byte-identical to a committed golden. Routing through
the provider keeps this test agnostic to the core's conditions type, so the same
suite locks behaviour across the flat-grid → per-source-group refactor.

The suite deliberately covers the degradation and partial-coverage paths, not only
the happy path where both sources are present (design D4): absence and misalignment
are exactly where a per-group model is most likely to drift.

Regenerate the goldens (only when a deliberate, reviewed behaviour change lands)
with ``PP_WRITE_GOLDENS=1 uv run pytest tests/test_golden_verdict.py``.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pierpressure.conditions.open_meteo import parse_open_meteo
from pierpressure.conditions.provider import (
    CachingProvider,
    SourceForecast,
    SourceReading,
    assemble_snapshot,
)
from pierpressure.conditions.seven_timer import parse_seven_timer
from pierpressure.core.clock import FixedClock
from pierpressure.core.config import PierConfig
from pierpressure.core.producer import produce_verdict

from .conftest import make_pier
from .offline_guard import no_network

_FIXTURES = Path(__file__).parent / "fixtures" / "golden"
_EXPECTED = _FIXTURES / "expected"

# A daytime instant a couple of hours before dusk at the London pier, so the dark
# window (20:30 → 03:25 UTC) and the moon are real and the freshness/lead-time
# factors are exercised rather than pinned at their extremes.
_INSTANT = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)
_FRESH_ISSUED = datetime(2026, 9, 8, 17, 0, tzinfo=UTC)  # 1h old → fresh
_STALE_ISSUED = datetime(2026, 9, 8, 7, 0, tzinfo=UTC)  # 11h old → near the stale floor

_WINDOW_SLOTS = [datetime(2026, 9, 8, h, 0, tzinfo=UTC) for h in (20, 21, 22, 23)] + [
    datetime(2026, 9, 9, h, 0, tzinfo=UTC) for h in (0, 1, 2, 3)
]


def _load_raw(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _base_full(issued_at: datetime = _FRESH_ISSUED) -> SourceForecast:
    """The full recorded Open-Meteo forecast (cloud + wind across the window)."""
    return parse_open_meteo(_load_raw("open_meteo_full.json"), issued_at=issued_at)


def _secondary_full() -> SourceForecast:
    """The full recorded 7Timer! forecast (seeing + transparency, resampled hourly)."""
    return parse_seven_timer(_load_raw("seven_timer_full.json"))


class _StubProvider:
    """A one-shot source provider, optionally failing, for the cache path."""

    def __init__(self, forecast: SourceForecast, *, fail: bool = False) -> None:
        self._forecast = forecast
        self.fail = fail

    def fetch(self, _pier: PierConfig) -> SourceForecast:
        if self.fail:
            raise RuntimeError("source down")
        return self._forecast


def _wind_without_cloud() -> SourceForecast:
    """The base source returned wind rows but no cloud (round-2 Critical case)."""
    full = _base_full()
    readings = {
        time: SourceReading(cloud_cover=None, wind_gust=reading.wind_gust)
        for time, reading in full.readings.items()
    }
    return SourceForecast(issued_at=full.issued_at, readings=readings)


def _subset(forecast: SourceForecast, times: list[datetime]) -> SourceForecast:
    readings = {t: forecast.readings[t] for t in times if t in forecast.readings}
    return SourceForecast(issued_at=forecast.issued_at, readings=readings)


def _over_stale_base() -> SourceForecast:
    """A base forecast served from cache while 11h old — near the staleness floor.

    Primes the cache with a stale-issued forecast, then a failed refresh reuses it
    (still within ``MAX_STALENESS``), so the served forecast keeps its old issue
    time and freshness decays toward its floor. This exercises the cache-reuse path
    into the freshness factor.
    """
    stub = _StubProvider(_base_full(issued_at=_STALE_ISSUED))
    caching = CachingProvider(inner=stub, now=lambda: _STALE_ISSUED + timedelta(minutes=1))
    primed = caching.fetch(make_pier())  # cache the stale-issued forecast
    stub.fail = True
    caching.now = lambda: _STALE_ISSUED + timedelta(hours=11)  # within 12h staleness
    reused = caching.fetch(make_pier())
    assert reused.readings and reused is primed  # served from cache, not dropped
    return reused


# Each case: name -> (pier, base forecast, secondary forecast). The verdict for
# each is captured once from the current code and committed as a golden.
_CASES: dict[str, Callable[[], tuple[PierConfig, SourceForecast, SourceForecast]]] = {
    "both_present": lambda: (make_pier(), _base_full(), _secondary_full()),
    "secondary_absent": lambda: (make_pier(), _base_full(), SourceForecast()),
    "base_absent": lambda: (make_pier(), SourceForecast(), _secondary_full()),
    "base_wind_without_cloud": lambda: (
        # A wind limit the forecast breaches, so the base source's own freshness
        # drives the NO-GO confidence even though cloud is entirely absent.
        make_pier_with_gust(15.0),
        _wind_without_cloud(),
        _secondary_full(),
    ),
    "gappy_coverage": lambda: (
        make_pier(),
        _subset(_base_full(), _WINDOW_SLOTS[:3]),  # cloud/wind only early
        _subset(_secondary_full(), _WINDOW_SLOTS[4:]),  # seeing only late
    ),
    "empty": lambda: (make_pier(), SourceForecast(), SourceForecast()),
    "over_stale_cache": lambda: (make_pier(), _over_stale_base(), _secondary_full()),
}


def make_pier_with_gust(max_gust: float) -> PierConfig:
    return PierConfig(
        id="backyard", latitude=51.5, longitude=-0.12, elevation_m=30.0, max_gust=max_gust
    )


def _verdict_json(pier: PierConfig, base: SourceForecast, secondary: SourceForecast) -> str:
    conditions = assemble_snapshot(base, secondary)
    with no_network():
        return produce_verdict(pier, FixedClock(_INSTANT), conditions).to_json()


@pytest.mark.parametrize("case", sorted(_CASES))
def test_verdict_matches_committed_golden(case: str) -> None:
    pier, base, secondary = _CASES[case]()
    actual = _verdict_json(pier, base, secondary)
    golden_path = _EXPECTED / f"{case}.json"

    if os.environ.get("PP_WRITE_GOLDENS"):
        _EXPECTED.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(actual + "\n", encoding="utf-8")

    expected = golden_path.read_text(encoding="utf-8").rstrip("\n")
    assert actual == expected
