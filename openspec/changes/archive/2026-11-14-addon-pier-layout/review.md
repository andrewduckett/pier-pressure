## Review Metadata

- **Review round**: 2
- **Prior round**: round 1 (gemini/gemini-3.8-flash, commit `832f442` before the rebase) gave APPROVE_WITH_CHANGES; its four required changes were applied, and one suggestion was declined.
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the plan's author is claude)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only. The working tree was clean before and after (`gitClean: true`).
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `0e7150c`. That commit sits on the newer main, where the `ha-addon` form requirement is split and ADR-0026 is taken. The reviewer also read the implementation already on the branch.
- **Effort**: low, from design.md's scrutiny tier

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The label requirement says a label ends with "the field's name in
   lower-case words", which reads as the schema key.** By that reading,
   `min_altitude` would be `Horizon: min altitude`, but the scenario and the
   translations say `Horizon: floor`. Check: Contradictions, Scenario
   testability. CONFIRMED (`specs/ha-addon/spec.md`, "Each pier field's label
   names its section").
2. **On a narrow phone dialog, `Equipment: sensor width` and
   `Equipment: sensor height` may both cut off as `Equipment: sensor...`.**
   Check: Assumption rows. REFUTED, see Rebuttals.

### 📌 Suggestions

3. **design.md's Test Seams still says "two new scenarios"; there are now
   three.** Check: Test seams. CONFIRMED.
4. **ADR-0040's frontmatter description is one 35-word sentence.** Check:
   Plain language. CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. specs/ha-addon/spec.md: the requirement "Each pier field's label names its
   section" lists the eleven labels instead of deriving them from the field's
   name.
2. design.md Test Seams: "two new scenarios" becomes "three new scenarios".
3. ADR-0040: split the frontmatter description into two sentences.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: the requirement now lists the labels, in section order.
2. Rebutted: design.md's Risks section already names cut-off labels in a narrow
   dialog. Its mitigation is that the help text under each field names the
   field in full: "Your camera sensor's long side" and "Your camera sensor's
   short side" (`ha-addon/translations/en.yaml`). Andrew tried these labels in
   real Home Assistant and chose them. The reviewer's width figures are not
   measured in this repository.
3. Fixed: design.md says "three new scenarios".
4. Fixed: the description is two sentences.
