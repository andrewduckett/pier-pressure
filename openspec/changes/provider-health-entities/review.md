## Review Metadata

- **Review round**: 2
- **Prior round**: Round 1: REVISE — 2 critical (restart retained time, error redaction), 6 moderate
- **Reviewer context**: cross-model (codex CLI, GPT family)
- **Tool restrictions**: read-only sandbox
- **Artifacts reviewed**: `proposal.md`, `design.md`, `adr.md`, `specs/conditions/spec.md`, `specs/ha-delivery/spec.md`, `docs/decisions/0015-provider-health-beside-verdict-in-memory.md`, `openspec/config.yaml`, the current conditions and HA delivery specs, and relevant source files and tests

## Findings

### 🔴 Critical (blocking)

1. **A normal startup can briefly show a pre-restart success as current.** `design.md:95–105` publishes the reset after `connect()` publishes `online` and expressly accepts that Home Assistant could “flash the old value.” Discovery is also published before the reset state (`design.md:120–142`). This contradicts `specs/ha-delivery/spec.md:17–26`, which says the sensor “SHALL NOT show a retained time from before the restart.” [Home Assistant replays retained MQTT sensor state](https://www.home-assistant.io/integrations/sensor.mqtt/). The plan needs an ordering that clears old state before the entity can be online with that state.

2. **The failed-startup path does not reliably mark retained health offline.** `design.md:99–100` and `specs/ha-delivery/spec.md:22–26` rely on the last will after a health publish failure. But `pierpressure/__main__.py:75–80` calls `delivery.close()` in `finally`, and `pierpressure/delivery/mqtt.py:556–560` disconnects cleanly; [paho says a clean disconnect does not send the will](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html). Further, `_publish()` checks only `info.rc` (`mqtt.py:447–451`), while [paho requires `wait_for_publish()` or equivalent to establish delivery](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html). A queued reset can be lost without raising. Define and test the broker acknowledgment and failure behavior before relying on either guarantee.

3. **The error “allowlist” still admits provider-controlled text.** `design.md:168–174` permits an HTTP response’s “reason”; `specs/conditions/spec.md:15–19` promises the published description can never contain a request URL or pier coordinates. The reason phrase is [part of the HTTP response](https://www.python-httpx.org/api/), so a response can supply `503` with a reason containing a coordinate or URL. Use a fixed description derived from the numeric status, or omit the reason. Test a malicious reason phrase.

### 🟡 Moderate

1. **An already-unknown sensor can still miss the intended alert after a Home Assistant restart.** `proposal.md:31–33` promises notification “including after a restart, when the last success is unknown.” `design.md:190–204` measures unknown age with `last_changed`, but `design.md:219–221` acknowledges that a Home Assistant restart resets that age. The start trigger then fails its condition, and notification waits another full threshold. Specify that delay in the promise or provide a way to retain the age. The stale-timestamp branch of the round 1 concern is fixed; the unknown branch is not.

2. **The discovery-validation THEN clause still names a schema that the test does not use.** `specs/ha-delivery/spec.md:10–15,48–53` says payloads validate against “Home Assistant’s MQTT discovery schema.” `pierpressure/delivery/ha_schema.py:1–8` calls the repository schema hand-authored, and `design.md:213–218` adds a separate manual Home Assistant check. Name the local schema in the mechanically asserted scenario and keep the manual rendering check separate.

3. **Successful fetches may have no issue time under the existing provider contract.** `specs/conditions/spec.md:5–9` says every successful outcome carries the returned data’s issue time; `specs/ha-delivery/spec.md:35` allows null only “when there is none.” Yet `pierpressure/conditions/provider.py:54–68` permits a nonempty `SourceForecast` with `issued_at=None`. Define whether that is a valid success and, if so, require a nullable issue time; otherwise require providers to supply one.

4. **Two passages still slow down readers.** `proposal.md:14–17` puts five attribute definitions in a 38-word sentence. `design.md:213–218` buries the manual acceptance check and a possible design change in one bracketed risk item. Split the attribute list and state the check and fallback as separate actions. The remaining prose in `adr.md`, both delta specs, and ADR-0015 is clear and findable.

### 📌 Suggestions

1. `design.md:102–105` calls the stale-state interval a “flash.” State its actual limit only after broker acknowledgment and message ordering are defined; otherwise the term understates an unbounded failure.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: REVISE

The retained-state and privacy guarantees remain unsatisfied. This is the second consecutive REVISE round; escalate to the human reviewer under the review instructions before generating test-plan, tasks, or implementation artifacts.

## Required Changes (if APPROVE WITH CHANGES)

Not applicable.

CHANGES_APPLIED: n/a

## Rebuttals

Round 1 reviewer adjudication; no author response has been entered for this round.

- 🔴 1, restart retained time — **not accepted**: the design accepts a visible stale interval and does not establish delivery of the reset or offline status on failure.
- 🔴 2, error redaction — **not accepted**: the permitted HTTP reason phrase remains uncontrolled response text.
- 🟡 1, automation after Home Assistant restart — **not accepted**: the stale-timestamp case is covered, but an already-unknown sensor loses its elapsed age.
- 🟡 2, untried state — **accepted by reviewer**: `specs/ha-delivery/spec.md:28–35,67–71` now defines and asserts null status and fetch time before the first fetch.
- 🟡 3, discovery schema validation — **not accepted**: the scenario still calls the hand-authored schema “Home Assistant’s MQTT discovery schema.”
- 🟡 4, separate Open-Meteo clock calls — **accepted by reviewer**: `design.md:15–20` no longer requires exact timestamp equality.
- 🟡 5, ADR determinism argument — **accepted by reviewer**: ADR-0015 now bases the decision on the frozen contract and document churn (`docs/decisions/0015-provider-health-beside-verdict-in-memory.md:46–54`).
- 🟡 6, terminology and dense ADR prose — **accepted by reviewer**: the event terminology is consistent and the cited ADR passages are shorter. The current proposal and design readability issues are listed above.
- 📌 1, speculative seeding — addressed: startup reset now gives seeding a present use.
### Author responses to round 2 (after escalation to the human, 2026-10-05)

The human chose the approach for 🔴 1, 🔴 2, and 🟡 1.

- 🔴 1 (startup shows an old time): fixed by the human's choice. design.md D4 resets health before `go_online()` publishes `online`. The spec adds "before it publishes its online availability" and a failed-reset scenario.
- 🔴 2 (last will and unconfirmed publishes): split out by the human's choice into bug #41, which affects every entity. The spec now promises only that a failed reset exits without publishing `online`. design.md D4 records the known limit.
- 🔴 3 (server reason phrase): fixed. design.md D6 takes the phrase from `http.HTTPStatus`, never from the response. The conditions spec adds a malicious-reason scenario.
- 🟡 1 (unknown age lost on an HA restart): fixed by the human's choice. Attributes gain `tracking_since`, and design.md D7 measures unknown age from it.
- 🟡 2 (schema wording): fixed. The new requirement says "the repository's discovery schema". design.md has a separate "Manual check in Home Assistant" section.
- 🟡 3 (success with no issue time): fixed. Both specs allow a null issue time after a success.
- 🟡 4 (dense passages): fixed. The proposal's attribute list is now bullets. The manual check is its own section with numbered steps.
- 📌 1 ("flash"): addressed. The window no longer exists.
