## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the plan's author is claude)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only. The working tree was clean before and after (`gitClean: true`).
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `832f442`. The reviewer also read the labelled trial's `translations/en.yaml` and copies of the Home Assistant frontend and Supervisor source.
- **Effort**: low, from design.md's scrutiny tier

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **design.md D5 kept `DOCS.md` to two tables, but the proposal says every
   place that names a pier field takes the new label.** `DOCS.md` also names
   **Horizon floor**, **Horizon points**, the equipment field table, the gate
   field table and the horizon row of its settings table by their old labels.
   Check: Contradictions, Scope. CONFIRMED (`ha-addon/DOCS.md` lines 27, 56,
   58, 74, 86–89, 129–130 and 215).
2. **The spec's scenario accepted any text after the section prefix.** The
   table listed schema keys, not labels, so `Horizon: min_altitude` would pass.
   Check: Scenario testability. CONFIRMED.
3. **The trial text says "Fill in Focal length, sensor width and height",
   naming a label that no longer exists.** Design's "word for word" goal would
   ship it. Check: Scope, Plain language. CONFIRMED
   (`.workspace/addon-trial/pierpressure_labelled_trial/translations/en.yaml`
   lines 67–68 and 73).

### 📌 Suggestions

4. **The rule that no other description starts with `<Section>:` couples
   future text to the test.** The reviewer suggests asserting the exact
   introduction sentences instead. Check: Test seams. Declined, see Rebuttals.
5. **Two sentences run past 30 words:** design.md's "section prefix" risk and
   adr.md's summary. Check: Plain language. CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md D5: `DOCS.md` takes the new label wherever it names a pier
   field's label: in bold text, in field tables and in label-to-`config.yaml`
   tables. Headings and prose that name a setting as an idea stay.
2. specs/ha-addon/spec.md: the section table gives each field's exact label,
   and the scenario asserts that label.
3. design.md Goals: the trial text ships with one exception. A description
   that names another field uses its new label, or plain lower-case words.
4. design.md Risks and adr.md Review Summary: split the two long sentences.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: design.md D5 rewritten as required change 1.
2. Fixed: specs/ha-addon/spec.md now has a Field and Label table, and the
   scenario "Each pier label names its section" asserts the label from it.
3. Fixed: design.md's second goal now names the cross-reference exception.
4. Declined: an exact-sentence assertion would fail on every wording change to
   an introduction, which is the text most likely to be reworded in #101. The
   prefix rule only forbids a description that starts with a section name and
   a colon. That would read as a second introduction, so it is wrong anyway.
5. Fixed: both sentences split.
