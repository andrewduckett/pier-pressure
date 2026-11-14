## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the author is claude)
- **Independent**: yes
- **Tool restrictions**: read-only; the resolver reported the working tree clean after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, docs/decisions/0037, relevant source files, at commit `58c4826`
- **Effort**: medium (design.md's scrutiny tier)

## Findings

### 🔴 Critical (blocking)

1. **The reason line sorts layers, and a null base breaks the sort.** The
   night-verdict delta said "lowest first", while null bases are kept. A
   report with `FEW030 BKN///` would make a naive sort raise `TypeError` in
   `produce_verdict`. Check: contradictions. **CONFIRMED.** Fixed by required
   change 1.
2. **`build_provider` does not wire the METAR fetcher.** `__main__.py` builds
   the stack with `build_provider`, and DD2 never said who constructs the
   fetcher. Check: test seams. **CONFIRMED** as a gap in the design, not a
   blocking defect: an unwired fetcher only means no observation. Fixed by
   required change 2.

### 🟡 Moderate

3. **`parse_metar` cannot match `icaoId` without the station.** Check:
   contradictions. **CONFIRMED.** Fixed by required change 3.
4. **A `CLR` or `SKC` entry inside `clouds` would read "CLR at an unknown
   height".** The live API returned `clouds: []` for EGLL's clear report, but
   nothing guarantees it. Check: scenario testability. **CONFIRMED** as a
   defensive gap. Fixed by required change 4.

### 📌 Suggestions

5. **No scenario covers the 204 response** that aviationweather.gov gives for
   an unknown station (design.md's Context records it). Check: scenario
   testability. **CONFIRMED.** Fixed by required change 5.
6. **Sentences over 30 words** in adr.md, proposal.md and design.md. Check:
   plain language. adr.md's summary sentence: **CONFIRMED**, fixed by
   required change 6. proposal.md lines 18–20 and design.md lines 38–41:
   **REFUTED**, see Rebuttals.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. specs/night-verdict: the reason line names layers in the order reported,
   not sorted; add a scenario with a known base then a null base. Make
   brainstorm.md D8 say "in the order reported". design.md DD4 says the
   reason never sorts.
2. design.md DD2: `build_provider` constructs the real `MetarFetcher` and
   takes a `metar` keyword that replaces it in tests.
3. design.md DD3: `parse_metar(payload, station)`; no report for the station
   raises `NoReport`.
4. specs/conditions and design.md DD3: a layer whose cover is `CLR`, `SKC`,
   `NCD` or `NSC` is left out; add a scenario.
5. specs/conditions: add a scenario for a 204 response with an empty body.
6. adr.md: split the long summary sentence.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: `specs/night-verdict/spec.md`, requirement "A usable observation
   adds one reason line that names its layers" and its new scenario "A layer
   with no base keeps its place among known bases"; `design.md` DD4;
   `brainstorm.md` D8.
2. Fixed: `design.md` DD2, last paragraph.
3. Fixed: `design.md` DD3, first bullet.
4. Fixed: `specs/conditions/spec.md`, requirement "An observation keeps cover
   codes as reported and a missing base as unknown" and scenario "A clear
   layer entry is left out"; `design.md` DD3.
5. Fixed: `specs/conditions/spec.md`, scenario "A 204 response returns no
   report".
6. Fixed for `adr.md` (Review Summary). Declined for the other two:
   proposal.md lines 18–20 hold two sentences of 18 and 8 words, and
   design.md lines 38–41 are four short bullets, none over 15 words.
