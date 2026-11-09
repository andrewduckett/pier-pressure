## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (`gemini/gemini-3.8-flash` through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only. The working tree stayed clean (`"gitClean": true`).
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `5178b19`
- **Effort**: low, from design.md's scrutiny tier

The reviewer gave the verdict APPROVE_WITH_CHANGES. It raised no Critical finding. The author adjudicates below: three small listed edits fix findings 1 and 2, so the verdict stands.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **"On an ordinary night, an instant on the exact dawn crossing still selects the ending night" has no scenario about an instant on the crossing.** Its one scenario, "A verdict after the exact dawn crossing judges the next night", tests an instant after it. — **CONFIRMED**. Fixed by required change 1.
2. **design.md Decision 4 does not list every rewording.** It leaves out the narrowed-test sentence, "including both extreme-latitude cases", the split of the last astronomy sentence, the dropped "Which exact end qualifies differs by case." and "and the selection still picks that window", and the move of "The `dark_window` field SHALL keep the whole night". — **CONFIRMED**. Fixed by required changes 2 and 3. A check by the author found two more: "Its score" became "The score", and bullets became sentences. Required change 3 lists them too.
3. **"The score reflects the extent and quality of the scored window's usable dark time" bundles the weighting of terms other than cloud with the extent of usable dark time.** — **REFUTED** (see Rebuttals).

### 📌 Suggestions

4. **The moon rationale, "a bright moon above the horizon during darkness", sits with illumination and phase, while `up_during_dark` is in the next requirement.** — **Declined** (see Rebuttals).
5. **Plain language:** sentences over 30 words in design.md and adr.md. — **Declined** (see Rebuttals).

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Add the scenario "An instant exactly on the dawn crossing still judges the ending night" under "On an ordinary night, an instant on the exact dawn crossing still selects the ending night", backed by `test_an_instant_exactly_on_the_dawn_crossing_has_no_dark_time_left`. Change the count of added scenarios from five to six in brainstorm.md (D9, D15, Changes from the story), proposal.md, design.md (Goals, Decision 3, Risks) and adr.md.
2. Restore "and the selection still picks that window" in the two case requirements: "On an ordinary night, an instant on the exact dawn crossing still selects the ending night" and "In continuous polar night, an instant on the exact solar-day boundary selects the next solar day".
3. In design.md Decision 4, list every rewording: the narrowed-test sentence, "including both extreme-latitude cases", "Its score" to "The score", the `moon` list wording, the split of the last astronomy sentence, the dropped connective "Which exact end qualifies differs by case.", the bullets that became sentences, and a pointer to Decision 1 for sentences that move.

CHANGES_APPLIED: yes

## Rebuttals

1. **Fixed.** Required change 1 is applied in `specs/night-verdict/spec.md` and in the four documents it names. The test asserts both THEN lines: `window[1] == dawn.replace(microsecond=0)` and `decision.scored_window == (window[1], window[1])` (`tests/test_verdict_eval.py:393` to `:399`). `openspec validate split-long-reqs-night-verdict-window --strict` still passes.
2. **Fixed.** Required changes 2 and 3 are applied in `specs/night-verdict/spec.md` and design.md Decision 4. Restoring the clause keeps the original's words, rather than relying on "up to and including" to imply them. The two requirements are now 417 and 426 characters. The SHALL count stays at 55, 9 of them SHALL NOT.
3. **Refuted.** The original's bullet says "Its score SHALL reflect the extent and quality of the usable portion". The next bullet, the weighting of other terms toward clear hours, is how the quality of the usable portion is measured (`pierpressure/core/scoring.py` weights each term by clarity, and `tests/test_scoring.py` `test_high_cloud_penalty_is_the_clarity_weighted_mean_of_high_over_100` asserts it for one term). Extent and quality together are one behavior: how the score reads the usable dark time. Splitting the weighting out would need another added scenario for a rule the original stated as part of the score. A later change that alters the weighting MODIFIES a requirement of 353 characters, not the original 924.
4. **Declined.** The sentence is about the `moon` object as a whole: a bright moon needs `illumination`, which is in this requirement, and being up needs `up_during_dark`. It sits with the requirement that introduces the object. In the next requirement it would bring that one to about 540 characters.
5. **Declined.** The long sentences are mostly lists of quoted requirement headings, which cannot be shortened without renaming. A wording pass on design.md and adr.md would change no decision.
