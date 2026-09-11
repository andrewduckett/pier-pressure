# ADR Review Manifest

- Status: completed
- Review date: 2026-09-10

## Review Summary

ADR review completed for this change. The design introduces one durable,
cross-cutting decision — the shape of the core's conditions input — which refines
(does not supersede) the provider-edge seam of ADR-0005. All in-force ADRs were
reviewed for supersession; none are superseded by this change.

## In-Force ADRs Reviewed

- ADR-0001 — Core is HA-agnostic and emits one JSON verdict contract.
- ADR-0002 — Gates then a banded score.
- ADR-0003 — Astronomical-night hard clamp.
- ADR-0004 — Deterministic, offline astronomy.
- ADR-0005 — Weather enters at a provider edge; the core takes a conditions
  snapshot. (Refined here; not superseded — the network still lives at the
  provider edge and the core still reads an injected snapshot.)

## New Durable ADRs Created

- `docs/adr/0006-conditions-as-per-source-groups.md` — the conditions snapshot is
  modelled as one self-stamped group per source (cloud, wind, seeing) rather than a
  flat hourly grid with side-channel issue-times. Full Context, Decision, and
  Consequences live in that file.
