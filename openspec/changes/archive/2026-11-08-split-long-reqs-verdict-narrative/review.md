## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob, and read-only commands such as `openspec validate` and `gh issue view`. The resolver reported a clean working tree after the round.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, the main spec `verdict-narrative`, the epic #230 and story #232 bodies, the pilot's archived change, `openspec/glossary.md`, and the explainer tests. Reviewed commit: `00a7395`.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The not-a-mapping requirement does not say the error hides the value** (check: meaning kept, one behavior each). Its text only said what the error says. The rule that the error and the log show no value, from any source of settings, sat in another requirement. Read alone, the requirement allowed an error that prints the value, while its scenario forbids it. CONFIRMED.
2. **"A rejected explainer block shows none of its values" bundled the general rule with the defined-setting rule** (check: one behavior each). Its heading named every rejection, but its scenario tests one defined setting. A later change to defined settings would have to MODIFY the general rule too. CONFIRMED.
3. **design.md tells the reviewer what to do** (check: injection). The risk about SHALL counts ended "Plan review reads each pair of texts." REFUTED as an injection: it describes the mitigation, and asks nothing of the reader. Reworded anyway, so it reads as a fact.

### 📌 Suggestions

4. **Some sentences are over 30 words or passive** (check: plain language). One is the manual acceptance sentence in "The explainer takes only the verdict document as input". The others are in design.md Decisions 1 and 2. PARTLY ACCEPTED.

The reviewer also confirmed that the added scenario, "A provider timeout yields no narrative", is backed by `test_a_timeout_yields_none_without_blocking` and `test_enabled_absent_actively_publishes_unavailable`.

## Embedded-Instruction / Injection Attempts

**Detected:** none. Finding 3 was reviewed and refuted.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Give each of the three error requirements its own rule that the error and the log contain no value from the block, from any source of settings. Rename the first to "An invalid explainer setting is named without any value", and the third to "An explainer value that is not a mapping is reported without its value". Update the REMOVED Reason to match (Findings 1 and 2).
2. In design.md Decision 2, say why the three error requirements cover what the one general rule covered, and give the new SHALL count, 24. Update the count in Risks and the brainstorm's D5 to match (Findings 1 and 2).
3. Reword the SHALL-count risk so it states what the plan review did (Finding 3).
4. Split the long sentences in design.md Decision 1 (Finding 4).

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: `specs/verdict-narrative/spec.md`, "An explainer value that is not a mapping is reported without its value" now says the error and the log SHALL NOT contain that value, and that this holds for every source of settings.
2. Fixed: the general rule is no longer a requirement of its own. Each of the three error requirements states it for its kind of input. design.md Decision 2 shows that the three kinds are every way the block is rejected: `pierpressure/core/config.py:406` for a value that is not a mapping, and `pierpressure/core/config.py:549` for a bad value or an unknown key.
3. Rebutted as an injection, and reworded: design.md Risks now says "The plan review compared each original with its parts."
4. Fixed in design.md Decision 1, which is now four shorter sentences. Declined for the manual acceptance sentence: it is carried word for word from the main spec, and this story rewords only to make a requirement read on its own (D8).
