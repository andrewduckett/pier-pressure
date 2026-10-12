## Review Metadata

- **Review round**: 2
- **Prior round**: REVISE — silent horizon overwrite, contradictory duplicate-azimuth scenario, and an ADR promise of identical messages.
- **Reviewer context**: cross-model (GPT `gpt-6-sol` via `codex exec`, read-only sandbox)
- **Tool restrictions**: read-only inspection; no files created, edited, or deleted
- **Artifacts reviewed**: proposal.md, design.md, both delta specs and their existing specs, adr.md, ADR-0022, and relevant source and tests. Issue #83 was unavailable because GitHub could not be reached.

This verdict applies only to the artifact contents reviewed in this round. A later edit to the proposal, design, or delta specs voids it.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The collision fix would reject configurations that work today.** [Design D2–D3](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/design.md:88) says to leave flattened fields unchanged whenever a saved `horizon` or `equipment` value is set. Consider a valid `horizon` block beside blank `horizon_points`, or a valid `equipment` block beside `equipment_focal_length_mm: null`. Today, translation removes those unset fields and keeps the block. Under the design, the core rejects the leftover fields as unknown. That conflicts with the [proposal’s compatibility promise](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/proposal.md:104) and the [delta spec’s treatment of blank horizon text as unset](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/ha-addon/spec.md:58). Preserve removal of fields that `is_set` counts as unset; leave **set** fields visible for core rejection. Specify and test both cases.

2. **Unexpected top-level saved settings can still disappear before core validation.** The [proposal](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/proposal.md:30), [delta requirement](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/ha-addon/spec.md:3), and [ADR-0022](/home/andrew/Git/projects/pier-pressure/docs/decisions/0022-core-is-the-only-place-that-validates-settings.md:31) say the add-on passes unexpected values to the core. But the planned translation retains the [current top-level construction](/home/andrew/Git/projects/pier-pressure/pierpressure/addon_options.py:118), which copies only `piers`, `interval_seconds`, and `mqtt`. For example, a hand-written `options.json` containing `explainer: {"enabled": "bad"}` silently loses that setting. Define whether the rule covers top-level saved values. If it does, specify how they reach core validation and cover the case; if it does not, narrow the promise consistently.

### 📌 Suggestions

- The [ha-addon delta](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/ha-addon/spec.md:60) says “This covers four cases” and then lists five. Correct the count to keep the requirement easy to scan.
- The [horizon-mask delta](/home/andrew/Git/projects/pier-pressure/openspec/changes/addon-options-core-validates/specs/horizon-mask/spec.md:5) carries forward a dense paragraph from the main spec. Splitting its ordering, range, and duplicate rules would improve findability. I found no new sentence over 30 words, hidden actor, or brainstorming narrative that independently blocks this round.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: REVISE

This is the second consecutive REVISE verdict. Escalate the unresolved findings to the human; do not generate a test plan or tasks under this verdict.

## Required Changes (if APPROVE WITH CHANGES)

Not applicable.

CHANGES_APPLIED: n/a

## Rebuttals

Author responses to round 2, applied before round 3. The human chose the
direction for both after the second REVISE.

1. **Moderate 1 — the collision fix keeps unset fields: fixed.** Design D2 and D3
   now drop each flat field that `is_set` counts as unset first. Only set fields
   stay beside a `horizon` or `equipment` value. The ha-addon delta adds the
   scenarios "A horizon mapping beside unset horizon fields is used" and "An
   equipment mapping beside unset equipment fields is used". The ADDED
   requirement states the unset-field rule.
2. **Moderate 2 — unknown top-level keys disappear: fixed by narrowing.** The
   proposal, the ADDED requirement and ADR-0022 now say the add-on passes on
   unexpected values only for the settings the form declares, and ignores any
   other top-level key, as the Supervisor does. The design lists this as a
   non-goal and a trade-off.
3. **Suggestion — "four cases" lists five: adopted.**
4. **Suggestion — split the dense horizon paragraph: declined.** It is unchanged
   text from the main spec.

Round 1 rebuttals were all accepted by the reviewer in round 2.
