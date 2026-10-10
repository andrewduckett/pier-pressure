## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (codex, GPT)
- **Tool restrictions**: read-only inspection and validation
- **Artifacts reviewed**: proposal.md, design.md, adr.md, both delta specs, OpenSpec configuration and main specs, relevant source and tests
- **Validation**: `openspec validate rename-rig-to-equipment --strict` passed

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The stated startup behavior is wrong for a config with multiple piers.** [proposal.md:16](openspec/changes/rename-rig-to-equipment/proposal.md:16) says a leftover `rig:` key makes the config fail at startup. `validate_piers` logs and skips that pier; startup fails only if no valid pier remains ([config.py:396](pierpressure/core/config.py:396)). [design.md:5](openspec/changes/rename-rig-to-equipment/design.md:5) and the new rejection scenario should distinguish a rejected pier from a failed application startup.

2. **The archive plan conflicts with this repository’s workflow.** [design.md:75](openspec/changes/rename-rig-to-equipment/design.md:75) places a direct main-spec edit in a commit *after* the archive commit. AGENTS.md requires the archive to be its own final commit before the PR is marked ready. Include the scenario-title and Purpose edits in the archive commit, after the spec sync.

3. **The replacement requirement contradicts the rename.** [pier-equipment/spec.md:28](openspec/changes/rename-rig-to-equipment/specs/pier-equipment/spec.md:28) says equipment “SHALL NOT change any existing configuration field,” while this change replaces the existing `rig` field. State that fields *other than the renamed key* retain their meaning.

4. **The spec deltas omit the changed verdict wording.** The proposal gives four exact `reasons[]` sentences ([proposal.md:20](openspec/changes/rename-rig-to-equipment/proposal.md:20)), but neither delta requires them. Record the four sentences and their existing emission conditions in a verdict-related requirement so the specified product behavior matches the planned tests.

5. **The modified ranking spec fails the plain-language requirement.** Its opening scoring sentence runs from [target-ranking/spec.md:5](openspec/changes/rename-rig-to-equipment/specs/target-ranking/spec.md:5) through line 18 and packs six factors and several rules into one sentence. The next paragraph also combines multiple rules in long sentences. Split these into short, findable statements without changing their meaning. The added [pier-equipment/spec.md:22](openspec/changes/rename-rig-to-equipment/specs/pier-equipment/spec.md:22) requirement likewise needs shorter sentences.

### 📌 Suggestions

- Fix the nested quotation marks in the story title at [proposal.md:11](openspec/changes/rename-rig-to-equipment/proposal.md:11).
- Replace “spec-mechanics calls” in [adr.md:12](openspec/changes/rename-rig-to-equipment/adr.md:12) with a plain description of the decision.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Correct the proposal, design, and rejection scenario to describe per-pier validation and the zero-valid-piers startup failure.
2. Revise D4 so the main-spec title and Purpose edits land in the archive commit.
3. Qualify the “existing configuration field” sentence in the added pier-equipment requirement.
4. Add a delta requirement for the four framing sentences and when they appear.
5. Shorten the cited spec sentences while preserving every scoring and equipment rule.

CHANGES_APPLIED: yes

## Rebuttals- **Moderate 1 — fixed.** proposal.md (What Changes, first bullet) and design.md (Context, first bullet) now say a `rig:` pier is logged and skipped, other piers keep running, and startup fails only with no valid pier. The pier-equipment scenario "The `rig` key is not accepted" now says the pier is skipped with a logged configuration error and other valid piers still produce verdicts.
- **Moderate 2 — fixed.** design.md D4 and its matching risk now put the direct main-spec edits (two target-ranking scenario titles, pier-equipment Purpose) inside the archive commit, which stays the last commit. *Accepted by reviewer in the round-1 re-check.*
- **Moderate 3 — fixed.** The pier-equipment ADDED requirement now says "Apart from the `equipment` key itself, equipment SHALL NOT change any other configuration field or its meaning." *Accepted by reviewer in the round-1 re-check.*
- **Moderate 4 — fixed.** target-ranking delta adds "Requirement: The verdict says how the top pick frames", with the four exact sentences, their emission conditions (gate-passing verdict, non-empty list, equipment configured, catalog object with known size), and four scenarios. proposal.md Capabilities notes it. *Accepted by reviewer in the round-1 re-check.*
- **Moderate 5 — fixed.** The target-ranking MODIFIED requirement's scoring and contribution paragraphs are split into lists and short sentences, with every rule kept. The pier-equipment ADDED requirement is split the same way. *Accepted by reviewer in the round-1 re-check.*
- **Suggestion (story title quotes) — fixed.** proposal.md uses single quotes inside the title.
- **Suggestion ("spec-mechanics calls") — fixed.** adr.md now says the decisions "choose names, sentence wording, and how the spec files carry the rename".

## Re-check of Required Changes (round 1)

Reviewer: cross-model (codex, GPT), read-only. Each Required Change was re-checked against the edited artifacts.

1. Accepted. The proposal, design, and `rig` rejection scenario describe per-pier skipping, and startup failure only when no valid pier remains.
2. Accepted. D4 places the main-spec edits in the final archive commit.
3. Accepted. The requirement exempts the renamed `equipment` key and keeps every other configuration field.
4. Accepted. The delta states all four framing sentences and when they appear.
5. Accepted. The shorter requirements keep every scoring and equipment rule in the current specs.

New blocking defects: none found. `openspec validate rename-rig-to-equipment --strict` passed.
