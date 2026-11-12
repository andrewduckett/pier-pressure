"""Once the night has started, targets are ranked on the rest of it (#110).

These rank the real vendored catalog at instants inside the London golden night
(dark window 20:30:49 to 03:25:52 UTC). The west pier sees only a south-west to
west sector, so its targets set during the night, which the "has set" and "under
the minimum left" cases need.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

import pierpressure.core.ranking as ranking
from pierpressure.core.catalog import load_catalog
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Target
from pierpressure.core.ranking import rank_targets
from pierpressure.core.scoring import MIN_USABLE_WINDOW
from pierpressure.core.sky import dark_window, moon_info

from .offline_guard import no_network

_BEFORE_DUSK = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)
# Inside the night and off the 5-minute grid, which starts at 20:30:49.
_MID_SESSION = datetime(2026, 9, 8, 23, 0, 0, 400_000, tzinfo=UTC)
_AFTER_MIDNIGHT = datetime(2026, 9, 9, 1, 0, tzinfo=UTC)


def _london(**overrides: object) -> PierConfig:
    base: dict[str, object] = {"id": "london", "latitude": 51.5, "longitude": -0.12}
    return PierConfig(**{**base, "elevation_m": 30.0, **overrides})  # type: ignore[arg-type]


def _west() -> PierConfig:
    return _london(
        id="west", horizon={"points": [[0, 85], [200, 85], [210, 15], [280, 15], [290, 85]]}
    )


def _rank(pier: PierConfig, instant: datetime) -> list[Target]:
    with no_network():
        window = dark_window(pier, _BEFORE_DUSK)
        moon = moon_info(pier, window, _BEFORE_DUSK)
        return rank_targets(pier, instant, window, moon)


def _dark_end() -> datetime:
    with no_network():
        end = dark_window(_london(), _BEFORE_DUSK)[1]
    assert end is not None
    return end


def test_a_target_already_up_starts_its_remaining_window_now() -> None:
    generated_at = _MID_SESSION.replace(microsecond=0)
    up = [t for t in _rank(_london(), _MID_SESSION) if t.window.start < generated_at]
    assert up
    for target in up:
        assert target.remaining_window.start == generated_at
        assert target.remaining_window.end == target.window.end


def test_a_target_that_has_set_is_absent() -> None:
    before = {t.id: t for t in _rank(_west(), _BEFORE_DUSK)}
    # NGC6895 is a pre-dusk pick whose only stretch ends at 00:13.
    assert before["NGC6895"].window.end < _AFTER_MIDNIGHT
    assert "NGC6895" not in {t.id for t in _rank(_west(), _AFTER_MIDNIGHT)}


def test_a_target_with_under_the_minimum_left_is_absent() -> None:
    before = {t.id: t for t in _rank(_west(), _BEFORE_DUSK)}
    # NGC7058 is a pre-dusk pick still up at 01:00, but only until 01:10.
    window = before["NGC7058"].window
    assert window.start < _AFTER_MIDNIGHT < window.end < _AFTER_MIDNIGHT + MIN_USABLE_WINDOW
    assert "NGC7058" not in {t.id for t in _rank(_west(), _AFTER_MIDNIGHT)}


@pytest.mark.parametrize("pier", [_london(), _west()], ids=["london", "west"])
@pytest.mark.parametrize("instant", [_MID_SESSION, _AFTER_MIDNIGHT], ids=["23h", "01h"])
def test_every_remaining_window_lies_in_the_scored_window_and_spans_the_minimum(
    pier: PierConfig, instant: datetime
) -> None:
    generated_at = instant.replace(microsecond=0)
    targets = _rank(pier, instant)
    assert targets
    for target in targets:
        remaining = target.remaining_window
        assert generated_at <= remaining.start < remaining.end <= _dark_end()
        assert remaining.end - remaining.start >= MIN_USABLE_WINDOW


def test_the_last_half_hour_of_the_night_has_no_targets() -> None:
    assert _rank(_london(), _dark_end() - timedelta(minutes=30)) == []


def test_at_the_end_of_the_night_there_are_no_targets() -> None:
    assert _rank(_london(), _dark_end()) == []


def test_a_target_with_a_second_stretch_ahead_is_ranked_on_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A narrow wall in the south-east hides M31 from about 00:50 to 01:18 as its
    # azimuth climbs. The catalog is cut to M31 and a few rivals so the list is
    # about this one target, not about the night's competition.
    chosen = {"NGC0224", "NGC0433", "NGC0657", "NGC7429"}
    monkeypatch.setattr(
        ranking, "load_catalog", lambda: [o for o in load_catalog() if o.id in chosen]
    )
    pier = _london(
        id="wall", horizon={"points": [[0, 0], [139, 0], [140, 89], [165, 89], [166, 0]]}
    )
    ranking._scan_cache.clear()
    try:
        before = {t.id: t for t in _rank(pier, _BEFORE_DUSK)}
        between = {t.id: t for t in _rank(pier, datetime(2026, 9, 9, 1, 5, tzinfo=UTC))}
    finally:
        ranking._scan_cache.clear()
    first = before["NGC0224"].window
    m31 = between["NGC0224"]
    assert m31.window == first
    assert first.end < datetime(2026, 9, 9, 1, 5, tzinfo=UTC) < m31.remaining_window.start
    assert m31.remaining_window.end == _dark_end()
    # The first stretch is the longer, so it stays the whole-night window.
    assert first.end - first.start > m31.remaining_window.end - m31.remaining_window.start


def test_a_later_recompute_matches_a_fresh_ranking(monkeypatch: pytest.MonkeyPatch) -> None:
    pier = _london()
    at_21 = datetime(2026, 9, 8, 21, 0, tzinfo=UTC)
    at_23 = datetime(2026, 9, 8, 23, 0, tzinfo=UTC)
    ranking._scan_cache.clear()
    fresh = [t.model_dump_json() for t in _rank(pier, at_23)]

    ranking._scan_cache.clear()
    scans = {"count": 0}
    real_scan = ranking._scan_night

    def counting_scan(*args: object, **kwargs: object) -> object:
        scans["count"] += 1
        return real_scan(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(ranking, "_scan_night", counting_scan)
    _rank(pier, at_21)
    later = [t.model_dump_json() for t in _rank(pier, at_23)]
    assert scans["count"] == 1
    assert later == fresh
