"""Tasks 3.1-3.4: the field-of-view-fit and brightness ranking sub-scores.

Both are pure functions over numbers — no astronomy — so the framing and
brightness curves are pinned exactly and independently of Skyfield (design
D3/D4). Both are clamped to ``[0, 1]`` like the four geometry sub-scores.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pierpressure.core.catalog import load_catalog
from pierpressure.core.config import Rig
from pierpressure.core.model import Target, TargetWindow
from pierpressure.core.ranking import (
    brightness_subscore,
    equipment_reasons,
    fov_fit_subscore,
)

# --------------------------------------------------------------------------- #
# Task 3.1 / 3.2 — the FOV-fit framing curve on r = size / fov_short
# --------------------------------------------------------------------------- #


def test_fov_fit_stays_within_unit_interval() -> None:
    for r in (0.0, 0.001, 0.05, 0.3, 1.0, 2.0, 50.0):
        assert 0.0 <= fov_fit_subscore(r) <= 1.0


def test_fov_fit_speck_scores_a_low_floor_not_zero() -> None:
    # A vanishingly small object is still imageable, just not ideal: a low floor,
    # strictly above zero and well below the sweet band.
    speck = fov_fit_subscore(0.001)
    assert 0.0 < speck < 0.5


def test_fov_fit_sweet_band_scores_near_one() -> None:
    # A comfortable fraction of the frame frames best.
    assert fov_fit_subscore(0.3) == pytest.approx(1.0)


def test_fov_fit_speck_scores_below_the_sweet_band() -> None:
    assert fov_fit_subscore(0.001) < fov_fit_subscore(0.3)


def test_fov_fit_oversize_decays_without_a_cliff() -> None:
    # Past r = 1 the object no longer fits; a slightly-too-big object still beats a
    # hugely-too-big one, and neither drops to a hard zero.
    slightly = fov_fit_subscore(1.2)
    hugely = fov_fit_subscore(5.0)
    assert slightly > hugely > 0.0
    assert slightly < fov_fit_subscore(0.3)


def test_fov_fit_is_monotonic_across_the_oversize_range() -> None:
    values = [fov_fit_subscore(r) for r in (1.1, 1.5, 2.0, 4.0, 8.0)]
    assert values == sorted(values, reverse=True)


# --------------------------------------------------------------------------- #
# Task 3.3 / 3.4 — the brightness curve, separate anchors per scale
# --------------------------------------------------------------------------- #


def test_brightness_is_none_when_both_inputs_unknown() -> None:
    assert brightness_subscore(surface_brightness=None, magnitude=None) is None


def test_brightness_stays_within_unit_interval() -> None:
    for sb in (10.0, 18.0, 21.5, 25.0, 30.0):
        value = brightness_subscore(surface_brightness=sb, magnitude=None)
        assert value is not None and 0.0 <= value <= 1.0
    for mag in (-2.0, 0.0, 6.0, 13.0, 20.0):
        value = brightness_subscore(surface_brightness=None, magnitude=mag)
        assert value is not None and 0.0 <= value <= 1.0


def test_brighter_surface_brightness_scores_higher() -> None:
    # Surface brightness is mag/arcsec²: a smaller number is brighter.
    brighter = brightness_subscore(surface_brightness=19.0, magnitude=None)
    fainter = brightness_subscore(surface_brightness=24.0, magnitude=None)
    assert brighter is not None and fainter is not None
    assert brighter > fainter


def test_brighter_magnitude_scores_higher() -> None:
    brighter = brightness_subscore(surface_brightness=None, magnitude=4.0)
    fainter = brightness_subscore(surface_brightness=None, magnitude=12.0)
    assert brighter is not None and fainter is not None
    assert brighter > fainter


def test_surface_brightness_preferred_over_magnitude_when_both_present() -> None:
    # When both are given, surface brightness is the input (design D4): the score
    # tracks the surface-brightness scale, not the magnitude.
    with_sb = brightness_subscore(surface_brightness=19.0, magnitude=12.0)
    sb_only = brightness_subscore(surface_brightness=19.0, magnitude=None)
    assert with_sb == sb_only


def test_each_scale_maps_through_its_own_anchors() -> None:
    # A mid surface-brightness object must NOT score as far fainter than a mid
    # magnitude object purely because its numbers are larger — separate anchors,
    # never one shared curve. A single shared curve would score sb=21.5 far below
    # mag=8. With per-scale anchors both mid-scale objects land near the middle.
    mid_sb = brightness_subscore(surface_brightness=21.5, magnitude=None)
    mid_mag = brightness_subscore(surface_brightness=None, magnitude=8.0)
    assert mid_sb is not None and mid_mag is not None
    assert abs(mid_sb - mid_mag) < 0.25
    assert mid_sb > 0.25  # not scored as if it were near-invisible


# --------------------------------------------------------------------------- #
# Task 5.4 — the equipment reasons describe the framing region truthfully
# --------------------------------------------------------------------------- #

_WINDOW = TargetWindow(
    start=datetime(2026, 9, 8, 21, 0, tzinfo=UTC),
    end=datetime(2026, 9, 9, 2, 0, tzinfo=UTC),
)


def _m31_target() -> Target:
    # A Target whose id maps to a real catalog object (M31, size 177.83′), so
    # equipment_reasons classifies from the object's raw size.
    m31 = next(o for o in load_catalog() if o.id == "NGC0224")
    return Target(
        id=m31.id,
        name=m31.name,
        type=m31.type,
        score=90,
        window=_WINDOW,
        max_altitude=60.0,
        transit_time=datetime(2026, 9, 8, 23, 30, tzinfo=UTC),
        moon_separation=100.0,
        size_arcmin=m31.size_arcmin,
        magnitude=m31.magnitude,
        surface_brightness=m31.surface_brightness,
    )


def _rig(focal_length_mm: float) -> Rig:
    # Short edge is the 15.7 mm sensor height; a shorter focal length widens the
    # field, so focal length is the knob that moves M31's size/fov ratio.
    return Rig(focal_length_mm=focal_length_mm, sensor_width_mm=23.5, sensor_height_mm=15.7)


def _framing_reason(focal_length_mm: float) -> str:
    reasons = equipment_reasons(_rig(focal_length_mm), _m31_target())
    framing = [r for r in reasons if "field of view" in r or "frames well" in r]
    assert framing, reasons
    return framing[0]


def test_framing_reason_names_each_region_truthfully() -> None:
    # A very wide field makes the galaxy small; a moderate field frames it well; a
    # field just under the galaxy's size has it nearly filling the frame; a narrow
    # field leaves it larger than the field of view. Crucially, the near-filling
    # case must NOT be described as "small".
    assert "small" in _framing_reason(8.0)
    assert "frames well" in _framing_reason(60.0)
    fills = _framing_reason(270.0)
    assert "fills most" in fills and "small" not in fills
    assert "larger than" in _framing_reason(600.0)


def test_no_rig_emits_no_framing_reason() -> None:
    assert equipment_reasons(None, _m31_target()) == []
