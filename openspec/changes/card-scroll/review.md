## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini, `gemini-4-argon`, through `lets delegate review run` on the t3 resolver)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `09cff75`

## Findings

### 🔴 Critical (blocking)

1. **Pointer capture on the strip swallows a press on the nested "Back to tonight" button** (contradictions, test seams). The button sat in the strip's top-left cell, and the strip captured every primary `pointerdown`, so a real browser sends the `click` to the strip, not the button. happy-dom does not retarget captured events, so the tests would pass. Activating the button by keyboard also dropped focus to the page. — **CONFIRMED.**
2. **Dusk and dawn lines are never checked against the axis** (contradictions). `nightLines` in `card/src/strip.ts` emits both lines whatever the axis, and the main spec's "Dusk and dawn lines mark the dark window" requires them whenever `dark_window` is valid. That contradicts the delta's "The next night" scenario, and a panned dusk line would draw over the row labels. design.md's Context wrongly said lines were already cut off. — **CONFIRMED.**
3. **Counting null points, and shifting every Rain chance point back an hour, adds a blank hour before the timeline** (contradictions). `timeline_attributes` in `pierpressure/delivery/mqtt.py` pads every sensor's `forecast` with nulls across all timeline hours, so a null Rain chance point at the first hour would start the reach an hour early. The requirement's "earliest hour any row fills" also disagreed with "whatever the point's value". — **CONFIRMED.**
4. **"Scrolling past the card on a phone" is untestable, and a vertical swipe pans the strip before the browser cancels it** (scenario testability). "The page scrolls" is not observable in happy-dom. A phone browser sends a few `pointermove`s before `pointercancel`, and the design panned on each with no threshold and no restore. A slipping tap had the same problem. — **CONFIRMED.**

### 🟡 Moderate

5. **The button in the top-left cell widens the label column and grows the first row mid-drag** (contradictions). The grid's first column is `max-content` and its rows `auto`, so the button resizes both, and the hours' width changes after the drag recorded it. — **CONFIRMED.**
6. **A pan the reach stops entirely still arms `heldStart`** (assumption rows, D11). On a night with no darkness, the next minute's redraw then freezes the axis and shows the button unprompted. — **CONFIRMED.**
7. **A second finger overwrites the drag's origin** (contradictions). Every touch contact has `button === 0`; the design tracked no `pointerId` and ignored `lostpointercapture`. — **CONFIRMED.**
8. **Ledger D4 had no support, and the design and spec disagreed on a panned axis's length when the opening axis changes length** (assumption rows, contradictions). — **CONFIRMED.**

### 📌 Suggestions

9. **Three words for one concept** ("view", "visible span", "axis"), an inaccurate D13, and sentences over 30 words in spec.md, adr.md, brainstorm.md and design.md (plain language). — **CONFIRMED.**
10. **Panning to a later night shows "No forecast" on rows past a weather source's horizon** (scope, docs). Open-Meteo asks for 2 days (`pierpressure/conditions/open_meteo.py`, `forecast_days: 2`), 7Timer! gives 3, so the docs' "No forecast" help would send users to debug a healthy provider. — **CONFIRMED.**

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: REVISE

## Required Changes (if APPROVE_WITH_CHANGES)

None: the verdict is REVISE. The plan was revised as the rebuttals say, for a new round.

CHANGES_APPLIED: n/a

## Rebuttals

1. Fixed. design.md D-8 moves the button to its own line above the strip, outside `.strip`. D-5 captures the pointer only once a drag has started. The spec's "A Back to tonight button returns the strip to the opening axis" adds "Pressing the button does not pan" and moves focus to the strip.
2. Fixed. The delta modifies "Dusk and dawn lines mark the dark window": each line shows only while its time is on the axis, with the "Dusk panned off the axis" scenario. design.md D-4 passes the axis to `nightLines`, and Context is corrected.
3. Fixed. "The reach counts every row's forecast" now defines a timeline hour by its point, and counts the hour before only for a Rain chance point with a number, with the "A null Rain chance at the first hour" scenario. design.md D-3 matches.
4. Fixed. The new requirement "A small or cancelled gesture pans nothing" has testable scenarios: a slipping tap, a cancelled swipe and a mostly vertical drag. design.md D-5 adds the 8 px threshold and restores the axis on `pointercancel`. Ledger D16 records the decision.
5. Fixed. design.md D-8: the button's line is always laid out, hidden with `visibility: hidden`, and at least 24 px tall. D-5 records the hours' width at `pointerdown`.
6. Fixed. design.md D-2: a pan clamps first, and a pan that moves nothing changes nothing. The spec adds "A pan against the reach's start".
7. Fixed. The new requirement "One pointer drags the strip at a time"; design.md D-5 tracks one `pointerId` and handles `lostpointercapture`.
8. Fixed. Ledger D4 cites #189 and #173. The spec says the axis is always as long as the opening axis, with "A new night of another length"; design.md D-2 says why.
9. Fixed. brainstorm.md, proposal.md and design.md now say "axis", "opening axis" and "reach" only, and D13 is corrected. The long spec sentences are split.
10. Fixed. Ledger D14 and the spec's docs requirement add the "No forecast" cause past a weather source's last hour.
