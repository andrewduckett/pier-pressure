"""Task 4.4-4.7: the ranking pipeline — gates, bounds, order, determinism, cache.

These exercise the whole engine against the real vendored catalog at the golden
suite's London night, so the gates, the top-N bound, the stable order, the
determinism guarantee, and the per-night cache are all checked end to end.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

import pierpressure.core.ranking as ranking
from pierpressure.core.catalog import load_catalog
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Moon, MoonPhase
from pierpressure.core.ranking import (
    TOP_N,
    altitude_subscore,
    combined_score,
    geometry_for,
    moon_subscore,
    rank_nights,
    rank_targets,
    transit_subscore,
    window_subscore,
)
from pierpressure.core.scoring import MIN_USABLE_WINDOW
from pierpressure.core.sky import dark_window, later_nights, moon_info

from .offline_guard import no_network

_INSTANT = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)


def _london(**overrides: object) -> PierConfig:
    return PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0, **overrides)  # type: ignore[arg-type]


# A widefield rig (short focal length, so a large field frames big objects) and a
# long rig (narrow field, so only small objects frame well) — they frame the
# candidates differently, which is what an equipment-change test needs.
_WIDEFIELD_EQUIPMENT = {"focal_length_mm": 250.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}
_LONG_EQUIPMENT = {"focal_length_mm": 2000.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}


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
    # pier without equipment still ranks on placement and brightness, so the test checks
    # placement, not identity.)
    targets = _rank(_london())
    top = targets[0]
    assert top.max_altitude >= 60.0
    assert (top.window.end - top.window.start) >= MIN_USABLE_WINDOW
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
# Equipment: piers with and without equipment both rank; changing it changes ranking
# --------------------------------------------------------------------------- #


def test_piers_with_and_without_equipment_both_rank_without_error() -> None:
    # A pier with equipment and a pier without it both produce a bounded, scored list.
    with_equipment = _rank(_london(equipment=_WIDEFIELD_EQUIPMENT))
    without_equipment = _rank(_london())
    for targets in (with_equipment, without_equipment):
        assert 0 < len(targets) <= TOP_N
        assert all(0 <= t.score <= 100 for t in targets)


def test_targets_carry_the_raw_catalog_facts() -> None:
    # Every emitted target carries size/magnitude/surface_brightness (null when the
    # catalog records none); each present value came straight from the catalog.
    catalog = {o.id: o for o in load_catalog()}
    for target in _rank(_london(equipment=_WIDEFIELD_EQUIPMENT)):
        source = catalog[target.id]
        assert target.size_arcmin == (
            None if source.size_arcmin is None else round(source.size_arcmin, 2)
        )
        assert target.magnitude == (
            None if source.magnitude is None else round(source.magnitude, 2)
        )


def test_an_equipment_change_changes_the_ranking() -> None:
    # The target-ranking "An equipment change changes the ranking" scenario: the same pier
    # and instant with two differently-framing rigs must differ in scores or order.
    ranking._scan_cache.clear()
    widefield = _rank(_london(equipment=_WIDEFIELD_EQUIPMENT))
    ranking._scan_cache.clear()
    long = _rank(_london(equipment=_LONG_EQUIPMENT))
    widefield_key = [(t.id, t.score) for t in widefield]
    long_key = [(t.id, t.score) for t in long]
    assert widefield_key != long_key


# --------------------------------------------------------------------------- #
# Task 4.4 — gates at the pipeline level
# --------------------------------------------------------------------------- #


def test_every_emitted_window_meets_the_minimum() -> None:
    for target in _rank(_london()):
        assert (target.window.end - target.window.start) >= MIN_USABLE_WINDOW


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
    ranking._scan_cache.clear()  # force a real second computation, not a cache hit
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


def _count_scans(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    # rank_targets resolves the module global at call time, so the wrapper is seen.
    calls = {"scans": 0}
    real_scan = ranking._scan_night

    def counting_scan(*args: object, **kwargs: object) -> object:
        calls["scans"] += 1
        return real_scan(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(ranking, "_scan_night", counting_scan)
    return calls


def test_before_dusk_the_remaining_window_is_the_window() -> None:
    targets = _rank(_london())
    assert targets
    for target in targets:
        assert target.remaining_window == target.window


def test_recomputes_within_one_night_reuse_the_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    pier = _london()
    ranking._scan_cache.clear()
    calls = _count_scans(monkeypatch)

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


def test_two_rigs_on_one_pier_share_a_scan_but_score_differently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ranking._scan_cache.clear()
    calls = _count_scans(monkeypatch)
    with no_network():
        window = dark_window(_london(), _INSTANT)
        moon = moon_info(_london(), window, _INSTANT)
        widefield = rank_targets(_london(equipment=_WIDEFIELD_EQUIPMENT), _INSTANT, window, moon)
        long = rank_targets(_london(equipment=_LONG_EQUIPMENT), _INSTANT, window, moon)
    assert calls["scans"] == 1
    assert [(t.id, t.score) for t in widefield] != [(t.id, t.score) for t in long]


def test_a_night_shorter_than_the_minimum_is_not_scanned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pier = PierConfig(id="may", latitude=52.0, longitude=0.0, elevation_m=0.0)
    instant = datetime(2026, 5, 19, 15, 0, tzinfo=UTC)
    calls = _count_scans(monkeypatch)
    with no_network():
        window = dark_window(pier, instant)
        targets = rank_targets(pier, instant, window, moon_info(pier, window, instant))
    start, end = window
    assert start is not None and end is not None
    assert end - start < MIN_USABLE_WINDOW
    assert (targets, calls["scans"]) == ([], 0)


def test_a_night_of_exactly_the_minimum_is_scanned(monkeypatch: pytest.MonkeyPatch) -> None:
    ranking._scan_cache.clear()
    calls = _count_scans(monkeypatch)
    start = datetime(2026, 1, 1, 20, 0, tzinfo=UTC)
    moon = Moon(illumination=0.1, phase=MoonPhase.NEW)
    with no_network():
        rank_targets(_london(), start, (start, start + MIN_USABLE_WINDOW), moon)
    assert calls["scans"] == 1


def _nights(pier: PierConfig, instant: datetime) -> list[tuple[Any, Moon]]:
    """Tonight and three later nights, each with the moon the producer gives it."""
    window = dark_window(pier, instant)
    nights = [(window, moon_info(pier, window, instant))]
    for night in later_nights(pier, instant, window, instant + timedelta(days=7)):
        day_start, day_end = night.solar_day
        midnight = (day_start + (day_end - day_start) / 2).replace(microsecond=0)
        nights.append((night.dark_window, moon_info(pier, night.dark_window, midnight)))
    return nights


def _dumped(lists: list[list[Any]]) -> list[list[str]]:
    return [[target.model_dump_json() for target in targets] for targets in lists]


_THREE_PIERS = (
    PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0),
    PierConfig(id="lisbon", latitude=38.7, longitude=-9.14, elevation_m=50.0),
    PierConfig(id="oslo", latitude=59.9, longitude=10.75, elevation_m=20.0),
)


def test_rank_targets_ranks_one_night_as_rank_nights_does() -> None:
    pier = _london()
    with no_network():
        window = dark_window(pier, _INSTANT)
        moon = moon_info(pier, window, _INSTANT)
        alone = rank_targets(pier, _INSTANT, window, moon)
        ranking._scan_cache.clear()
        listed = rank_nights(pier, _INSTANT, [(window, moon)])
    assert _dumped([alone]) == _dumped(listed)


@pytest.mark.usefixtures("sample_catalog")
def test_rank_nights_gives_one_list_per_night_in_order() -> None:
    pier = _london()
    with no_network():
        nights = _nights(pier, _INSTANT)
        lists = rank_nights(pier, _INSTANT, nights)
        each = [rank_targets(pier, _INSTANT, window, moon) for window, moon in nights]
    assert len(lists) == 4
    assert _dumped(lists) == _dumped(each)


@pytest.mark.usefixtures("sample_catalog")
def test_a_recompute_reuses_every_scan_of_three_piers(monkeypatch: pytest.MonkeyPatch) -> None:
    with no_network():
        nights = {pier.id: _nights(pier, _INSTANT) for pier in _THREE_PIERS}
        fresh = rank_nights(_THREE_PIERS[0], _INSTANT, nights["london"])
        ranking._scan_cache.clear()
        for pier in _THREE_PIERS:
            rank_nights(pier, _INSTANT, nights[pier.id])
        calls = _count_scans(monkeypatch)
        again = rank_nights(_THREE_PIERS[0], _INSTANT, nights["london"])
    assert calls["scans"] == 0
    assert _dumped(again) == _dumped(fresh)


def test_the_cache_keeps_only_the_nights_the_last_call_ranked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A persistent container recomputes night after night; the cache must not grow
    # one entry per night forever.
    ranking._scan_cache.clear()
    real_scan = ranking._scan_night
    monkeypatch.setattr(
        ranking, "_scan_night", lambda pier, window: real_scan(pier, window, objects=())
    )
    pier = _london()
    moon = Moon(illumination=0.1, phase=MoonPhase.NEW)
    base = datetime(2026, 1, 1, 20, 0, tzinfo=UTC)
    for day in range(10):
        start = base + timedelta(days=day)
        nights: list[tuple[Any, Moon]] = [
            ((start + timedelta(days=n), start + timedelta(days=n, hours=6)), moon)
            for n in range(4)
        ]
        rank_nights(pier, start, nights)
        kept = {(key[-2], key[-1]) for key in ranking._scan_cache[pier.id]}
        assert kept == {window for window, _ in nights}
    assert not hasattr(ranking, "_CACHE_MAXSIZE")


def test_one_piers_ranking_leaves_another_piers_scans(monkeypatch: pytest.MonkeyPatch) -> None:
    ranking._scan_cache.clear()
    real_scan = ranking._scan_night
    monkeypatch.setattr(
        ranking, "_scan_night", lambda pier, window: real_scan(pier, window, objects=())
    )
    moon = Moon(illumination=0.1, phase=MoonPhase.NEW)
    start = datetime(2026, 1, 1, 20, 0, tzinfo=UTC)
    rank_nights(_THREE_PIERS[0], start, [((start, start + timedelta(hours=6)), moon)])
    rank_nights(_THREE_PIERS[1], start, [((start, start + timedelta(hours=7)), moon)])
    assert len(ranking._scan_cache["london"]) == 1


def _count_ranks(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    calls = {"ranks": 0}
    real_rank = ranking._rank

    def counting_rank(*args: object, **kwargs: object) -> object:
        calls["ranks"] += 1
        return real_rank(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(ranking, "_rank", counting_rank)
    return calls


@pytest.fixture
def sample_catalog(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # A slice of the catalog keeps the rankings quick; the reuse does not depend on it.
    # The cache is cleared on both sides, so no sliced scan reaches another test.
    sample = load_catalog()[::40]
    monkeypatch.setattr(ranking, "load_catalog", lambda: sample)
    ranking._scan_cache.clear()
    yield
    ranking._scan_cache.clear()


@pytest.mark.usefixtures("sample_catalog")
def test_a_recompute_ranks_tonight_only(monkeypatch: pytest.MonkeyPatch) -> None:
    pier = _london()
    with no_network():
        nights = _nights(pier, _INSTANT)
        first = rank_nights(pier, _INSTANT, nights)
        calls = _count_ranks(monkeypatch)
        again = rank_nights(pier, _INSTANT, nights)
    assert calls["ranks"] == 1
    assert _dumped(again) == _dumped(first)


@pytest.mark.usefixtures("sample_catalog")
def test_a_later_night_on_another_moon_is_ranked_again(monkeypatch: pytest.MonkeyPatch) -> None:
    pier = _london()
    with no_network():
        nights = _nights(pier, _INSTANT)
        rank_nights(pier, _INSTANT, nights)
        window, moon = nights[1]
        brighter = moon.model_copy(update={"illumination": 0.9})
        calls = _count_ranks(monkeypatch)
        rank_nights(pier, _INSTANT, [nights[0], (window, brighter), *nights[2:]])
    assert calls["ranks"] == 2


@pytest.mark.usefixtures("sample_catalog")
def test_a_later_night_with_other_equipment_is_ranked_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with no_network():
        nights = _nights(_london(), _INSTANT)
        rank_nights(_london(), _INSTANT, nights)
        calls = _count_ranks(monkeypatch)
        rank_nights(_london(equipment=_LONG_EQUIPMENT), _INSTANT, nights)
    assert calls["ranks"] == 4


@pytest.mark.usefixtures("sample_catalog")
def test_a_recompute_in_the_same_night_reuses_the_later_nights_lists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pier = _london()
    an_hour_on = _INSTANT + timedelta(hours=1)
    with no_network():
        first = rank_nights(pier, _INSTANT, _nights(pier, _INSTANT))
        nights = _nights(pier, an_hour_on)
        calls = _count_ranks(monkeypatch)
        again = rank_nights(pier, an_hour_on, nights)
    assert calls["ranks"] == 1
    assert _dumped(again[1:]) == _dumped(first[1:])


@pytest.mark.usefixtures("sample_catalog")
def test_a_later_night_that_has_started_is_ranked_on_its_remaining_window() -> None:
    pier = _london()
    with no_network():
        nights = _nights(pier, _INSTANT)
        rank_nights(pier, _INSTANT, nights[:2])
        window, moon = nights[1]
        assert window[0] is not None
        inside = window[0] + timedelta(hours=3)
        listed = rank_nights(pier, inside, nights[:2])[1]
        alone = rank_targets(pier, inside, window, moon)
    assert alone
    assert _dumped([listed]) == _dumped([alone])
