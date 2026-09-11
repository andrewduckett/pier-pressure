"""Tasks 1.x–3.x: the canonical horizon representation, query, and importers."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from pierpressure.core.horizon import (
    ALTITUDE_DECIMALS,
    Horizon,
    flat,
    from_points,
    open_sky,
    parse_horizon_text,
    parse_nina,
)

# --------------------------------------------------------------------------- #
# 1.1 / 1.2 — building the immutable Horizon value
# --------------------------------------------------------------------------- #


def test_samples_are_sorted_by_azimuth() -> None:
    horizon = Horizon.from_samples([(270, 25), (10, 40), (180, 5)])
    azimuths = [az for az, _ in horizon.samples]
    assert azimuths == sorted(azimuths)
    assert azimuths == [10.0, 180.0, 270.0]


def test_altitudes_are_rounded_to_fixed_precision_at_construction() -> None:
    horizon = Horizon.from_samples([(10, 40.1234567)])
    assert horizon.samples[0][1] == round(40.1234567, ALTITUDE_DECIMALS)


def test_duplicate_azimuth_with_equal_rounded_altitude_is_dropped() -> None:
    # Two altitudes that differ only by sub-precision noise round equal -> one sample.
    horizon = Horizon.from_samples([(90, 30.0), (90, 30.00001)])
    assert len(horizon.samples) == 1
    assert horizon.samples[0] == (90.0, 30.0)


def test_duplicate_azimuth_with_conflicting_altitude_raises() -> None:
    with pytest.raises(ValueError):
        Horizon.from_samples([(90, 30.0), (90, 45.0)])


def test_at_least_one_sample_is_required() -> None:
    with pytest.raises(ValueError):
        Horizon.from_samples([])


# --------------------------------------------------------------------------- #
# 1.3 / 1.4 — alt_at(az): interpolation, wrap, single-sample, normalization
# --------------------------------------------------------------------------- #


def test_a_sampled_azimuth_returns_its_own_altitude() -> None:
    horizon = Horizon.from_samples([(10, 40), (180, 5), (270, 25)])
    assert horizon.alt_at(180) == 5.0


def test_altitude_between_samples_is_linearly_interpolated() -> None:
    horizon = Horizon.from_samples([(0, 0), (100, 50)])
    assert horizon.alt_at(50) == 25.0


def test_interpolation_wraps_across_the_360_0_boundary() -> None:
    # Between 350 (alt 60) and 10 (alt 20): a 20-degree arc across the seam.
    horizon = Horizon.from_samples([(10, 20), (350, 60)])
    # az 0 is the midpoint of that wrap arc.
    assert horizon.alt_at(0) == 40.0


def test_sparse_samples_interpolate_across_north_rather_than_leaving_a_gap() -> None:
    # Spec scenario: [170,40] and [190,40] -> az 0 reads 40 via the wrap arc.
    horizon = Horizon.from_samples([(170, 40), (190, 40)])
    assert horizon.alt_at(0) == 40.0


def test_a_single_sample_horizon_is_flat_everywhere() -> None:
    horizon = Horizon.from_samples([(123, 17)])
    for az in (0, 45, 123, 200, 359.9):
        assert horizon.alt_at(az) == 17.0


def test_input_azimuth_of_exactly_360_behaves_as_zero() -> None:
    horizon = Horizon.from_samples([(0, 10), (180, 40)])
    assert horizon.alt_at(360) == horizon.alt_at(0) == 10.0


def test_the_queried_altitude_is_rounded_to_the_fixed_precision() -> None:
    # A slope whose interpolated value has a long fractional tail is rounded.
    horizon = Horizon.from_samples([(0, 0), (3, 1)])
    value = horizon.alt_at(1)  # 1/3 -> 0.333...
    assert value == round(1.0 / 3.0, ALTITUDE_DECIMALS)
    # No unrounded float leaks through.
    assert not math.isclose(value, 1.0 / 3.0)


# --------------------------------------------------------------------------- #
# 1.5 — above/below classification
# --------------------------------------------------------------------------- #


def test_a_point_higher_than_the_terrain_is_above() -> None:
    horizon = Horizon.from_samples([(0, 20), (180, 20)])
    assert horizon.is_above(90, 25.0) is True


def test_a_point_lower_than_the_terrain_is_below() -> None:
    horizon = Horizon.from_samples([(0, 20), (180, 20)])
    assert horizon.is_above(90, 15.0) is False


def test_a_grazing_point_exactly_on_the_terrain_is_above() -> None:
    horizon = Horizon.from_samples([(0, 20), (180, 20)])
    assert horizon.is_above(90, 20.0) is True


# --------------------------------------------------------------------------- #
# 2.1 — flat floor and default open sky
# --------------------------------------------------------------------------- #


def test_a_flat_floor_applies_in_every_direction() -> None:
    horizon = flat(30)
    for az in (0, 90, 180, 270, 359):
        assert horizon.alt_at(az) == 30.0


def test_open_sky_is_flat_zero_everywhere() -> None:
    horizon = open_sky()
    for az in (0, 90, 180, 270, 359):
        assert horizon.alt_at(az) == 0.0


@pytest.mark.parametrize("bad", [-1.0, 91.0])
def test_a_flat_floor_out_of_range_is_rejected(bad: float) -> None:
    with pytest.raises(ValueError):
        flat(bad)


# --------------------------------------------------------------------------- #
# 2.2 — inline points builder and validation
# --------------------------------------------------------------------------- #


def test_unordered_points_are_accepted_and_ordered() -> None:
    horizon = from_points([(270, 25), (10, 40), (180, 5)])
    assert [az for az, _ in horizon.samples] == [10.0, 180.0, 270.0]


@pytest.mark.parametrize(
    "pair",
    [(-1, 10), (361, 10), (10, -1), (10, 91)],
)
def test_an_out_of_range_pair_is_rejected(pair: tuple[float, float]) -> None:
    with pytest.raises(ValueError):
        from_points([pair])


def test_azimuth_360_normalizes_to_zero_and_deduplicates() -> None:
    horizon = from_points([(0, 20), (360, 20)])
    assert [az for az, _ in horizon.samples] == [0.0]


def test_azimuth_360_conflicting_with_zero_is_rejected() -> None:
    with pytest.raises(ValueError):
        from_points([(0, 20), (360, 45)])


def test_at_least_one_point_is_required() -> None:
    with pytest.raises(ValueError):
        from_points([])


_NINA_FIXTURE = Path(__file__).parent / "fixtures" / "nina_horizon.hrz"

# The inline pairs equivalent to the committed fixture (its 360 closer folds onto
# the 0 sample, deduplicated because their altitudes are equal).
_NINA_EQUIVALENT_POINTS = [
    (0, 12),
    (45, 18),
    (90, 25),
    (135, 30),
    (180, 22),
    (225, 15),
    (270, 20),
    (315, 16),
]


# --------------------------------------------------------------------------- #
# 3.1 — a real NINA .hrz fixture imports to the equivalent horizon
# --------------------------------------------------------------------------- #


def test_nina_fixture_imports_to_the_equivalent_inline_points_horizon() -> None:
    imported = parse_nina(_NINA_FIXTURE.read_text(encoding="utf-8"))
    equivalent = from_points([(float(a), float(b)) for a, b in _NINA_EQUIVALENT_POINTS])

    assert imported.samples == equivalent.samples
    # Queries agree at samples, between samples, and across the wrap seam.
    for az in (0, 45, 90, 135, 180, 225, 270, 315, 22.5, 300, 350, 360):
        assert imported.alt_at(az) == equivalent.alt_at(az)


# --------------------------------------------------------------------------- #
# 3.2 — NINA text parser edge cases
# --------------------------------------------------------------------------- #


def test_nina_ignores_blank_and_comment_lines() -> None:
    text = """
