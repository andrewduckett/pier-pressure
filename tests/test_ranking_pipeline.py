"""Task 4.4-4.7: the ranking pipeline — gates, bounds, order, determinism, cache.

These exercise the whole engine against the real vendored catalog at the golden
suite's London night, so the gates, the top-N bound, the stable order, the
determinism guarantee, and the per-night cache are all checked end to end.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

import pierpressure.core.ranking as ranking
from pierpressure.core.catalog import load_catalog
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Moon, MoonPhase
from pierpressure.core.ranking import (
    MIN_WINDOW,
    TOP_N,
    altitude_subscore,
    combined_score,
    geometry_for,
    moon_subscore,
    rank_targets,
    transit_subscore,
    window_subscore,
)
from pierpressure.core.sky import dark_window, moon_info

from .offline_guard import no_network

_INSTANT = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)


def _london(**overrides: object) -> PierConfig:
    return PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0, **overrides)  # type: ignore[arg-type]


# A widefield rig (short focal length, so a large field frames big objects) and a
# long rig (narrow field, so only small objects frame well) — they frame the
# candidates differently, which is what a rig-change test needs.
_WIDEFIELD_RIG = {"focal_length_mm": 250.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}
_LONG_RIG = {"focal_length_mm": 2000.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}


def _rank(pier: PierConfig) -> list:
    with no_network():
        window = dark_window(pier, _INSTANT)
        moon = moon_info(pier, window, _INSTANT)
        return rank_targets(pier, _INSTANT, window, moon)


# --------------------------------------------------------------------------- #
# Task 4.5 — bound, order, and "every emitted target is refined and gated"
# --------------------------------------------------------------------------- #


def test_list_is_bounded_to_top_n() -> None:
    targets = _rank(_london())
    assert 0 < len(targets) <= TOP_N


def test_list_is_ordered_by_score_then_id() -> None:
    targets = _rank(_london())
    keys = [(-t.score, t.id) for t in targets]
    assert keys == sorted(keys)


def test_every_emitted_target_is_whole_second_and_scored() -> None:
    for target in _rank(_london()):
        assert target.window.start.microsecond == 0
        assert target.window.end.microsecond == 0
        assert target.transit_time.microsecond == 0
        assert 0 <= target.score <= 100


def test_top_target_is_genuinely_well_placed() -> None:
    # The pipeline surfaces objectively well-placed targets: the top one reaches a
    # high altitude, stays up for most of the night, and transits inside its
    # window. (Which object wins now also depends on brightness and framing, but a
    # rig-less pier still ranks on placement and brightness, so the test checks
    # placement, not identity.)
    targets = _rank(_london())
    top = targets[0]
    assert top.max_altitude >= 60.0
    assert (top.window.end - top.window.start) >= MIN_WINDOW
    assert top.window.start <= top.transit_time <= top.window.end


def test_m31_geometry_alone_scores_well() -> None:
    # M31 is a well-placed autumn target: on the four geometry factors alone it
    # scores highly (>= 90) on this night, even though it does not make the top ten
    # because it transits after the window midpoint. (In the full pipeline M31 is
    # also marked down by the equipment terms — its low surface brightness and, for
    # a typical rig, its large size — so this checks geometry, not the full score.)
    pier = _london()
    m31 = next(o for o in load_catalog() if o.id == "NGC0224")
    with no_network():
        window = dark_window(pier, _INSTANT)
        moon = moon_info(pier, window, _INSTANT)
        geo = geometry_for(pier, m31, window, _INSTANT)
    assert geo is not None
    dark = window[1] - window[0]  # type: ignore[operator]
    score = combined_score(
        altitude_subscore(geo.max_altitude),
        window_subscore(geo.window_end - geo.window_start, dark),
        moon_subscore(geo.moon_separation, moon.illumination, geo.moon_up_at_peak),
        transit_subscore(geo.transit_time, geo.window_start, geo.window_end),
    )
    assert score >= 90


def test_far_southern_object_that_never_rises_is_absent() -> None:
    # 47 Tucanae (NGC0104, dec ~-72) never clears the horizon from London, so it
    # can never be a candidate — the gates discriminate unobservable objects out.
    ids = {t.id for t in _rank(_london())}
    assert "NGC0104" not in ids


# --------------------------------------------------------------------------- #
# Equipment: rig-configured and rig-less piers both rank; a rig changes ranking
# --------------------------------------------------------------------------- #


def test_rig_configured_and_rig_less_piers_both_rank_without_error() -> None:
    # A pier with a rig and a pier without one both produce a bounded, scored list.
    with_rig = _rank(_london(rig=_WIDEFIELD_RIG))
    without_rig = _rank(_london())
    for targets in (with_rig, without_rig):
        assert 0 < len(targets) <= TOP_N
        assert all(0 <= t.score <= 100 for t in targets)


def test_targets_carry_the_raw_catalog_facts() -> None:
    # Every emitted target carries size/magnitude/surface_brightness (null when the
    # catalog records none); each present value came straight from the catalog.
    catalog = {o.id: o for o in load_catalog()}
    for target in _rank(_london(rig=_WIDEFIELD_RIG)):
        source = catalog[target.id]
        assert target.size_arcmin == (
            None if source.size_arcmin is None else round(source.size_arcmin, 2)
        )
        assert target.magnitude == (
            None if source.magnitude is None else round(source.magnitude, 2)
        )


def test_a_rig_change_changes_the_ranking() -> None:
    # The target-ranking "A rig change changes the ranking" scenario: the same pier
    # and instant with two differently-framing rigs must differ in scores or order.
    ranking._rank_cache.clear()
    widefield = _rank(_london(rig=_WIDEFIELD_RIG))
    ranking._rank_cache.clear()
    long = _rank(_london(rig=_LONG_RIG))
    widefield_key = [(t.id, t.score) for t in widefield]
    long_key = [(t.id, t.score) for t in long]
    assert widefield_key != long_key


def test_the_rig_joins_the_cache_key() -> None:
    # Two rigs must not collide in the per-night cache: the second rig recomputes
    # rather than serving the first rig's ranking.
    ranking._rank_cache.clear()
    with no_network():
        window = dark_window(_london(), _INSTANT)
        moon = moon_info(_london(), window, _INSTANT)
        first = rank_targets(_london(rig=_WIDEFIELD_RIG), _INSTANT, window, moon)
        second = rank_targets(_london(rig=_LONG_RIG), _INSTANT, window, moon)
    assert [(t.id, t.score) for t in first] != [(t.id, t.score) for t in second]


# --------------------------------------------------------------------------- #
# Task 4.4 — gates at the pipeline level
# --------------------------------------------------------------------------- #


def test_every_emitted_window_meets_the_minimum() -> None:
    for target in _rank(_london()):
        assert (target.window.end - target.window.start) >= MIN_WINDOW


def test_object_that_never_clears_the_mask_is_absent() -> None:
    # A near-zenith 89-degree mask: M31 peaks below 80 degrees, so it never clears
    # the mask and must be absent from the list.
    blocked = _london(horizon={"min_altitude": 89.0})
    ids = {t.id for t in _rank(blocked)}
    assert "NGC0224" not in ids


# --------------------------------------------------------------------------- #
# Task 4.6 — determinism and the empty-night case
# --------------------------------------------------------------------------- #


def test_ranking_is_byte_identical_for_same_pier_and_instant() -> None:
    first = _rank(_london())
    ranking._rank_cache.clear()  # force a real second computation, not a cache hit
    second = _rank(_london())
    assert [t.model_dump_json() for t in first] == [t.model_dump_json() for t in second]


def test_no_dark_window_yields_empty_list() -> None:
    pier = _london()
    with no_network():
        moon = moon_info(pier, (None, None), _INSTANT)
        assert rank_targets(pier, _INSTANT, (None, None), moon) == []


def test_polar_day_pier_yields_empty_list() -> None:
    # A high-latitude pier at midsummer has no astronomical night at all.
    svalbard = PierConfig(id="svalbard", latitude=78.2, longitude=15.6, elevation_m=10.0)
    midsummer = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
    with no_network():
        window = dark_window(svalbard, midsummer)
        moon = moon_info(svalbard, window, midsummer)
        assert window == (None, None)
        assert rank_targets(svalbard, midsummer, window, moon) == []


# --------------------------------------------------------------------------- #
# Task 4.7 — the per-night cache
# --------------------------------------------------------------------------- #


def test_recomputes_within_one_night_reuse_the_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    pier = _london()
    ranking._rank_cache.clear()

    # Count real pipeline scans by wrapping _rank; rank_targets resolves the module
    # global at call time, so the wrapper is seen.
    calls = {"scans": 0}
    real_rank = ranking._rank

    def counting_rank(*args: object, **kwargs: object) -> list:
        calls["scans"] += 1
        return real_rank(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(ranking, "_rank", counting_rank)

    with no_network():
        window = dark_window(pier, _INSTANT)
        moon = moon_info(pier, window, _INSTANT)
        first = rank_targets(pier, _INSTANT, window, moon)
        assert calls["scans"] == 1  # first call scanned
        # A second call denser near dusk selects the same night -> same key.
        later = datetime(2026, 9, 8, 19, 30, tzinfo=UTC)
        window2 = dark_window(pier, later)
        second = rank_targets(pier, later, window2, moon)
        assert calls["scans"] == 1  # second call reused the cache, no rescan

    assert window2 == window  # same night selected
    assert [t.model_dump_json() for t in first] == [t.model_dump_json() for t in second]


def test_cache_is_bounded_so_a_long_running_container_does_not_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A persistent container recomputes night after night; the cache must not grow
    # one entry per night forever. With the scan stubbed out, feed many distinct
    # nights and assert the cache stays within its bound.
    ranking._rank_cache.clear()
    monkeypatch.setattr(ranking, "_rank", lambda pier, window, moon: [])
    pier = _london()
    moon = Moon(illumination=0.1, phase=MoonPhase.NEW)
    base = datetime(2026, 1, 1, 20, 0, tzinfo=UTC)
    for day in range(ranking._CACHE_MAXSIZE + 5):
        start = base + timedelta(days=day)
        window = (start, start + timedelta(hours=6))
        rank_targets(pier, start, window, moon)
    assert len(ranking._rank_cache) <= ranking._CACHE_MAXSIZE
