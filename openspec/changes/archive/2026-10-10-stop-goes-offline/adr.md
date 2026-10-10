# ADR Review Manifest

- Status: completed
- Review date: 2026-10-10

## Review Summary

ADR review completed for this change. No design decision meets the bar for a
new ADR. D1 (publish `offline` in `close()`) and D2 (a two-second wait that
never raises) live in one short method, and changing either is cheap. D3 (map
SIGTERM to `KeyboardInterrupt`) is one line in the entry point. D4 is test
support. The design and the `ha-delivery` spec explain the why of each.

## In-Force ADRs Reviewed

- ADR-0001 to ADR-0019 in `docs/decisions/`. None is superseded. ADR-0006 is
  deprecated and does not apply.
- Most relevant:
  - ADR-0012: only the main thread publishes. `close()` runs on the main thread,
    so the `offline` publish keeps this rule.
  - ADR-0018: paho owns every broker retry. This change adds no retry.
  - ADR-0019: a publish never stops PierPressure, and the replay repairs a lost
    message. This change keeps both. Only the stop waits for a confirmation, and
    that wait never raises.

## New Durable ADRs Created

- No major durable architectural decisions were introduced, and no new
  repository-level ADR files were created.
