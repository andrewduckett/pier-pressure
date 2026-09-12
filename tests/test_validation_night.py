"""Task 6.1: the six base weights and the framing/brightness anchors, validated.

The equipment constants (weights and curve anchors in ``core/ranking``) are fixed
in code, not configuration. They were chosen and retained on a documented
validation night — the London pier on 2026-09-08, the method M5 used in its task
8.2 — and this test is the check-in of that reasoning: it asserts the constants
are the locked values and that the top-of-list behaviour on that night is
defensible, so any future change to a weight or anchor is a deliberate, reviewed
diff rather than silent drift.

Findings on the validation night (600 mm refractor, APS-C sensor → ~90′ short
edge): a bright, well-framed showpiece such as the North America Nebula scores at
the top, and swapping in a rig that frames a target better raises its score while
one that frames it worse lowers it — so field-of-view fit does real, correctly
signed work. Objects with unknown brightness are scored on the factors that ARE
known (geometry, and framing when a size is recorded) rather than on a guessed
brightness, per ADR-0010.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pierpressure.core.catalog import load_catalog
from pierpressure.core.config import PierConfig
from pierpressure.core.ranking import (
    WEIGHT_ALTITUDE,
    WEIGHT_BRIGHTNESS,
    WEIGHT_FOV,
    WEIGHT_MOON,
    WEIGHT_TRANSIT,
    WEIGHT_WINDOW,
    _fov_short_arcmin,
    altitude_subscore,
    brightness_subscore,
    combined_score,
    fov_fit_subscore,
    geometry_for,
    moon_subscore,
    rank_targets,
    transit_subscore,
    window_subscore,
)
from pierpressure.core.sky import dark_window, moon_info

from .offline_guard import no_network

_VALIDATION_INSTANT = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)
# A modest imaging rig: a 600 mm refractor on an APS-C-sized sensor.
_REFERENCE_RIG = {"focal_length_mm": 600.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}
_WIDEFIELD_RIG = {"focal_length_mm": 250.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}
_LONG_RIG = {"focal_length_mm": 1500.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}


def _pier(rig: dict[str, float]) -> PierConfig:
    return PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0, rig=rig)  # type: ignore[arg-type]


def _score_on_validation_night(pier: PierConfig, object_id: str) -> int:
    obj = next(o for o in load_catalog() if o.id == object_id)
    with no_network():
        window = dark_window(pier, _VALIDATION_INSTANT)
        moon = moon_info(pier, window, _VALIDATION_INSTANT)
        geo = geometry_for(pier, obj, window, _VALIDATION_INSTANT)
    assert geo is not None
    dark = window[1] - window[0]  # type: ignore[operator]
    fov_short_arcmin = _fov_short_arcmin(pier.rig)
    assert fov_short_arcmin is not None and obj.size_arcmin is not None
    return combined_score(
        altitude_subscore(geo.max_altitude),
        window_subscore(geo.window_end - geo.window_start, dark),
        moon_subscore(geo.moon_separation, moon.illumination, geo.moon_up_at_peak),
        transit_subscore(geo.transit_time, geo.window_start, geo.window_end),
        brightness=brightness_subscore(obj.surface_brightness, obj.magnitude),
        fov_fit=fov_fit_subscore(obj.size_arcmin / fov_short_arcmin),
    )


def test_base_weights_are_the_locked_validated_values() -> None:
    assert (WEIGHT_ALTITUDE, WEIGHT_WINDOW, WEIGHT_MOON, WEIGHT_TRANSIT) == (
        0.28,
        0.24,
        0.18,
        0.10,
    )
    assert (WEIGHT_BRIGHTNESS, WEIGHT_FOV) == (0.12, 0.08)


def test_a_well_framed_bright_target_scores_at_the_top() -> None:
    # The North America Nebula (bright, mag 4) frames well in a widefield rig and
    # ranks near the ceiling on the validation night.
    score = _score_on_validation_night(_pier(_WIDEFIELD_RIG), "NGC7000")
    assert score >= 90


def test_a_rig_that_frames_a_target_better_scores_it_higher() -> None:
    # Same bright target, three rigs: the widefield frames the large nebula in the
    # sweet band, the reference makes it oversize, the long rig worse still — so the
    # field-of-view term does correctly signed work.
    widefield = _score_on_validation_night(_pier(_WIDEFIELD_RIG), "NGC7000")
    reference = _score_on_validation_night(_pier(_REFERENCE_RIG), "NGC7000")
    long = _score_on_validation_night(_pier(_LONG_RIG), "NGC7000")
    assert widefield > reference > long


def test_validation_night_top_ten_is_bounded_and_scored() -> None:
    pier = _pier(_REFERENCE_RIG)
    with no_network():
        window = dark_window(pier, _VALIDATION_INSTANT)
        moon = moon_info(pier, window, _VALIDATION_INSTANT)
        targets = rank_targets(pier, _VALIDATION_INSTANT, window, moon)
    assert 0 < len(targets) <= 10
    # A defensible list: ordered by score, and the top target is strongly placed.
    assert [(-t.score, t.id) for t in targets] == sorted((-t.score, t.id) for t in targets)
    assert targets[0].score >= 90
