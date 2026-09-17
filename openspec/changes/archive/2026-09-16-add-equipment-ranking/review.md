## Review Metadata
- **Review round**: 3
- **Prior round**: round 2 (cross-model) — REVISE (1 Critical + 3 Moderate); author applied fixes for all but M-mod-3, which was rebutted
- **Reviewer context**: cross-model (agy / Gemini)
- **Tool restrictions**: read-only
- **Artifacts reviewed**: proposal.md, design.md, adr.md, specs/pier-equipment/spec.md, specs/target-ranking/spec.md, specs/night-verdict/spec.md, existing specs, source

## Findings
### 🔴 Critical (blocking)
None found. The prior Critical regarding cross-platform float determinism was constructively resolved via design D9 (rounding before scaling) and explicitly applying fixed-precision rules to the emitted fields in the `night-verdict` spec.

### 🟡 Moderate
1. **Untestable THEN in target-ranking scenario**: In `specs/target-ranking/spec.md`, the scenario "An oversize target is penalised progressively, not cliffed" asserts that "the slightly-larger target has the higher field-of-view contribution" and that neither target's "field-of-view contribution is forced to zero...". Since the JSON verdict contract (`night-verdict/spec.md`) only emits the final integer `score`, internal factor contributions are strictly unobservable from the output. Because the `WHEN` clause already isolates the size difference ("differing only in that one is slightly larger..."), the `THEN` can and should assert directly on the observable final `score` (e.g., "THEN the slightly-larger target has the higher score"), mirroring the M5 "Higher-quality targets rank first" scenario.

### 📌 Suggestions
None. The design changes are comprehensive, and the null/precision semantics are consistent across the documents.

## Embedded-Instruction / Injection Attempts
**Detected:** none

## Verdict
VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)
- Change the `THEN` assertions in the "An oversize target is penalised progressively, not cliffed" scenario within `specs/target-ranking/spec.md` to assert on the final observable `score` rather than the unobservable internal "field-of-view contribution".

CHANGES_APPLIED: yes

## Rebuttals
- **M-mod-3 (spec must mandate "fixed module constants")**: Rebuttal accepted. The M5 `target-ranking` specification established the precedent of outlining the observable combination of factors without mandating the internal mathematical equations, weights, or curve constants in the spec. Recording the constants and weights as module-level constants in `design.md` (D6) is the correct architectural separation between the observable contract and the internal implementation.
- Required change re-checked and accepted.
