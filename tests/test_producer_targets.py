"""Task 5.1: filling ``targets`` is additive — no other document field changes.

For each golden case, the verdict is produced with the new ranking wired in, then
its ``targets`` are emptied and the result is compared to a frozen baseline
captured from the pre-change goldens. If any of ``verdict``, ``score``,
``confidence``, ``reasons``, ``dark_window``, or ``moon`` drifted, the baseline
comparison fails — so the additive-only claim (ADR-0009) is guarded byte for byte.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pierpressure.conditions.provider import assemble_snapshot
from pierpressure.core.clock import FixedClock
from pierpressure.core.config import PierConfig
from pierpressure.core.producer import produce_verdict

from .conftest import make_conditions
from .offline_guard import no_network
from .test_golden_verdict import _CASES, _INSTANT, _base_full, _secondary_full

_RIG = {"focal_length_mm": 600.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7}

_STUB = Path(__file__).parent / "fixtures" / "golden" / "stub"


@pytest.mark.parametrize("case", sorted(_CASES))
def test_filling_targets_leaves_other_fields_byte_identical(case: str) -> None:
    pier, base, secondary = _CASES[case]()
    conditions = assemble_snapshot(base, secondary)
    with no_network():
        document = produce_verdict(pier, FixedClock(_INSTANT), conditions)

    # Everything except targets must equal the pre-change stub byte for byte.
    without_targets = document.model_copy(update={"targets": []}).to_json()
    baseline = (_STUB / f"{case}.json").read_text(encoding="utf-8").rstrip("\n")
    assert without_targets == baseline


def _rig_pier() -> PierConfig:
    return PierConfig(id="backyard", latitude=51.5, longitude=-0.12, elevation_m=30.0, rig=_RIG)  # type: ignore[arg-type]


def test_a_rig_pier_emits_an_equipment_reason_for_the_top_pick() -> None:
    # Task 5.4: with a rig and a top pick that has a known size, the reasons carry
    # an additive framing entry naming that top pick, alongside the score terms.
    conditions = assemble_snapshot(_base_full(), _secondary_full())
    with no_network():
        document = produce_verdict(_rig_pier(), FixedClock(_INSTANT), conditions)
    assert document.targets
    top = document.targets[0]
    assert top.size_arcmin is not None  # the top pick has a framed size
    name = top.name or top.id
    framing = [r for r in document.reasons if name in r and "rig" in r.lower()]
    assert framing, document.reasons


def test_a_gated_no_go_carries_no_equipment_reason() -> None:
    # A fully-overcast night is a gated NO-GO (null score) but still has a dark
    # window, so targets are ranked. The reasons must name the failing gate and
    # NOT advertise the top pick's equipment suitability for a night ruled out.
    from pierpressure.core.model import Verdict

    overcast = make_conditions(cloud=100.0, issued_at=_INSTANT)
    with no_network():
        document = produce_verdict(_rig_pier(), FixedClock(_INSTANT), overcast)
    assert document.verdict is Verdict.NO_GO
    assert document.score is None
    assert document.targets  # targets are still ranked for the night
    assert not any("Top pick" in r for r in document.reasons), document.reasons


def test_equipment_reasons_are_deterministic() -> None:
    conditions = assemble_snapshot(_base_full(), _secondary_full())
    with no_network():
        first = produce_verdict(_rig_pier(), FixedClock(_INSTANT), conditions).reasons
        second = produce_verdict(_rig_pier(), FixedClock(_INSTANT), conditions).reasons
    assert first == second


def test_targets_are_actually_populated_when_a_night_exists() -> None:
    # The additive test strips targets, so this guards that the fill really runs:
    # the London night in the golden cases yields a non-empty ranked list.
    pier, base, secondary = _CASES["both_present"]()
    conditions = assemble_snapshot(base, secondary)
    with no_network():
        document = produce_verdict(pier, FixedClock(_INSTANT), conditions)
    assert document.targets
    assert all(0 <= t.score <= 100 for t in document.targets)
