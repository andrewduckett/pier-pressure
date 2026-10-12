## Review Metadata

- **Review round**: 3
- **Prior round**: REVISE — a traceback could expose an unknown key name; four moderate findings also remained.
- **Reviewer context**: cross-model (OpenAI, via Codex exec, independent read-only context)
- **Tool restrictions**: read-only inspection; no files changed
- **Artifacts reviewed**: proposal.md, design.md, specs/, adr.md, issue #89 story packet, AGENTS.md, existing capability specs, relevant source files and tests. `openspec/project.md` is absent.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The bare unknown MQTT key scenario still covers an add-on path that will not reject the key.** The ha-delivery delta spec says its requirement holds when the form and file are combined, then says a bare unknown key in `config.yaml` makes the process stop with an error. The add-on merge drops keys with no value before core validation (`pierpressure/addon_settings.py`, `_merge` and `_set_values`). The proposal and design now acknowledge this behavior and assign the wider validation rule to #83, but the spec’s scenario does not limit itself to a standalone file. Narrow that scenario so its expected error matches the path that receives the key.

### 📌 Suggestions

None. The proposal, design, both delta specs, and ADR are otherwise clear and findable. I found no separate plain-language issue that would prevent a reader from acting on them.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

The remaining defect has one specific spec edit. The reviewer needs to re-check that edit before downstream work proceeds.

## Required Changes (if APPROVE WITH CHANGES)

1. In `specs/ha-delivery/spec.md`, limit the bare unknown key scenario’s **WHEN** to a standalone `config.yaml` load. Keep the add-on’s dropped bare key outside that scenario, consistent with proposal.md and design D5. The unknown key with a value must still be covered on the combined add-on path.

CHANGES_APPLIED: no

## Rebuttals

Round 2 findings, re-checked against the revised artifacts:

1. **Critical — traceback cause exposes an unknown key name: resolved.** Design D1 specifies `raise ... from None`, and D6 requires a rendered traceback check with a marker key name.
2. **Moderate — `CombinedSettings` representation prints secrets: resolved.** Design D4 adds `field(repr=False)` for its raw mapping; D6 includes its representation in the planned tests.
3. **Moderate — add-on merge drops a bare unknown MQTT key: partly resolved.** The proposal and design now state the behavior and its scope. The ha-delivery scenario still implies rejection on that path; Required Change 1 addresses the remaining mismatch.
4. **Moderate — Pydantic `msg` assumed input-free: resolved.** Design D1 limits the assumption to the models’ present built-in checks and calls for a code comment and marker tests.
5. **Moderate — empty explainer wording contradicted itself: resolved.** The verdict-narrative spec now names rejected shapes and separately requires both a null block and an empty mapping to disable the explainer.