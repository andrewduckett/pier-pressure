## Review Metadata

- **Review round**: 2
- **Prior round**: 1
- **Reviewer context**: cross-model (OpenAI Codex CLI)
- **Tool restrictions**: read-only inspection
- **Artifacts reviewed**: proposal.md, design.md, specs/ha-delivery/spec.md, adr.md

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **SIGTERM can miss cleanup after connection.** [design.md](openspec/changes/stop-goes-offline/design.md:104) says the existing `main()` path handles SIGTERM. In [__main__.py](pierpressure/__main__.py:139), `subscribe_refresh()` and the following log call sit between the `connect()` handler and the `service.run()` `try/finally`. SIGTERM there raises `KeyboardInterrupt` without calling `close()` or returning status 0. The proposed handler needs a cleanup path covering this interval.

2. **The promised offline outcome is stronger than the design can deliver.** [design.md](openspec/changes/stop-goes-offline/design.md:40) promises that every connected planned stop *leaves* retained availability `offline`, but [D2](openspec/changes/stop-goes-offline/design.md:98) correctly says that a timed-out publish may never reach the broker. A subsequent clean DISCONNECT suppresses the will, leaving `online` retained. The reconnecting case also assumes the broker has already sent the will; a connection can be lost before the broker detects it. Align the proposal, goal, and spec with the bounded, best-effort behavior the design actually provides.

3. **The delta spec is hard to scan and leaves the wait imprecise.** The dense paragraphs at [spec.md:5](openspec/changes/stop-goes-offline/specs/ha-delivery/spec.md:5) and [spec.md:7](openspec/changes/stop-goes-offline/specs/ha-delivery/spec.md:7) combine the existing will contract, planned-stop rule, failure behavior, and rationale in long sentences. Split them into short statements. Give the “bounded time” scenario a measurable limit consistent with D2 so a test can assert the timeout passed to paho.

### 📌 Suggestions

1. A reconnect between the `_phase` check and `disconnect()` could produce a clean disconnect without an `offline` publish. [design.md:78](openspec/changes/stop-goes-offline/design.md:78) should acknowledge this residual race when narrowing the guarantee. A new synchronization scheme for this rare case would be disproportionate to the stated small fix.
2. [proposal.md:10](openspec/changes/stop-goes-offline/proposal.md:10) uses “avoids it” without naming the stale availability it means. [adr.md:28](openspec/changes/stop-goes-offline/adr.md:28) repeats “None” in the same bullet. Both are small plain-language cleanups; the rest of those artifacts is clear.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Revise D3 and the SIGTERM scenario so cleanup and status 0 also cover termination after `connect()` returns and before `service.run()` begins. Specify that the entry point’s cleanup scope includes `subscribe_refresh()`.
2. Revise the absolute offline claims in the proposal, design goal, and delta spec to state the actual guarantee: attempt a retained QoS 1 `offline` publish, wait up to two seconds for confirmation, then finish shutdown. State plainly that a broker which never receives it can retain `online`; do not claim the will has necessarily fired as soon as the client detects a disconnection.
3. Split the two opening spec paragraphs into short, findable requirements and make the two-second wait mechanically assertable in the unconfirmed-message scenario.

CHANGES_APPLIED: yes

## Rebuttals

- **Moderate 1 (SIGTERM gap after connect): fixed.** design.md D3 now moves the `try`/`finally` that calls `close()` to start right after `connect()` returns, covering `subscribe_refresh()`, the log and `service.run()`. The SIGTERM scenario now says "at any time after the broker accepts the connection". — accepted by reviewer: D3 covers the identified interval, and the scenario specifies status 0.
- **Moderate 2 (overstated guarantee): fixed.** The proposal, the design goal and the delta spec now call the offline publish a best effort, say a broker that never receives it keeps `online`, and no longer say the broker has already sent the last-will. — accepted by reviewer: the subscriber guarantee now concerns unexpected death; planned stops require an attempted retained QoS 1 publish, a wait of at most two seconds, and shutdown even without confirmation.
- **Moderate 3 (dense spec, imprecise wait): fixed.** The spec's new rules are a short list. The wait is "at most two seconds", and the unconfirmed-message scenario asserts it. — accepted by reviewer: the opening requirements are now split into short statements, and the scenario gives a measurable two-second limit.
- **Suggestion 1 (reconnect race): fixed.** design.md Risks now names the race and accepts it.
- **Suggestion 2 (plain-language cleanups): fixed.** proposal.md now says what the add-on stop leaves; adr.md no longer repeats "None".