## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only; the resolver reported a clean working tree after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit 26ecf11

## Findings

### 🔴 Critical (blocking)

1. **The restated verdict-document requirement contradicts `target-ranking`, and its scenario fails against the code.** The new requirement "The horizon mask has no consumer in the verdict document" says `targets` stays empty and the document is byte-identical. `tests/test_horizon_contract.py` lines 48–51 assert that the horizon changes `targets`. A new heading makes the old rule look freshly agreed. Check: **REFUTED in part, CONFIRMED in part.** The contradiction is not new: the main spec already states it, word for word, at `openspec/specs/horizon-mask/spec.md` lines 253–266, and the scenario is a byte-for-byte copy. Epic #230 rules out changing meaning (Shared decision 3; Won't: "Change any code, test or behavior"). The part that holds is the look of fresh agreement: the REMOVED **Reason** did not say the rule is out of date. Required change 2 fixes that.
2. **The added scenario under "A horizon is a set of azimuth and altitude samples" tests the query, not the sample rule.** It queried azimuth 360, while the requirement's SHALL is that a supplied 360 is normalized in the samples. A regression in `Horizon.from_samples` could keep 360 while the scenario still passes. Check: **CONFIRMED.** `pierpressure/core/horizon.py` normalizes in both `from_samples` (line 68) and `alt_at` (line 90), so the two can drift apart. Required change 1 fixes it.

### 🟡 Moderate

3. **The empty-list scenario is written at the configuration seam, but the cited test is at the horizon builder.** `test_at_least_one_point_is_required` calls `from_points([])`. No test drives `points: []` through `validate_piers`. Check: **CONFIRMED** for the design's wording. The behavior holds: `pierpressure/core/config.py` lines 202–203 pass the list to `from_points`, and a hand run of `validate_piers` with `points: []` skipped the pier. Adding a test is out of scope (the epic changes no test). Required change 3 makes design.md say this plainly.
4. **Brainstorm D9 is an `Assumption` with nothing to support it.** Check: **REFUTED.** D9 cites its support: epic #230 Shared decision 3 and its Won't list. The user delegated the brainstorm and asked for recommendations to be recorded, not raised. The pull request names the drift so the maintainer can decide on a fix.

### 📌 Suggestions

5. **Three ADDED sentences run past 30 words** (the NINA quirks at 67, the closed ring at 49, the azimuth convention at 43). Check: **CONFIRMED, declined.** The text is kept as close to the original as each requirement allows, so its meaning cannot drift (D10). Splitting sentences is fair work for a later change that touches these requirements.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Replace the added scenario under "A horizon is a set of azimuth and altitude samples" with "A sample at azimuth 360 is held at azimuth 0", backed by `tests/test_horizon.py` `test_azimuth_360_normalizes_to_zero_and_deduplicates`. Update the citations in design.md Decision 2 and brainstorm.md D4.
2. In the REMOVED **Reason** for "The horizon does not change the verdict document", say that its `targets` rule is out of date, why the restated requirement keeps it, and that the pull request reports the drift. Say the same in design.md's matching risk.
3. In design.md Decision 2 and Test Seams, say that the empty-list scenario's test asserts the rejection at the horizon builder only, and how the configuration reaches it.

CHANGES_APPLIED: yes

## Rebuttals

1. Rebutted in part: `openspec/specs/horizon-mask/spec.md` lines 253–266 already hold the requirement and scenario, so this change introduces no contradiction. The fair part is fixed by required change 2, in commit 59e16cb.
2. Fixed by required change 1, in commit 59e16cb.
3. Fixed by required change 3, in commit 59e16cb. No test is added, because epic #230 changes no test.
4. Rebutted: D9 cites epic #230 Shared decision 3 and its Won't list as its support.
5. Declined: wording stays close to the original so the meaning cannot drift (D10).
