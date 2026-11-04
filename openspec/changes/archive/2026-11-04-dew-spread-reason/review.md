## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon via `lets delegate review run`, resolver t3)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit e802bb4. Required changes applied at 3fb70ba.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Contradiction.** The delta spec said the line appears "when every hard gate passes", which includes the missing-cloud `MAYBE` (score 0), while design D2 excluded that path and wrongly called its score null. CONFIRMED.
2. **Scenario testability / remaining night.** No scenario exercised a passed hour before a mid-session instant, or the boundary slot that starts before the scored window. CONFIRMED.
3. **Assumption / safety.** `Field(ge=0.0)` accepts `.inf`, which would make every hour qualify. The project guards no float field this way today. CONFIRMED for this field.

### 📌 Suggestions

4. **Assumption rows.** Brainstorm D6 said both values come from "the hour's filled series", and the design's two risk bullets contradicted each other on whether temperature and dew point share a provider. Neither variable is in a bundle, so they fill independently. CONFIRMED.
5. **Plain language.** Four sentences in the delta spec ran over 30 words, including the 65-word tuning requirement inherited from the main spec. CONFIRMED.
6. **Test seams.** Design D7 would have reworded the agreement test to "directly follows the score line", which is false when a cap line sits between them. CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Align design D2 with the spec and brainstorm D2: the line is appended on every gate-passing path, including the missing-cloud `MAYBE`; add a spec scenario for it.
2. Add a spec scenario for a mid-session verdict: a passed hour is not named, and the boundary slot names its top-of-hour start.
3. Add `allow_inf_nan=False` to `dew_margin` in design D3; the spec rejects a non-finite margin and its scenario covers `.inf`.
4. Fix brainstorm D6 and the design's risk bullets: each value comes from its own filled series; a negative spread is under the margin.
5. Shorten the delta spec's long sentences; the tuning requirement becomes a bullet list.
6. Rewrite design D7: the agreement test stays; new tests assert the tail with a dew line, and the order after a cap line. Add a spec scenario for the cap case.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: design D2 rewritten; spec scenario "Missing cloud still gets the line" added.
2. Fixed: spec scenario "A passed hour is not named, and a boundary hour names its start" added, under a new requirement "The dew walk reads the scored window's hours in order" that also holds the skip rules (the split keeps the first requirement under the validator's length limit).
3. Fixed: design D3 and the tuning requirement's scenario "A negative or infinite dew margin is rejected".
4. Fixed: brainstorm D6 row and the two risk bullets in design.md.
5. Fixed: the first requirement's text is split into short sentences; the tuning requirement is a bullet list.
6. Fixed: design D7 rewritten; spec scenarios "The line follows the agreement line and is last" and "The line follows a cap line and the agreement line".
