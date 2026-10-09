## Review Metadata

- **Review round**: 3
- **Prior round**: Round 1 REVISE on pause timing, the Supervisor wait, logging coverage, thread death, retained online state and plain language. Round 2 REVISE (escalated to the human, who approved the fixes and this round): paho’s immediate tries bypassed the stated pause and log rules; a failed immediate try ended the thread; the blocking-connect alternative rested on an incorrect premise.
- **Reviewer context**: cross-model (Codex CLI, GPT family), fresh context
- **Tool restrictions**: read-only inspection; no files changed
- **Artifacts reviewed**: `proposal.md`, `design.md`, `specs/ha-delivery/spec.md`, `adr.md`, ADR-0018, AGENTS.md, the existing delivery spec, ADR-0012, relevant source and tests, add-on documentation, installed paho 2.1.0 source, and the Supervisor checkout. `openspec/project.md` is absent.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

None. The revised requirements and design agree with the checked paho paths. The proposal, design, spec, and ADR use clear, actionable language; I found no plain-language defect that warrants a finding.

### 📌 Suggestions

1. **Tighten one callback claim.** Design D4 says paho calls `on_disconnect` “after a socket failure” (`design.md:180`). An initial socket-open failure calls `on_connect_fail` without `on_disconnect` (`paho/mqtt/client.py:2279–2287`). This does not affect the proposed logging rule, but the sentence should distinguish socket-open failure from loss of an established socket.
2. **Extend the real-paho checks if practical.** D5 tests the code 1 fallback and thread death (`design.md:217–225`). A focused code 2 test would also pin the generated-client-ID path that the spec permits.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE

## Required Changes (if APPROVE WITH CHANGES)

None.

CHANGES_APPLIED: n/a

## Rebuttals

1. **Round 2 Critical 1 — fixed.** The spec now defines paho’s code 1 and code 2 immediate tries as part of the preceding attempt (`spec.md:23–28`). The installed paho source confirms both paths return before `on_connect` and each can occur at most once with this client’s defaults (`client.py:3867–3889`).
2. **Round 2 Critical 2 — fixed.** D2 restarts a thread that ends without an outcome, and the spec covers a failed socket open during the immediate version fallback (`design.md:126–144`; `spec.md:85–91`). Paho clears `_thread` on exit, and a subsequent `loop_start()` can start a thread that waits before reconnecting (`client.py:2332–2349, 4521–4545`).
3. **Round 2 Moderate 1 — fixed.** D1 and ADR-0018 now acknowledge that a blocking-connect loop could observe CONNACK through a callback and a wait. They compare its additional retry loop against the paho approach on that basis (`design.md:93–108`; ADR-0018:57–64).

### Author responses to round 3 suggestions

- **Suggestion 1 (on_disconnect after a socket failure): declined, no change.** The
  sentence is accurate for the whole attempt. After `on_connect_fail`, paho waits,
  leaves its first-connection loop, and its next `_loop` call has no socket, so it
  calls `on_disconnect` (`client.py:2281-2297`, `_loop_rc_handle`). The logging
  rule handles either order, as the reviewer notes. Editing the design now would
  void this verdict for no change in behaviour.
- **Suggestion 2 (a real-paho test for code 2): accepted in `tasks.md`.** The task
  list adds a third focused test for the generated-client-ID path. This adds a test
  only, and changes no reviewed artifact.

### Post-approval correction found during apply

- **Design D3, login advice: changed with the human's approval.** The manual
  check against Mosquitto 2.1.2 (task 5.2) showed that Mosquitto answers a wrong
  password with "Not authorized", not "Bad user name or password". D3 gave each
  reason its own advice, so a wrong password got "check the user's permissions".
  Both reasons now get the same advice: check `mqtt.username`, `mqtt.password`,
  and the user's permissions. The delta spec is unchanged, and both of its
  rejected-login scenarios still hold. No other reviewed content changed.

