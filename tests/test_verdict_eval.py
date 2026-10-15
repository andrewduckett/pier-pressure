"""Tasks 2.4-2.7: hard gates, banded score, confidence, and the degradation ladder."""

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
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Band, Moon, MoonPhase, Verdict
from pierpressure.core.scoring import Decision, evaluate, hour_slots
from pierpressure.core.sky import _local_solar_day, _night_transitions, dark_window

from .offline_guard import no_network

_START = datetime(2026, 9, 8, 21, 0, tzinfo=UTC)
_END = datetime(2026, 9, 9, 3, 0, tzinfo=UTC)
_WINDOW = (_START, _END)
_NO_WINDOW: tuple[None, None] = (None, None)
# Long before dusk by default, so tests set the instant deliberately when it
# matters (confidence, lead time).
_INSTANT = datetime(2026, 9, 8, 20, 0, tzinfo=UTC)


def _pier(**kw: object) -> PierConfig:
    base: dict[str, object] = {"id": "p", "latitude": 51.5, "longitude": -0.12, "elevation_m": 30.0}
    base.update(kw)
    return PierConfig(**base)  # type: ignore[arg-type]


def _new_moon() -> Moon:
    return Moon(illumination=0.0, phase=MoonPhase.NEW, up_during_dark=False, rise=None, set=None)


def _snapshot(
    *,
    cloud: float | None = 0.0,
    wind: float | None = None,
    seeing: float | None = None,
    transparency: float | None = None,
    issued_at: datetime | None = _INSTANT,
    window: tuple[datetime, datetime] = _WINDOW,
) -> Conditions:
    slots = hour_slots(*window)
    base = BaseGroup.of(
        GroupMeta(source="base", issued_at=issued_at),
        tuple(BaseHour(time=s, cloud_cover=cloud, wind_gust=wind) for s in slots),
    )
    secondary = SecondaryGroup.of(
        GroupMeta(source="secondary", issued_at=issued_at),
        tuple(SecondaryHour(time=s, seeing=seeing, transparency=transparency) for s in slots),
    )
    return Conditions(base=base, secondary=secondary)


# --------------------------------------------------------------------------- #
# 2.4 hard gates and their precedence
# --------------------------------------------------------------------------- #


def test_no_dark_window_gates_to_no_go_with_null_score() -> None:
    decision = evaluate(_pier(), _INSTANT, _NO_WINDOW, Conditions(), _new_moon())
    assert decision.verdict is Verdict.NO_GO
    assert decision.score is None
    assert any(
        "astronomical night" in r.lower() or "dark window" in r.lower() for r in decision.reasons
    )


def test_overcast_window_gates_to_no_go() -> None:
    decision = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=100.0), _new_moon())
    assert decision.verdict is Verdict.NO_GO
    assert decision.score is None
    assert any("overcast" in r.lower() or "cloud" in r.lower() for r in decision.reasons)


def test_wind_gust_over_limit_gates_to_no_go() -> None:
    snap = _snapshot(cloud=0.0, wind=60.0)
    decision = evaluate(_pier(max_gust=40.0), _INSTANT, _WINDOW, snap, _new_moon())
    assert decision.verdict is Verdict.NO_GO
    assert decision.score is None
    assert any("wind" in r.lower() for r in decision.reasons)


def test_overcast_gate_does_not_fire_when_cloud_is_entirely_absent() -> None:
    decision = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=None), _new_moon())
    assert decision.verdict is not Verdict.NO_GO


def test_gates_passing_yields_non_null_score_between_0_and_100() -> None:
    decision = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=20.0), _new_moon())
    assert decision.verdict is not Verdict.NO_GO
    assert decision.score is not None
    assert 0 <= decision.score <= 100


# --------------------------------------------------------------------------- #
# 2.5 banded score and the GO / MAYBE split
# --------------------------------------------------------------------------- #


def test_score_at_or_above_threshold_with_cloud_is_go() -> None:
    decision = evaluate(
        _pier(go_threshold=50), _INSTANT, _WINDOW, _snapshot(cloud=0.0), _new_moon()
    )
    assert decision.score is not None and decision.score >= 50
    assert decision.verdict is Verdict.GO


