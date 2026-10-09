## Review Metadata

- **Review round**: 2
- **Prior round**: Round 1 — REVISE: one critical thread-recovery gap and four moderate findings about broker outcomes, ADR alignment, startup order, and plain language.
- **Reviewer context**: cross-model (Codex CLI, GPT family; separate from the authoring context)
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/ha-delivery/spec.md, adr.md, the durable ha-delivery spec, relevant source and tests, ADR-0012, ADR-0018, and AGENTS.md. `openspec/project.md` is absent. GitHub issues were unavailable from the sandbox.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

1. **An older `online` publish can reach a restarted broker before the replayed state.** The proposal says no entity shows as available while its state is missing (`proposal.md:30–32`), and the spec requires state before `online` (`specs/ha-delivery/spec.md:19–27`). Consider an earlier QoS 1 `online` publish that paho accepted but the broker had not acknowledged when the connection failed. If the broker restarts without retained messages, paho 2.1 keeps that outgoing message across a clean-session reconnect (`client.py:3712–3740`) and resends it after CONNACK (`client.py:3949–3986`). That resend can precede the main thread’s queued replay. The broker can therefore hold `online` while discovery and state are still missing, even though PierPressure publishes nothing during the outage. The design must account for pending paho messages or narrow the availability promise and its acceptance criteria. The proposed call-order tests cannot establish the current promise.

### 🟡 Moderate

1. **The plan treats a subscription call as proof that Refresh works.** D2 says a Refresh press is “never lost while the main thread is busy” (`design.md:93–100`), and the spec says Refresh works after reconnect (`specs/ha-delivery/spec.md:47–52`). Paho’s `subscribe()` returns a result and message ID; calling it does not establish that the broker accepted the subscription (`client.py:1894–1901`, `2035–2038`). A broker can accept CONNACK but reject a topic subscription. State whether the requirement assumes the broker grants the same topic access, and specify how a failed subscription is observed or reported.

2. **The revised prose still blurs a queued publish with a delivered one.** D4 says it records a message after `_publish` “succeeds” (`design.md:148–154`), while the proposal calls this the state PierPressure “sent” (`proposal.md:26–32`). The current adapter checks only `info.rc` (`mqtt.py:656–660`); pinned paho says delivery requires a separate `is_published()` or `wait_for_publish()` check (`client.py:1733–1745`). Say “accepted for sending” where that is the evidence. This distinction also makes the ordering limit in the critical finding easier to understand. The proposal, delta spec, and ADR are otherwise structured clearly; this is the remaining plain-language defect in the reviewed artifacts.

### 📌 Suggestions

- Add a contract test with an unacknowledged QoS 1 `online` message at reconnect. It would expose paho’s automatic resend order, which the scripted fake does not model.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: REVISE

The availability-order guarantee fails on a paho 2.1 resend path. This is the second consecutive REVISE verdict; escalate to the human before another author-review loop. Do not generate test-plan or tasks while this verdict is in force.

## Required Changes (if APPROVE WITH CHANGES)

Not applicable.

CHANGES_APPLIED: n/a

## Rebuttals

- **Round 1 Critical 1 — paho thread can end after startup:** accepted by reviewer. D7 adds a lifetime watcher and the spec covers a failed immediate try after an outage; the new critical finding concerns pending publishes, not thread recovery.
- **Round 1 Moderate 1 — unverifiable broker outcomes:** accepted by reviewer for the cited scenario. The revised scenario asserts PierPressure’s publish calls, payloads, retain flags, and order. This review identifies a separate resend path that defeats the proposal’s stronger availability claim.
- **Round 1 Moderate 2 — ADR-0018 conflict:** accepted by reviewer. The dated amendment records callback subscriptions, reconnect logging, and the lifetime watcher.
- **Round 1 Moderate 3 — startup-reconnect order:** accepted by reviewer. The revised scenario names a drop and return before the startup health reset, followed by one stated publish order.
- **Round 1 Moderate 4 — plain language:** accepted by reviewer for the cited passages. Those passages were revised; the remaining queued-versus-delivered wording is identified above.
- **Round 1 Suggestion 1 — drain wording:** accepted by reviewer. The design now says only markers present in one drain are merged.
- **Round 1 Suggestion 2 — post-startup thread-exit contract test:** accepted by reviewer as a planned test. D6 specifies the test against a real paho client.