# NINA custom horizon
0 20

   # indented comment
180 40
"""
    horizon = parse_nina(text)
    assert horizon.alt_at(0) == 20.0
    assert horizon.alt_at(180) == 40.0


def test_nina_normalizes_360_and_clamps_sub_horizon_altitude() -> None:
    text = "0 20\n90 -5\n360 20\n"
    horizon = parse_nina(text)
    assert horizon.alt_at(90) == 0.0  # -5 clamped to 0
    assert [az for az, _ in horizon.samples] == [0.0, 90.0]  # 360 deduped against 0


def test_nina_malformed_line_raises() -> None:
    with pytest.raises(ValueError):
        parse_nina("0 20\nnot-a-pair\n")


# --------------------------------------------------------------------------- #
# 3.3 — format registry
# --------------------------------------------------------------------------- #


def test_registry_parses_nina() -> None:
    horizon = parse_horizon_text("nina", "0 20\n180 40\n")
    assert horizon.alt_at(0) == 20.0


@pytest.mark.parametrize("fmt", ["stellarium", "telescopius"])
def test_recognized_but_unsupported_formats_raise_clearly(fmt: str) -> None:
    with pytest.raises(ValueError, match="not yet supported"):
        parse_horizon_text(fmt, "0 20\n")


def test_unknown_format_raises() -> None:
    with pytest.raises(ValueError):
        parse_horizon_text("nonsense", "0 20\n")
