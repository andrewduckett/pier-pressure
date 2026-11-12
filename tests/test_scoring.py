"""Tasks 2.1-2.7: the pure, deterministic core verdict math (design D3-D6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from pierpressure.core.conditions import Conditions, Series, Variable
from pierpressure.core.model import AgreementBand, Band, Moon, MoonPhase, Verdict
from pierpressure.core.scoring import (
    AGREE_MAX_GAP,
    MIXED_MAX_GAP,
    OVERCAST_EPSILON,
    AgreementTerm,
    assemble_score,
    atmosphere_mean,
    clarity_weight,
    clear_hours_total,
    cloud_agreement,
    cloud_score_term,
    confidence,
    coverage_weight,
    dew_reason,
    evaluate,
    high_cloud_penalty,
    hour_slots,
    moon_penalty,
    moon_up_at,
    optional_term_mean,
    score_terms,
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


def _series(window: tuple[datetime, datetime], values: list[float | None]) -> Series:
    """A series with one value per window hour and no issue time."""
    return Series(
        provider="p", issued_at=None, values=dict(zip(hour_slots(*window), values, strict=True))
    )


def _conditions(window: tuple[datetime, datetime], **per_hour: float | None) -> Conditions:
    """Conditions with the given uniform cloud value across every window hour."""
    hours = len(hour_slots(*window))
    return Conditions(series={"cloud_cover": _series(window, [per_hour.get("cloud")] * hours)})


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
    # Clear where known, but only the first three hours carry cloud data.
    partial = Conditions(series={"cloud_cover": _series(window, [0.0] * 3 + [None] * 3)})
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
    # Clear all night; seeing = 0.8 for the first three hours, absent thereafter.
    # Cloud and seeing are separate series, correlated by hour.
    snap = Conditions(
        series={
            "cloud_cover": _series(window, [0.0] * 6),
            "seeing": _series(window, [0.8] * 3 + [None] * 3),
        }
    )
    mean = optional_term_mean(window, snap, "seeing")
    assert mean is not None
    # A partial-coverage gap must not depress the mean below the present values.
    assert abs(mean - 0.8) < 1e-9


def test_optional_term_mean_is_none_when_the_term_is_entirely_absent() -> None:
    window = _window(6)
    snap = _conditions(window, cloud=0.0)  # no seeing anywhere
    assert optional_term_mean(window, snap, "seeing") is None


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
    """Conditions with the given per-hour cloud and cloud_high series."""
    return Conditions(
        series={"cloud_cover": _series(window, cloud), "cloud_high": _series(window, high)}
    )


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


def test_clouding_out_the_one_cirrus_hour_never_raises_the_score() -> None:
    # Ten clear hours, one with 100% high cloud and nine with no reading: only that
    # hour is cut, so clouding it out loses its 0.7 of an hour, never gains.
    window = _window(10)
    high: list[float | None] = [100.0] + [None] * 9
    clear = _conditions_high(window, cloud=[0.0] * 10, high=high)
    clouded = _conditions_high(window, cloud=[100.0] + [0.0] * 9, high=high)
    assert assemble_score(window, clear, _moon(0.0, up_during_dark=False)) == 97
    assert assemble_score(window, clouded, _moon(0.0, up_during_dark=False)) == 90


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


def test_an_nws_total_with_no_high_cloud_series_leaves_the_high_cloud_penalty_none() -> None:
    # Listing nws before Open-Meteo leaves the layers unfilled (nws-provider D1).
    window = _window(6)
    total = Series(provider="nws", issued_at=None, values=dict.fromkeys(hour_slots(*window), 10.0))
    snap = Conditions(series={"cloud_cover": total})
    terms = score_terms(window, snap, _moon(0.0, up_during_dark=False))
    assert terms.high_cloud is None


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


# --------------------------------------------------------------------------- #
# score-remaining-night 1.1: seeing and transparency scale the cloud term
# --------------------------------------------------------------------------- #


def _conditions_atmosphere(
    window: tuple[datetime, datetime],
    *,
    cloud: list[float | None],
    seeing: list[float | None],
    transparency: list[float | None],
) -> Conditions:
    """Conditions with per-hour cloud, seeing and transparency series."""
    return Conditions(
        series={
            "cloud_cover": _series(window, cloud),
            "seeing": _series(window, seeing),
            "transparency": _series(window, transparency),
        }
    )


_DARK = _moon(0.0, up_during_dark=False)


def test_atmosphere_mean_is_one_when_no_hour_carries_seeing_or_transparency() -> None:
    window = _window(6)
    snap = _conditions_atmosphere(
        window, cloud=[0.0] * 6, seeing=[None] * 6, transparency=[None] * 6
    )
    assert atmosphere_mean(window, snap) == 1.0


def test_atmosphere_mean_uses_the_one_term_an_hour_carries() -> None:
    window = _window(6)
    snap = _conditions_atmosphere(
        window, cloud=[0.0] * 6, seeing=[0.4] * 6, transparency=[None] * 6
    )
    assert abs(atmosphere_mean(window, snap) - 0.4) < 1e-9


def test_a_mostly_cloudy_night_with_good_atmosphere_scores_14() -> None:
    # The issue's night: cloud 78% gives a clarity weight, and so a cloud term, of 0.15.
    window = _window(6)
    snap = _conditions_atmosphere(
        window, cloud=[78.0] * 6, seeing=[0.71] * 6, transparency=[0.71] * 6
    )
    assert abs(cloud_score_term(window, snap) - 0.15) < 1e-9
    assert assemble_score(window, snap, _DARK) == 14


def test_atmosphere_moves_a_clear_night_from_70_to_100() -> None:
    window = _window(6)
    worst = _conditions_atmosphere(
        window, cloud=[0.0] * 6, seeing=[0.0] * 6, transparency=[0.0] * 6
    )
    best = _conditions_atmosphere(window, cloud=[0.0] * 6, seeing=[1.0] * 6, transparency=[1.0] * 6)
    assert assemble_score(window, worst, _DARK) == 70
    assert assemble_score(window, best, _DARK) == 100


def test_clouding_out_a_poor_atmosphere_hour_never_raises_the_score() -> None:
    # Ten clear hours: eight without seeing or transparency, one at 1, one at 0.
    window = _window(10)
    atmosphere: list[float | None] = [None] * 8 + [1.0, 0.0]
    clear = _conditions_atmosphere(
        window, cloud=[0.0] * 10, seeing=atmosphere, transparency=atmosphere
    )
    clouded = _conditions_atmosphere(
        window, cloud=[0.0] * 9 + [100.0], seeing=atmosphere, transparency=atmosphere
    )
    assert assemble_score(window, clear, _DARK) == 97
    assert assemble_score(window, clouded, _DARK) == 90


def test_the_score_never_exceeds_the_rounded_cloud_term() -> None:
    window = _window(6)
    for cloud in (0.0, 30.0, 50.0, 78.0, 89.0):
        for quality in (0.0, 0.5, 1.0):
            snap = _conditions_atmosphere(
                window, cloud=[cloud] * 6, seeing=[quality] * 6, transparency=[quality] * 6
            )
            ceiling = round(100.0 * cloud_score_term(window, snap))
            assert assemble_score(window, snap, _DARK) <= ceiling


def test_a_half_way_score_rounds_to_the_even_integer() -> None:
    # One clear hour of eight, no atmosphere data: 100 * 1/8 = 12.5, which rounds to 12.
    window = _window(8)
    snap = _conditions_atmosphere(
        window, cloud=[0.0] + [100.0] * 7, seeing=[None] * 8, transparency=[None] * 8
    )
    assert assemble_score(window, snap, _DARK) == 12


# --------------------------------------------------------------------------- #
# score-remaining-night 1.3: the reasons explain the atmosphere factor
# --------------------------------------------------------------------------- #


def test_a_scored_verdict_states_the_atmosphere_factor() -> None:
    window = _window(6)
    snap = _conditions_atmosphere(window, cloud=[0.0] * 6, seeing=[0.0] * 6, transparency=[0.0] * 6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, snap, _DARK)
    assert "Atmosphere factor 70%." in decision.reasons


def test_full_coverage_atmosphere_lines_carry_no_coverage_note() -> None:
    window = _window(6)
    snap = _conditions_atmosphere(
        window, cloud=[0.0] * 6, seeing=[0.71] * 6, transparency=[0.71] * 6
    )
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, snap, _DARK)
    assert "Seeing quality 71%." in decision.reasons
    assert "Transparency quality 71%." in decision.reasons


def test_partial_atmosphere_lines_state_the_share_of_usable_sky_they_cover() -> None:
    # Nine clear hours without seeing or transparency, one clear hour with both at 0.
    window = _window(10)
    atmosphere: list[float | None] = [None] * 9 + [0.0]
    snap = _conditions_atmosphere(
        window, cloud=[0.0] * 10, seeing=atmosphere, transparency=atmosphere
    )
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, snap, _DARK)
    assert "Atmosphere factor 97%." in decision.reasons
    assert "Seeing quality 0% (covers 10% of the usable sky)." in decision.reasons
    assert "Transparency quality 0% (covers 10% of the usable sky)." in decision.reasons


# --------------------------------------------------------------------------- #
# Cloud agreement: the clarity-weighted mean gap (cloud-agreement DD3)
# --------------------------------------------------------------------------- #


def _keyed(provider: str, window: tuple[datetime, datetime], values: list[float | None]) -> Series:
    return Series(
        provider=provider,
        issued_at=None,
        values=dict(zip(hour_slots(*window), values, strict=True)),
    )


def _agreeing(
    window: tuple[datetime, datetime],
    filled: list[float | None],
    *alternates: list[float | None],
) -> Conditions:
    """Cloud cover from provider ``a``, with one alternate per list from ``b``, ``c``, ..."""
    return Conditions(
        series={"cloud_cover": _keyed("a", window, filled)},
        alternates={
            "cloud_cover": tuple(
                _keyed(chr(ord("b") + i), window, values) for i, values in enumerate(alternates)
            )
        },
    )


def test_agreement_is_the_gap_when_every_hour_differs_by_the_same_amount() -> None:
    window = _window(6)
    term = cloud_agreement(window, _agreeing(window, [20.0] * 6, [28.0] * 6))
    assert term is not None
    assert term.mean_gap == 8.0
    assert term.providers == ("a", "b")


def test_agreement_leaves_out_an_hour_only_one_provider_covers() -> None:
    window = _window(6)
    term = cloud_agreement(window, _agreeing(window, [20.0] * 6, [60.0] * 3 + [None] * 3))
    assert term is not None
    assert term.mean_gap == 40.0


def test_agreement_weighs_clear_hours_more_than_cloudy_ones() -> None:
    window = _window(4)
    conditions = _agreeing(window, [5.0, 5.0, 85.0, 85.0], [55.0, 55.0, 90.0, 90.0])
    term = cloud_agreement(window, conditions)
    assert term is not None
    assert abs(term.mean_gap - 50.0) < abs(term.mean_gap - 5.0)


def test_agreement_counts_disagreement_in_an_hour_the_filled_series_calls_overcast() -> None:
    window = _window(6)
    term = cloud_agreement(window, _agreeing(window, [95.0] * 6, [20.0] * 6))
    assert term is not None
    assert term.mean_gap == 75.0


def test_agreement_is_zero_when_every_weight_is_zero() -> None:
    window = _window(6)
    term = cloud_agreement(window, _agreeing(window, [95.0] * 6, [100.0] * 6))
    assert term is not None
    assert term.mean_gap == 0.0


def test_agreement_is_none_without_an_alternate() -> None:
    window = _window(6)
    assert cloud_agreement(window, _conditions(window, cloud=20.0)) is None


def test_agreement_is_none_when_providers_never_share_an_hour() -> None:
    window = _window(4)
    conditions = _agreeing(window, [20.0, 20.0, None, None], [None, None, 60.0, 60.0])
    assert cloud_agreement(window, conditions) is None


def test_agreement_is_none_when_the_alternate_covers_only_passed_hours() -> None:
    window = _window(6)
    conditions = _agreeing(window, [20.0] * 6, [60.0] * 2 + [None] * 4)
    remaining = (window[0] + timedelta(hours=2), window[1])
    assert cloud_agreement(remaining, conditions) is None


def test_agreement_lists_only_providers_with_a_value_in_a_counted_hour() -> None:
    window = _window(4)
    conditions = _agreeing(window, [20.0] * 4, [30.0] * 4, [None] * 4)
    term = cloud_agreement(window, conditions)
    assert term is not None
    assert term.providers == ("a", "b")


def test_agreement_lists_the_filled_provider_first_then_alternates_in_order() -> None:
    window = _window(2)
    conditions = _agreeing(window, [None, 20.0], [30.0, None], [40.0, 50.0])
    term = cloud_agreement(window, conditions)
    assert term is not None
    assert term.providers == ("a", "b", "c")


@pytest.mark.parametrize(
    ("gap", "band"),
    [
        (0.0, AgreementBand.AGREE),
        (14.4, AgreementBand.AGREE),
        (15.0, AgreementBand.MIXED),
        (35.0, AgreementBand.MIXED),
        (35.4, AgreementBand.MIXED),
        (36.0, AgreementBand.DISAGREE),
    ],
)
def test_agreement_band_follows_the_rounded_spread(gap: float, band: AgreementBand) -> None:
    assert AgreementTerm(gap, ("a", "b")).band is band


def test_agreement_band_is_mixed_when_a_14_6_point_gap_rounds_to_15() -> None:
    term = AgreementTerm(14.6, ("a", "b"))
    assert term.spread == 15
    assert term.band is AgreementBand.MIXED


def test_agreement_band_thresholds_are_15_and_35() -> None:
    assert (AGREE_MAX_GAP, MIXED_MAX_GAP) == (15, 35)


# --------------------------------------------------------------------------- #
# Confidence falls with low agreement (cloud-agreement DD4)
# --------------------------------------------------------------------------- #


def _confident(
    window: tuple[datetime, datetime], issued: datetime, *, cloud_hours: int | None = None
) -> Conditions:
    """Complete, freshly issued cloud, seeing and transparency over ``window``.

    ``cloud_hours`` leaves cloud on only the first that many hours, which thins
    completeness to that share of the window.
    """
    slots = hour_slots(*window)
    covered = slots if cloud_hours is None else slots[:cloud_hours]

    def series(values: dict[datetime, float | None]) -> Series:
        return Series(provider="a", issued_at=issued, values=values)

    return Conditions(
        series={
            "cloud_cover": series(dict.fromkeys(covered, 20.0)),
            "seeing": series(dict.fromkeys(slots, 0.7)),
            "transparency": series(dict.fromkeys(slots, 0.7)),
        }
    )


_AGREE = AgreementTerm(8.0, ("a", "b"))
_MIXED = AgreementTerm(25.0, ("a", "b"))
_DISAGREE = AgreementTerm(45.0, ("a", "b"))


def _value(
    instant: datetime,
    window: tuple[datetime, datetime],
    conditions: Conditions,
    agreement: AgreementTerm | None,
) -> int:
    return confidence(make_pier(), instant, window, conditions, agreement)[1]


def test_confidence_is_unchanged_by_agreement_that_agrees() -> None:
    window = _window(10)
    instant = window[0] - timedelta(hours=1)
    conditions = _confident(window, instant)
    assert _value(instant, window, conditions, _AGREE) == _value(instant, window, conditions, None)


def test_confidence_falls_when_agreement_is_mixed() -> None:
    window = _window(10)
    instant = window[0] - timedelta(hours=1)
    conditions = _confident(window, instant)
    assert _value(instant, window, conditions, _MIXED) == 90


def test_confidence_falls_further_when_forecasts_disagree() -> None:
    window = _window(10)
    instant = window[0] - timedelta(hours=1)
    conditions = _confident(window, instant)
    assert _value(instant, window, conditions, _DISAGREE) < _value(
        instant, window, conditions, _MIXED
    )


def test_confidence_from_100_stays_medium_when_forecasts_disagree() -> None:
    window = _window(10)
    instant = window[0] - timedelta(hours=1)
    assert confidence(make_pier(), instant, window, _confident(window, instant), _DISAGREE) == (
        Band.MEDIUM,
        67,
    )


def test_confidence_a_day_out_is_clamped_to_medium_when_forecasts_disagree() -> None:
    window = _window(10)
    instant = window[0] - timedelta(hours=24)
    conditions = _confident(window, instant)
    assert _value(instant, window, conditions, None) == 50
    assert confidence(make_pier(), instant, window, conditions, _DISAGREE) == (Band.MEDIUM, 40)


def test_confidence_already_low_still_falls_when_forecasts_disagree() -> None:
    window = _window(10)
    instant = window[0] - timedelta(hours=1)
    conditions = _confident(window, instant, cloud_hours=3)
    assert _value(instant, window, conditions, None) == 30
    assert _value(instant, window, conditions, _DISAGREE) == 20


def test_confidence_ignores_an_alternates_issue_time() -> None:
    window = _window(10)
    instant = window[0] - timedelta(hours=1)
    base = _confident(window, instant)
    slots = hour_slots(*window)

    def with_alternate(issued: datetime) -> Conditions:
        alternate = Series(provider="b", issued_at=issued, values=dict.fromkeys(slots, 28.0))
        return Conditions(series=base.series, alternates={"cloud_cover": (alternate,)})

    fresh, stale = with_alternate(instant), with_alternate(instant - timedelta(days=2))
    assert _value(instant, window, fresh, _AGREE) == _value(instant, window, stale, _AGREE)


# --------------------------------------------------------------------------- #
# Reasons name the agreement (cloud-agreement DD5)
# --------------------------------------------------------------------------- #


def test_a_scored_verdict_ends_its_reasons_with_the_agreement() -> None:
    window = _window(6)
    conditions = _agreeing(window, [10.0] * 6, [18.0] * 6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.GO
    assert decision.reasons[-2:] == [
        f"Score {decision.score}/100.",
        "Cloud agreement agree: 2 providers, spread 8 points.",
    ]


def test_a_gated_verdict_names_the_gate_reason_then_the_agreement() -> None:
    window = _window(6)
    conditions = _agreeing(window, [95.0] * 6, [35.0] * 6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.NO_GO
    assert decision.reasons == [
        "Overcast for the whole dark window: no usably clear sky.",
        "Cloud agreement disagree: 2 providers, spread 60 points. Confidence lowered.",
    ]


def test_a_wind_gated_verdict_names_the_agreement_after_the_gate_reason() -> None:
    window = _window(6)
    slots = hour_slots(*window)
    agreeing = _agreeing(window, [10.0] * 6, [35.0] * 6)
    wind = Series(provider="a", issued_at=None, values=dict.fromkeys(slots, 80.0))
    conditions = Conditions(
        series={**agreeing.series, "wind_gust": wind}, alternates=agreeing.alternates
    )
    pier = make_pier().model_copy(update={"max_gust": 40.0})
    decision = evaluate(pier, _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.NO_GO
    assert decision.reasons == [
        "Wind gust over the 40 km/h limit during the dark window.",
        "Cloud agreement mixed: 2 providers, spread 25 points. Confidence lowered.",
    ]


def test_a_verdict_from_one_provider_adds_no_agreement_reason() -> None:
    window = _window(6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, _conditions(window, cloud=10.0), _DARK)
    assert decision.agreement is None
    assert not any(line.startswith("Cloud agreement") for line in decision.reasons)


def test_a_verdict_without_a_dark_window_adds_no_agreement_reason() -> None:
    window = _window(6)
    conditions = _agreeing(window, [10.0] * 6, [60.0] * 6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, (None, None), conditions, _DARK)
    assert decision.agreement is None
    assert decision.reasons == ["No astronomical night tonight: the sun never drops below -18°."]


def test_a_verdict_carries_the_agreement_its_confidence_used() -> None:
    window = _window(6)
    conditions = _agreeing(window, [10.0] * 6, [35.0] * 6)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.agreement == AgreementTerm(25.0, ("a", "b"))
    assert (decision.band, decision.confidence) == confidence(
        make_pier(), _EVAL_INSTANT, window, conditions, decision.agreement
    )


# --------------------------------------------------------------------------- #
# Reasons name the first dew or frost hour (dew-spread-reason D1, D5)
# --------------------------------------------------------------------------- #

# 20:30 -> 03:25 UTC: slots 20:00 .. 03:00.
_DEW_WINDOW = (
    datetime(2026, 9, 8, 20, 30, tzinfo=UTC),
    datetime(2026, 9, 9, 3, 25, tzinfo=UTC),
)


def _weather(
    window: tuple[datetime, datetime],
    temperature: list[float | None],
    dew_point: list[float | None],
    *,
    cloud: float | None = 10.0,
) -> Conditions:
    """Cloud, temperature and dew point, one value per window hour."""
    hours = len(hour_slots(*window))
    series: dict[Variable, Series] = {
        "temperature": _series(window, temperature),
        "dew_point": _series(window, dew_point),
    }
    if cloud is not None:
        series["cloud_cover"] = _series(window, [cloud] * hours)
    return Conditions(series=series)


def _spreads(
    window: tuple[datetime, datetime], spreads: list[float], temperature: float = 10.0
) -> Conditions:
    """Weather at a fixed temperature whose spread per hour is as given."""
    return _weather(window, [temperature] * len(spreads), [temperature - s for s in spreads])


def test_dew_reason_names_the_first_hour_under_the_margin() -> None:
    conditions = _spreads(_DEW_WINDOW, [6.0, 5.0, 3.5, 2.0, 2.0, 2.0, 2.0, 2.0])
    assert dew_reason(_DEW_WINDOW, conditions, 4.0) == "Dew likely from 2026-09-08T22:00:00Z."


def test_dew_reason_names_frost_when_the_first_hour_under_the_margin_is_freezing() -> None:
    temperature = [5.0, 3.0, 1.0, 0.0, -1.0, -1.0, -1.0, -1.0]
    dew_point = [-5.0, -5.0, -5.0, -1.0, -2.0, -2.0, -2.0, -2.0]
    conditions = _weather(_DEW_WINDOW, temperature, dew_point)
    assert dew_reason(_DEW_WINDOW, conditions, 4.0) == "Frost likely from 2026-09-08T23:00:00Z."


def test_dew_reason_gives_one_dew_line_when_frost_comes_later() -> None:
    temperature = [8.0, 2.0, 1.0, -1.0, -1.0, -1.0, -1.0, -1.0]
    dew_point = [0.0, 0.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0]
    conditions = _weather(_DEW_WINDOW, temperature, dew_point)
    assert dew_reason(_DEW_WINDOW, conditions, 4.0) == "Dew likely from 2026-09-08T21:00:00Z."


def test_dew_reason_is_none_when_the_spread_equals_the_margin() -> None:
    assert dew_reason(_DEW_WINDOW, _spreads(_DEW_WINDOW, [4.0] * 8), 4.0) is None


def test_dew_reason_is_none_with_a_zero_margin() -> None:
    assert dew_reason(_DEW_WINDOW, _spreads(_DEW_WINDOW, [1.0] * 8), 0.0) is None


def test_dew_reason_is_none_when_no_hour_is_under_the_margin() -> None:
    assert dew_reason(_DEW_WINDOW, _spreads(_DEW_WINDOW, [8.0] * 8), 4.0) is None


def test_dew_reason_is_none_without_temperature_or_dew_point() -> None:
    assert dew_reason(_DEW_WINDOW, _conditions(_DEW_WINDOW, cloud=10.0), 4.0) is None


def test_dew_reason_skips_an_hour_missing_a_dew_point() -> None:
    temperature: list[float | None] = [10.0] * 8
    dew_point: list[float | None] = [None, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0]
    conditions = _weather(_DEW_WINDOW, temperature, dew_point)
    assert dew_reason(_DEW_WINDOW, conditions, 4.0) == "Dew likely from 2026-09-08T21:00:00Z."


def test_dew_reason_skips_an_hour_missing_a_temperature() -> None:
    temperature: list[float | None] = [None, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
    conditions = _weather(_DEW_WINDOW, temperature, [9.0] * 8)
    assert dew_reason(_DEW_WINDOW, conditions, 4.0) == "Dew likely from 2026-09-08T21:00:00Z."


def test_dew_reason_names_a_boundary_slot_by_its_start_and_never_a_passed_one() -> None:
    # Mid-session at 23:30: the 22:00 hour has passed, and the 23:00 slot is
    # only half inside the scored window but is still named by its start.
    conditions = _spreads(_DEW_WINDOW, [6.0, 6.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    scored = (datetime(2026, 9, 8, 23, 30, tzinfo=UTC), _DEW_WINDOW[1])
    assert dew_reason(scored, conditions, 4.0) == "Dew likely from 2026-09-08T23:00:00Z."


def test_dew_reason_ignores_cloud() -> None:
    spreads = [6.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    temperature = [10.0] * 8
    dew_point = [10.0 - s for s in spreads]
    for cloud in (None, 0.0, 100.0):
        conditions = _weather(_DEW_WINDOW, temperature, dew_point, cloud=cloud)
        assert dew_reason(_DEW_WINDOW, conditions, 4.0) == "Dew likely from 2026-09-08T21:00:00Z."


def _with_weather(conditions: Conditions, window: tuple[datetime, datetime]) -> Conditions:
    """``conditions`` plus a 1 °C spread above freezing in every window hour."""
    hours = len(hour_slots(*window))
    weather = {"temperature": _series(window, [10.0] * hours)}
    weather["dew_point"] = _series(window, [9.0] * hours)
    return Conditions(series={**conditions.series, **weather}, alternates=conditions.alternates)


_DEW_LINE = "Dew likely from 2026-09-08T21:00:00Z."


def test_a_scored_verdict_ends_with_the_agreement_then_the_dew_line() -> None:
    window = _window(6)
    conditions = _with_weather(_agreeing(window, [10.0] * 6, [18.0] * 6), window)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.GO
    assert decision.reasons[-3:] == [
        f"Score {decision.score}/100.",
        "Cloud agreement agree: 2 providers, spread 8 points.",
        _DEW_LINE,
    ]


def test_a_wind_capped_verdict_puts_the_dew_line_after_the_cap_and_the_agreement() -> None:
    window = _window(6)
    conditions = _with_weather(_agreeing(window, [10.0] * 6, [18.0] * 6), window)
    pier = make_pier().model_copy(update={"max_gust": 40.0})
    decision = evaluate(pier, _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.MAYBE
    assert decision.reasons[-3:] == [
        "Wind data unavailable: the safety limit cannot be confirmed, so not a GO.",
        "Cloud agreement agree: 2 providers, spread 8 points.",
        _DEW_LINE,
    ]


def test_a_short_window_puts_the_dew_line_last() -> None:
    start = datetime(2026, 9, 8, 21, 0, tzinfo=UTC)
    window = (start, start + timedelta(minutes=30))
    conditions = _with_weather(_conditions(window, cloud=10.0), window)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.MAYBE
    assert decision.reasons[-1] == _DEW_LINE


def test_missing_cloud_still_gets_the_dew_line() -> None:
    window = _window(6)
    conditions = _with_weather(Conditions(), window)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.MAYBE
    assert decision.reasons[0].startswith("Conditions unavailable")
    assert decision.reasons[-1] == _DEW_LINE


def test_a_gated_no_go_carries_no_dew_line() -> None:
    window = _window(6)
    conditions = _with_weather(_conditions(window, cloud=100.0), window)
    decision = evaluate(make_pier(), _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.NO_GO
    assert not any(line.startswith(("Dew", "Frost")) for line in decision.reasons)


def test_a_wind_gated_no_go_carries_no_dew_line() -> None:
    window = _window(6)
    slots = hour_slots(*window)
    wind = Series(provider="p", issued_at=None, values=dict.fromkeys(slots, 80.0))
    weather = _with_weather(_conditions(window, cloud=10.0), window)
    conditions = Conditions(series={**weather.series, "wind_gust": wind})
    pier = make_pier().model_copy(update={"max_gust": 40.0})
    decision = evaluate(pier, _EVAL_INSTANT, window, conditions, _DARK)
    assert decision.verdict is Verdict.NO_GO
    assert not any(line.startswith(("Dew", "Frost")) for line in decision.reasons)


def test_a_zero_dew_margin_adds_no_dew_line() -> None:
    window = _window(6)
    conditions = _with_weather(_conditions(window, cloud=10.0), window)
    pier = make_pier().model_copy(update={"dew_margin": 0.0})
    decision = evaluate(pier, _EVAL_INSTANT, window, conditions, _DARK)
    assert not any(line.startswith(("Dew", "Frost")) for line in decision.reasons)


@pytest.mark.parametrize(
    ("temperature", "dew_point"),
    [(10.0, 9.0), (-1.0, -2.0), (10.0, 2.0)],
)
def test_temperature_and_dew_point_dew_changes_nothing_else(
    temperature: float, dew_point: float
) -> None:
    window = _window(6)
    hours = len(hour_slots(*window))
    dry = _agreeing(window, [10.0] * 6, [18.0] * 6)
    weather = {
        "temperature": _series(window, [temperature] * hours),
        "dew_point": _series(window, [dew_point] * hours),
    }
    wet = Conditions(series={**dry.series, **weather}, alternates=dry.alternates)
    before = evaluate(make_pier(), _EVAL_INSTANT, window, dry, _DARK)
    after = evaluate(make_pier(), _EVAL_INSTANT, window, wet, _DARK)
    assert (after.verdict, after.score, after.band, after.confidence) == (
        before.verdict,
        before.score,
        before.band,
        before.confidence,
    )
    extra = after.reasons[len(before.reasons) :]
    assert after.reasons[: len(before.reasons)] == before.reasons
    assert len(extra) <= 1
    assert all(line.startswith(("Dew likely from ", "Frost likely from ")) for line in extra)
