## Review Metadata

- **Review round**: 3
- **Prior round**: Rounds 1 and 2 both returned REVISE; the author revised the thread recovery plan, broker outcome claims, ADR alignment, startup order, resend handling, subscription reporting, and publish wording.
- **Reviewer context**: cross-model (Codex CLI, GPT family; separate from the authoring context)
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/ha-delivery/spec.md, adr.md, the durable ha-delivery spec, relevant source and tests, ADR-0012, ADR-0018, and AGENTS.md. `openspec/project.md` is absent. GitHub issues were unavailable from the sandbox.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **A subscription refusal can lose its topic name in the startup race.** [D2](openspec/changes/reconnect-restores-delivery/design.md) says the adapter maps the message ID returned by `subscribe()` to a topic, but specifies a lock only for the topic-to-pier map. Startup subscribes on the main thread while paho reads SUBACK on its network thread. The pinned client queues SUBSCRIBE before returning its message ID (`client.py:3612–3652`), so `on_subscribe` can run before the adapter records that ID. The promised warning may then lack the refused topic. D2 needs synchronization for message-ID registration and acknowledgement handling.

2. **The disconnected-publish claim is too absolute.** The design says `publish()` while disconnected returns `MQTT_ERR_NO_CONN` ([design.md](openspec/changes/reconnect-restores-delivery/design.md), lines 26–28), and the proposal says a publish during the outage “still raises `DeliveryError`” ([proposal.md](openspec/changes/reconnect-restores-delivery/proposal.md), lines 48–52). In pinned paho 2.1, a QoS 1 publish returns success and enters its queue when the inflight limit is already full (`client.py:1787–1817`), without checking the socket on that branch. This does not bring outage publishes into this change’s scope, but the explanation of that boundary is inaccurate.

3. **“The state follows within moments” promises a time the design cannot bound.** The phrase in [proposal.md](openspec/changes/reconnect-restores-delivery/proposal.md), line 36, conflicts with [D3 and Risks](openspec/changes/reconnect-restores-delivery/design.md): the main thread handles a reconnect marker after any recompute already in progress. Replace the time claim with that observable sequence. This is the remaining material plain-language issue; the revised spec and ADR are clear and findable.

### 📌 Suggestions

None.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. In D2, specify that startup and reconnect subscription calls register their returned message IDs under the same lock used by `on_subscribe` to look up and remove them. Add a planned test that makes a startup SUBACK arrive before the subscribing thread can otherwise record the ID, and asserts that a refusal warning names the topic.
2. Qualify the disconnected-publish statements in the proposal and design. State that outage publishes retain the existing adapter behavior and remain outside this change; do not claim every such call returns `MQTT_ERR_NO_CONN` or raises `DeliveryError`.
3. Replace “The state follows within moments” in the proposal with wording that allows the replay to wait for the main thread’s current recompute.

CHANGES_APPLIED: yes

## Rebuttals

- **Round 2 Critical 1 — earlier `online` resent before replay:** accepted by reviewer. The revised proposal, design, and spec disclose the resend and limit the order requirement to messages published after reconnect.
- **Round 2 Moderate 1 — a subscribe call does not prove Refresh works:** accepted by reviewer. The revised design checks both the call result and SUBACK, while the spec states the broker-access assumption and requires a topic-specific warning. Finding 1 above concerns a separate race in associating a SUBACK with its topic.
- **Round 2 Moderate 2 — queued versus delivered wording:** accepted by reviewer. D4 now says paho “accepts it for sending,” and the spec defines what “publish” means for this requirement.
- **Round 2 suggestion — resend contract test:** accepted by reviewer as a planned test. D6 now calls for a real-paho test of the unacknowledged QoS 1 resend.
- **Round 1 findings:** accepted in round 2; no prior finding is reopened here.

Author responses for round 3. The re-check of these items follows below.

- **Required change 1 (subscription race):** applied in D2. One subscription
  lock covers the subscribe call and the message ID registration, and
  `on_subscribe` takes it too. D2 explains why the lock cannot deadlock with
  paho's locks. D6 adds a test that makes the broker's answer race the
  registration.
- **Required change 2 (disconnected-publish claim):** applied in the design's
  Context and the proposal's Out of scope. Both now say that a publish during
  the outage keeps the adapter's existing behaviour, and that paho usually, not
  always, reports it as not connected.
- **Required change 3 ("within moments"):** applied in the proposal. The replay
  follows once the main thread is free, after any recompute in progress.

## Round 3 Re-check

Codex re-checked only the listed Required Changes, in a fresh context.

- **Required change 1:** accepted by reviewer. D2 synchronizes message ID
  registration and SUBACK handling, and D6 plans the race test.
- **Required change 2:** at first not accepted, because a Risks entry still said
  a publish during the outage stops the process. The author qualified that
  entry. On a second re-check: accepted by reviewer. The design and proposal
  keep the existing adapter behaviour and qualify the outcomes of a publish
  during the outage.
- **Required change 3:** accepted by reviewer. The proposal now says the replay
  waits for any recompute in progress.

All Required Changes are applied and re-checked, so the author set
`CHANGES_APPLIED: yes`.
