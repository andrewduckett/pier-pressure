## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family
- **Independent**: yes. gemini/gemini-3.8-flash reviewed through the t3 resolver; the author is Claude.
- **Tool restrictions**: read-only. The resolver reported a clean working tree after the review.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md at commit 3578899; the main spec `openspec/specs/night-card/spec.md`; `openspec/glossary.md`; the tests named in design.md Decision 2

## Findings

### 🔴 Critical (blocking)

1. **The split narrows the condition on "SHALL NOT throw".** CONFIRMED. The original says, with no condition, that the card SHALL NOT throw and SHALL draw the other rows. The ADDED "A missing Moon altitude or weather sensor does not stop the other rows" put a "When a row's sensor is missing, unavailable or has no `forecast` list" clause in front of it. That drops the guarantee for an available sensor with an unreadable `datetime`, against epic #230 decision 3 and brainstorm D7. Check: lost or changed SHALL.

### 🟡 Moderate

2. **"Each of the four cloud rows reads its cloud sensor" does not say which row reads which sensor.** CONFIRMED. Read on its own, it names neither the four rows nor their mapping to the four sensors. Check: one behavior, reads on its own. The reviewer also notes that the added scenario asserts only Cloud high: REFUTED as a defect, see Rebuttals.
3. **Skipping an unreadable point and not throwing are two behaviors in one requirement.** REFUTED, see Rebuttals. Check: one behavior.
4. **"Before the first verdict" does not fit "The strip opens on the opening axis".** REFUTED, see Rebuttals. Check: lost or changed scenario (placement).

### 📌 Suggestions

5. **The heading "An earlier pan keeps its start as the opening axis moves on" says "moves on" where the SHALL says "moves away from it".** Accepted. Check: plain language, two words for one concept.
6. **The lead sentence of "The cloud rows come under Moon altitude" has 36 words.** Accepted. Check: plain language.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

The reviewer answered REVISE because of Finding 1. Each confirmed finding is fixed by a small, unambiguous edit listed below, so the verdict that follows from the findings is APPROVE_WITH_CHANGES.

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. In specs/night-card/spec.md, rename "A missing Moon altitude or weather sensor does not stop the other rows" to "Missing or unreadable Moon altitude or weather data does not stop the other rows". Make its "SHALL NOT throw, and SHALL draw the other rows as usual" hold whether a sensor is missing, unavailable or has no `forecast` list, or a point has no readable `datetime` (Finding 1).
2. In "Each of the four cloud rows reads its cloud sensor", name the rows: "The Cloud cover, Cloud low, Cloud mid and Cloud high rows SHALL each read ...", and end the sensor list with "in that order" (Finding 2).
3. Rename "An earlier pan keeps its start as the opening axis moves on" to "An earlier pan keeps its start as the opening axis moves away from it" (Suggestion 5).
4. In "The cloud rows come under Moon altitude", split the lead sentence in two: "the card SHALL draw the four cloud rows. After Cloud cover, the card SHALL draw the Cloud range row, unless ..." (Suggestion 6).
5. In design.md Decision 4 and Risks, record changes 1, 2 and 4, and the SHALL count they give: 30 in the ADDED requirements, against 28 in the originals.

CHANGES_APPLIED: yes

## Rebuttals

1. **Finding 1** — fixed by Required Change 1. `openspec validate split-long-reqs-night-card --strict` passes after the edit.
2. **Finding 2** — fixed by Required Change 2. The part about the scenario is rebutted: the moved scenario "The rows and their sensors" asserts all four sensors (main spec, lines 194–197), and it stays under "The cloud rows come under Moon altitude" because its THEN is the order (design.md Decision 3). The added scenario is one example, which `card/test/strip.test.ts` "reads the cloud sensors named from the pier" asserts.
3. **Finding 3** — rebutted. After Required Change 1 the requirement states one behavior: bad input from these sensors never stops the card, and skipping an unreadable point is how it keeps drawing. A requirement of its own for skipping would need an added scenario, and no test asserts skipping for these rows (`card/test/rows.test.ts` has none; `card/test/strip.test.ts` line 335 tests only Cloud low, which another requirement covers). Brainstorm D3 adds a scenario only where an existing test asserts it. The new heading now names both cases.
4. **Finding 4** — rebutted. The scenario's THEN is "the card still draws the strip, with its axis from ...", with no pan: the strip opens, on the opening axis. Its values come from the fallback, as do "A night with no astronomical darkness" and "A window that ends before it starts", which sit with the start-and-length requirement. The "until a pan, and after `Back to tonight`" half is also asserted by the scenarios of "A Back to tonight button returns the strip to the opening axis" (main spec, "Going back" and "Going back after the night has moved on", lines 1500–1508), which this change keeps.
5. **Suggestion 5** — fixed by Required Change 3.
6. **Suggestion 6** — fixed by Required Change 4.
