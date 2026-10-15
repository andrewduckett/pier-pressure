## Why

A mostly cloudy night can still score about 30 and read `MAYBE`. On 2026-10-13
the pier at 42.23, −87.88 got `MAYBE`, 31, while it rained under cloud all night.

Two faults in the score cause this. First, seeing and transparency add to the
score with a fixed 30% weight, even when almost no sky is clear. They describe
how good the clear sky is, not how much of it there is. Second, the score always
covers the whole night, from dusk to dawn. Hours that have already passed still
count, so a clear evening keeps a socked-in rest of the night afloat.

Issue: #97. Issue #98 (rain) builds on this change.

## What Changes

- **Seeing and transparency scale the cloud term instead of adding to it.** The
  score becomes the usable-sky term multiplied by an atmosphere factor, then by
  the existing moon and high-cloud factors. The atmosphere factor runs from 0.7
  for the worst seeing and transparency to 1.0 for the best. When both are
  missing, the factor is 1.0 and confidence drops, as it does today. The night
  in the issue would score about 14 instead of 32.
- **Once the night has started, the verdict judges the rest of the night.** The
  score, the overcast gate, the wind gate, and the completeness part of
  confidence all cover the span from the evaluation instant to dawn. Before
  dusk, that span is the whole night, so nothing changes until the night begins.
  The night in the issue would score about 3 at 21:52 local time.
- **`dark_window` keeps the whole night.** Its meaning does not change. A new
  additive `scored_window` field, with the same `{ start, end }` shape, reports
  the span the verdict judged. Before dusk the two are equal.
- **The reasons name the scored span.** Once the night has started, the cloud
  reason says the usable share is of the remaining night, and a new reason line
  states the span judged.
- **A verdict at dawn scores zero usable time.** When the evaluation instant
  lands on dawn, the remaining span is empty. The verdict reports no usable
  sky left rather than "conditions unavailable".

Out of scope:

- Target ranking. The ranked list still judges the whole night. Issue #110
  covers ranking the rest of the night.
- Rain. Issue #98 adds precipitation as a separate change on top of this one.
- Any change to the clarity curve, the moon penalty, or the high-cloud penalty.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: the score combines seeing and transparency as a factor on the
  usable-sky term; the gates, score, and completeness judge the remaining night
  once it has started; the document gains `scored_window`; the reasons name the
  scored span.

## Impact

- **Changed code:** `pierpressure/core/scoring.py` (the score assembly, the
  window the gates and score use, the reasons), `pierpressure/core/producer.py`
  (the new field), `pierpressure/core/model.py` (the new field).
- **Changed documents:** every scored verdict changes. The golden fixtures under
  `tests/fixtures/golden/expected/` are regenerated as a reviewed diff. A new
  decision record explains why the verdict judges the remaining night.
- **Delivery:** no change to MQTT topics, entities, or the entity mapping. The
  new field travels in the document only. Home Assistant automations that read
  `score` see lower scores on partly clear nights, and scores that fall during
  the night as clear hours pass.
- **Docs:** the README's document table gains `scored_window`.
- **Tests:** unit tests for the new score assembly and the clamped window, a
  mid-session verdict test, a dawn-instant test, and the regenerated goldens.
