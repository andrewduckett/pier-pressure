# ADR Review Manifest

- Status: completed
- Review date: 2026-11-11

## Review Summary

ADR review completed for this change. Of the design's decisions, only D5 and the
ranking rule it publishes pass the test: the `remaining_window` field is a
permanent part of the frozen document, and it reverses an accepted constraint
of ADR-0023. D1 (a shared scored-window function), D2 to D4 (the cached night
scan and the remaining grid) and D6 (the cache bound) can all be read from the
code and changed cheaply, so they stay in design.md.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to
  [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md),
  [ADR-0007](../../../docs/decisions/0007-canonical-horizon-representation.md) to
  [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md),
  and [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md) to
  [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md).
  ADR-0006 and ADR-0026 are superseded, and were read as history only.
- Most relevant: [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md)
  (the frozen, additive-only document),
  [ADR-0004](../../../docs/decisions/0004-deterministic-offline-astronomy.md)
  (byte-identical output),
  [ADR-0009](../../../docs/decisions/0009-targets-structured-additive-fill.md)
  (numbers-only targets, new facts as added fields) and
  [ADR-0023](../../../docs/decisions/0023-verdict-judges-the-remaining-night.md)
  (the verdict judges the scored window; ranking the rest of the night was left
  for a separate change).

## New Durable ADRs Created

- [ADR-0036: Once the night has started, targets are ranked on the rest of it, beside their whole-night window](../../../docs/decisions/0036-targets-ranked-on-the-remaining-night.md)
