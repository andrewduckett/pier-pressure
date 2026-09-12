# ADR Review Manifest

- Status: completed
- Review date: 2026-09-11

## Review Summary

ADR review completed for this change. Design.md was reviewed for decisions that are
hard to reverse, surprising without context, and the result of a real trade-off.
Two decisions cleared that bar and became repository-level ADRs: sourcing the
catalog by vendoring the full OpenNGC data, and the additive shape of the `targets`
element. The ranking math itself (four weighted sub-scores, per-target gates) did
not: it follows the established gates-then-score philosophy (ADR-0002) at target
granularity, and its weights and cutoffs are tunable rather than hard to reverse.

## In-Force ADRs Reviewed

- ADR-0001 — Home-Assistant-agnostic core with a JSON verdict contract (the frozen,
  additively-grown contract that ADR-0009 fills).
- ADR-0002 — Hard gates then a banded score (the philosophy the target gates and
  score mirror).
- ADR-0003 — Target observability hard-clamped to astronomical night (the clamp the
  observable window enforces).
- ADR-0004 — Deterministic offline astronomy with a pinned ephemeris (the
  determinism guarantee ADR-0008 extends to the catalog).
- ADR-0005 — Weather enters at a provider edge; the core takes a snapshot (the
  contrast that justifies loading the static catalog inside the core, not passing
  it in).
- ADR-0006 — Conditions modelled as per-source groups (no interaction; reviewed).
- ADR-0007 — Canonical horizon representation (the stable seam target ranking reads
  via `is_above`).

No in-force ADRs are superseded by this change.

## New Durable ADRs Created

- ADR-0008 — The deep-sky object catalog is the full OpenNGC vendored as pinned
  in-repo data (`docs/adr/0008-vendored-openngc-catalog.md`).
- ADR-0009 — The `targets` field is filled additively with a structured,
  numbers-only target element (`docs/adr/0009-targets-structured-additive-fill.md`).
