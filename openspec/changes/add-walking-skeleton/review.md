## Review Metadata

- **Review round**: 3
- **Prior round**: round 2 verdict was REVISE (1 Critical: two ha-delivery scenarios still asserting HA-internal behavior; 1 Moderate: threading.Event could not carry pier identity)
- **Reviewer context**: cross-model (agy / Gemini 3.1 Pro High), read-only, headless
- **Tool restrictions**: read-only (read/grep/glob only)
- **Artifacts reviewed**: proposal.md, design.md, specs/night-verdict, specs/ha-delivery, docs/adr/0001-0003, docs/roadmap.md

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in this round. -->

## Findings

### 🔴 Critical (blocking) — resolved as the Required Change below

- **File:** `design.md` (D7) — queue-timeout starvation.
  **Problem:** `queue.get(timeout=interval_seconds)` uses a fresh timeout per call, which resets on every successful dequeue. If on-demand refreshes arrive more frequently than the interval, `queue.Empty` is never raised and the periodic all-pier recompute is starved indefinitely.
  **Fix:** track an absolute deadline (`deadline = time.monotonic() + interval_seconds`) and wait only the remaining time (`timeout = max(0.0, deadline - time.monotonic())`); on a dequeued refresh, recompute that pier without moving the deadline; on `queue.Empty`/deadline, recompute all piers and set a new deadline.

### 🟡 Moderate

(None)

### 📌 Suggestions (non-blocking — carried into tasks.md, not applied to design to preserve this verdict)

- **Drain/dedupe duplicate refreshes (D7):** collapse repeated identical pier ids (spammed refresh button) into a single recompute per loop by draining the queue into a set.
- **`has_entity_name: true` in discovery payloads (D5):** add it so entities name cleanly as "PierPressure backyard Verdict" rather than literally "Verdict".

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Update `design.md` D7 to use an absolute monotonic deadline for the periodic-refresh wait, so on-demand refreshes cannot reset and starve the interval recompute.

CHANGES_APPLIED: yes

## Rebuttals

Author assessment: the Required Change is accepted (a genuine timeout-starvation bug) and applied to design.md D7 (absolute monotonic deadline). The two suggestions are accepted as valid but are implementation-level and are recorded for tasks.md rather than applied to design.md — editing design beyond the listed Required Change would void this verdict under the staleness rule.

Reviewer re-check (focused, agy / Gemini 3.1 Pro High, read-only): RESOLVED / RECHECK: PASS — confirmed D7 now uses an absolute `time.monotonic()` deadline with the wait computed as the remaining time, on-demand refresh recomputes a single pier without moving the deadline, and the periodic all-pier recompute is deadline-driven and cannot be starved. CHANGES_APPLIED flipped to yes on this re-check.
