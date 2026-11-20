<!-- Plain language: Make each record link identify the decision so a reader can find its rationale. Keep this manifest separate from the records themselves. -->

# ADR Review Manifest

- Status: completed
- Review date: 2026-11-20

## Review Summary

ADR review completed for this change. None of design.md's three decisions
passes the test. Each is cheap to reverse and recoverable from the code or
the specs:

- DD1, the `disagree` flag on the `Band`, is an implementation detail that
  lives in a few lines of `card/src/strip.ts` and `card/src/pierpressure-card.ts`.
- DD2, the 35-point edge on the clamped values, is a requirement: the
  night-card spec states the edge, the clamping and the boundary scenarios,
  and the tests enforce them. The constant's comment names its source in the
  core.
- DD3, the amber `#b58900`, is a requirement: the spec names the colour and
  the contrast it must reach, and a test enforces the contrast.

Using the core's DISAGREE edge in the card is a product decision the ledger
records (D2). It is not a fork between technical approaches, so it gets no
record.

## In-Force ADRs Reviewed

- [ADR-0029](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md): the core keeps its agreement measure and bands unchanged. The card reuses only the DISAGREE edge's number, for one hour at a time, to colour a column; it feeds nothing back into a gate, the score or confidence.
- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core and its verdict document do not change; only the card draws differently.
- [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md): the Cloud range row still reads the cloud cover min and max timeline sensors as they are; no sensor or attribute changes.
- [ADR-0034](../../../docs/decisions/0034-pierpressure-ships-its-own-dashboard-card-through-hacs.md): the card still only displays published entities. The amber column is a display choice and computes no verdict.
- [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md): `docs/night-card.md` stays the one dashboard page, and this change edits it.
- Every other accepted record in `docs/decisions/` (ADR-0002 to ADR-0005, ADR-0007 to ADR-0024, ADR-0027, ADR-0028, ADR-0030 to ADR-0033, ADR-0036 to ADR-0042) was read and is not affected. ADR-0006 and ADR-0026 are superseded.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
