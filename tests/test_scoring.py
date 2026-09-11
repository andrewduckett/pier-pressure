"""Tasks 2.1-2.7: the pure, deterministic core verdict math (design D3-D6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pierpressure.core.conditions import (
    BaseGroup,
    BaseHour,
    Conditions,
    GroupMeta,
    SecondaryGroup,
    SecondaryHour,
)
from pierpressure.core.model import Moon, MoonPhase, Verdict
from pierpressure.core.scoring import (
    OVERCAST_EPSILON,
    assemble_score,
    clarity_weight,
    clear_hours_total,
    cloud_score_term,
    coverage_weight,
    evaluate,
    high_cloud_penalty,
    hour_slots,
    moon_penalty,
    moon_up_at,
    optional_term_mean,
)

from .conftest import make_pier


def _moon(
    illumination: float = 0.0,
    *,
    rise: datetime | None = None,
    set: datetime | None = None,
    up_during_dark: bool | None = None,
) -> Moon:
    return Moon(
        illumination=illumination,
        phase=MoonPhase.NEW,
        up_during_dark=up_during_dark,
        rise=rise,
        set=set,
    )


# --------------------------------------------------------------------------- #
# 2.1 clarity weight q(cloud) and coverage weight w
# --------------------------------------------------------------------------- #


def test_clarity_weight_is_one_for_clear_sky() -> None:
    assert clarity_weight(0.0) == 1.0


def test_clarity_weight_is_zero_for_overcast_sky() -> None:
    assert clarity_weight(100.0) == 0.0


def test_clarity_weight_is_monotonic_non_increasing() -> None:
    values = [clarity_weight(c) for c in range(0, 101, 5)]
    assert all(later <= earlier for earlier, later in zip(values, values[1:], strict=False))
    assert all(0.0 <= v <= 1.0 for v in values)


def test_coverage_weight_is_one_for_a_fully_enclosed_hour() -> None:
    w_start = datetime(2026, 9, 8, 21, 0, tzinfo=UTC)
    w_end = datetime(2026, 9, 9, 4, 0, tzinfo=UTC)
    assert coverage_weight(datetime(2026, 9, 8, 23, 0, tzinfo=UTC), w_start, w_end) == 1.0


def test_coverage_weight_is_fractional_for_a_boundary_hour() -> None:
    # Window starts at 21:20, so the 21:00-22:00 slot is only 40 minutes dark.
    w_start = datetime(2026, 9, 8, 21, 20, tzinfo=UTC)
    w_end = datetime(2026, 9, 9, 4, 0, tzinfo=UTC)
    w = coverage_weight(datetime(2026, 9, 8, 21, 0, tzinfo=UTC), w_start, w_end)
    assert 0.0 < w < 1.0
    assert abs(w - 40.0 / 60.0) < 1e-9


def test_hour_slots_tile_the_window_from_the_top_of_the_hour() -> None:
    start = datetime(2026, 9, 8, 21, 20, tzinfo=UTC)
    end = datetime(2026, 9, 8, 23, 40, tzinfo=UTC)
    slots = hour_slots(start, end)
    assert slots[0] == datetime(2026, 9, 8, 21, 0, tzinfo=UTC)
    assert slots[-1] == datetime(2026, 9, 8, 23, 0, tzinfo=UTC)
    # Total coverage equals the window duration in hours.
    total = sum(coverage_weight(s, start, end) for s in slots)
    assert abs(total - (end - start) / timedelta(hours=1)) < 1e-9


# --------------------------------------------------------------------------- #
# 2.2 W = Σ(w·q) and the cloud score term W / Σ_allh(w)
# --------------------------------------------------------------------------- #


def _window(hours: int, minute: int = 0) -> tuple[datetime, datetime]:
    start = datetime(2026, 9, 8, 21, minute, tzinfo=UTC)
    return start, start + timedelta(hours=hours)


def _conditions(window: tuple[datetime, datetime], **per_hour: float | None) -> Conditions:
    """Conditions with the given uniform cloud value across every window hour."""
    start, end = window
    base = BaseGroup.of(
        GroupMeta(source="base"),
        tuple(BaseHour(time=s, cloud_cover=per_hour.get("cloud")) for s in hour_slots(start, end)),
    )
    return Conditions(base=base)


def test_cloud_term_is_one_for_a_wholly_clear_window() -> None:
    window = _window(6)
    snap = _conditions(window, cloud=0.0)
    assert abs(cloud_score_term(window, snap) - 1.0) < 1e-9


def test_cloud_term_stays_in_unit_range_for_a_non_whole_hour_window() -> None:
    window = _window(3, minute=20)  # 21:20 -> 00:20, not whole hours
    snap = _conditions(window, cloud=30.0)
    term = cloud_score_term(window, snap)
    assert 0.0 <= term <= 1.0


def test_uncovered_cloud_hours_depress_the_score_but_do_not_inflate_it() -> None:
    window = _window(6)
    start, end = window
    slots = hour_slots(start, end)
    # Clear where known, but only the first three hours carry cloud data.
    partial = Conditions(
        base=BaseGroup.of(
            GroupMeta(source="base"),
            tuple(
                BaseHour(time=s, cloud_cover=0.0 if i < 3 else None) for i, s in enumerate(slots)
            ),
        )
    )
    full = _conditions(window, cloud=0.0)
    partial_term = cloud_score_term(window, partial)
    full_term = cloud_score_term(window, full)
    # Missing cloud hours count as not-known-usable: lower, never higher.
    assert partial_term < full_term
    assert abs(full_term - 1.0) < 1e-9
    assert abs(partial_term - 0.5) < 1e-9  # 3 of 6 hours usable


def test_clear_hours_total_is_zero_for_an_overcast_window() -> None:
    window = _window(6)
    snap = _conditions(window, cloud=100.0)
    assert clear_hours_total(window, snap) <= OVERCAST_EPSILON


# --------------------------------------------------------------------------- #
# 2.3 clarity-weighted optional-term means and the moon term
# --------------------------------------------------------------------------- #


def test_optional_term_mean_ignores_hours_where_the_term_is_absent() -> None:
    window = _window(6)
    start, end = window
    slots = hour_slots(start, end)
    # Clear all night; seeing = 0.8 for the first three hours, absent thereafter.
    # Cloud is on the base group; seeing on the secondary group, correlated by hour.
    snap = Conditions(
        base=BaseGroup.of(
            GroupMeta(source="base"),
            tuple(BaseHour(time=s, cloud_cover=0.0) for s in slots),
        ),
        secondary=SecondaryGroup.of(
            GroupMeta(source="secondary"),
            tuple(
                SecondaryHour(time=s, seeing=0.8 if i < 3 else None) for i, s in enumerate(slots)
            ),
        ),
    )
    mean = optional_term_mean(window, snap, lambda h: h.seeing)
    assert mean is not None
    # A partial-coverage gap must not depress the mean below the present values.
    assert abs(mean - 0.8) < 1e-9


def test_optional_term_mean_is_none_when_the_term_is_entirely_absent() -> None:
    window = _window(6)
    snap = _conditions(window, cloud=0.0)  # no seeing anywhere
    assert optional_term_mean(window, snap, lambda h: h.seeing) is None


def test_moon_up_at_reconstructs_up_interval_from_rise_then_set() -> None:
    window = (
        datetime(2026, 9, 8, 21, 0, tzinfo=UTC),
        datetime(2026, 9, 9, 5, 0, tzinfo=UTC),
    )
    moon = _moon(
        0.9,
        rise=datetime(2026, 9, 8, 23, 0, tzinfo=UTC),
        set=datetime(2026, 9, 9, 3, 0, tzinfo=UTC),
        up_during_dark=True,
    )
    assert moon_up_at(datetime(2026, 9, 8, 22, 0, tzinfo=UTC), moon, window) is False
    assert moon_up_at(datetime(2026, 9, 9, 0, 0, tzinfo=UTC), moon, window) is True
    assert moon_up_at(datetime(2026, 9, 9, 4, 0, tzinfo=UTC), moon, window) is False


def test_moon_up_at_reconstructs_up_interval_from_set_then_rise() -> None:
    window = (
        datetime(2026, 9, 8, 21, 0, tzinfo=UTC),
        datetime(2026, 9, 9, 5, 0, tzinfo=UTC),
    )
    moon = _moon(
        0.9,
        set=datetime(2026, 9, 8, 23, 0, tzinfo=UTC),
        rise=datetime(2026, 9, 9, 3, 0, tzinfo=UTC),
        up_during_dark=True,
    )
    assert moon_up_at(datetime(2026, 9, 8, 22, 0, tzinfo=UTC), moon, window) is True
    assert moon_up_at(datetime(2026, 9, 9, 0, 0, tzinfo=UTC), moon, window) is False
    assert moon_up_at(datetime(2026, 9, 9, 4, 0, tzinfo=UTC), moon, window) is True


def test_bright_moon_up_during_darkness_adds_a_penalty() -> None:
    window = _window(6)
    snap = _conditions(window, cloud=0.0)
    start, _ = window
    # A full moon up the whole (clear) window.
    bright_up = _moon(1.0, up_during_dark=True)
    # No moon.
    dark = _moon(0.0, up_during_dark=False)
    assert moon_penalty(window, snap, bright_up) > moon_penalty(window, snap, dark)
    assert moon_penalty(window, snap, dark) == 0.0


def test_moon_penalty_is_zero_without_usable_dark_hours() -> None:
    window = _window(6)
    overcast = _conditions(window, cloud=100.0)
    assert moon_penalty(window, overcast, _moon(1.0, up_during_dark=True)) == 0.0


# --------------------------------------------------------------------------- #
# 4.1 high/thin-cloud penalty: clarity-weighted mean over both-present hours
# --------------------------------------------------------------------------- #


def _conditions_high(
    window: tuple[datetime, datetime],
    *,
    cloud: list[float | None],
    high: list[float | None],
) -> Conditions:
    """Conditions whose base hours carry the given per-hour cloud and cloud_high."""
    start, end = window
    slots = hour_slots(start, end)
    hours = tuple(
        BaseHour(time=s, cloud_cover=cloud[i], cloud_high=high[i]) for i, s in enumerate(slots)
    )
    return Conditions(base=BaseGroup.of(GroupMeta(source="base"), hours))


def test_high_cloud_penalty_is_the_clarity_weighted_mean_of_high_over_100() -> None:
    window = _window(6)
    snap = _conditions_high(window, cloud=[0.0] * 6, high=[50.0] * 6)
    penalty = high_cloud_penalty(window, snap)
    assert penalty is not None
    assert abs(penalty - 0.5) < 1e-9  # clear sky (q=1), high=50% -> 0.5


def test_high_cloud_penalty_restricts_the_denominator_to_both_present_hours() -> None:
    # Three hours carry cloud_high=60; the rest carry none. A partial-coverage
    # window is not diluted: the penalty is the mean over the present hours.
    window = _window(6)
    snap = _conditions_high(window, cloud=[0.0] * 6, high=[60.0, 60.0, 60.0, None, None, None])
    penalty = high_cloud_penalty(window, snap)
    assert penalty is not None
    assert abs(penalty - 0.6) < 1e-9


def test_high_cloud_penalty_is_none_when_no_hour_carries_high() -> None:
    window = _window(6)
    snap = _conditions_high(window, cloud=[0.0] * 6, high=[None] * 6)
    assert high_cloud_penalty(window, snap) is None


def test_high_cloud_penalty_excludes_hours_missing_the_total_cloud() -> None:
    # cloud_high present but cloud_cover absent -> the hour carries only one of the
    # pair, so it qualifies for neither numerator nor denominator: None overall.
    window = _window(6)
    snap = _conditions_high(
        window,
        cloud=[0.0, 0.0, 0.0, None, None, None],
        high=[None, None, None, 80.0, 80.0, 80.0],
    )
    assert high_cloud_penalty(window, snap) is None


def test_high_cloud_penalty_ignores_overcast_hours_via_clarity_weight() -> None:
    # Overcast hours (q=0) are already fully penalised by the total-cloud term, so
    # they add no high-cloud penalty even with heavy cirrus aloft: the penalty is
    # the mean over the usably-clear hours only.
    window = _window(6)
    snap = _conditions_high(
        window,
        cloud=[0.0, 0.0, 0.0, 100.0, 100.0, 100.0],
        high=[20.0, 20.0, 20.0, 90.0, 90.0, 90.0],
    )
    penalty = high_cloud_penalty(window, snap)
    assert penalty is not None
    assert abs(penalty - 0.2) < 1e-9


# --------------------------------------------------------------------------- #
# 4.3 assemble_score folds the penalty in as an independent multiplicative factor
# --------------------------------------------------------------------------- #


def test_assemble_score_folds_high_cloud_penalty_as_an_independent_factor() -> None:
    # Clear all night, no moon, no optional terms: quality is 1.0, so the score is
    # driven purely by the high-cloud factor (1 - 0.30 * 0.5) = 0.85.
    window = _window(6)
    dark = _moon(0.0, up_during_dark=False)
    snap = _conditions_high(window, cloud=[0.0] * 6, high=[50.0] * 6)
    assert assemble_score(window, snap, dark) == 85


def test_assemble_score_treats_missing_high_cloud_as_factor_one() -> None:
    # No cloud_high anywhere -> penalty None -> factor 1 -> the perfect-clear score.
    window = _window(6)
    dark = _moon(0.0, up_during_dark=False)
    snap = _conditions_high(window, cloud=[0.0] * 6, high=[None] * 6)
    assert assemble_score(window, snap, dark) == 100


def test_assemble_score_is_monotonic_non_increasing_in_high_cloud() -> None:
    # Holding total cloud cover and every other input fixed, more high cloud never
    # raises the score (night-verdict spec).
    window = _window(6)
    dark = _moon(0.0, up_during_dark=False)
    scores = [
        assemble_score(window, _conditions_high(window, cloud=[0.0] * 6, high=[h] * 6), dark)
        for h in (0.0, 25.0, 50.0, 75.0, 100.0)
    ]
    assert all(later <= earlier for earlier, later in zip(scores, scores[1:], strict=False))
    assert scores[0] == 100  # zero high cloud -> no penalty
    assert scores[-1] < scores[0]  # full high cloud -> a real cut


# --------------------------------------------------------------------------- #
# 4.4 the high-cloud term never gates; missing data drops it silently
# --------------------------------------------------------------------------- #

_EVAL_INSTANT = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)


def test_high_cirrus_never_gates_the_verdict() -> None:
    # Usably-clear total cloud with heavy cirrus aloft, every hard gate passing:
    # the night is scored, not gated (night-verdict spec).
    window = _window(6)
    snap = _conditions_high(window, cloud=[10.0] * 6, high=[90.0] * 6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, snap, _moon(0.0, up_during_dark=False))
    assert decision.verdict is not Verdict.NO_GO
    assert decision.score is not None
    assert 0 <= decision.score <= 100


def test_missing_high_cloud_component_applies_no_penalty_and_no_reason() -> None:
    # Total cloud available, high component unavailable: no high-cloud penalty and
    # no high-cloud reason line (the term drops out like the other optional terms).
    window = _window(6)
    dark = _moon(0.0, up_during_dark=False)
    without_high = _conditions_high(window, cloud=[10.0] * 6, high=[None] * 6)
    with_clear_high = _conditions_high(window, cloud=[10.0] * 6, high=[0.0] * 6)
    missing = evaluate(make_pier(), _EVAL_INSTANT, window, without_high, dark)
    clear = evaluate(make_pier(), _EVAL_INSTANT, window, with_clear_high, dark)
    # An unavailable component is not penalised any more than a clear one.
    assert missing.score == clear.score
    assert not any("High cloud" in reason for reason in missing.reasons)


# --------------------------------------------------------------------------- #
# 4.5 the high-cloud reason is a distinct line, guarded on the rounded percentage
# --------------------------------------------------------------------------- #


def test_high_cloud_reason_is_a_distinct_line_when_the_penalty_bites() -> None:
    window = _window(6)
    snap = _conditions_high(window, cloud=[10.0] * 6, high=[60.0] * 6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, snap, _moon(0.0, up_during_dark=False))
    high_lines = [r for r in decision.reasons if r.startswith("High cloud penalty")]
    assert len(high_lines) == 1
    assert high_lines[0] == "High cloud penalty 60% (thin cirrus aloft)."
    # It is separate from the total-cloud line, not folded into it.
    assert any(r.startswith("Cloud:") for r in decision.reasons)


def test_high_cloud_reason_is_absent_for_a_sub_half_percent_penalty() -> None:
    # cloud_high = 0.4% -> penalty 0.004 -> round(0.4) == 0, so no "0%" line.
    window = _window(6)
    snap = _conditions_high(window, cloud=[10.0] * 6, high=[0.4] * 6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, snap, _moon(0.0, up_during_dark=False))
    assert not any("High cloud" in r for r in decision.reasons)
