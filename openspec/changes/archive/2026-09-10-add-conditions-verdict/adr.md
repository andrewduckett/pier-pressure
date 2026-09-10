# ADR Review Manifest

- Status: completed
- Review date: 2026-09-09

## Review Summary

ADR review completed for this change. The design was checked for decisions that
are hard to reverse, surprising without context, and the result of a real
trade-off. One decision met the bar — the provider-edge seam — and was recorded
as a new repository-level ADR. The other design decisions (the clarity-weight
aggregation, the gate-only NO-GO with a single GO/MAYBE threshold, the
degradation ladder, and the two knobs) are either elaborations of an in-force
ADR (gates-then-banded-score, ADR0002) or contained algorithm/policy choices
that live adequately in design.md and can be revised without architectural
upheaval; no new ADR was created for them.

## In-Force ADRs Reviewed

- ADR0001 — Home-Assistant-agnostic core with a JSON verdict contract (accepted)
- ADR0002 — Verdict uses hard gates then a banded score (accepted)
- ADR0003 — Target observability is hard-clamped to astronomical night (accepted)
- ADR0004 — Deterministic offline astronomy via Skyfield with pinned data (accepted)

None are superseded by this change; ADR0005 builds on ADR0004 without replacing it.

## New Durable ADRs Created

- ADR0005 — Weather enters at a provider edge; the core takes a conditions
  snapshot (`docs/adr/0005-conditions-provider-edge-seam.md`)
