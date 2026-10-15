## 1. The atmosphere factor (design D3)

- [x] 1.1 Write failing tests in `tests/test_scoring.py` for a new `atmosphere_mean` helper and the new `assemble_score`. Cover: a factor of 1 when no hour carries seeing or transparency; an hour with only one term uses that term; the issue night (cloud term 0.15, both terms 0.71, moon down, no high cloud) scores 14; a fully clear window with both terms moving from 0 to 1 scores 70 then 100; the ten-hour case scores 97, then 90 when the poor-atmosphere hour is overcast; the score never exceeds the rounded cloud term; and one half-way value rounds to the even integer. Verify they fail.
- [x] 1.2 Replace the weighted mean in `assemble_score` with the product `cloud_term × (ATMOSPHERE_FLOOR + (1 − ATMOSPHERE_FLOOR) × A) × moon factor × high-cloud factor`, with `ATMOSPHERE_FLOOR = 0.7`. Implement `A` as the coverage-and-clarity-weighted mean of each hour's `a`, where an hour without both terms has `a = 1`. Remove the three old weights. Update the module docstring. Verify the 1.1 tests pass and the rest of `tests/test_scoring.py` still passes.
- [x] 1.3 Write failing tests for the atmosphere reasons: a scored verdict carries "Atmosphere factor N%."; a seeing or transparency line adds "(covers N% of the usable sky)" when its coverage is below 100% and omits it at 100%; the nine-plus-one case reports a factor of 97% and both qualities at 0% covering 10%. Verify they fail, then add the lines in `_score_reasons` and verify they pass.

## 2. The scored window (design D1, D2)

- [x] 2.1 Write failing tests in `tests/test_verdict_eval.py` for the clamp. Cover: before dusk the decision's scored window equals the dark window; mid-session it starts at the instant floored to the second; a clear-then-overcast night is `NO-GO` after the clear hours and not before dusk; a gust in a passed hour does not gate; a wind gap in a passed hour does not cap; completeness reads the scored window. Verify they fail.
- [x] 2.2 In `evaluate`, floor the instant to a whole second, compute `scored = (min(max(now, start), end), end)`, pass `scored` to every condition rule, keep the lead-time factor on the dark window's start, and return `scored` on `Decision`. Verify the 2.1 tests pass and the existing tests in the file still pass.
- [x] 2.3 Write failing tests for the empty window and the short-window cap. Cover: an instant in the floored dawn second, and an instant exactly on the crossing, give `MAYBE`, score 0, the no-dark-time reason, and no "conditions unavailable" reason; an instant after the crossing selects the next night; in polar night the exact noon selects the next day and the second before it is empty; thirty minutes before the end caps a threshold-passing `GO` at `MAYBE` with the computed score and the short-window reason; a 50-minute whole night is capped before dusk; sixty minutes before the end with no wind limit is `GO`. Use microsecond instants for the boundary cases. Verify they fail.
- [x] 2.3a Added during apply: `_local_solar_day` in `pierpressure/core/sky.py` searched only one day either side for solar noons. In polar night near the solstice, noon drifts about 30 seconds a day, so an instant within about 30 seconds of noon found no noon on one side and raised `IndexError`. The 2.3 polar boundary tests need this to work. Write a failing test in `tests/test_sky_dark_window.py` for an instant at solar noon in polar night, then widen the search to two days either side. Verify both pass.
- [x] 2.4 Add the empty-window path after the no-dark-window gate and before the wind gate, and the `MIN_SCORED` (60 minutes) cap beside the missing-wind cap, with the reason "Less than an hour of dark time to score: not worth setting up." Verify the 2.3 tests pass.

## 3. The reasons name the span (design D4)

- [ ] 3.1 Write failing tests that, when the scored window is narrowed, the first reason is "Scored from <start> to <end> (the rest of tonight)." with both endpoints equal to the document's timestamp strings, on the scored path, both gates, the missing-cloud path, and the empty-window path. Cover the reworded lines: "Cloud: N% of the remaining night usable.", "No usably clear sky in the forecast for the rest of the night.", and "Wind gust over the N km/h limit during the rest of the night.". Cover that an instant in the dusk second and an instant before dusk keep today's wording with no span line. Verify they fail.
- [ ] 3.2 Add the span line and the narrowed wording in `pierpressure/core/scoring.py`, sharing the timestamp formatter with `pierpressure/core/model.py`. Verify the 3.1 tests pass.

## 4. The document field (design D5)

- [ ] 4.1 Write failing tests in `tests/test_producer.py` and `tests/test_model.py`: the document has `scored_window` after `dark_window`; before dusk it equals `dark_window`; mid-session its start equals `generated_at`; it is null-null without a dark window; the field round-trips through JSON. Verify they fail.
- [ ] 4.2 Add `scored_window: DarkWindow` to `VerdictDocument` and emit the decision's scored window from `produce_verdict`. Verify the 4.1 tests pass and `tests/test_determinism.py` and `tests/test_core_boundary.py` still pass.
- [ ] 4.3 Update the README's document table and the paragraph after it: describe `scored_window`, say the score and gates judge it, and say the targets still judge the whole night (issue #110). Verify by reading the rendered Markdown.

## 5. Goldens (design D6)

- [ ] 5.1 Add a mid-session golden case to `tests/test_golden_verdict.py` that runs the recorded forecasts at an instant inside the dark window. Verify it fails for want of an expected file.
- [ ] 5.2 Regenerate every golden with `PP_WRITE_GOLDENS=1 uv run pytest tests/test_golden_verdict.py` in one commit. Verify the diff shows only the expected changes: scores under the new formula, the new `scored_window` field, the atmosphere reason lines, and the mid-session span line and wording in the new case.

## 6. Verification

- [ ] 6.1 Run `just check` and verify it is green.
- [ ] 6.2 Run the core against the issue's night (42.23, −87.88, 2026-10-13, live or recorded forecasts) at a pre-dusk instant and at 21:52 CDT. Verify the pre-dusk score is about 14 and the mid-session verdict is `NO-GO` for no usably clear sky, or `MAYBE` with a single-digit score, and record both results in the PR.
