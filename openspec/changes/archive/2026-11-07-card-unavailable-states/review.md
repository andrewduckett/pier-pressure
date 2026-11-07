## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through `lets delegate review run`; the plan's author is Claude)
- **Independent**: yes. `lets delegate` gave up after 900000 ms (exit 6) while the review was still running, and left the raw file empty. The review then finished in its T3 thread, c4dc33a6-04be-4c3b-b1c2-b402c218d7f3, and its findings were recovered from that thread's final message. It was not run again.
- **Tool restrictions**: read-only, plan mode: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit f5b61ad

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The message's CSS fails in a real browser, and no check renders it** (check: contradictions, test seams). design.md DD3 styled an inline span with a 4 px indent. `text-indent` does nothing on an inline box, and the track has no line height of its own, so the text would sit low and could wrap. Vitest's `happy-dom` computes no layout, and D16 only stopped PierPressure, which draws no strip. CONFIRMED.
2. **The plan misstates when a real run shows "No forecast"** (check: Assumption rows). When every weather source fails, the core still publishes a verdict, but the timeline is empty, so all fifteen rows say "No forecast" beside a live verdict (`pierpressure/core/producer.py`, `_timeline`). A provider without a condition, or a short-range run, also leaves a row with no value. The design's risk list blamed only a stale state, so the docs would have missed the health sensors and the `providers` setting. CONFIRMED.
3. **Scenarios leave clauses unasserted or contradictory** (check: scenario testability). (a) The docs scenario let troubleshooting bullets alone satisfy the strip-section clause. (b) No scenario asserted the Moon up lane's hover text. (c) "The moon stays down" was also true of an empty forecast, which must say "No forecast". (d) The note's place was asserted only as "above the strip". (e) "A null hour is blank" conflicts with a row of nulls now showing a message. (a) to (d) CONFIRMED. (e) REFUTED, see Rebuttals.

### 📌 Suggestions

4. **Plain language** (check: ISO 24495). Several sentences ran over 30 words, the darkness requirement's heading was passive, and the note's place had four names. CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md DD3: make `.missing` a block sized to its text, with `padding-left: 4px`, no wrapping and an ellipsis. brainstorm.md D16: check a row message and the darkness note in the dashboard check's Home Assistant, through **Developer Tools** > **States**.
2. design.md Risks, and the docs requirements in specs/: name both causes of "No forecast", and point the docs to the health sensors and the `providers` setting.
3. specs/: split the docs requirement into the strip section and the troubleshooting section, each with its own scenario; assert the Moon up lane's hover text; give "The moon stays down" a value on the axis; assert that the note comes after the confidence and before the strip.
4. specs/, proposal.md, brainstorm.md: split the long sentences, name the darkness requirement actively, and call the note's place "between the confidence and the strip" everywhere.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed. design.md DD3 gives the full `.missing` rule as a block with `width: fit-content`, `max-width: 100%`, `padding-left: 4px`, `white-space: nowrap` and `text-overflow: ellipsis`. brainstorm.md D16 now checks a row message, the note and the offline message by eye.
2. Fixed. design.md Risks names the all-sources-failed case, the provider-coverage case and the first-install case. specs/ adds "The docs name the causes of No forecast", which asks for the health sensors and the `providers` setting.
3. (a) to (d) fixed in specs/night-card/spec.md: "The docs describe the row messages and the darkness note" and "The docs say what to do when something is missing" replace the single docs requirement; "The moon sensor is not there" asserts the hover; "The moon stays down" holds a value on the axis; "A summer night far north" asserts the note's place. (e) rebutted: "A null hour is blank" (`openspec/specs/night-card/spec.md`, lines 244 to 266) requires only that the card draws no cell for the hour. A message in the track is not a cell, and a row of nulls still draws none. The tests in `card/test/rows.test.ts`, lines 333 to 365, assert only the missing cell, so they still pass. design.md Test Seams now says so.
4. Fixed: the requirement is now "The card notes a night with no astronomical darkness"; the long MODIFIED sentences are split; proposal.md and brainstorm.md D10 use "between the confidence and the strip".
