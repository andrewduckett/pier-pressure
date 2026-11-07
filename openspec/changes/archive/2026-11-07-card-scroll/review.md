## Review Metadata

- **Review round**: 2
- **Prior round**: round 1 (gemini-4-argon, at `09cff75`) gave REVISE with four Critical findings: the button inside the strip lost its click to pointer capture, dusk and dawn lines ignored the axis, the reach gained a blank hour, and touch slop panned the strip. All ten findings were fixed in `699c686`.
- **Reviewer context**: fresh context, other family (gemini, `gemini-3.8-flash`, through `lets delegate review run` on the t3 resolver). `gemini-4-argon` was tried first and refused on quota. `lets delegate` then logged "the session stopped to ask (thread ab986af4-0ffc-4db8-b937-5f5a773d4b4a)" and left the raw file empty. The review had finished: its findings were recovered from that thread's final message.
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, review.md (round 1), relevant source files, at commit `699c686`

## Findings

The reviewer confirmed round 1's findings 1, 2, 4, 5, 7, 8 and 10 fixed, and findings 3, 6 and 9 partly fixed, as findings 3, 1 and 5 below say.

### 🔴 Critical (blocking)

1. **Panning back to the opening axis by hand leaves `heldStart` set** (contradictions, D11). After Right then Left, the axis is on the opening start but `heldStart` holds a number. On a night with no darkness the next minute's redraw freezes the axis and shows "Back to tonight"; on a normal night, the next day's `dark_window` would not move the axis. design.md D-2. — **CONFIRMED.**

### 🟡 Moderate

2. **A change of pier keeps the old pier's `heldStart`** (contradictions, D3). Round 1's design noted a reset in `setConfig`; the revision dropped it, and no spec says it. — **CONFIRMED.**
3. **The reach counts the hour after a Rain chance point** (contradictions). The spec counted every point's own hour and, for Rain chance, also the hour before. A Rain chance point fills only the hour before its time. Harmless while every sensor shares the timeline's hours (`pierpressure/delivery/mqtt.py`, `timeline_attributes`), but the rule was wrong. — **CONFIRMED.**
4. **"Pressing the button does not pan" needs a `click` the test must send** (scenario testability). happy-dom does not turn pointer events into a click. — **CONFIRMED**, as a note on the test seam and the scenario's wording.

### 📌 Suggestions

5. **Sentences over 30 words remain** in adr.md, the spec's fallback list intro, design.md, brainstorm.md and proposal.md (plain language). — **CONFIRMED** for adr.md; the others are declined in the rebuttals.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

The reviewer wrote REVISE. Each open finding, the Critical included, is fixed by a small, unambiguous edit listed below, so the verdict is APPROVE_WITH_CHANGES. No third round is needed.

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md D-2: a pan whose clamped start equals the opening axis's start sets `heldStart` to `undefined`. The spec's "The strip stays where the user panned it" says a pan back to the opening axis counts as selecting `Back to tonight`, with the scenario "Panning back by hand".
2. design.md D-2: `setConfig` sets `heldStart` to `undefined` when the pier changes. The same requirement gains the scenario "A new pier".
3. The spec's "The reach counts every row's forecast" and design.md D-3: a Rain chance point counts only when it holds a number, and only for the hour before its time.
4. design.md Test Seams: the button test sends the pointer events, then a `click`. The scenario "Pressing the button does not pan" says the browser clicks the button.
5. adr.md: split the 51-word summary sentence.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: required change 1.
2. Fixed: required change 2.
3. Fixed: required change 3.
4. Fixed: required change 4.
5. Fixed for adr.md (required change 5). Declined for the rest. The spec's fallback sentence is the main spec's own wording, kept word for word so the MODIFIED requirement changes only what it must; it introduces a list, which is the plain-language remedy for a long sentence. The design.md, brainstorm.md and proposal.md sentences flagged run 33 to 40 words and are each one condition and one outcome; splitting them would separate a rule from its reason.
