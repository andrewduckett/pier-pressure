## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (OpenAI via codex CLI)
- **Tool restrictions**: read-only sandbox
- **Artifacts reviewed**: proposal.md, design.md, specs/conditions/spec.md, adr.md; the current conditions and night-verdict specs; relevant source, tests, ADRs, and repository guidance

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The freshness rationale attributes confidence to the wrong source.** [proposal.md](../../../openspec/changes/remove-conditions-cache/proposal.md:27) says retaining freshness matters for 7Timer!’s model runs. [design.md](../../../openspec/changes/remove-conditions-cache/design.md:15) describes decay from each source’s age. In [scoring.py](../../../pierpressure/core/scoring.py:484), confidence uses only the base group’s issue time; the secondary issue time is provenance and does not affect freshness. This matters when 7Timer! returns an old model run: the stated reason for D2 does not match the behavior being preserved. Correct the proposal and design to distinguish base-source freshness from secondary-source completeness.

2. **The plan does not preserve a regression check for the defect that motivates it.** The proposal removes the cache tests, while the new [spec scenario](../../../openspec/changes/remove-conditions-cache/specs/conditions/spec.md:59) covers only two fetches for the same pier. The reported failure involves a shared provider serving one pier another pier’s forecast. Add a cross-pier scenario and plan a test using one provider instance across two piers, with a successful fetch followed by a failed or empty fetch. The test should assert that no earlier values or issue time appear in the failed pier’s snapshot.

3. **The conditions delta needs shorter, more direct requirement prose.** In [spec.md](../../../openspec/changes/remove-conditions-cache/specs/conditions/spec.md:39), the sentence beginning “The failure of one source SHALL NOT prevent…” runs beyond 30 words and combines the rule with both examples. The issue-time requirement at line 26 similarly combines the rule and its rationale. Split these into short, independently findable statements. The proposal, design, and ADR are otherwise readable and purposeful.

### 📌 Suggestions

- [proposal.md](../../../openspec/changes/remove-conditions-cache/proposal.md:14) states that an Open-Meteo failure yields `MAYBE` with score 0. Qualify this as a pier with a dark window; without one, the existing astronomy gate yields `NO-GO`.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Correct the proposal and design’s freshness explanation to state that confidence uses the base source’s issue time; secondary-source absence affects completeness, while its issue time does not affect confidence.
2. Add a cross-pier failure scenario to the conditions delta and specify a regression test that checks values and issue time after a failed or empty fetch using the same provider instance.
3. Split the long conditions requirement sentences identified in finding 3 into shorter statements without changing their meaning.

CHANGES_APPLIED: yes

## Rebuttals

- **Moderate 1 (freshness source)** — fixed. proposal.md "What Changes" and design.md Context and D2 now say confidence reads only the base source's issue time, that the secondary's issue time is provenance only, and that without the cache the term stays at full strength in practice. After the re-check, both also state that a missing secondary source lowers confidence through the completeness term.
- **Moderate 2 (cross-pier regression)** — fixed. specs/conditions/spec.md adds the scenario "A failed fetch for one pier is not filled from another pier's fetch" and the requirement text now says "whether for the same pier or another pier". design.md D1 specifies two regression tests (same pier, two piers) on one provider stack, asserting the failed source's group is `None`.
- **Moderate 3 (long sentences)** — fixed. The issue-time and "No single source is load-bearing" requirement texts are split into short statements with the same meaning.
- **Suggestion (dark window)** — applied. proposal.md now says "on a night with a dark window".


Re-check pass 1 (codex): required change 1 not accepted (missing the completeness statement); changes 2 and 3 accepted. The author added the statement.

### Re-check pass 2 (round 1 required changes, accepted by reviewer)

- Required change 1: ACCEPTED — The proposal and design identify base issue time as the freshness input and secondary absence as a completeness loss.
- Required change 2: ACCEPTED — The delta covers a cross-pier failure, and the design specifies a same-provider regression check for values and issue time.
- Required change 3: ACCEPTED — The identified requirement sentences are split into shorter statements with their meaning preserved.

