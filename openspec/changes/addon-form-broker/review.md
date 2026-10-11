## Review Metadata

- **Review round**: 2
- **Prior round**: Round 1 — VERDICT: REVISE. Two broker-source and error-advice conflicts were critical; the password logging check was ambiguous.
- **Reviewer context**: cross-model (GPT, `gpt-6-sol` via `codex exec`)
- **Tool restrictions**: read-only sandbox (`codex exec -s read-only`)
- **Artifacts reviewed**: The specified proposal, design, ADR manifest, delta spec, current `ha-addon` spec, repository guidance, ADRs, source files, tests, and Supervisor reference.

<!-- STALENESS: This verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ other than -->
<!-- applying the Required Change voids the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The password logging guarantee is impossible as written.** The delta spec requires the log to name the broker host, but also says no log line or error message may contain the password field’s value ([delta spec](openspec/changes/addon-form-broker/specs/ha-addon/spec.md:401)). If the user enters the same text for host and password, logging the host contains that value. The [proposal](openspec/changes/addon-form-broker/proposal.md:35) makes the same absolute claim. The new scenarios use distinct values, resolving the test ambiguity but not the wording conflict.

### 📌 Suggestions

- Keep the result of the [design’s live form check](openspec/changes/addon-form-broker/design.md:171), including the recorded Home Assistant and Supervisor versions, with implementation verification.
- No material ISO 24495 plain-language issue was found in the proposal, design, delta spec, or ADR manifest.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

The round 1 broker-source and error-advice conflicts are resolved. One wording correction remains.

## Required Changes (if APPROVE WITH CHANGES)

1. In the proposal and delta spec, replace the absolute password-value claim with a requirement that the service does not read or interpolate `mqtt.password` to construct a log or error message. Allow the host to be logged when the user independently enters the same text as the password. Keep the distinct-value log and rejected-login scenarios.

CHANGES_APPLIED: no

## Rebuttals

- **Supervisor default versus form broker:** Resolved. The modified requirement applies to file settings; the added requirement covers the [form broker](openspec/changes/addon-form-broker/specs/ha-addon/spec.md:381).
- **Supervisor errors pointing form users to `config.yaml`:** Resolved. The spec gives advice by settings source, and [design D5](openspec/changes/addon-form-broker/design.md:129) passes the setting location to `fetch_mqtt_broker`.
- **Password logging check:** The distinct-value and rejected-login scenarios resolve the test ambiguity. The absolute prose claim remains open as the Required Change.
- **Live form check:** Addressed. The design specifies four checks and records Home Assistant and Supervisor versions.
- **ADR summary:** The reviewer accepts the author’s response. The manifest adequately identifies the decision considered and the relevant ADRs.

This is not a second consecutive `REVISE` verdict, so the stated escalation condition is not met.