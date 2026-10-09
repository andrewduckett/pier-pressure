## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (Codex, GPT family; separate from the authoring context)
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/ha-delivery/spec.md, adr.md, the durable ha-delivery spec, relevant source and tests, ADR-0012, ADR-0018, and AGENTS.md. `openspec/project.md` is absent. GitHub issues #41, #43, and #44 could not be read because `gh` could not reach GitHub.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

1. **The process can stop reconnecting permanently after an outage.** `design.md:195–201` accepts having no network-thread check after startup, but the delta spec (`specs/ha-delivery/spec.md:5–11`) requires the process to keep trying. In pinned paho 2.1, `_handle_connack` can make an immediate MQTT-version or client-ID retry after a refused connection (`client.py:3858–3889`). If that retry raises `OSError`, the network thread can end; `_thread_main` then clears `_thread` (`client.py:4521–4525`). The existing contract test demonstrates this failure path at startup. It can also occur after a previously successful connection, when a replacement broker rejects the protocol or client ID. With no post-startup watcher, neither replay nor another reconnect follows. The plan needs a recovery mechanism for a stopped thread, or evidence and a narrower requirement showing this path cannot occur after startup.

### 🟡 Moderate

1. **The spec asserts broker and Home Assistant outcomes that the proposed tests cannot establish.** `specs/ha-delivery/spec.md:64–69` says every entity’s configuration and state are retained on the broker and that no entity waits to reappear. The design records a message when `_publish` returns success (`design.md:147–153`), but pinned paho says `publish()` returns an `MQTTMessageInfo` whose delivery status must be checked separately (`client.py:1709–1744`). A successful return does not prove broker receipt. The durable ha-delivery spec limits automated scenarios to observable MQTT output and reserves entity rendering for manual acceptance. Specify the publish calls, payloads, retain flags, and ordering that PierPressure controls; identify any broker-level acceptance check separately. This also requires correcting “exactly what the broker last received” in `design.md:151`.

2. **The ADR review is marked complete while an identified ADR conflict remains unresolved.** `adr.md:29–33` notes that ADR-0018 says callbacks “only record the outcome for the main thread,” while D2 makes `on_connect` subscribe on the network thread. The manifest then leaves a future “review step” to decide whether the ADR needs clarification. Resolve that conflict in this change’s ADR review, including whether ADR-0018 needs an amendment, before calling the review complete.

3. **The reconnect startup scenario does not define one testable event order.** `specs/ha-delivery/spec.md:83–87` combines a drop before every pier has a verdict with the existing startup order. `design.md:128–132` describes a narrower case in which startup finishes before the queued replay runs. The scenario does not say whether the drop occurs before or after `online`, or whether a publish occurs while disconnected; the latter exits under the stated #43 boundary. Name the connection and publish sequence that the change supports, then assert its MQTT output.

4. **Plain-language issues obscure the acceptance boundary.** In the delta spec, “every entity’s discovery config and state is retained on the broker again” and “no entity waits for the next interval to reappear” (`specs/ha-delivery/spec.md:68–69`) shift from PierPressure’s observable actions to outcomes it cannot directly verify. In `design.md:151–153`, “exactly what the broker last received” states an unverified guarantee. In `adr.md:8–9`, “ADR review completed” hides who resolved the review, although `adr.md:33` leaves a decision open. State the actor, observable action, and acceptance evidence in each place. The proposal is generally clear and has no separate plain-language finding.

### 📌 Suggestions

1. `design.md:49–50` says draining queued markers caps frequent reconnects, but it only merges markers present in one drain. Say that directly; a later reconnect can cause another replay.
2. Add a contract test for the post-startup thread-exit path if the revised design depends on detecting and recovering from it.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: REVISE

The post-startup thread-exit path defeats the change’s core reconnect requirement. Revise the artifacts and run a full review in a fresh context.

## Required Changes (if APPROVE WITH CHANGES)

Not applicable.

CHANGES_APPLIED: n/a

## Rebuttals

Author responses for round 1. All findings are fixed, not rebutted. A new full
review round in a fresh context re-checks them.

- **Critical 1 (paho thread can end after startup):** fixed. Design D7 adds a
  watcher that keeps paho's thread running for the life of the process. The delta
  spec adds a scenario for a failed immediate try during a reconnect. The Risks
  entry that accepted this gap is removed.
- **Moderate 1 (outcomes PierPressure cannot verify):** fixed. The scenario now
  asserts the publish calls, payloads, retain flags and order. Design D4 now says
  "what PierPressure last published", not "what the broker last received".
- **Moderate 2 (ADR-0018 conflict left open):** fixed. ADR-0018 gains an
  amendment for this change, and `adr.md` records it.
- **Moderate 3 (startup reconnect scenario has no single order):** fixed. The
  scenario now names one sequence: the connection drops and returns before the
  startup health reset, and the process publishes nothing while disconnected.
- **Moderate 4 (plain language):** fixed in the places cited.
- **Suggestion 1 (drain wording):** applied in design Non-Goals and Risks.
- **Suggestion 2 (contract test for post-startup thread exit):** applied in D6.
