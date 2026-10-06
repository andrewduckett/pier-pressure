## Review Metadata

- **Review round**: 3
- **Prior round**: Round 1: REVISE on the core boundary, errors, deadline, TLS advice, Purpose and ADR criterion. Round 2: REVISE on the deadline, relative horizon paths, MQTT 3.1 and Purpose, with one plain-language suggestion.
- **Reviewer context**: cross-model (Codex CLI, GPT family), fresh context
- **Tool restrictions**: read-only inspection
- **Artifacts reviewed**: proposal, delta and main specifications, design, ADR manifest, ADR-0017, relevant source and tests, Supervisor source, Mosquitto discovery source, and the README add-on section

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The Supervisor token could be sent through an environment-configured proxy.** [design.md](../../../openspec/changes/ha-addon-mqtt-service/design.md) specifies `Authorization: Bearer $SUPERVISOR_TOKEN` for `http://supervisor/services/mqtt`, then says the client “takes an `httpx.Client`” without specifying how the production client handles proxies. HTTPX uses `HTTP_PROXY` and `ALL_PROXY` by default, so a proxy set in the container could receive that bearer token. [HTTPX documents this default](https://www.python-httpx.org/environment_variables/). **Require a direct request to the local Supervisor in the delta spec; specify `trust_env=False` for the production client in the design, and test the behavior with proxy variables set.**

2. **The startup scenario promises more than polling can guarantee.** The [delta spec](../../../openspec/changes/ha-addon-mqtt-service/specs/ha-addon/spec.md) says that if “the service appears within 60 seconds,” PierPressure uses it. [design.md](../../../openspec/changes/ha-addon-mqtt-service/design.md) instead stops *starting* requests after 60 seconds. A request begun just before the limit can time out after the broker appears, leaving no permitted retry. **Make the success scenario depend on a request begun within the limit returning usable broker details. State the corresponding failure condition in terms of requests, too.** This does not change the maintainer’s chosen timeout policy.

### 📌 Suggestions

1. **Correct two stale statements in the design.** [design.md](../../../openspec/changes/ha-addon-mqtt-service/design.md) says the client “reads five fields” after listing six (`host`, `port`, `username`, `password`, `ssl`, `protocol`). It also says “`tasks.md` lists this as an explicit archive task,” although that file does not yet exist. **Say six fields, and phrase the archive task as work to include when `tasks.md` is created.**

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Add the direct-to-Supervisor token requirement, production `trust_env=False` decision, and proxy-environment test described in Moderate 1.
2. Align the startup success and failure scenarios with the request-based retry rule described in Moderate 2.

CHANGES_APPLIED: yes

## Rebuttals

Author responses to round 3. All findings were fixed; none was rebutted.

- **Moderate 1 (token through a proxy): fixed.** The delta spec now requires the
  service to send its requests and the token straight to the Supervisor, with a
  "Proxy settings do not reach the token" scenario. Design D3 builds the
  production client with `trust_env=False` and names the proxy-variable test.
  The proposal's test list includes it.
- **Moderate 2 (startup scenarios): fixed.** The wait requirement and both
  startup scenarios now depend on a request started within the 60 seconds
  returning usable broker details.
- **Suggestion (stale statements): fixed.** D3's risk note says six fields. The
  Migration Plan says `tasks.md` must include the Purpose update when written.

Reviewer re-check of the listed items (cross-model, Codex CLI, GPT family):

- First re-check: all three items applied. It flagged a new wording slip, "the
  broker's request", in the wait requirement. RECHECK: FAIL.
- The author changed it to "a request started within those 60 seconds".
- Second re-check: all three items applied, and no new issues. RECHECK: PASS.
  Accepted by reviewer.

## Review History

- **Round 1: REVISE.** 1 Critical: an injected lookup let the core trigger
  network access, against ADR-0005. 4 Moderate: the main spec's Purpose was
  edited before archive; 401 and 403 gave misleading advice; the 60-second limit
  was not defined at the request boundary; the TLS advice still failed. 1
  Suggestion: name the ADR bar. All fixed.
- **Round 2: REVISE.** 1 Critical: an `httpx` timeout cannot enforce a strict
  60-second total. 3 Moderate: the config split lost the folder for relative
  horizon files; Supervisor protocol 3.1 was unhandled; the Purpose would stay
  wrong after archive. 1 Suggestion: a sentence over 30 words. After two REVISE
  rounds, the maintainer was consulted. They chose to bound the wait by when
  requests start, rather than build a wall-clock cut-off, and to apply the
  other fixes.
- **Round 3: APPROVE_WITH_CHANGES.** Shown above. Required Changes applied and
  re-checked.
