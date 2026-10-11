"""Tasks 1.1-1.4: the optional per-pier ``Equipment`` and its derived field of view.

The ``Equipment`` is raw optics (design D1): a focal length, a sensor size, and an
optional reducer, each strictly positive. The field of view is derived offline
from those (design D2), so ranking can judge how well a target frames without the
user pre-computing anything.
"""

from __future__ import annotations

import math
import re
import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pierpressure.core.config import Equipment, PierConfig, validate_piers

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
# Task 1.1 / 1.2 — the Equipment config model and its validation
# --------------------------------------------------------------------------- #


def test_valid_equipment_loads_on_a_pier() -> None:
    pier = _pier(
        equipment={
            "focal_length_mm": 600.0,
            "sensor_width_mm": 23.5,
            "sensor_height_mm": 15.7,
        }
    )
    assert pier.equipment is not None
    assert pier.equipment.focal_length_mm == 600.0
    assert pier.equipment.sensor_width_mm == 23.5
    assert pier.equipment.sensor_height_mm == 15.7
    assert pier.equipment.reducer == 1.0  # defaulted


def test_pier_without_equipment_is_none() -> None:
    assert _pier().equipment is None


def test_equipment_reducer_can_be_set() -> None:
    equipment = Equipment(
        focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7, reducer=0.8
    )
    assert equipment.reducer == 0.8


@pytest.mark.parametrize(
    "field",
    ["focal_length_mm", "sensor_width_mm", "sensor_height_mm", "reducer"],
)
@pytest.mark.parametrize("bad", [0.0, -5.0])
def test_non_positive_equipment_value_is_rejected(field: str, bad: float) -> None:
    values: dict[str, float] = {
        "focal_length_mm": 600.0,
        "sensor_width_mm": 23.5,
        "sensor_height_mm": 15.7,
        "reducer": 1.0,
    }
    values[field] = bad
    with pytest.raises(ValidationError):
        Equipment(**values)  # type: ignore[arg-type]


def test_a_pier_with_a_non_positive_equipment_value_is_invalid() -> None:
    with pytest.raises(ValidationError):
        _pier(
            equipment={
                "focal_length_mm": 0.0,
                "sensor_width_mm": 23.5,
                "sensor_height_mm": 15.7,
            }
        )


_OPTICS = {"focal_length_mm": 600.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}


def test_the_old_rig_key_is_rejected() -> None:
    # A plain rename (#68): ``rig`` is not an alias, so it fails like any unknown key.
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        _pier(rig=_OPTICS)


def test_a_pier_with_the_old_rig_key_is_skipped_and_the_others_run() -> None:
    base = {"latitude": 51.5, "longitude": -0.12, "elevation_m": 30.0}
    raw = [
        {"id": "old", **base, "rig": _OPTICS},
        {"id": "new", **base, "equipment": _OPTICS},
    ]
    valid = validate_piers(raw)
    assert [pier.id for pier in valid] == ["new"]
    assert valid[0].equipment is not None


# --------------------------------------------------------------------------- #
# Task 1.3 / 1.4 — the derived field of view
# --------------------------------------------------------------------------- #


def _fov_axis(sensor_mm: float, f_eff_mm: float) -> float:
    return math.degrees(2.0 * math.atan(sensor_mm / (2.0 * f_eff_mm)))


def test_field_of_view_matches_the_known_equipment() -> None:
    equipment = Equipment(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7)
    width, height = equipment.field_of_view_deg()
    assert width == pytest.approx(_fov_axis(23.5, 600.0), abs=1e-9)
    assert height == pytest.approx(_fov_axis(15.7, 600.0), abs=1e-9)
    # The short edge is the smaller axis (here the height).
    assert equipment.fov_short_deg == pytest.approx(height, abs=1e-9)
    assert equipment.fov_short_deg <= width


def test_reducer_below_one_widens_the_field() -> None:
    plain = Equipment(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7)
    reduced = Equipment(
        focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7, reducer=0.8
    )
    plain_w, plain_h = plain.field_of_view_deg()
    reduced_w, reduced_h = reduced.field_of_view_deg()
    assert reduced_w > plain_w
    assert reduced_h > plain_h


def test_barlow_above_one_narrows_the_field() -> None:
    plain = Equipment(focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7)
    barlow = Equipment(
        focal_length_mm=600.0, sensor_width_mm=23.5, sensor_height_mm=15.7, reducer=2.0
    )
    assert barlow.fov_short_deg < plain.fov_short_deg


def test_field_of_view_is_deterministic_and_offline() -> None:
    equipment = Equipment(
        focal_length_mm=800.0, sensor_width_mm=36.0, sensor_height_mm=24.0, reducer=0.8
    )
    with no_network():
        first = equipment.field_of_view_deg()
        second = equipment.field_of_view_deg()
    assert first == second


# --------------------------------------------------------------------------- #
# The README's fuller pier example uses the `equipment` key (#68)
# --------------------------------------------------------------------------- #

_ROOT = Path(__file__).resolve().parent.parent


def _readme_fuller_pier_example() -> list[object]:
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(
        r"A fuller pier uses the optional settings:\s*```yaml\n(.*?)```", readme, re.S
    )
    assert match, "README lost its fuller pier example"
    piers: list[object] = yaml.safe_load(match.group(1))["piers"]
    return piers


def test_the_readme_fuller_pier_example_loads_with_equipment(tmp_path: Path) -> None:
    # The example's horizon file is relative to the config file, so give it one.
    (tmp_path / "horizons").mkdir()
    shutil.copy(
        _ROOT / "tests" / "fixtures" / "nina_horizon.hrz", tmp_path / "horizons" / "backyard.hrz"
    )
    valid = validate_piers(_readme_fuller_pier_example(), base_dir=tmp_path)
    assert len(valid) == 1
    assert valid[0].equipment is not None
