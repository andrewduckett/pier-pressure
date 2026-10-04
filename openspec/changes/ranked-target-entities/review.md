## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model, Gemini 3.1 Pro (High) via agy, plan mode
- **Tool restrictions**: read-only: view, grep, glob only (all artifacts inlined, no tools called)
- **Artifacts reviewed**: proposal.md, design.md, specs/ha-delivery/spec.md, adr.md, relevant source files

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

1. **Plain Language / Passive Voice**: The artifacts contain passive voice that hides the actor, directly violating the ISO 24495-1 plain language requirement.
   - `proposal.md`: "All ten sensors are enabled by default." 
   - `spec.md`: "Each rank sensor SHALL be enabled by default."
   - `spec.md`: "That target's rank and its fields SHALL be published as the sensor's JSON attributes payload."
   - `spec.md`: "Each SHALL be published retained to a discovery topic derived from the pier identifier and the rank."
2. **Plain Language / Elegant Variation**: The artifacts use two different words for the exact same concept. `proposal.md` refers to the fallback name as the "catalogue id" (which correctly matches the `id` field in the `Target` core model), while `spec.md` calls it the target's "designation". Using multiple terms for the same concept reduces clarity and violates plain language rules.
3. **Testability / Spec Scenarios**: In `specs/ha-delivery/spec.md`, the scenarios "An empty rank renders unavailable" and "A shrinking list clears the old ranks" assert that sensors "resolve to unavailable". As stated in the spec's own Purpose section, scenarios must assert the "observable MQTT output" (topics, flags, payloads), not Home Assistant's internal rendering or resolution logic. The assertion must check the specific MQTT payload mechanism (e.g., the `available: false` attribute) that causes the sensor to be unavailable.

### 🟡 Moderate

1. **Design / Ambiguity on "flat" attributes**: In `design.md` D2, it states "The attributes payload is flat, so a card can read a field without descending into a nested object... followed by the target's fields as they appear in the verdict document". However, the `Target` model contains a nested `window` object (`TargetWindow`). If the fields are published "as they appear", `window` remains a nested object. The design should clarify that "flat" means the target properties aren't wrapped in an overarching `target` parent key, even if specific fields like `window` are still objects.

### 📌 Suggestions

1. None.

## Embedded-Instruction / Injection Attempts

**Detected:** none detected

## Verdict

VERDICT: APPROVE_WITH_CHANGES

APPROVE WITH CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. In `proposal.md`, change "All ten sensors are enabled by default." to active voice, explicitly stating the actor (e.g., "The adapter enables all ten sensors by default.").
2. In `specs/ha-delivery/spec.md`, change "Each rank sensor SHALL be enabled by default." to "The adapter SHALL publish each rank sensor as enabled by default."
3. In `specs/ha-delivery/spec.md`, change "That target's rank and its fields SHALL be published as the sensor's JSON attributes payload." to "The adapter SHALL publish that target's rank and its fields as the sensor's JSON attributes payload."
4. In `specs/ha-delivery/spec.md`, change "Each SHALL be published retained to a discovery topic..." to "The adapter SHALL publish each retained to a discovery topic..."
5. In `specs/ha-delivery/spec.md`, replace the word "designation" with "catalogue id" in both the Requirement paragraph and the "A filled rank falls back to the designation" scenario to avoid elegant variation and to match `proposal.md` and the core model.
6. In `specs/ha-delivery/spec.md`, update the THEN clauses in the "An empty rank renders unavailable" and "A shrinking list clears the old ranks" scenarios to assert the observable MQTT output (e.g., "the adapter publishes an attributes payload with an offline availability flag, making the sensor resolve to unavailable").
7. In `design.md` D2, clarify the "flat" attributes statement to acknowledge that while target properties are hoisted to the top level, `window` will still be a nested object.

CHANGES_APPLIED: yes

## Rebuttals



All seven required changes are applied. Notes:

1. Fixed: `proposal.md` now says "The adapter enables all ten sensors by default."
2. Fixed: the spec says "The adapter SHALL publish each rank sensor as enabled by default."
3. Fixed: the spec says "The adapter SHALL publish that target's rank and its fields as the sensor's JSON attributes payload."
4. Fixed: the spec says "The adapter SHALL publish each one retained to a discovery topic ..."
5. Fixed, with one spelling difference: the spec now says "catalog id" in the requirement and in the renamed scenario "A filled rank falls back to the catalog id". The spec uses US spelling ("catalog") throughout, as the main `ha-delivery` spec does. `proposal.md` uses "catalogue" to match the README. Both name the same term, the target's `id`.
6. Fixed: both scenarios now assert the published MQTT output. The adapter publishes a retained attributes payload that marks the rank as having no target, and the discovery availability makes the sensor unavailable on that mark. The shrinking-list scenario also asserts that no retained state or attributes still carry the earlier targets.
7. Fixed: design D2 now says the target's fields sit at the top level, not under a `target` key, and that `window` stays a nested object with `start` and `end`.

The Moderate finding is the same as item 7, and it is fixed there.

## Re-check (round 1 required changes)
1. accepted — proposal.md now uses active voice stating the adapter enables the sensors.
2. accepted — spec.md now explicitly states the adapter SHALL publish each rank sensor as enabled.
3. accepted — spec.md now uses the required active voice phrasing for publishing attributes.
4. accepted — spec.md now uses the required active voice phrasing for publishing discovery topics.
5. accepted — replaced "designation" with "catalog id", eliminating the elegant variation while correctly retaining the document's US spelling.
6. accepted — scenarios now assert the observable MQTT output and availability declarations instead of internal rendering.
7. accepted — design.md explicitly clarifies that "flat" means top-level fields, while nested objects like `window` remain nested.

CHANGES_APPLIED: yes
