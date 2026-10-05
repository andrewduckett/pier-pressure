## Review Metadata

- **Review round**: 3
- **Prior round**: Round 2: REVISE — escalated to the human, who chose the fixes for startup order, the last-will split (#41), and tracking_since
- **Reviewer context**: cross-model (codex CLI, GPT family)
- **Tool restrictions**: read-only sandbox
- **Artifacts reviewed**: `proposal.md`, `design.md`, `adr.md`, `specs/conditions/spec.md`, `specs/ha-delivery/spec.md`, `docs/decisions/0015-provider-health-beside-verdict-in-memory.md`, `openspec/config.yaml`, the current conditions and HA delivery specs, and relevant source files and tests

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The proposal promises an alert count that survives a PierPressure restart, but the design resets it.** `proposal.md:34–37` says measuring from the tracking start means “a restart of PierPressure or of Home Assistant does not reset the count.” `design.md:95–97,140–141` creates a new `tracking_since` when `run()` starts and discards health on restart; ADR-0015:38–40 accepts that reset. If a provider has never succeeded and PierPressure restarts just before the alert threshold, the unknown-age count starts again. The promise must describe a Home Assistant restart only, or the design must retain age across PierPressure restarts.

2. **“When the process started” does not identify the time the design records.** `proposal.md:17` and `specs/ha-delivery/spec.md:31` define the attribute as the time the process started. `design.md:95` records it when `Service.run()` starts, after configuration loading, broker connection, and service construction in `pierpressure/__main__.py:52–76`. A slow startup makes the published time later than the stated start time and delays an unknown-age alert. Define the attribute as the instant `run()` begins, before the reset, and use that meaning consistently.

3. **The ADR manifest treats MQTT topic names as cheap to change.** `adr.md:14–17` includes “the topic names” among decisions that “can be read from the code and changed cheaply.” `AGENTS.md` calls the delivery surface, including topics and entity mapping, a frozen contract. After users bind automations to a health sensor, renaming its topic or identity would break that contract. The manifest must identify the new topic names as durable delivery choices.

4. **The promised Home Assistant restart alert has no acceptance check.** `design.md:221–241` describes a template trigger and a Home Assistant start trigger; `proposal.md:34–37` promises notification after a Home Assistant restart. The scenarios in `specs/ha-delivery/spec.md:69–86` check the sensor reset, while the manual checks in `design.md:267–275` stop at sensor display and availability. If the start trigger evaluates before retained attributes arrive, the alert depends on the template’s later transition. Add a verification case that starts Home Assistant with an already-old `tracking_since` and an unknown sensor, then checks that the automation notifies.

### 📌 Suggestions

1. **Correct the rationale for the rejected verdict-field alternative.** ADR-0015:46–54 says adding health to the verdict “would become a new input to the core.” An adapter could append it without passing it to the core. The durable-contract change and document churn stated in the same passage are sufficient reasons; removing the inevitable-core-input claim would make the decision easier to trust.

2. **Give the manual check a useful failure path.** `design.md:277–278` proposes a `value_template` that maps the payload to `None` if the unknown-state check fails. It does not explain how that differs from the literal `None` payload already specified in `design.md:166–168`. State what failure the template would address before prescribing it. Home Assistant’s [MQTT sensor documentation](https://www.home-assistant.io/integrations/sensor.mqtt/) describes `None` as an unknown-state payload.

3. **Make the design’s trade-offs easier to scan.** The bracket-and-arrow entries in `design.md:250–265` mix risks, effects, and responses in one line. Plain “Risk” and “Response” sentences would make each decision more findable. The conditions delta spec, HA delivery delta spec, proposal attribute list, ADR manifest, and ADR-0015 otherwise use short, direct prose.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

The four moderate findings have bounded edits and checks. No new critical defect was found.

## Required Changes (if APPROVE WITH CHANGES)

1. Correct `proposal.md:34–37` to say that a Home Assistant restart preserves the unknown-age calculation, while a PierPressure restart begins a new count.
2. Define `tracking_since` in the proposal and HA delivery spec as the time `Service.run()` begins, before startup health is reset.
3. Revise `adr.md:14–17` so it does not describe MQTT topic names as cheaply changeable; identify them as part of the stable delivery surface.
4. Add a verification case for the README automation after a Home Assistant restart with an unknown sensor whose `tracking_since` is already past the threshold.

CHANGES_APPLIED: yes

## Rebuttals

### Reviewer adjudication of round 2

- 🔴 1, old time during startup — **accepted by reviewer**: `design.md:99–118` now orders the health reset before `go_online()`.
- 🔴 2, last will and unconfirmed publishes — **accepted by reviewer**: the human assigned that shared delivery gap to issue #41; `design.md:127–130` records the limit.
- 🔴 3, server reason phrase — **accepted by reviewer**: `design.md:196–207` uses the fixed `http.HTTPStatus` phrase, and `specs/conditions/spec.md:46–50` covers a hostile response phrase.
- 🟡 1, unknown age after a Home Assistant restart — **accepted by reviewer**: `tracking_since` supplies an age independent of Home Assistant’s `last_changed`. The separate PierPressure restart promise is finding 1 above.
- 🟡 2, discovery schema wording — **accepted by reviewer**: `specs/ha-delivery/spec.md:10–12,55` names the repository schema; `design.md:267–275` separates the real Home Assistant check.
- 🟡 3, success without issue time — **accepted by reviewer**: `specs/conditions/spec.md:8–9` and `specs/ha-delivery/spec.md:36–37` permit null.
- 🟡 4, dense passages — **accepted by reviewer**: the proposal now lists attributes in bullets, and the manual Home Assistant check has its own section.

### Author responses to round 3
- Required 1 (🟡 1): applied. proposal.md now says a Home Assistant restart keeps the count, and a PierPressure restart starts a new one.
- Required 2 (🟡 2): applied. proposal.md and the ha-delivery spec define `tracking_since` as the moment the service loop starts, just before the startup reset. design.md D3 matches.
- Required 3 (🟡 3): applied. adr.md no longer lists topic names as cheap to change. It names the new topics, identities, and attribute names as part of the stable delivery surface.
- Required 4 (🟡 4): applied. design.md "Manual check in Home Assistant" adds check 5 for the README automation after a Home Assistant restart.
- 📌 1: applied. ADR-0015 Alternative 1 drops the "new input to the core" claim.
- 📌 2: applied. design.md now says what failure the fallback addresses: Home Assistant treating the literal `None` as an invalid timestamp.
- 📌 3: declined. The bracket-and-arrow risk format matches the earlier designs in this repository.

### Reviewer re-check of required changes (round 3)

- Required 1: accepted by reviewer — The proposal says a Home Assistant restart preserves the count and a PierPressure restart begins a new one.
- Required 2: accepted by reviewer — The proposal, HA delivery spec, and design define `tracking_since` as the time `Service.run()` begins, just before the startup reset.
- Required 3: accepted by reviewer — The ADR manifest identifies the new topics, entity identities, and attribute names as part of the stable delivery surface.
- Required 4: accepted by reviewer — The design adds a manual check that the README automation notifies after Home Assistant restarts with an already-old `tracking_since` and an unknown sensor.

