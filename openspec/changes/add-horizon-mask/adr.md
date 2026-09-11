# ADR Review Manifest

- Status: completed
- Review date: 2026-09-11

## Review Summary

ADR review completed for this change. Design.md was re-read against the three bars
(hard to reverse, surprising without context, the result of a real trade-off). One
decision qualified — the canonical horizon representation and its azimuth convention
(design D1/D2), which the NINA importer and M5's target-visibility test both bind to.
The remaining decisions (D3 resolve-at-config-load, D4 parsers-take-text, D5 reuse
per-pier validation) are consequences of existing accepted ADRs (0004 offline/deterministic,
0005 provider-edge purity) and the existing config isolation, not new durable choices.

## In-Force ADRs Reviewed

- ADR-0001 — Home-Assistant-agnostic core with a JSON verdict contract
- ADR-0002 — Verdict uses hard gates then a banded score (already names "target altitude above the horizon mask")
- ADR-0003 — Target observability is hard-clamped to astronomical night
- ADR-0004 — Deterministic offline astronomy via Skyfield with pinned data
- ADR-0005 — Weather enters at a provider edge; the core takes a conditions snapshot
- ADR-0006 — The conditions snapshot is modelled as per-source groups

No supersession chains are in force; the highest sequence number in use was 0006.

## New Durable ADRs Created

- ADR-0007 — The horizon is a cyclic set of (az, alt) samples with linear interpolation
  (`docs/adr/0007-canonical-horizon-representation.md`). Pins the canonical shape,
  north-zero-clockwise azimuth convention, linear interpolation, cyclic wraparound, and
  the inclusive above-horizon boundary that the importers and M5 bind to.
