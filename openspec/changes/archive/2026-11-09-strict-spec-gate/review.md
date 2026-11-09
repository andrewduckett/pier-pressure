## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the `t3` resolver, review thread b8c394c5-e69e-4912-97b8-44baebf53559). The run exited 0.
- **Independent**: yes. The author is claude; the meta line says `"independent": true`.
- **Tool restrictions**: read-only: view, grep, glob only. The working tree was clean before and after (`"gitClean": true`).
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit 0a8b28e. Effort: low, from design.md's scrutiny tier.

## Findings

### 🔴 Critical (blocking)

1. **Two scenarios do not assert an outcome a test can check.** "Every main spec passes strict validation" ends with "the other checks decide the result". "Only a change in progress has a long requirement" names no command in its WHEN. Check: scenario testability. **CONFIRMED.** Fixed by required change 1.
2. **The contract test would look for the spec name and the warning on the wrong stream.** OpenSpec 1.16.0 prints `✗ spec/<name>` and the warning on standard error, and only the totals on standard output. Check: test seams. **CONFIRMED** by running the probe with each stream on its own. Fixed by required change 2.

The reviewer labelled both Critical, and listed a small, unambiguous edit that fixes each, so neither is open.

### 🟡 Moderate

3. **The throwaway specs could fail strict validation for reasons other than length.** Strict mode also warns on a `## Purpose` under 50 characters, and on a requirement with no SHALL or MUST. Check: test seams. **CONFIRMED**: the D2 probe needed a long enough Purpose. Fixed by required change 2.
4. **A subprocess `env` without the parent's environment loses `PATH`.** Then `openspec` and Node cannot be found. Check: assumptions. **CONFIRMED** as a gap in the design's wording. Fixed by required change 2.
5. **D4 is an `Assumption` with no evidence.** `[tasks.check]` holds only task references, which supports it. Check: assumption rows. **CONFIRMED.** Fixed by required change 3.

### 📌 Suggestions

6. **The design's blast radius counts three documents, but only AGENTS.md and the README change.** **CONFIRMED.** Fixed by required change 3.
7. **Three sentences run over 30 words** (design.md Context, design.md decision 7, proposal.md What Changes). Check: plain language. **CONFIRMED.** Fixed by required change 4, and the decision 7 sentence too.
8. **The `check` task's `description` in `mise.toml` would still say "lint + typecheck + test + the card".** `mise tasks` would then misstate what `check` runs. **CONFIRMED.** Fixed by required change 3.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. In `specs/dev-checks/spec.md`, "Every main spec passes strict validation" ends with "the spec check exits with status 0". "Only a change in progress has a long requirement" adds "a developer runs `mise run specs`" to its WHEN, and ends with "the command exits with status 0".
2. In design.md, decision 3 says the test reads standard output and standard error together, and that each throwaway main spec has a Purpose of at least 50 characters and SHALL in every requirement. Decision 4 says the subprocess gets a copy of the test's environment, so `PATH` still finds `openspec` and Node.
3. In brainstorm.md, D4's source adds "Evidence: `mise.toml` `[tasks.check]` holds only task references". In design.md, the blast radius names two documents (AGENTS.md and the README), and says the `check` task's description changes. In proposal.md, Impact says the `check` task's description changes.
4. Split the sentences over 30 words in design.md's Context and decision 7, and in proposal.md's What Changes.

CHANGES_APPLIED: yes

## Rebuttals

- Findings 1 to 8: fixed by the required changes above, in the commit "docs: apply the plan review's changes to strict-spec-gate (#245)". None is rebutted.