def test_score_below_threshold_is_maybe() -> None:
    # A hazy-but-not-overcast night scores low; a high threshold makes it MAYBE.
    decision = evaluate(
        _pier(go_threshold=95), _INSTANT, _WINDOW, _snapshot(cloud=60.0), _new_moon()
    )
    assert decision.score is not None and decision.score < 95
    assert decision.verdict is Verdict.MAYBE


def test_a_clear_night_scores_higher_than_an_identical_clouded_one() -> None:
    clear = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=0.0), _new_moon())
    clouded = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=70.0), _new_moon())
    assert clear.score is not None and clouded.score is not None
    assert clear.score > clouded.score


def test_bright_moon_up_during_darkness_lowers_the_score() -> None:
    dark = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=0.0), _new_moon())
    bright = Moon(illumination=1.0, phase=MoonPhase.FULL, up_during_dark=True, rise=None, set=None)
    lit = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=0.0), bright)
    assert dark.score is not None and lit.score is not None
    assert lit.score < dark.score


def test_go_threshold_zero_still_needs_cloud_present_for_go() -> None:
    decision = evaluate(
        _pier(go_threshold=0), _INSTANT, _WINDOW, _snapshot(cloud=None), _new_moon()
    )
    assert decision.verdict is Verdict.MAYBE
    assert decision.verdict is not Verdict.GO


def test_a_window_off_whole_hours_still_yields_a_bounded_score() -> None:
    window = (datetime(2026, 9, 8, 21, 23, tzinfo=UTC), datetime(2026, 9, 9, 3, 47, tzinfo=UTC))
    snap = _snapshot(cloud=10.0, window=window)
    decision = evaluate(_pier(), _INSTANT, window, snap, _new_moon())
    assert decision.score is not None and 0 <= decision.score <= 100


# --------------------------------------------------------------------------- #
# 2.6 confidence
# --------------------------------------------------------------------------- #


def test_astronomy_only_no_go_is_high_confidence_100() -> None:
    decision = evaluate(_pier(), _INSTANT, _NO_WINDOW, Conditions(), _new_moon())
    assert decision.band is Band.HIGH
    assert decision.confidence == 100


def test_confidence_rises_as_dusk_nears_with_freshness_held_equal() -> None:
    far = datetime(2026, 9, 8, 6, 0, tzinfo=UTC)  # 15h before dusk
    near = datetime(2026, 9, 8, 20, 0, tzinfo=UTC)  # 1h before dusk
    conf_far = evaluate(
        _pier(), far, _WINDOW, _snapshot(cloud=0.0, issued_at=far), _new_moon()
    ).confidence
    conf_near = evaluate(
        _pier(), near, _WINDOW, _snapshot(cloud=0.0, issued_at=near), _new_moon()
    ).confidence
    assert conf_near >= conf_far


def test_missing_optional_data_lowers_confidence_without_gating() -> None:
    with_optional = evaluate(
        _pier(), _INSTANT, _WINDOW, _snapshot(cloud=0.0, seeing=0.8, transparency=0.8), _new_moon()
    )
    without_optional = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=0.0), _new_moon())
    assert without_optional.confidence < with_optional.confidence
    assert without_optional.verdict is not Verdict.NO_GO
    assert without_optional.score is not None


# --------------------------------------------------------------------------- #
# 2.7 degradation ladder and reasons
# --------------------------------------------------------------------------- #


def test_missing_cloud_caps_at_maybe_score_0_confidence_0_low() -> None:
    decision = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=None), _new_moon())
    assert decision.verdict is Verdict.MAYBE
    assert decision.score == 0
    assert decision.confidence == 0
    assert decision.band is Band.LOW
    assert any("unavailable" in r.lower() for r in decision.reasons)


def test_failed_wind_gate_is_no_go_even_when_cloud_is_missing() -> None:
    # No cloud, but wind data present and over the limit -> safety NO-GO wins.
    snap = _snapshot(cloud=None, wind=80.0)
    decision = evaluate(_pier(max_gust=40.0), _INSTANT, _WINDOW, snap, _new_moon())
    assert decision.verdict is Verdict.NO_GO
    assert decision.score is None


def test_missing_wind_caps_at_maybe_when_a_limit_is_configured() -> None:
    # Clear night, cloud present, but wind data absent and max_gust set.
    decision = evaluate(_pier(max_gust=40.0), _INSTANT, _WINDOW, _snapshot(cloud=0.0), _new_moon())
    assert decision.verdict is Verdict.MAYBE
    assert decision.verdict is not Verdict.GO
    assert any("wind" in r.lower() for r in decision.reasons)


