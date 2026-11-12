## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the first attempt, gemini/gemini-4-argon, stopped on a quota message and returned no review)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only (the resolver reported a clean git tree afterwards)
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0036, relevant source files, at commit 6b6a7b3

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Scenarios assert sub-score factors that `Target` does not expose.** Check: scenario testability. `specs/target-ranking/spec.md`, the three scenarios under "The geometry factors judge the remaining window", assert an altitude factor, a transit timing factor and a window length factor. `Target` publishes only the combined `score`, and its `max_altitude` and `transit_time` keep whole-night values. Verdict: CONFIRMED.
2. **The window factor is named "observable window length", which the glossary reserves for the whole-night `window`.** Check: contradictions, domain language. `specs/target-ranking/spec.md`, the requirement's second bullet and its third scenario. Implemented literally, the factor would read the whole-night length. Verdict: CONFIRMED.
3. **The proposal says the producer passes the scored window to ranking, which design D1 rules out.** Check: contradictions. `proposal.md`, the Impact section's Code line. Verdict: CONFIRMED.

### 📌 Suggestions

4. **No scenario checks that the emitted `remaining_window` spans the minimum duration.** Check: scenario testability. The gate requirement says it, but no scenario asserts it on the emitted field. Verdict: CONFIRMED.
5. **Some sentences run over 30 words.** Check: plain language. The proposal's first bullet, the gate requirement's second sentence, a scenario WHEN line, the night-verdict field list and the ADR's front-matter description. Verdict: CONFIRMED in part (see Rebuttals).

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. `design.md`, Test Seams: say that the single-factor scenarios are asserted through `geometry_for`'s remaining-window geometry fed to the pure sub-score functions, because `Target` exposes only `score`.
2. `specs/target-ranking/spec.md`: rename the factor "remaining window length as a share of the scored window", and its scenario's THEN to "its window length factor is 1".
3. `proposal.md`, Impact: replace the producer line with `pierpressure/core/scoring.py` (the shared scored-window function).
4. `specs/target-ranking/spec.md`: add the scenario "Every remaining window spans the minimum duration" to "Each target carries its remaining window".
5. Split the proposal's first bullet and the gate requirement's second sentence into shorter sentences.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed (required change 1). The factor-level THENs stay, because the main spec already states factor-level behavior the same way ("the moon separation factor is neutral"). The reviewer's proposed wording ("its score reflects the 40° peak") is vaguer, and no test could assert it. The design now names the seam that asserts each factor.
2. Fixed (required change 2).
3. Fixed (required change 3).
4. Fixed (required change 4).
5. Fixed in part (required change 5). Declined for the night-verdict field list: it repeats the existing requirement word for word apart from the one added field, so the delta stays a one-field diff. Declined for the scenario WHEN line: its length is the concrete setup a test needs. Declined for the ADR's front-matter description: it is metadata for the record index, not body prose.
