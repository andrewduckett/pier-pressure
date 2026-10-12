## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (GPT, `gpt-6-sol` via `codex exec`, reasoning effort medium, fresh context). The reviewer read the instructions as asking it to launch a further reviewer; that nested launch failed, and it reviewed in its own fresh context.
- **Tool restrictions**: read-only inspection; no files were created, edited, or deleted
- **Artifacts reviewed**: the proposal, design, both delta specs and their existing specs, the ADR manifest, ADR-0022, and relevant source and tests. Issue #83 was unavailable because GitHub could not be reached.

This verdict applies only to the artifact contents reviewed in this round. An edit to the proposal, design, or specs beyond the findings below requires a new full review.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **A saved horizon can be silently replaced.** The proposal says the add-on passes unexpected values to the core, but the planned horizon translation retains behavior that overwrites an existing `horizon` block when `horizon_points` or `min_altitude` is set. A hand-written `options.json` pier containing both can therefore use the flattened value without rejecting the discarded block. The proposal covers the comparable `equipment` collision but omits this case. Specify core rejection and a test for the horizon collision. [Proposal](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/proposal.md:26), [design](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/design.md:84), [current translation](/home/andrew/Git/projects/pier-pressure/pierpressure/addon_options.py:179).

2. **The horizon requirement contradicts its scenario.** The delta spec says duplicate azimuths with equal rounded altitudes “SHALL be deduplicated,” while its scenario says two pairs at the same azimuth are rejected. The latter lacks the different-altitude condition, so the expected result cannot be asserted consistently. Qualify the rejection scenario and add one for equal-altitude deduplication. [Horizon-mask delta spec](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/horizon-mask/spec.md:9), [scenario](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/horizon-mask/spec.md:32).

3. **The cross-interface error promise exceeds the specified guarantee.** ADR-0022 promises “the same check and the same message from every interface,” but the add-on spec requires only an error naming the same setting. A malformed YAML file and malformed YAML text in `horizon_points` fail at different stages, so identical messages are not established. State the guarantee consistently in the proposal, spec, and ADR. [ADR-0022](/home/andrew/Git/projects/pier-pressure/docs/decisions/0022-core-is-the-only-place-that-validates-settings.md:44), [add-on delta spec](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/ha-addon/spec.md:25).

### 📌 Suggestions

- **Make the horizon rules easier to find.** The opening paragraph packs ordering, ranges, normalization, duplicate handling, and minimum count into one dense block. Split those conditions and outcomes. [Horizon-mask delta spec](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/horizon-mask/spec.md:5).
- Replace “an adopter on any install” with “users of every install.” Shorten ADR-0022’s frontmatter description so it states the decision directly. [Proposal](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/proposal.md:10), [ADR-0022](/home/andrew/Git/projects/pier-pressure/docs/decisions/0022-core-is-the-only-place-that-validates-settings.md:6).
- The design asks to include the YAML reader’s message in an error. Parser messages can quote input, and pier validation logs the resulting error. Record this exposure as a security trade-off or address it in the separate secret-hiding work identified by the proposal; the current add-on already logs parser messages, so this is not treated as a new blocking regression. [Design](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/design.md:62), [logging](/home/andrew/Git/projects/pier-pressure/pierpressure/core/config.py:509), [proposal scope](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/proposal.md:60).
- Add a mapping-text case alongside `"5"` to test the stated boundary that YAML text must contain a list. [Design](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/design.md:71).

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

The silent overwrite and contradictory scenario require a revised artifact set and a new full review before downstream work proceeds.

VERDICT: REVISE

## Required Changes (if APPROVE WITH CHANGES)

Not applicable. Resolve the Moderate findings before requesting a new review.

CHANGES_APPLIED: n/a

## Rebuttals

Author responses, applied before round 2. Round 2 must re-check each one.

1. **Moderate 1 — a saved horizon can be silently replaced: fixed.** When a pier's `horizon` value is set, the add-on now leaves its horizon fields unchanged, and the core rejects them as unknown fields (design D2, D3). The ha-addon delta adds the case and the scenario "A horizon mapping beside horizon fields skips the pier". The proposal and design D6 add it too.
2. **Moderate 2 — the duplicate-azimuth scenario contradicts the requirement: fixed.** The scenario now needs different rounded altitudes, and a new scenario covers deduplicating equal ones. The defect came from the main spec.
3. **Moderate 3 — the ADR promises the same message: fixed.** ADR-0022 and the proposal now promise the same check, and an error that names the same setting.
4. **Suggestion — split the dense horizon paragraph: declined.** It is unchanged text from the main spec, and rewriting it is outside this story.
5. **Suggestion — wording in the proposal and ADR front matter: adopted.**
6. **Suggestion — the YAML message can quote input: adopted** as a risk in the design. Pier errors show values on purpose.
7. **Suggestion — test text that holds a mapping: adopted.** `"{a: 1}"` is in the horizon-mask scenario and design D6.
