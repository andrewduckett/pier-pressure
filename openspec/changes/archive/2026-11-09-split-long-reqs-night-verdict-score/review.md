## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (`gemini/gemini-3.8-flash` through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only. The working tree stayed clean (`"gitClean": true`).
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `0e00132`
- **Effort**: low, from design.md's scrutiny tier

The reviewer gave the verdict APPROVE_WITH_CHANGES. It raised no Critical finding. The author adjudicates below: three small listed edits fix findings 1 to 3, so the verdict stands.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The added scenario "A pier configuration sets all three tuning knobs" is not asserted by any one test.** `test_go_threshold_and_max_gust_load_from_yaml` sets two knobs and `test_dew_margin_loads_from_yaml` the third, in separate configurations. — **CONFIRMED**. Fixed by required change 1.
2. **"An unavailable wind-gust limit caps the verdict at MAYBE" leans on the requirement before it ("this way"), and the scenario under "A wind-gust limit that wind data does not fully cover is unavailable" asserts the cap, which only the next requirement states.** — **CONFIRMED** for the "this way" reference, fixed by required change 2. **REFUTED** for the scenario's placement (see Rebuttals).
3. **The added scenario "An hour with only seeing takes its quality from the seeing" asserts `A`, an intermediate value, not a field of the verdict document.** — **CONFIRMED** that design.md did not say so. Fixed by required change 3.

### 📌 Suggestions

4. **Plain language:** twelve sentences in the split requirements are over 30 words. — **Declined** (see Rebuttals).
5. **"Targets list is present and ordered when targets are rankable" asserts the catalog fields and the order, which now sit in other requirements.** — **Declined** (see Rebuttals).

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Replace the added scenario under "A pier has three optional tuning knobs and no others" with "A pier configuration sets its go-threshold and wind-gust limit": a go-threshold of 70 and a wind-gust limit of 45, as `test_go_threshold_and_max_gust_load_from_yaml` sets and asserts them. Update design.md Decision 3.
2. In "An unavailable wind-gust limit caps the verdict at MAYBE", replace "When the wind-gust limit is treated as unavailable this way" with "When a configured wind-gust limit is treated as unavailable because wind data does not cover every hour of the scored window". Update design.md Decision 4.
3. In design.md Decision 3, say that `A` is the spec's own quantity, defined in its requirement, and that the scenario asserts it at the unit seam.

CHANGES_APPLIED: yes

## Rebuttals

1. **Fixed.** Required change 1 is applied in `specs/night-verdict/spec.md` and design.md Decision 3. The test loads `go_threshold: 70` and `max_gust: 45` from one file and asserts both (`tests/test_config.py`, `test_go_threshold_and_max_gust_load_from_yaml`). The dew margin's own scenarios, "Omitted dew margin is 4 °C" and "A negative or infinite dew margin is rejected", still cover the third knob.
2. **Fixed in part, refuted in part.** Required change 2 is applied: the cap now names its own trigger. The requirement is 311 characters. The second half of the finding asks the first requirement to restate the cap. That would add an obligation to a requirement whose original sentence stated none, and say one behavior twice. "Treated as unavailable" is observable only through the cap, so a scenario about it has to assert the cap. "Partial wind coverage caps the verdict at MAYBE when a limit is configured" sits there because it tests the "only for some of its hours" sentence (design.md Decision 2). The epic forbids changing its words. Joined, the two requirements run to 503 characters, which is why they split (design.md Decision 1).
3. **Fixed.** Required change 3 is applied in design.md Decision 3. `A` is not internal to the code: "The atmosphere factor rests on a clarity-weighted mean of each hour's quality" defines it, and the original requirement did the same. `test_atmosphere_mean_uses_the_one_term_an_hour_carries` asserts it. An assertion on the 82% reason line instead would rest on no existing test.
4. **Declined.** The long sentences are the originals' own, such as the target field list. Epic #230 allows rewording only for clarity, and a wording pass on every carried sentence would widen the diff a reviewer must check against the originals.
5. **Declined.** Epic #230 decision 2 keeps a scenario that tests two behaviors whole, under the requirement it fits best. Its first THEN line lists the fields, so it sits with the field requirement (design.md Decision 2).
