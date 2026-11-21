**Why:** The target-ranking spec leaves out the "is a bright target" sentence and the one-hour scored-window guard that the code already applies, so the spec no longer describes every "Top pick" sentence the verdict can carry.

## Story

#274 top-pick-sentences-drift — the target-ranking spec covers the bright-target sentence and the short-window case
https://github.com/andrewduckett/pier-pressure/issues/274

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What is in scope? | Spec the bright-target sentence and the short-window guard, and add a test for the bright-target sentence, written first. The code's sentences and the framing sentences' wording stay as they are. | Evidence: #274 issue body (Scope) |
| D2 | How does the spec say when the top pick counts as bright? | By the same brightness judgment the ranking uses, with no numbers, as the frames-well requirement refers to the ranking's field-of-view fit. Scenarios use clear cases: Pleiades is bright, Andromeda Galaxy is not. | Assumption |
| D3 | Does the bright-target sentence get its own requirement, or widen the framing one? | Its own requirement, "A bright top pick gets the bright-target sentence". It holds when the verdict passes its gates, the target list is not empty, the scored window is at least one hour, and the top pick is a catalog object whose brightness is known and counts as bright. It needs no equipment, names the top pick by name, else designation, comes after the framing sentence when both appear, and changes no other reason. | Assumption |
| D4 | Which scenarios does the bright-target requirement get? | Three: a bright pick with no equipment gets only the bright sentence; a bright pick with equipment gets the framing sentence, then the bright sentence; a faint pick (Andromeda Galaxy) gets no bright sentence. | Assumption |
| D5 | How does the spec cover the short-window case? | Add "the scored window is at least one hour (`MIN_USABLE_WINDOW`)" to the conditions of "The verdict gets one framing sentence about the top pick", with a scenario: under one hour, no sentence starts "Top pick". Today a window that short always has an empty target list, so the spec states it as a guard, not a separate observable case. | Assumption |
| D6 | Does the short-window scenario need a new test? | No. `test_a_window_not_worth_setting_up_for_carries_no_equipment_reason` in `tests/test_producer_targets.py` already asserts it. | Evidence: tests/test_producer_targets.py |
| D7 | Where does the bright-target test go, and how is it shown to fail? | Unit tests on `equipment_reasons` in `tests/test_ranking_suitability.py`, using Pleiades (`Mel022`). With no equipment the result is exactly `["Top pick Pleiades is a bright target."]`; with equipment, the framing sentence comes first, then the bright sentence. The code already emits it, so the build briefly disables the bright branch, watches the test fail, then restores the code. | Assumption |

## Changes from the story

None.

Confirmed by user: yes
