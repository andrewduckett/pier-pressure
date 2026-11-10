## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (`gemini/gemini-3.8-flash` through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only. The working tree stayed clean (`"gitClean": true`).
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `51041ab`
- **Effort**: low, from design.md's scrutiny tier

The reviewer gave the verdict APPROVE_WITH_CHANGES. It raised no Critical finding. The author adjudicates below: two small listed edits fix findings 1 and 2, so the verdict stands.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **"The top-target sensor's state is the top target's name" also requires the ordered list in the attributes, which its heading does not name and its added scenario does not assert.** The scenario that asserts the list, "Top-target discovery and state are published", sits under the discovery requirement. — **CONFIRMED** for the heading. Fixed by required change 1.
2. **"Each configured provider has a health sensor named after it" carries "publish discovery for every configured provider, including a provider not tried on this publish", with no reason in design.md and no scenario for an untried provider.** — **CONFIRMED** for the missing reason. Fixed by required change 2. The missing scenario is **OUT-OF-SCOPE** (see Rebuttals).
3. **The scenario "A narrative entity from an earlier configuration is left in place" sets up a retained broker state that `test_disabled_delivery_publishes_no_narrative` does not.** — **REFUTED** (see Rebuttals).

### 📌 Suggestions

4. **Plain language:** sentences of 37 to 46 words in three narrative and Cloud cover requirements. — **Declined** (see Rebuttals).
5. **"sixteen keys" in a heading, where the glossary's term is "variable".** — **Declined** (see Rebuttals).

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. In the delta, rename "The top-target sensor's state is the top target's name" to "The top-target sensor shows the top target's name and the ordered list". Use the new heading in design.md, and record in design.md Decision 1 which scenario asserts the list.
2. In design.md Decision 1, add the reason that the untried-provider sentence stays with one health sensor per configured provider.

CHANGES_APPLIED: yes

## Rebuttals

1. **Fixed.** Required change 1 is applied in `specs/ha-delivery/spec.md`, design.md Decisions 1 and 3, and the REMOVED Reason the build script writes. `openspec validate split-long-reqs-ha-delivery-entities --strict` still passes. The two statements stay in one requirement because they are the original's two sentences about what the sensor shows. Splitting them would leave one with no scenario, or need a second added scenario.
2. **Fixed, and the scenario is out of scope.** Required change 2 is applied in design.md Decision 1. The untried-provider sentence says which providers get a sensor, which is the same behavior as one sensor per configured provider. The main spec has no scenario for an untried provider today. The epic adds a scenario only where a split leaves a requirement with none (decision 4), and this requirement has the added names scenario. A later change can add one.
3. **Refuted.** The adapter never reads retained discovery: it subscribes only to each pier's refresh command topic (`pierpressure/delivery/mqtt.py:1182` to `:1203`, `subscribe_refresh` and `_subscribe_all`). So a retained narrative discovery on the broker cannot change what the adapter publishes, which is the reviewer's own condition for the finding not to matter. The test's assertion, that no narrative topic gets any message while disabled, is exactly the scenario's THEN.
4. **Declined.** Two of the three sentences are the main spec's own, copied unchanged. The Cloud cover sentence is the original's, with "that hour" spelled out as "the hour that contains the document's generation timestamp" so that it reads alone. A wording pass across `ha-delivery` is a separate change.
5. **Declined.** "Key" is the accurate word. The glossary defines a variable as a quantity the conditions carry, but `sun_altitude` and `moon_altitude` are computed by the core, and the requirement's own text and scenarios already say "keys". The heading follows them.
