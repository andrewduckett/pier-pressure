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
from pierpressure.core.producer import produce_verdict

from .offline_guard import no_network
from .test_golden_verdict import _CASES, _INSTANT

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


def test_targets_are_actually_populated_when_a_night_exists() -> None:
    # The additive test strips targets, so this guards that the fill really runs:
    # the London night in the golden cases yields a non-empty ranked list.
    pier, base, secondary = _CASES["both_present"]()
    conditions = assemble_snapshot(base, secondary)
    with no_network():
        document = produce_verdict(pier, FixedClock(_INSTANT), conditions)
    assert document.targets
    assert all(0 <= t.score <= 100 for t in document.targets)
