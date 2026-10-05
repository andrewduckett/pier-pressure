## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (codex CLI, GPT family)
- **Tool restrictions**: read-only sandbox
- **Artifacts reviewed**: `proposal.md`, `design.md`, `adr.md`, `specs/conditions/spec.md`, `specs/ha-delivery/spec.md`, `docs/decisions/0015-provider-health-beside-verdict-in-memory.md`, and relevant source files

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

1. **A restart can expose an old retained success time as current.** `design.md:104–111` says health starts with no history but is published *after* the verdict. `specs/ha-delivery/spec.md:17–20,60–64` requires that a pre-restart success time never be shown as current. The existing startup path publishes retained `online` availability before `Service.run()` fetches or publishes (`pierpressure/delivery/mqtt.py:427–445`; `pierpressure/__main__.py:58–76`). If that fetch stalls, the explainer delays publication, or verdict publication fails, Home Assistant can display the old retained health timestamp while the entity is available. Retained state is replayed when discovery subscribes to its topic. [Home Assistant MQTT documentation](https://www.home-assistant.io/integrations/mqtt). This concern would not matter only if the design guaranteed that old health state is cleared before the entity can appear online, including when startup publication fails.

2. **The proposed error redaction cannot meet its privacy requirement.** `design.md:155–164` says generic errors use the exception’s text with URLs removed. `proposal.md:27–28` and `specs/conditions/spec.md:15–16,44–47` promise that neither coordinates nor the request URL can appear. A provider exception such as `RuntimeError("bad latitude 51.5")` has no URL to remove and would publish the coordinate in retained attributes and Home Assistant history. The design needs an allowlisted description or another rule that covers coordinates outside URLs, plus tests for that case. URL removal alone cannot establish the stated guarantee.

### 🟡 Moderate

1. **The promised automation can miss a provider that is already stale or unknown when Home Assistant restarts.** `proposal.md:29–31` promises notification “including after a restart”; `design.md:166–175` specifies an age-based template trigger and an `unknown` state trigger with `for`. Home Assistant resets pending `for` timers on restart or automation reload, and a template trigger fires on a false-to-true transition. An already stale value can therefore remain stale without causing either trigger to fire. [Home Assistant trigger documentation](https://www.home-assistant.io/docs/automation/trigger/). Add a scenario for this sequence and specify a trigger and condition that checks the current state after restart.

2. **The attribute contract excludes the seeded, untried state that the design requires.** `specs/ha-delivery/spec.md:5–8,22–28` requires discovery for configured providers that were not tried, but describes latest status only as `ok` or `failed` and latest fetch time as a time. `design.md:91–94,146` instead seeds providers with no history and sets both fields to null. Specify nullable status and attempt time for an untried provider, with a scenario that asserts the published state and attributes.

3. **“Validates against Home Assistant’s MQTT discovery schema” is not a mechanically defined test.** `specs/ha-delivery/spec.md:10–15,41–46` requires this validation, while `pierpressure/delivery/ha_schema.py:3–8` says its schema is hand-authored and Home Assistant ships no single machine-readable discovery schema. Passing the local schema cannot prove the stated THEN clause. Define the exact local checks and separately require a Home Assistant integration check for the resulting timestamp and availability behavior. The proposed literal `None` payload itself is supported by current MQTT sensor code. [Home Assistant MQTT sensor source](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/mqtt/sensor.py).

4. **The design equates two timestamps taken by separate clock calls.** `design.md:17–18,173–175` says Open-Meteo’s issue time “always equals” last success, but `pierpressure/conditions/open_meteo.py:95–97` stamps `issued_at` during `fetch()`, while `design.md:100–102` adds a separate attempt timestamp in `CompositeProvider`. A production clock can advance between those calls. State whether these timestamps may differ or require one sampled instant for both.

5. **ADR-0015 gives an incorrect determinism argument.** `docs/decisions/0015-provider-health-beside-verdict-in-memory.md:48–52` says a health field would break byte identity because a document could differ for “identical conditions.” The repository’s guarantee is identity for the *same inputs*, including the evaluation instant (`AGENTS.md`, “Pure, deterministic core”). Health could be another explicit input without violating determinism. The ADR can justify separation using the frozen verdict contract and operational boundary, but should not claim that determinism alone rules out the alternative.

6. **Terminology and dense prose make the artifacts harder to use together.** The same reported event is a “fetch outcome” in `proposal.md:54–56` and `specs/conditions/spec.md:3–9`, but a `FetchAttempt` or “attempt” in `design.md:45–54`. `adr.md:8–13` compresses the decision and the disposition of several design choices into a long paragraph; the ADR’s front-matter description at `docs/decisions/0015-provider-health-beside-verdict-in-memory.md:6` is also a single dense sentence. Use one term for the event across the artifacts and split those passages so readers can find the decision and its reason quickly. The remaining proposal and scenario prose is generally clear.

### 📌 Suggestions

1. `design.md:91–98` seeds untried providers chiefly for a future failover chain, although `design.md:93–94` says both current providers are always tried. State whether this is a present requirement or future provision; the latter commits the service to extra metadata wiring without a current user case.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: REVISE

The restart and privacy failures affect explicit requirements. Revise the artifacts and run a full new review before generating downstream work.

## Required Changes (if APPROVE WITH CHANGES)

Not applicable.

CHANGES_APPLIED: n/a

## Rebuttals

- 🔴 1 (restart shows old retained time): fixed. design.md D3 now publishes every configured provider's empty health first in `run()`, before any fetch or explainer call. A failed publish raises, the process exits, and the last-will message marks it offline. ha-delivery spec adds the startup scenario.
- 🔴 2 (redaction cannot meet the privacy rule): fixed. design.md D5 now builds the error from an allowlist (error type, plus status code and reason for HTTP status errors). It never uses free-form exception text. The conditions spec adds a scenario for a message that carries coordinates without a URL.
- 🟡 1 (automation misses an already-stale sensor after an HA restart): fixed. design.md D6 now uses one template trigger that covers both stale and long-unknown, plus a Home Assistant start trigger with the same condition.
- 🟡 2 (untried state excluded): fixed. ha-delivery spec makes status and attempt time null before the first fetch, with a scenario.
- 🟡 3 (schema validation not mechanical): rebutted. The ha-delivery Purpose already defines this phrase for every existing requirement: payloads are checked against the repository's hand-authored discovery schemas, and Home Assistant's own rendering is a manual check. design.md Risks now names the manual check for timestamp, `None`, and availability.
- 🟡 4 (Open-Meteo times from separate clock calls): fixed. design.md and the README note now say the two times come from the same fetch and differ by moments at most.
- 🟡 5 (ADR determinism argument): fixed. ADR-0015 Alternative 1 now argues from the frozen contract and document churn, not determinism.
- 🟡 6 (terminology, dense prose): fixed. "Fetch outcome" and `FetchOutcome` are now the one term. adr.md summary and the ADR description are split into shorter sentences.
- 📌 1 (seeding is speculative): addressed. Seeding is now needed today, for the startup publish in 🔴 1.
