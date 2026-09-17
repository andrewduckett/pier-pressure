## Review Metadata

- **Review round**: 4
- **Prior round**: round 3 verdict REVISE (stateless-removal contradiction; failure-wording contradiction; text-vs-sensor terminology) — all three addressed
- **Reviewer context**: cross-model (agy / gemini-3.1-pro-high)
- **Tool restrictions**: read-only: read_file, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/, adr.md, docs/adr/0011-*, relevant source files

## Findings

### 🔴 Critical (blocking)

### 🟡 Moderate

### 📌 Suggestions

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE

## Required Changes (if APPROVE WITH CHANGES)

None.

CHANGES_APPLIED: n/a

## Rebuttals

All round 3 findings are now resolved:
1. Stateless removal contradiction: `design.md` and `specs/ha-delivery/spec.md` now explicitly and consistently state that the stateless service will not auto-remove a prior-enabled entity, and clearing it is an operator step. 
2. Failure-wording contradiction: `specs/verdict-narrative/spec.md` now correctly aligns with `ha-delivery`, specifying an active unavailable publish on provider failure instead of a skipped publish.
3. Terminology: `proposal.md` and `design.md` correctly use the updated "read-only sensor entity" terminology instead of "text entity".

## Rules

- Any open 🔴 Critical FORBIDS APPROVE. Verdict must follow from findings.
- CHANGES_APPLIED: "no" for APPROVE_WITH_CHANGES; "n/a" for APPROVE/REVISE.
- Emit `VERDICT:` once on its own line.
