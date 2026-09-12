"""Tasks 1.1-1.4: the optional per-pier ``Rig`` and its derived field of view.

The ``Rig`` is raw optics (design D1): a focal length, a sensor size, and an
optional reducer, each strictly positive. The field of view is derived offline
from those (design D2), so ranking can judge how well a target frames without the
user pre-computing anything.
"""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from pierpressure.core.config import PierConfig, Rig

from .offline_guard import no_network


def _pier(**overrides: object) -> PierConfig:
    base: dict[str, object] = {
        "id": "backyard",
        "latitude": 51.5,
        "longitude": -0.12,
        "elevation_m": 30.0,
    }
    base.update(overrides)
    return PierConfig(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Task 1.1 / 1.2 — the Rig config model and its validation
# --------------------------------------------------------------------------- #


def test_valid_rig_loads_on_a_pier() -> None:
    pier = _pier(
        rig={
            "focal_length_mm": 600.0,
            "sensor_width_mm": 23.5,
            "sensor_height_mm": 15.7,
        }
    )
    assert pier.rig is not None
    assert pier.rig.focal_length_mm == 600.0
    assert pier.rig.sensor_width_mm == 23.5
    assert pier.rig.sensor_height_mm == 15.7
    assert pier.rig.reducer == 1.0  # defaulted


def test_pier_without_a_rig_is_none() -> None:
    assert _pier().rig is None


def test_rig_reducer_can_be_set() -> None:
    rig = Rig(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7, reducer=0.8)
    assert rig.reducer == 0.8


@pytest.mark.parametrize(
    "field",
    ["focal_length_mm", "sensor_width_mm", "sensor_height_mm", "reducer"],
)
@pytest.mark.parametrize("bad", [0.0, -5.0])
def test_non_positive_rig_value_is_rejected(field: str, bad: float) -> None:
    values: dict[str, float] = {
        "focal_length_mm": 600.0,
        "sensor_width_mm": 23.5,
        "sensor_height_mm": 15.7,
        "reducer": 1.0,
    }
    values[field] = bad
    with pytest.raises(ValidationError):
        Rig(**values)  # type: ignore[arg-type]


def test_a_pier_with_a_non_positive_rig_value_is_invalid() -> None:
    with pytest.raises(ValidationError):
        _pier(
            rig={
                "focal_length_mm": 0.0,
                "sensor_width_mm": 23.5,
                "sensor_height_mm": 15.7,
            }
        )


# --------------------------------------------------------------------------- #
# Task 1.3 / 1.4 — the derived field of view
# --------------------------------------------------------------------------- #


def _fov_axis(sensor_mm: float, f_eff_mm: float) -> float:
    return math.degrees(2.0 * math.atan(sensor_mm / (2.0 * f_eff_mm)))


def test_field_of_view_matches_the_known_rig() -> None:
    rig = Rig(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7)
    width, height = rig.field_of_view_deg()
    assert width == pytest.approx(_fov_axis(23.5, 600.0), abs=1e-9)
    assert height == pytest.approx(_fov_axis(15.7, 600.0), abs=1e-9)
    # The short edge is the smaller axis (here the height).
    assert rig.fov_short_deg == pytest.approx(height, abs=1e-9)
    assert rig.fov_short_deg <= width


def test_reducer_below_one_widens_the_field() -> None:
    plain = Rig(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7)
    reduced = Rig(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7, reducer=0.8)
    plain_w, plain_h = plain.field_of_view_deg()
    reduced_w, reduced_h = reduced.field_of_view_deg()
    assert reduced_w > plain_w
    assert reduced_h > plain_h


def test_barlow_above_one_narrows_the_field() -> None:
    plain = Rig(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7)
    barlow = Rig(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7, reducer=2.0)
    assert barlow.fov_short_deg < plain.fov_short_deg


def test_field_of_view_is_deterministic_and_offline() -> None:
    rig = Rig(focal_length_mm=800.0, sensor_width_mm=36.0, sensor_height_mm=24.0, reducer=0.8)
    with no_network():
        first = rig.field_of_view_deg()
        second = rig.field_of_view_deg()
    assert first == second
