# ADR Review Manifest

- Status: completed
- Review date: 2026-10-09

## Review Summary

ADR review completed for this change. Design decision D1 (hold publishes while
disconnected, and let the replay repair them) is a real fork. A reader of the
code could plausibly reverse it by handing every message to paho, or by capping
paho's queue. Either reversal breaks recovery after a long outage, so the why is
recorded in a new ADR. D2 to D5 follow from D1 or can be read from the code, and
need no ADR.

## In-Force ADRs Reviewed

- ADR-0001 to ADR-0018 in `docs/decisions/`. None is superseded.
- Most relevant: ADR-0012 (only the main thread publishes, through a work
  queue), ADR-0015 (provider health is held in memory beside the verdict), and
  ADR-0018 (paho owns every broker retry). This change keeps all three. It adds
  no retry loop, and only the main thread publishes.

## New Durable ADRs Created

- `docs/decisions/0019-replay-repairs-outage-publishes.md`: the replay after a
  reconnect, not paho's queue, repairs what an outage missed. A publish never
  stops PierPressure.
