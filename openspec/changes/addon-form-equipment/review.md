## Review Metadata

- **Review round**: 3
- **Prior round**: Round 2 — VERDICT: REVISE. The file-versus-form ranking scenario did not fix every input or a known-size target; zero and negative coverage missed the sensor fields; there was no `null` scenario; the manual check was not a task; the proposal overstated the effect; the ADR manifest restated the design. The author revised all of these, and the user approved a third round.
- **Reviewer context**: cross-model (GPT, `gpt-6-sol` via `codex exec`, reasoning effort medium)
- **Tool restrictions**: read-only sandbox (`codex exec -s read-only`)
- **Artifacts reviewed**: proposal.md, design.md, adr.md, specs/ha-addon/spec.md, and relevant source files

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

- **[design.md](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-form-equipment/design.md:146), “a manual check … is its own task in tasks.md.”** There is no `tasks.md` in this change. The plan still has no trackable task for checking that Home Assistant displays, saves, and clears these fields. Add the task with the four pass conditions listed in the design, and record the Home Assistant and Supervisor versions used.

### 🟡 Moderate

- **[specs/ha-addon/spec.md](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-form-equipment/specs/ha-addon/spec.md:112), “the top pick at the chosen evaluation instant has a known catalog size.”** The instant, conditions, catalog fixture, and expected top pick remain unspecified. A test can select inputs after seeing the result, weakening the ranking check. Name a fixed instant and complete input fixture, including a known-size target; assert the expected field-of-view reason as well as document equality.

- **[design.md](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-form-equipment/design.md:44), “Any other key passes through, and the core rejects it as unknown.”** That does not say what happens if saved JSON contains both an `equipment` block and flat equipment fields. An implementation could overwrite the block and silently discard an unexpected value. Specify that an existing `equipment` key passes through to core validation or causes that pier to be skipped; add a test. The options file is an input boundary even when the form normally prevents this combination.

- **[design.md](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-form-equipment/design.md:158), “the user should clear the four fields before rolling back.”** The migration section also says the older schema lacks those fields and the Supervisor may retain them. It therefore gives a rollback step the user may be unable to perform in that form. Resolve the saved-value behavior or give a workable rollback procedure. [Home Assistant’s configuration documentation](https://developers.home-assistant.io/docs/apps/configuration/) recommends removing options when a deployed app removes schema keys.

### 📌 Suggestions

- **[specs/ha-addon/spec.md](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-form-equipment/specs/ha-addon/spec.md:22), “Each SHALL be a number of at least 0.”** Say explicitly that this is the *form’s save bound* and that the service rejects zero. That makes the two validation stages easier to find and reconciles this sentence with the strictly positive equipment rule.

- **[design.md](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-form-equipment/design.md:9), “The edge is the code outside the pure core…”** The first fact bullet runs past 30 words and interrupts the account of what `addon_options.py` does. Split the definition from the code fact. The ADR manifest’s review summary also repeats the design’s translation decision; shorten it to the ADR outcome and references.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

## Required Changes (if APPROVE WITH CHANGES)

None. The verdict is REVISE.

CHANGES_APPLIED: n/a

## Rebuttals

This is the third REVISE in a row. After round 2 the review was escalated to the
user. The user approved round 3 and told the author to continue to tasks after
it, without a fourth round. The rebuttals below have not been re-checked by the
reviewer.

- 🔴 **No `tasks.md` holds the manual check** — rebutted. The schema writes
  `tasks.md` only after this review, so the reviewer could not see it.
  `tasks.md` now carries the manual check as its own task, with the four pass
  conditions and the versions to record.
- 🟡 **The ranking scenario does not fix its inputs** — partly fixed, partly
  rebutted. The scenario already requires both piers to share every input and
  to say how the top pick fits in `reasons[]`. Choosing the exact instant and
  fixture is a test detail, so it lives in `tasks.md`: the test fixes them
  before running and asserts the expected reason.
- 🟡 **An `equipment` key beside the flat fields** — fixed. Design D1 now skips
  such a pier with an error that names `equipment`. The spec adds the case and a
  scenario.
- 🟡 **The rollback step may be impossible** — fixed. The migration plan now
  tells the user to clear the four fields on the new version's form, which still
  shows them, before rolling back.
- 📌 **Save bound versus the service's rule** — fixed in the spec's form
  requirement.
- 📌 **A long sentence in the design's context, and a recap in the ADR
  manifest** — fixed. The definition of "the edge" is split out, and the manifest
  now states only its outcome.
