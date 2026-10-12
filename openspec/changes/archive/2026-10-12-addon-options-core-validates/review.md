## Review Metadata

- **Review round**: 3
- **Prior round**: REVISE — the collision fix kept unset fields, and unknown top-level keys silently disappeared.
- **Reviewer context**: cross-model (GPT `gpt-6-sol` via Codex, read-only)
- **Tool restrictions**: read-only inspection; no files created, edited, or deleted
- **Artifacts reviewed**: proposal.md, design.md, both delta specs and their existing specs, adr.md, ADR-0022, and relevant source, tests, and add-on files. Issue #83 was not retrieved.

This verdict applies only to the artifact contents reviewed in this round. Later edits to the proposal, design, or delta specs void it, except for the Required Change below.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The horizon requirement is too dense to use as a reference.** The [horizon-mask delta spec](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/horizon-mask/spec.md:5) puts ordering, ranges, normalization, and duplicate handling in one paragraph. Its sentence beginning “Two pairs at the same azimuth” exceeds 30 words and combines two outcomes and their rationale. The new paragraph’s sentence beginning “The pier’s configuration SHALL be invalid” also exceeds 30 words. Split these rules into short sentences or bullets without changing their meaning. This plain-language issue remains even though the first paragraph came from the existing spec.

### 📌 Suggestions

None.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

The behavior and failure paths are coherent. The specified prose edit needs a focused re-check before downstream work proceeds.

## Required Changes (if APPROVE WITH CHANGES)

1. Revise the two dense paragraphs in the [horizon-mask delta requirement](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/horizon-mask/spec.md:5). Make ordering, ranges, duplicate outcomes, and invalid YAML text separately findable; keep every rule and scenario outcome unchanged.

CHANGES_APPLIED: yes

## Rebuttals

1. **Round 2 Moderate 1 — collision handling: accepted by reviewer.** Design D2–D3 now remove fields that `is_set` treats as unset before retaining set fields beside a `horizon` or `equipment` value, and the delta spec covers both unset-field cases.
2. **Round 2 Moderate 2 — unknown top-level keys: accepted by reviewer.** The proposal, design, delta spec, and ADR consistently limit the pass-through promise to settings the add-on reads and state that other top-level saved keys are ignored.
3. **Round 2 suggestion — “four cases” listed five: adopted.** The count now says five.
4. **Round 2 suggestion — dense horizon paragraph: declined by author, but raised above as a required plain-language change.** Its origin in the existing spec does not make the modified requirement easier to read.

Round 3 Required Change 1, applied and re-checked:

5. **Required Change 1 — split the dense horizon requirement: fixed, re-checked by reviewer (PASS).** The requirement now lists order, ranges, repeated azimuths and size as separate rules, and lists the three ways YAML text fails. A focused re-check by the same reviewer (GPT `gpt-6-sol` via Codex, read-only) found every rule preserved and no sentence over 30 words.

