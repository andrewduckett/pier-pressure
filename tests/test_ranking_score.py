"""Task 4.3-4.4: the four sub-scores, the weighted score, and the gates (design D4).

These are pure functions over numbers and datetimes — no astronomy — so the
scoring math is pinned exactly and independently of Skyfield.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from pierpressure.core.ranking import (
    MIN_WINDOW,
    WEIGHT_ALTITUDE,
    WEIGHT_BRIGHTNESS,
    WEIGHT_FOV,
    WEIGHT_MOON,
    WEIGHT_TRANSIT,
    WEIGHT_WINDOW,
    altitude_subscore,
    combined_score,
    meets_minimum,
    moon_subscore,
    observable_window,
    transit_subscore,
    window_subscore,
)

_GEOMETRY_WEIGHT = WEIGHT_ALTITUDE + WEIGHT_WINDOW + WEIGHT_MOON + WEIGHT_TRANSIT

_START = datetime(2026, 9, 8, 21, 0, tzinfo=UTC)
_END = datetime(2026, 9, 9, 1, 0, tzinfo=UTC)  # 4h window


# --------------------------------------------------------------------------- #
# Altitude sub-score = sin(altitude)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("alt", "expected"),
    [(90.0, 1.0), (0.0, 0.0), (30.0, 0.5), (60.0, math.sin(math.radians(60.0)))],
)
def test_altitude_subscore(alt: float, expected: float) -> None:
    assert altitude_subscore(alt) == pytest.approx(expected)


def test_altitude_subscore_is_clamped_to_unit_interval() -> None:
    assert altitude_subscore(-5.0) == 0.0
    assert altitude_subscore(95.0) == 1.0


# --------------------------------------------------------------------------- #
# Window sub-score = observable / dark-window duration
# --------------------------------------------------------------------------- #


def test_window_subscore_is_fraction_of_dark_window() -> None:
    dark = timedelta(hours=8)
    assert window_subscore(timedelta(hours=4), dark) == pytest.approx(0.5)
    assert window_subscore(timedelta(hours=8), dark) == pytest.approx(1.0)


def test_window_subscore_clamps_at_one() -> None:
    # A window bounded by the dark window can never exceed it, but guard anyway.
    assert window_subscore(timedelta(hours=9), timedelta(hours=8)) == 1.0


# --------------------------------------------------------------------------- #
# Moon sub-score = 1 - impact*(1 - sep_score); neutral when the moon is down
# --------------------------------------------------------------------------- #


def test_moon_subscore_neutral_when_moon_down() -> None:
    assert moon_subscore(0.0, illumination=1.0, moon_up=False) == 1.0


def test_moon_subscore_full_moon_on_target_is_worst() -> None:
    assert moon_subscore(0.0, illumination=1.0, moon_up=True) == pytest.approx(0.0)


def test_moon_subscore_far_from_full_moon_is_neutral() -> None:
    assert moon_subscore(90.0, illumination=1.0, moon_up=True) == pytest.approx(1.0)
    # Beyond 90 degrees stays saturated at neutral.
    assert moon_subscore(150.0, illumination=1.0, moon_up=True) == pytest.approx(1.0)


def test_moon_subscore_scales_with_separation_and_illumination() -> None:
    assert moon_subscore(45.0, illumination=1.0, moon_up=True) == pytest.approx(0.5)
    assert moon_subscore(0.0, illumination=0.5, moon_up=True) == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
# Transit sub-score = 1 at window centre, 0 at an edge or outside
# --------------------------------------------------------------------------- #


def test_transit_subscore_one_at_centre() -> None:
    mid = _START + (_END - _START) / 2
    assert transit_subscore(mid, _START, _END) == pytest.approx(1.0)


def test_transit_subscore_zero_at_edges() -> None:
    assert transit_subscore(_START, _START, _END) == pytest.approx(0.0)
    assert transit_subscore(_END, _START, _END) == pytest.approx(0.0)


def test_transit_subscore_half_at_quarter_point() -> None:
    quarter = _START + (_END - _START) / 4
    assert transit_subscore(quarter, _START, _END) == pytest.approx(0.5)


def test_transit_subscore_zero_outside_window() -> None:
    # A daytime transit (before dusk) sits outside the window -> 0.
    before = _START - timedelta(hours=3)
    assert transit_subscore(before, _START, _END) == 0.0
    after = _END + timedelta(hours=3)
    assert transit_subscore(after, _START, _END) == 0.0


# --------------------------------------------------------------------------- #
# Weighted 0-100 score, renormalised over the live factors (task 4.1, ADR-0010)
# --------------------------------------------------------------------------- #


def test_combined_score_all_perfect_is_100() -> None:
    assert combined_score(1.0, 1.0, 1.0, 1.0) == 100
    # All six factors ideal is still 100.
    assert combined_score(1.0, 1.0, 1.0, 1.0, brightness=1.0, fov_fit=1.0) == 100


def test_combined_score_all_zero_is_0() -> None:
    assert combined_score(0.0, 0.0, 0.0, 0.0) == 0
    assert combined_score(0.0, 0.0, 0.0, 0.0, brightness=0.0, fov_fit=0.0) == 0


def test_geometry_only_renormalises_over_the_four_geometry_weights() -> None:
    # No brightness and no fov_fit: five/six factors drop to four, and the four
    # geometry weights are renormalised to sum to 1 before the weighted mean.
    weighted = (
        WEIGHT_ALTITUDE * 0.8 + WEIGHT_WINDOW * 0.6 + WEIGHT_MOON * 0.9 + WEIGHT_TRANSIT * 0.4
    ) / _GEOMETRY_WEIGHT
    assert combined_score(0.8, 0.6, 0.9, 0.4) == round(100 * weighted)


def test_brightness_factor_renormalises_over_five_factors() -> None:
    live = _GEOMETRY_WEIGHT + WEIGHT_BRIGHTNESS
    weighted = (
        WEIGHT_ALTITUDE * 0.8
        + WEIGHT_WINDOW * 0.6
        + WEIGHT_MOON * 0.9
        + WEIGHT_TRANSIT * 0.4
        + WEIGHT_BRIGHTNESS * 0.5
    ) / live
    assert combined_score(0.8, 0.6, 0.9, 0.4, brightness=0.5) == round(100 * weighted)


def test_all_six_factors_renormalise_over_the_full_base() -> None:
    live = _GEOMETRY_WEIGHT + WEIGHT_BRIGHTNESS + WEIGHT_FOV
    weighted = (
        WEIGHT_ALTITUDE * 0.8
        + WEIGHT_WINDOW * 0.6
        + WEIGHT_MOON * 0.9
        + WEIGHT_TRANSIT * 0.4
        + WEIGHT_BRIGHTNESS * 0.5
        + WEIGHT_FOV * 0.7
    ) / live
    assert combined_score(0.8, 0.6, 0.9, 0.4, brightness=0.5, fov_fit=0.7) == round(100 * weighted)


def test_geometry_only_target_can_still_reach_100() -> None:
    # Dropping the missing factors renormalises the live weights, so a
    # geometry-only target scored on four ideal factors still reaches the full
    # range rather than being compressed below 100.
    assert combined_score(1.0, 1.0, 1.0, 1.0) == 100


@pytest.mark.parametrize(
    ("brightness", "fov_fit"),
    [(None, None), (0.5, None), (None, 0.5), (0.5, 0.5)],
)
def test_combined_score_stays_within_range(brightness: float | None, fov_fit: float | None) -> None:
    for a, w, m, t in [(0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (0.3, 0.7, 0.2, 0.9)]:
        assert 0 <= combined_score(a, w, m, t, brightness=brightness, fov_fit=fov_fit) <= 100


def test_base_weights_sum_to_one() -> None:
    total = (
        WEIGHT_ALTITUDE
        + WEIGHT_WINDOW
        + WEIGHT_MOON
        + WEIGHT_TRANSIT
        + WEIGHT_BRIGHTNESS
        + WEIGHT_FOV
    )
    assert total == pytest.approx(1.0)


def test_geometry_dominates_the_two_new_factors() -> None:
    # Design D5/D6: geometry stays dominant so neither new term dominates placement.
    assert _GEOMETRY_WEIGHT > (WEIGHT_BRIGHTNESS + WEIGHT_FOV)


def test_score_is_stable_near_an_integer_half_boundary() -> None:
    # Design D9: rounding the pre-scaled weighted mean to a fixed precision before
    # the integer scaling shrinks the epsilon surface around integer .5 boundaries.
    # All four geometry factors equal to v give a renormalised weighted mean of v,
    # so v = 0.505 sits the pre-scaled value exactly on 50.5. A sub-microscopic
    # perturbation of one sub-score must not flip the emitted integer.
    baseline = combined_score(0.505, 0.505, 0.505, 0.505)
    for epsilon in (1e-9, -1e-9, 1e-10, -1e-10):
        assert combined_score(0.505 + epsilon, 0.505, 0.505, 0.505) == baseline
        assert combined_score(0.505, 0.505 + epsilon, 0.505, 0.505) == baseline


# --------------------------------------------------------------------------- #
# Gates: minimum duration and the observable-window extraction
# --------------------------------------------------------------------------- #


def test_meets_minimum_exactly_at_threshold() -> None:
    start = datetime(2026, 9, 8, 21, 0, tzinfo=UTC)
    assert meets_minimum(start, start + MIN_WINDOW)
    assert not meets_minimum(start, start + MIN_WINDOW - timedelta(seconds=1))


def _grid(n: int, step_min: int = 5) -> list[datetime]:
    base = datetime(2026, 9, 8, 20, 30, tzinfo=UTC)
    return [base + timedelta(minutes=step_min * i) for i in range(n)]


def test_observable_window_is_none_when_never_above() -> None:
    times = _grid(5)
    assert observable_window(times, [False] * 5) is None


def test_observable_window_spans_the_contiguous_run() -> None:
    times = _grid(6)
    above = [False, True, True, True, False, False]
    start_i, end_i = observable_window(times, above)  # type: ignore[misc]
    assert (start_i, end_i) == (1, 3)


def test_observable_window_takes_the_longest_of_several_runs() -> None:
    times = _grid(9)
    # Two runs: indices 1-2 (len 2) and 4-7 (len 4); the longer wins.
    above = [False, True, True, False, True, True, True, True, False]
    start_i, end_i = observable_window(times, above)  # type: ignore[misc]
    assert (start_i, end_i) == (4, 7)


def test_observable_window_clamps_to_grid_edges() -> None:
    times = _grid(4)
    above = [True, True, True, True]
    start_i, end_i = observable_window(times, above)  # type: ignore[misc]
    assert (start_i, end_i) == (0, 3)