def test_partial_wind_coverage_caps_at_maybe_when_a_limit_is_configured() -> None:
    # Clear night; wind present and safe for most hours, but one hour has no wind
    # data. The limit cannot be confirmed for that hour, so never GO.
    slots = hour_slots(*_WINDOW)
    base = BaseGroup.of(
        GroupMeta(source="base", issued_at=_INSTANT),
        tuple(
            BaseHour(
                time=s,
                cloud_cover=0.0,
                wind_gust=None if i == len(slots) - 1 else 10.0,  # last hour missing
            )
            for i, s in enumerate(slots)
        ),
    )
    snap = Conditions(base=base)
    decision = evaluate(_pier(max_gust=40.0, go_threshold=50), _INSTANT, _WINDOW, snap, _new_moon())
    assert decision.verdict is Verdict.MAYBE
    assert decision.verdict is not Verdict.GO
    assert any("wind" in r.lower() for r in decision.reasons)


def test_missing_wind_without_a_limit_is_irrelevant() -> None:
    # No max_gust configured: absent wind must not cap a clear night.
    decision = evaluate(
        _pier(go_threshold=50), _INSTANT, _WINDOW, _snapshot(cloud=0.0), _new_moon()
    )
    assert decision.verdict is Verdict.GO


def test_every_verdict_carries_at_least_one_reason() -> None:
    decision = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=20.0), _new_moon())
    assert decision.reasons and all(r.strip() for r in decision.reasons)


# --------------------------------------------------------------------------- #
# score-remaining-night 2.1: once the night has started, judge the rest of it
# --------------------------------------------------------------------------- #

# Inside the dark window, with a fractional second.
_MID = datetime(2026, 9, 8, 23, 30, 0, 400_000, tzinfo=UTC)


def _hourly_snapshot(
    *, cloud: list[float | None], wind: list[float | None] | None = None
) -> Conditions:
    """A base group with per-hour cloud (and wind) across the six-hour ``_WINDOW``."""
    slots = hour_slots(*_WINDOW)
    gusts = wind if wind is not None else [None] * len(slots)
    return Conditions(
        base=BaseGroup.of(
            GroupMeta(source="base", issued_at=_INSTANT),
            tuple(
                BaseHour(time=s, cloud_cover=cloud[i], wind_gust=gusts[i])
                for i, s in enumerate(slots)
            ),
        )
    )


def test_before_dusk_the_scored_window_is_the_dark_window() -> None:
    decision = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=0.0), _new_moon())
    assert decision.scored_window == _WINDOW


def test_mid_session_the_scored_window_starts_at_the_floored_instant() -> None:
    decision = evaluate(_pier(), _MID, _WINDOW, _snapshot(cloud=0.0), _new_moon())
    assert decision.scored_window == (datetime(2026, 9, 8, 23, 30, 0, tzinfo=UTC), _END)


def test_without_a_dark_window_the_scored_window_is_null() -> None:
    decision = evaluate(_pier(), _INSTANT, _NO_WINDOW, Conditions(), _new_moon())
    assert decision.scored_window == (None, None)


def test_passed_clear_hours_no_longer_lift_the_night() -> None:
    # Clear for 21:00-23:00, overcast after.
    snap = _hourly_snapshot(cloud=[0.0, 0.0, 100.0, 100.0, 100.0, 100.0])
    before = evaluate(_pier(), _INSTANT, _WINDOW, snap, _new_moon())
    during = evaluate(_pier(), _MID, _WINDOW, snap, _new_moon())
    assert before.verdict is not Verdict.NO_GO
    assert during.verdict is Verdict.NO_GO
    assert during.score is None


def test_a_gust_in_a_passed_hour_does_not_gate() -> None:
    snap = _hourly_snapshot(cloud=[0.0] * 6, wind=[60.0, 10.0, 10.0, 10.0, 10.0, 10.0])
    decision = evaluate(_pier(max_gust=40.0), _MID, _WINDOW, snap, _new_moon())
    assert decision.verdict is not Verdict.NO_GO


