"""Task 5.1: lock the chosen tuning constants against representative inputs.

These constants were the design's deferred Open Questions. Fixing them here — as
assertions on representative inputs, not just as literals — turns any future
change to a curve or threshold into a deliberate, reviewed diff rather than
silent drift. The chosen values are recorded in the change's design.md.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pierpressure.conditions.provider import MAX_STALENESS
from pierpressure.core.config import DEFAULT_GO_THRESHOLD
from pierpressure.core.model import Band
from pierpressure.core.scoring import (
    _HIGH_CLOUD_MAX_PENALTY,
    _MOON_MAX_PENALTY,
    CLOUD_CLEAR,
    CLOUD_OVERCAST,
    _band_for,
    clarity_weight,
    freshness_factor,
    lead_time_factor,
)

_START = datetime(2026, 9, 8, 21, 0, tzinfo=UTC)
_WINDOW = (_START, _START + timedelta(hours=6))


def test_clarity_curve_knees_and_midpoint() -> None:
    assert (CLOUD_CLEAR, CLOUD_OVERCAST) == (10.0, 90.0)
    assert clarity_weight(10.0) == 1.0  # at/below the clear knee
    assert clarity_weight(90.0) == 0.0  # at/above the overcast knee
    assert clarity_weight(50.0) == 0.5  # midpoint of the linear ramp


def test_default_go_threshold_is_locked() -> None:
    assert DEFAULT_GO_THRESHOLD == 65


def test_band_thresholds_are_40_and_70() -> None:
    assert _band_for(70) is Band.HIGH
    assert _band_for(69) is Band.MEDIUM
    assert _band_for(40) is Band.MEDIUM
    assert _band_for(39) is Band.LOW


def test_lead_time_curve_saturation_and_floor() -> None:
    def lead(hours_until: float) -> float:
        return lead_time_factor(_START - timedelta(hours=hours_until), _WINDOW)

    assert lead(3.0) == 1.0  # saturates within 3h of dusk
    assert lead(13.5) == 0.75  # halfway down the ramp
    assert lead(24.0) == 0.5  # floor reached 24h out
    assert lead(48.0) == 0.5  # stays at the floor beyond


def test_freshness_curve_saturation_and_floor() -> None:
    def fresh(age_hours: float) -> float:
        return freshness_factor(_START, _START - timedelta(hours=age_hours))

    assert fresh(0.0) == 1.0
    assert fresh(1.0) == 1.0  # fresh within the refresh cadence
    assert fresh(6.5) == 0.6  # halfway down the ramp
    assert fresh(12.0) == 0.2  # floor at the stale point


def test_missing_issue_time_is_treated_as_maximally_stale() -> None:
    assert freshness_factor(_START, None) == 0.2


def test_cache_max_staleness_is_twelve_hours() -> None:
    assert timedelta(hours=12) == MAX_STALENESS


def test_high_cloud_max_penalty_is_a_fixed_constant_below_the_moon_penalty() -> None:
    # A fixed penalty factor in (0, 1), and kept below the moon's (design D2): high
    # cirrus is a meaningful but non-catastrophic hit.
    assert 0.0 < _HIGH_CLOUD_MAX_PENALTY < 1.0
    assert _HIGH_CLOUD_MAX_PENALTY < _MOON_MAX_PENALTY
