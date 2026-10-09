## Review Metadata

- **Review round**: 2
- **Prior round**: round 1: REVISE (2 critical, 2 moderate, 1 suggestion)
- **Reviewer context**: cross-model: Gemini 3.1 Pro (High) via agy, plan mode, files inlined, no tools, fresh context
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/, openspec/project.md (if present), relevant source files

## Findings

### 🔴 Critical (blocking)

1. **Code does not implement the proposed design:** The provided source code completely lacks the implementation of the core design decisions D1, D2, D3, and D5.
   - `pierpressure/delivery/mqtt.py`: `_publish` still calls `_send` *before* recording to `_retained`, and its docstring still says "The record is made once paho accepts the message for sending" (violating D2). `_send` still unconditionally raises `DeliveryError` for any non-success return code and does not check `_phase` (violating D1 and D3).
   - `pierpressure/__main__.py`: `main()` still catches `DeliveryError` from `service.run()` (violating D5).
   - `pierpressure/service.py`: `_reset_health` docstring still claims it `Raises :class:~pierpressure.delivery.mqtt.DeliveryError if the publish fails, so the process exits`.
   The change cannot proceed when the source code actively contradicts the approved design and proposal.
2. **Spec Contradicts Design and Code on Startup Reconnect (Unresolved from Round 1):** The scenario "A reconnect during startup keeps the startup order" in `specs/ha-delivery/spec.md` is factually incorrect under the new design. The spec defines "publish" as handing a message to the MQTT client. When disconnected, the design (D1) requires holding messages, NOT handing them to the client. Therefore, the process does *not* publish them during the outage. The scenario's assertion `- **THEN** the process publishes the startup health reset, then its online availability, then a verdict for each pier` followed by `- **AND** it then publishes that same health and those verdicts again` is false. The MODIFIED block must update this scenario to reflect the reality of the replay order, not preserve a legacy requirement that is no longer accurate.
3. **Untestable Scenario with Fake Client (Unresolved from Round 1):** The scenario "A message still being sent at the drop does not change the order" requires the connection to drop "before the broker acknowledges it". `FakeMqttClient`'s `publish` method is synchronous and immediately appends to `self.published`. It does not model in-flight messages or asynchronous PUBACKs. A test that verifies behavior "with online already published" is not testing a drop *before* acknowledgement. The scenario must be rewritten to describe a condition that the fake client can mechanically assert.

### 🟡 Moderate

1. **Plain Language (ISO 24495) violations - Passive Voice:** The spec contains passive voice that hides the actor.
   - `specs/ha-delivery/spec.md`: "A delivery failure SHALL NOT corrupt or partially publish an entity's state such that a stale value is presented as current without indication." (Change "is presented" to active).
   - `specs/ha-delivery/spec.md`: "It SHALL be published retained to the discovery topic..." (Change to active, e.g., "The system SHALL publish it...").
   - `specs/ha-delivery/spec.md`: "Health SHALL be held in memory only..." (Change to active, e.g., "The system SHALL hold health...").
   - `specs/ha-delivery/spec.md`: "A message handed to the client before then MAY be sent again by the client..." (Change to active).

### 📌 Suggestions

*(None for this round)*

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: REVISE

## Required Changes (if APPROVE WITH CHANGES)

CHANGES_APPLIED: n/a

## Rebuttals

- Critical 1 (startup order on reconnect) — REJECTED. The MODIFIED block is explicitly for modifying requirements that change. Since D1 causes messages to be held (not handed to the MQTT client, which is the spec's definition of "publish"), the scenario's assertion that the process publishes them during the outage and then publishes them again is factually false. The scenario must be updated to match the replay order reality.
- Critical 2 (untestable "A message still being sent at the drop" scenario) — REJECTED. The MODIFIED block must accurately reflect testable reality. `FakeMqttClient` does not model PUBACKs or in-flight messages. Testing a drop *after* `FakeMqttClient` has appended the message to `self.published` does not satisfy the condition "before the broker acknowledges it". The scenario must be rewritten to match what is mechanically assertable.
- Moderate 1 (passive voice) — ACCEPTED by reviewer (Fixed in proposal.md, design.md, and ADR-0019).
- Moderate 2 ("ADR review completed for this change." as filler) — ACCEPTED by reviewer (Schema completion marker).
- Suggestion 1 (online lost on a drop between replay and go_online) — ACCEPTED by reviewer (Documented in D1).

### Author responses to round 2 (awaiting human decision: two consecutive REVISE verdicts)

- Critical 1 (code does not implement the design) — REBUTTED. This is a planning review; implementation follows in the apply phase, after `tasks.md`. Unchanged source code is expected at this stage.
- Critical 2 (startup reconnect scenario false under D1) — REBUTTED. In "A reconnect during startup keeps the startup order", the new connection is accepted *before* the process publishes the startup reset. The phase is then `CONNECTED`, so D1 holds nothing: the process hands the startup order, then the replay, to the client, exactly as the scenario says. D1 holds messages only while the phase is `RECONNECTING`.
- Critical 3 (untestable "A message still being sent at the drop") — PARTLY CONCEDED, OUT OF SCOPE. The fake client does not model a missing acknowledgement. The scenario is #44's unchanged text, and #44's test accepted it. Rewriting #44's scenarios is not part of this story; a follow-up can make the fake client model in-flight messages.
- Moderate 1 (passive voice in the spec) — FIXED for the sentence this change adds ("The MQTT client MAY send a message it received before then again after the reconnect"). The other three sentences are existing spec text that this change does not touch.
