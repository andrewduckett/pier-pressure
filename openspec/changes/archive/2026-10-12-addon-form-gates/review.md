## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (OpenAI, via codex exec, read-only sandbox)
- **Tool restrictions**: read-only inspection; no files edited, created, or deleted
- **Artifacts reviewed**: `proposal.md`, `design.md`, `specs/ha-addon/spec.md`, `adr.md`; `.workspace/issue74.md`; `AGENTS.md`; the current `openspec/specs/ha-addon/spec.md`; `pierpressure/addon_options.py`, `pierpressure/addon_settings.py`, `pierpressure/core/config.py`, `pierpressure/core/scoring.py`; `ha-addon/config.yaml`, `ha-addon/translations/en.yaml`, `ha-addon/DOCS.md`; `README.md`; `tests/test_ha_addon.py`, `tests/test_addon_options.py`, relevant `tests/test_addon_settings.py`; ADR-0020, ADR-0021; the archived equipment design; and [Home Assistant’s app configuration documentation](https://developers.home-assistant.io/docs/apps/configuration/).

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in this round. Any later edit to proposal.md, design.md, or specs/ other than applying the Required Changes voids it. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The default scenarios do not show how to test the stated behavior.** In `specs/ha-addon/spec.md:139–153`, “uses a GO threshold of 65,” “has no wind gate,” and “uses a gust limit of 40” have no controlled score or gust against which to assert the result. A verdict alone does not expose those settings. Add observable boundary cases or say explicitly that the test inspects the validated pier configuration.

2. **The proposal describes set and unset values as though they take the same path.** `proposal.md:19–25` says the service passes “both values to the core unchanged,” then says it removes an empty field. The design correctly distinguishes them: set values pass through; unset values are omitted. State that distinction in the proposal.

### 📌 Suggestions

- In `proposal.md:21–22` and `specs/ha-addon/spec.md:115–119`, name the service as the actor: “The service skips the invalid pier, logs an error, and publishes the others.” This makes the behavior easier to follow. The four artifacts otherwise use short sentences and largely consistent terms.
- The [Home Assistant documentation](https://developers.home-assistant.io/docs/apps/configuration/) confirms the optional `?` syntax and the `int(min,max)` and `float(min,max)` forms. It does not state whether bounds are inclusive. The equipment design is a precedent for `float(0,)?`; a live Supervisor check of 0 and the range endpoints would verify the design’s save behavior.

The main code claims checked out: `translate_form` currently passes flat pier keys through; `pier_settings` and `combine_settings` already recognize both keys; a saved null `go_threshold` reaches `PierConfig` and fails validation, while omission uses 65; and the wind reason names the configured km/h limit. No design–spec conflict or unvalidated new trust boundary was found.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Revise the default and file-fill scenarios in `specs/ha-addon/spec.md` so each stated threshold or wind-limit outcome has a mechanically assertable check. Use controlled scores and gusts, or explicitly inspect the validated pier configuration.
2. Revise `proposal.md:19–25` to say that set values pass unchanged and unset values are omitted before core validation.

CHANGES_APPLIED: yes

## Rebuttals

- **Moderate 1 (default scenarios not testable): fixed.** "Empty fields use the
  defaults" now says the pier passes the service's checks, and its checked
  settings hold a `go_threshold` of 65 and no `max_gust`. "config.yaml fills an
  empty field" now says the pier's checked settings hold a `max_gust` of 40. The
  scenario "A gust over the form's limit is a NO-GO" still covers the gate's
  observable effect.
- **Moderate 2 (proposal merged set and unset paths): fixed.** The proposal now
  says the service passes a set value to the core unchanged, and leaves out a
  cleared field before the core checks the pier.
- **Suggestion 1 (name the actor): applied.** The proposal and the new
  requirement now say the service skips the pier, logs an error and publishes
  the other piers.
- **Suggestion 2 (live check of the Supervisor's bounds): declined for this
  round.** The equipment fields already rely on the inclusive lower bound of
  `float(0,)`. The tasks will include a live check of 0 and of the range ends on
  a Home Assistant instance, as the equipment change did.

Reviewer re-check of the Required Changes (same reviewer, read-only):

- Moderate 1: accepted by reviewer. The revised scenarios make the default
  threshold and wind limit assertable through the pier's checked settings.
- Moderate 2: accepted by reviewer. The proposal now separates set values,
  passed unchanged, from cleared fields, left out before the core's checks.
