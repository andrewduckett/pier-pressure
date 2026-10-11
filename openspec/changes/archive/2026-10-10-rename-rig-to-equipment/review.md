## Review Metadata

- **Review round**: 2
- **Prior round**: Round 1 — APPROVE_WITH_CHANGES; 5 required changes applied and accepted by reviewer.
- **Reviewer context**: cross-model (codex, GPT)
- **Tool restrictions**: read-only inspection and validation
- **Artifacts reviewed**: proposal.md, design.md, adr.md, both delta specs, current main specs, relevant source files and tests
- **Validation**: `openspec validate rename-rig-to-equipment --strict` passed

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The proposal and design still show a framing sentence the implementation cannot produce for the example object.** The table in [proposal.md](openspec/changes/rename-rig-to-equipment/proposal.md:24) and the example in [design.md](openspec/changes/rename-rig-to-equipment/design.md:52) use “Top pick M31”. The catalog identifies that object as `NGC0224` with the name “Andromeda Galaxy”; the implementation uses the name, falling back to the catalog id. The corrected scenario uses “Andromeda Galaxy”. These examples should agree with the specified output.

2. **The four-region scenario is hard to read and does not assert the full required sentences.** The single **THEN** at [target-ranking/spec.md](openspec/changes/rename-rig-to-equipment/specs/target-ranking/spec.md:142) exceeds 30 words and lists fragments. Split it into four short, mechanically assertable outcomes that use the complete sentences specified above it.

### 📌 Suggestions

None.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Replace “M31” in the proposal’s four-row table and design D2’s example with “Andromeda Galaxy”, or use the defined `<name>` placeholder consistently.
2. Rewrite the four-region scenario with separate assertions for all four complete framing sentences.

CHANGES_APPLIED: yes

## Rebuttals
- **Moderate 1 — fixed.** proposal.md's four-row table and design.md D2's example now say "Top pick Andromeda Galaxy". No "M31" remains in the proposal, design, or specs. *Accepted by reviewer in the round-2 re-check.*
- **Moderate 2 — fixed.** The four-region scenario is replaced by three single-outcome scenarios (small, fills most, larger than), each asserting one complete sentence. The well-framed case is already covered by "A well-framed top pick gets the exact framing sentence". The small scenario also says "and does not frame well", because the code checks "frames well" first. *Accepted by reviewer in the round-2 re-check.*

## Re-check of Required Changes (round 2)

Reviewer: cross-model (codex, GPT), read-only.

1. Accepted. The proposal table and design example use "Andromeda Galaxy".
2. Accepted. The scenarios assert complete sentences, and their conditions follow the code's check order.

New blocking defects: none. `openspec validate rename-rig-to-equipment --strict` passed.
