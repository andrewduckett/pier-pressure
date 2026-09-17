# ADR Review Manifest

- Status: completed
- Review date: 2026-09-11

## Review Summary

ADR review completed for this change. The design was checked against the three
tests — hard to reverse, surprising without context, the result of a real
trade-off. One decision cleared the bar: the ranking's drop-and-renormalise
scoring model. The other design decisions did not (see below), so no ADR was
invented for them.

## In-Force ADRs Reviewed

- ADR-0001 — Home-Assistant-agnostic core with a JSON verdict contract
- ADR-0002 — Hard gates then a banded score
- ADR-0003 — Target observability hard-clamped to astronomical night
- ADR-0004 — Deterministic offline astronomy (Skyfield, pinned ephemeris)
- ADR-0005 — Weather enters at a provider edge
- ADR-0006 — Conditions modelled as per-source groups
- ADR-0007 — Canonical horizon as `(az, alt)` samples
- ADR-0008 — Deep-sky catalog vendored as pinned OpenNGC data
- ADR-0009 — The `targets` field filled additively with numbers-only elements

No supersessions. ADR-0009 (additive, numbers-only target fill) governs this
change's new `size_arcmin`, `magnitude`, and `surface_brightness` target fields;
this change extends that pattern rather than revising it.

## New Durable ADRs Created

- [ADR-0010 — The ranking score renormalises over the factors whose inputs are known](../../../docs/adr/0010-ranking-renormalises-over-known-factors.md)

## Decisions Considered and Not Recorded

- **Equipment as raw optics rather than a pre-computed field of view** (design D1)
  — a conventional, additive config choice; low reversal cost.
- **Surface-brightness-then-magnitude as the brightness input** (design D4) — a
  tunable science choice, not a hard-to-reverse architecture; captured in
  ADR-0010's decision statement as the factor's input.
- **Emitting raw catalog facts on each target** (design D8) — follows the existing
  additive, numbers-only pattern already set by ADR-0009.