def test_a_wind_gap_in_a_passed_hour_does_not_cap() -> None:
    snap = _hourly_snapshot(cloud=[0.0] * 6, wind=[None, 10.0, 10.0, 10.0, 10.0, 10.0])
    decision = evaluate(_pier(max_gust=40.0, go_threshold=50), _MID, _WINDOW, snap, _new_moon())
    assert decision.verdict is Verdict.GO
    assert not any(r.startswith("Wind data unavailable") for r in decision.reasons)


def test_completeness_reads_the_scored_window() -> None:
    # Cloud is missing only for hours that have passed by _MID.
    gappy = _hourly_snapshot(cloud=[None, None, 0.0, 0.0, 0.0, 0.0])
    full = _hourly_snapshot(cloud=[0.0] * 6)
    assert (
        evaluate(_pier(), _MID, _WINDOW, gappy, _new_moon()).confidence
        == evaluate(_pier(), _MID, _WINDOW, full, _new_moon()).confidence
    )


# --------------------------------------------------------------------------- #
# score-remaining-night 2.3: an empty or short scored window is never GO
# --------------------------------------------------------------------------- #

_NO_DARK_TIME = "No dark time remains to score."
_SHORT_WINDOW = "Less than an hour of dark time to score: not worth setting up."
_LONDON = PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0)
_HIGH_ARCTIC = PierConfig(id="high-arctic", latitude=88.0, longitude=0.0, elevation_m=0.0)


def _exact_dawn(pier: PierConfig, instant: datetime) -> datetime:
    """The exact (unfloored) astronomical dawn that ends the night selected at ``instant``."""
    return next(
        t for t, entering in _night_transitions(pier, instant) if not entering and t >= instant
    )


def _evaluate_at(pier: PierConfig, instant: datetime) -> tuple[tuple[datetime, datetime], Decision]:
    """Select the night at ``instant`` and evaluate it against a clear sky with cloud data."""
    with no_network():
        window = dark_window(pier, instant)
    start, end = window
    assert start is not None and end is not None
    snap = _snapshot(cloud=0.0, window=(start, end), issued_at=instant)
    return (start, end), evaluate(pier, instant, window, snap, _new_moon())


def _assert_no_dark_time(window: tuple[datetime, datetime], decision: Decision) -> None:
    assert decision.scored_window == (window[1], window[1])
    assert decision.verdict is Verdict.MAYBE
    assert decision.score == 0
    assert _NO_DARK_TIME in decision.reasons
    assert not any("unavailable" in r.lower() for r in decision.reasons)


