"""Tasks 2.4-2.7: hard gates, banded score, confidence, and the degradation ladder."""

from __future__ import annotations

from datetime import UTC, datetime

from pierpressure.core.conditions import ConditionsSnapshot, HourlyConditions
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Band, Moon, MoonPhase, Verdict
from pierpressure.core.scoring import evaluate, hour_slots

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
) -> ConditionsSnapshot:
    hours = tuple(
        HourlyConditions(
            time=s, cloud_cover=cloud, wind_gust=wind, seeing=seeing, transparency=transparency
        )
        for s in hour_slots(*window)
    )
    return ConditionsSnapshot(hours=hours, base_issued_at=issued_at, secondary_issued_at=issued_at)


# --------------------------------------------------------------------------- #
# 2.4 hard gates and their precedence
# --------------------------------------------------------------------------- #


def test_no_dark_window_gates_to_no_go_with_null_score() -> None:
    decision = evaluate(_pier(), _INSTANT, _NO_WINDOW, ConditionsSnapshot(), _new_moon())
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
    decision = evaluate(_pier(), _INSTANT, _NO_WINDOW, ConditionsSnapshot(), _new_moon())
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


def test_missing_wind_without_a_limit_is_irrelevant() -> None:
    # No max_gust configured: absent wind must not cap a clear night.
    decision = evaluate(
        _pier(go_threshold=50), _INSTANT, _WINDOW, _snapshot(cloud=0.0), _new_moon()
    )
    assert decision.verdict is Verdict.GO


def test_every_verdict_carries_at_least_one_reason() -> None:
    decision = evaluate(_pier(), _INSTANT, _WINDOW, _snapshot(cloud=20.0), _new_moon())
    assert decision.reasons and all(r.strip() for r in decision.reasons)
