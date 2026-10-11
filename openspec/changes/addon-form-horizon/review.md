## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model — OpenAI Codex CLI 0.159.3, model gpt-6-sol, reasoning effort medium
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/ha-addon/spec.md, adr.md, the existing ha-addon and horizon-mask specs, relevant ADRs, source files, add-on files, tests, and AGENTS.md. `openspec/project.md` is absent.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Malformed saved values can escape the promised per-pier isolation.** The design says the edge strips and parses each pier’s fields, but does not specify what happens when a pier is not a mapping or `horizon_points` is not a string ([design.md:49](openspec/changes/addon-form-horizon/design.md:49), [design.md:74](openspec/changes/addon-form-horizon/design.md:74), [design.md:102](openspec/changes/addon-form-horizon/design.md:102)). The stated Supervisor check converts a value to `str` *for matching*; that does not establish that the saved value is a string. A malformed `options.json` can therefore cause an edge-level exception while another pier is valid, whereas the existing core skips invalid piers individually ([addon_options.py:42](pierpressure/addon_options.py:42), [config.py:396](pierpressure/core/config.py:396)). Specify type checks and per-pier handling before string operations or YAML parsing, with a scenario covering a malformed saved value beside a valid pier.

2. **The relationship to ADR-0020 needs an explicit correction.** ADR-0020 says a list of horizon points does not fit the form’s nesting limit ([0020-addon-form-translated-to-config-file-shape.md:22](docs/decisions/0020-addon-form-translated-to-config-file-shape.md:22)). This change fits those points by accepting a *text representation* ([design.md:106](openspec/changes/addon-form-horizon/design.md:106)). The ADR review says ADR-0020 is simply applied ([adr.md:13](openspec/changes/addon-form-horizon/adr.md:13)). Clarify that the earlier statement concerned a structured list and record how this text field changes that premise, so a later maintainer can reconcile the two decisions.

3. **The save-check test cannot establish that the Home Assistant form works.** The proposed test runs Python `re.match` against a pattern read from the manifest ([design.md:121](openspec/changes/addon-form-horizon/design.md:121), [spec.md:38](openspec/changes/addon-form-horizon/specs/ha-addon/spec.md:38)). It can pass if the Supervisor or frontend handles the optional `match(...)` field differently from the stated claims. The design mentions a manual check but leaves its pass criteria implicit ([design.md:159](openspec/changes/addon-form-horizon/design.md:159)). Specify the real-instance check: both fields appear, a bracketed value saves, an unbracketed value is rejected, and clearing each field saves.

### 📌 Suggestions

- **Make the prose more direct.** The ADR’s explanation of ADR-0020 runs beyond 30 words and can be split at the distinction between form translation and the nesting limit ([adr.md:15](openspec/changes/addon-form-horizon/adr.md:15)). Its opening “review completed” sentences add no decision for the reader ([adr.md:6](openspec/changes/addon-form-horizon/adr.md:6)). The design’s opening directs readers back to the proposal instead of stating the decision immediately ([design.md:1](openspec/changes/addon-form-horizon/design.md:1)). The proposal and delta spec are otherwise clear; I found no comparable plain-language issue in them.
- **Describe the rollback consequence as lost form values.** The design correctly says the old Supervisor schema drops the new fields ([design.md:163](openspec/changes/addon-form-horizon/design.md:163)). State plainly that a user who rolls back must enter those horizon values again after upgrading.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Define and test per-pier handling for non-mapping pier entries and non-string `horizon_points` values in saved options.
2. Reconcile the structured-list statement in ADR-0020 with this change’s text-field approach in `adr.md` or the relevant decision record.
3. Add explicit pass criteria for manual verification of the fields and save behavior in a real Home Assistant instance.

CHANGES_APPLIED: yes

## Rebuttals


- **Moderate 1 — fixed; accepted by reviewer** (re-check 1: the design defines type checks and per-pier handling, and the spec covers malformed saved values beside a valid pier.) Design D3 now says that the edge checks types before
  any string work. A pier entry that is not a mapping passes through, and the
  core skips it. A `horizon_points` value that is not text skips its pier at the
  edge, with an error naming `horizon_points`. The spec adds this case to the
  skip list, and adds the scenario "Malformed saved values skip only their
  pier".
- **Moderate 2 — fixed; accepted by reviewer** (re-check 1: the ADR review distinguishes a structured list from a text field and explains how this changes ADR-0020's example.) `adr.md` now says that ADR-0020's remark about horizon
  points concerns a structured list, which still does not fit. This change holds
  the points as one text field, so ADR-0020's decision holds. Only its example
  is out of date. The accepted ADR itself is not edited.
- **Moderate 3 — fixed; accepted by reviewer** (re-check 1: the design gives explicit pass criteria for the fields and save behaviour in a real Home Assistant instance.) The design's risks section now lists five pass
  criteria for the real-instance check. They cover the field labels, a bracketed
  value, an unbracketed value, and clearing each field. The check also records
  the Home Assistant and Supervisor versions.
- **Suggestion: plain language — partly applied.** The long ADR-manifest
  sentence is split. The "review completed" sentence is kept, because the schema
  requires the manifest to state it. The design still opens by pointing to the
  proposal, because the schema tells the design not to restate the proposal.
- **Suggestion: rollback — applied.** The migration plan now says that a user
  who rolls back and upgrades again must enter their horizon values again.