def test_an_instant_in_the_floored_dawn_second_has_no_dark_time_left() -> None:
    dawn = _exact_dawn(_LONDON, datetime(2026, 9, 9, 1, 0, tzinfo=UTC))
    assert dawn.microsecond > 0
    inside = dawn.replace(microsecond=dawn.microsecond // 2)
    window, decision = _evaluate_at(_LONDON, inside)
    assert window[1] == dawn.replace(microsecond=0)
    _assert_no_dark_time(window, decision)


def test_an_instant_exactly_on_the_dawn_crossing_has_no_dark_time_left() -> None:
    # The crossing as found from inside the night. Searching again from it finds the
    # same crossing to within Skyfield's precision, still at or after the instant.
    dawn = _exact_dawn(_LONDON, datetime(2026, 9, 9, 1, 0, tzinfo=UTC))
    window, decision = _evaluate_at(_LONDON, dawn)
    assert window[1] == dawn.replace(microsecond=0)
    _assert_no_dark_time(window, decision)


def test_an_instant_after_the_dawn_crossing_judges_the_next_night() -> None:
    dawn = _exact_dawn(_LONDON, datetime(2026, 9, 9, 1, 0, tzinfo=UTC))
    # Skyfield finds the crossing to about a millisecond, so step clear of it.
    window, decision = _evaluate_at(_LONDON, dawn + timedelta(milliseconds=10))
    assert window[0] > dawn
    assert decision.scored_window == window


def test_in_polar_night_the_noon_boundary_starts_the_next_window() -> None:
    noon = _local_solar_day(_HIGH_ARCTIC, datetime(2026, 12, 21, 15, 0, tzinfo=UTC))[1]
    # Skyfield finds noon to about a millisecond, so step just clear of it.
    window, decision = _evaluate_at(_HIGH_ARCTIC, noon + timedelta(milliseconds=10))
    assert window[0] == noon.replace(microsecond=0)
    assert decision.scored_window == window


def test_in_polar_night_the_floored_second_before_noon_has_no_dark_time_left() -> None:
    noon = _local_solar_day(_HIGH_ARCTIC, datetime(2026, 12, 21, 15, 0, tzinfo=UTC))[1]
    assert noon.microsecond > 10_000
    window, decision = _evaluate_at(_HIGH_ARCTIC, noon - timedelta(milliseconds=10))
    assert window[1] == noon.replace(microsecond=0)
    _assert_no_dark_time(window, decision)


def test_half_an_hour_left_caps_a_go_at_maybe() -> None:
    decision = evaluate(
        _pier(go_threshold=50), _END - timedelta(minutes=30), _WINDOW, _snapshot(), _new_moon()
    )
    assert decision.verdict is Verdict.MAYBE
    assert decision.score is not None and decision.score >= 50
    assert _SHORT_WINDOW in decision.reasons


def test_a_whole_night_under_an_hour_is_capped_before_dusk() -> None:
    window = (_START, _START + timedelta(minutes=50))
    snap = _snapshot(window=window)
    decision = evaluate(_pier(go_threshold=50), _INSTANT, window, snap, _new_moon())
    assert decision.verdict is Verdict.MAYBE
    assert _SHORT_WINDOW in decision.reasons


def test_an_hour_left_can_still_be_go() -> None:
    decision = evaluate(
        _pier(go_threshold=50), _END - timedelta(hours=1), _WINDOW, _snapshot(), _new_moon()
    )
    assert decision.verdict is Verdict.GO
    assert _SHORT_WINDOW not in decision.reasons


# --------------------------------------------------------------------------- #
# score-remaining-night 3.1: the reasons name the span once it is narrowed
# --------------------------------------------------------------------------- #

_SPAN = "Scored from 2026-09-08T23:30:00Z to 2026-09-09T03:00:00Z (the rest of tonight)."


def test_a_mid_session_scored_verdict_names_its_span_first() -> None:
    decision = evaluate(_pier(), _MID, _WINDOW, _snapshot(cloud=0.0), _new_moon())
    assert decision.score is not None
    assert decision.reasons[0] == _SPAN
    assert "Cloud: 100% of the remaining night usable." in decision.reasons


def test_a_mid_session_overcast_gate_names_its_span_and_the_rest_of_the_night() -> None:
    decision = evaluate(_pier(), _MID, _WINDOW, _snapshot(cloud=100.0), _new_moon())
    assert decision.reasons == [
        _SPAN,
        "No usably clear sky in the forecast for the rest of the night.",
    ]


def test_a_mid_session_wind_gate_names_its_span_and_the_rest_of_the_night() -> None:
    snap = _snapshot(cloud=0.0, wind=60.0)
    decision = evaluate(_pier(max_gust=40.0), _MID, _WINDOW, snap, _new_moon())
    assert decision.reasons == [
        _SPAN,
        "Wind gust over the 40 km/h limit during the rest of the night.",
    ]


def test_a_mid_session_missing_cloud_verdict_names_its_span() -> None:
    decision = evaluate(_pier(), _MID, _WINDOW, _snapshot(cloud=None), _new_moon())
    assert decision.reasons[0] == _SPAN
    assert any("unavailable" in r.lower() for r in decision.reasons[1:])


def test_an_empty_scored_window_names_its_span() -> None:
    dawn = _exact_dawn(_LONDON, datetime(2026, 9, 9, 1, 0, tzinfo=UTC))
    _, decision = _evaluate_at(_LONDON, dawn)
    end = dawn.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert decision.reasons[0] == f"Scored from {end} to {end} (the rest of tonight)."


def test_an_instant_in_the_dusk_second_keeps_the_whole_night_wording() -> None:
    in_dusk_second = _START.replace(microsecond=500_000)
    decision = evaluate(_pier(), in_dusk_second, _WINDOW, _snapshot(cloud=0.0), _new_moon())
    assert decision.scored_window == _WINDOW
    assert not any(r.startswith("Scored from") for r in decision.reasons)
    assert "Cloud: 100% of the dark window usable." in decision.reasons


def test_a_verdict_before_dusk_keeps_the_whole_night_wording() -> None:
    decision = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=100.0), _new_moon())
    assert decision.reasons == ["Overcast for the whole dark window: no usably clear sky."]
