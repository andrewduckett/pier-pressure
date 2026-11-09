## Review Metadata

- **Review round**: 2
- **Prior round**: Round 1 (commit `49c1e61`, gemini-3.8-flash): REVISE. The epic's scenario check passed silently when it failed (Critical), and the plan left out the story's "any fix the check needs" (Moderate). Brainstorm rows D4 to D6 were unsupported `Assumption` rows (Moderate), and the REMOVED Reason sentences were too long (Suggestion). All four were fixed in commit `940311b`.
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob, and read-only commands such as `openspec validate` and `git show`. The resolver reported a clean working tree after each round.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, the proposed check in `.workspace/check.sh`, the main specs `pier-equipment` and `release-image`, the epic #230 and story #231 bodies, `openspec/glossary.md`. Reviewed commit: `940311b`.

## Findings

### 🔴 Critical (blocking)

1. **The check exits 0 when an earlier spec fails** (check: contradictions with D10). Only the last spec in the loop set the exit status. So a lost scenario in `pier-equipment`, followed by a pass for `release-image`, exited 0. CONFIRMED by reading the loop.

### 🟡 Moderate

2. **The check fails on scenarios added on purpose** (check: contradictions with epic decisions 4 and 6). Any diff at all made it fail, but the epic allows `>` lines for scenarios added under decision 4. CONFIRMED.
3. **A failed `git fetch` stops the check** (check: where it stops working). Offline, the check exited even when `origin/<target>` was already present locally. CONFIRMED.
4. **One REMOVED Reason sentence has 38 words** (check: plain language). This was the second sentence of the Reason in `specs/release-image/spec.md`. CONFIRMED.

### 📌 Suggestions

5. **Two sentences in design.md are over 30 words** (check: plain language). They were in Decision 2 and in the risk about the check's own flaws. CONFIRMED.

The reviewer also confirmed these points: every ADDED requirement is under 500 characters (the longest has 424), all 9 SHALL/MAY statements in `pier-equipment` and all 7 in `release-image` keep their meaning, all 9 scenarios are word for word, and strict validation passes.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

The reviewer gave REVISE, the second in a row. As `lets-review-plan` requires, the author stopped and asked the user. Each finding has a small, clear fix, so the user chose to apply the listed changes without a round 3. The verdict below records that decision.

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Track a failure flag across the loop, and exit non-zero if any spec fails (Finding 1).
2. Compare scenario blocks as counted sets. Fail only on lost or changed blocks. Pass with a list when blocks are only added (Finding 2).
3. Make `git fetch` warn instead of exit, and take BASE from the local `origin/<target>` (Finding 3).
4. Split the long Reason sentence in `specs/release-image/spec.md` into two sentences (Finding 4).
5. Split the two long sentences in design.md (Finding 5).

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: the check in design.md Decision 5 sets `fail=1` on any spec's failure and ends with `exit $fail`. Tested: a scenario deleted from the first spec exits 1.
2. Fixed: design.md Decision 5's `compare` uses `Counter` differences. A spec with only added blocks prints `OK: <cap>: N scenario(s) added; list them in the pull request` and passes. Tested.
3. Fixed: `git fetch -q origin || echo "warning: ..."`, then `merge-base` against the local `origin/<target>`. Tested with a fetch that fails.
4. Fixed: `specs/release-image/spec.md`, the REMOVED Reason now names the first two requirements in one sentence and the other two in the next.
5. Fixed: design.md Decision 2 is now three sentences. The risk about the check's own flaws is now a list of six cases.

Round 1 fixes, for the record: D10 and design Decision 5 add the check fix to the plan (Findings 1 and 2). D4 to D6 now cite the main specs as evidence (Finding 3). Both REMOVED Reasons were split into shorter sentences (Finding 4).
