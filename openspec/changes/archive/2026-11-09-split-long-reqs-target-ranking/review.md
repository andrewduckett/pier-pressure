## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only; the resolver reported a clean working tree after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit 11dabbb

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The test cited for the added scenario "A target with a surface brightness carries the catalog magnitude" never meets its WHEN.** `tests/test_ranking_pipeline.py` `test_targets_carry_the_raw_catalog_facts` ranks 10 targets for London with the widefield rig, and none has a surface brightness, so the test cannot tell whether the brightness choice reaches the carried magnitude. Check: **CONFIRMED.** A run while checking listed the 10 targets: only NGC7380 has a magnitude (7.2), and none has a surface brightness. The behavior holds: `pierpressure/core/ranking.py` line 770 builds each target with `magnitude=obj.magnitude`. Adding a test is out of scope, because epic #230 changes no test. Required change 1 makes the plan say this plainly.
2. **No pipeline test would catch a regression that overwrites the carried magnitude for a target with both values.** Check: **CONFIRMED, OUT-OF-SCOPE.** It is the same gap as finding 1, seen as a future risk. Epic #230 changes no code or test. The pull request reports the gap so the maintainer can add a test.

### 📌 Suggestions

3. **brainstorm.md D6 says "the other ten scenarios" move over, but the requirement has 11.** Check: **CONFIRMED.** All 11 move; the moon factor's scenario is added beside them. Required change 2 fixes the count.
4. **The framing requirement has a 104-character line, and its 492 characters leave little margin.** Check: **CONFIRMED in part.** The long line came from an edit; rewrapping changes no count. The margin is already a design risk, accepted there. Required change 3 rewraps the line.
5. **Four ADDED sentences run past 30 words.** Check: **CONFIRMED, declined.** The text is kept as close to the original as each requirement allows, so its meaning cannot drift (D10). Shorter sentences are fair work for a later change that touches these requirements.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Say in brainstorm.md D7 and in design.md (Decision 2's table row and closing sentence, Test Seams, and the matching risk) that `test_targets_carry_the_raw_catalog_facts` asserts the carried magnitude only for targets without a surface brightness, that `ranking.py` line 770 carries the catalog magnitude directly, and that the pull request reports the gap.
2. In brainstorm.md D6, say that all 11 scenarios move over whole.
3. Rewrap the long line in "The verdict gets one framing sentence about the top pick" in the delta spec.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed by required change 1. No test is added, because epic #230 changes no test.
2. Out of scope: epic #230 changes no code or test. The pull request reports the gap.
3. Fixed by required change 2.
4. Fixed in part by required change 3. The margin is accepted in design.md Risks.
5. Declined: wording stays close to the original so the meaning cannot drift (D10).
