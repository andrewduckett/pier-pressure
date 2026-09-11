## Review Metadata

- **Review round**: 2
- **Prior round**: round 1 verdict REVISE (three new findings: 1 Critical config-load architecture, 2 Moderate float-dedup + unbounded-read, 1 suggestion comment-token) — all addressed by the author before this round
- **Reviewer context**: cross-model (gemini-3.1-pro-high via agy, read-only plan mode). codex/gpt was attempted first but hit its usage limit.
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/, docs/adr/0007-canonical-horizon-representation.md, relevant source files

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

None.

### 📌 Suggestions

- **Broaden the mutual-exclusivity clause in the spec**: Under "Flat floor and default open sky", the spec forbade configuring "both inline points and a flat floor", inadvertently omitting the third source (an imported file). Design D3 states all three sources are mutually exclusive. Elevated to a Required Change for spec/design alignment.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. In `spec.md`, update the mutual-exclusivity constraint under "Flat floor and default open sky" to cover all three sources: "A pier SHALL NOT configure more than one horizon source (inline points, a flat floor, or an imported file); doing so SHALL make the pier's configuration invalid, so a horizon has exactly one source."

CHANGES_APPLIED: yes

## Rebuttals

Round-1 fixes, verified resolved by the round-2 reviewer:

- **config-load architecture** (was Critical): Resolved. Design D3 now leverages `ValidationInfo.context` in Pydantic V2 to pass the config directory into per-pier validation; file parsing happens within the existing `validate_piers` loop, and exceptions become `ValidationError`s, preserving per-pier isolation without duplicating logic. (Cite: `design.md` D3.)
- **float dedup** (was Moderate): Resolved. Altitudes are rounded to a fixed precision at construction and the duplicate-azimuth rule compares rounded values, stable across float noise and aligned with the determinism guarantee. (Cite: `spec.md` Canonical horizon representation.)
- **unbounded file read** (was Moderate): Resolved. An imported horizon file is operator-supplied local config at the same trust level as `config.yaml`; no remote vulnerability. (Cite: `design.md` Risks / Trade-offs.)
- **comment token** (was Suggestion): Resolved. A comment line is one whose first non-whitespace character is `#`. (Cite: `spec.md` NINA horizon import.)

Required Change (round 2):

- **Mutual-exclusivity clause**: Applied verbatim as specified — spec "Flat floor and default open sky" now forbids configuring more than one of inline points, a flat floor, or an imported file, and the "Two sources at once are rejected" scenario is generalized to any two sources. Reviewer re-check accepted (see round-2 re-check note below).

### Round-2 re-check of the applied Required Change

- **Accepted by reviewer.** The independent reviewer re-checked the applied spec edit against Required Change #1 and confirmed it resolves the finding (spec now aligns with design D3; no new issue introduced). CHANGES_APPLIED flipped to yes on that basis.
