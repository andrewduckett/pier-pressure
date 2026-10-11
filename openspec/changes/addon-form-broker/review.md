## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (GPT, `gpt-6-sol` via `codex exec`)
- **Tool restrictions**: read-only sandbox (`codex exec -s read-only`)
- **Artifacts reviewed**: proposal.md, design.md, adr.md, the `ha-addon` delta and current spec, repository guidance, ADR-0017, ADR-0020, relevant source, add-on files, README, tests, and `.workspace/options.py`

<!-- This verdict applies only to the artifact contents reviewed in this round. -->

## Findings

### 🔴 Critical (blocking)

- **The broker-source requirements conflict when an ignored file exists.** The [delta spec](openspec/changes/addon-form-broker/specs/ha-addon/spec.md:189) requires a form with `mqtt.host` to supply all four connection settings without asking the Supervisor. The [current spec](openspec/specs/ha-addon/spec.md:477) still requires all four settings from the Supervisor when `config.yaml` has no host. Both conditions can hold when the form lists piers and an ignored file has no host. Limit the existing requirement and its scenarios to the file-settings path.

- **Supervisor error advice conflicts across requirements.** The [delta spec](openspec/changes/addon-form-broker/specs/ha-addon/spec.md:98) directs form users to the Configuration tab. The [current spec](openspec/specs/ha-addon/spec.md:569) directs users facing a missing broker, access refusal, TLS requirement, or unsupported MQTT version to `config.yaml`. Make that advice depend on whether the service is using form or file settings.

### 🟡 Moderate

- **The password-log guarantee is too absolute to test as written.** The [delta spec](openspec/changes/addon-form-broker/specs/ha-addon/spec.md:207) requires the log to name the host while forbidding any log line containing the password. A user could enter identical host and password text. Specify that the password field’s value must never be logged *as a credential*, and test with distinct host and password values.

### 📌 Suggestions

- **Make the live form check reproducible.** The [design](openspec/changes/addon-form-broker/design.md:150) says a Home Assistant OS check confirmed the empty block and password field work, but gives no version or check record. Record the version and steps or link to durable evidence.

- **Tighten the ADR summary.** “ADR review completed” and “No major durable architectural decisions” in the [ADR manifest](openspec/changes/addon-form-broker/adr.md:8) leave the review’s scope and “major” unclear. Name the decision reviewed and why the existing ADRs cover it. No sentence over 30 words or material filler was found elsewhere in the change artifacts.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: REVISE

## Required Changes (if APPROVE WITH CHANGES)

Not applicable.

CHANGES_APPLIED: n/a

## Rebuttals

None.