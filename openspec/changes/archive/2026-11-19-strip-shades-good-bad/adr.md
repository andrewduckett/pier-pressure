<!-- Plain language: Make each record link identify the decision so a reader can find its rationale. Keep this manifest separate from the records themselves. -->

# ADR Review Manifest

- Status: completed
- Review date: 2026-11-19

## Review Summary

ADR review completed for this change. None of design.md's five decisions
passes the test. Each is cheap to reverse and recoverable from the code or
the specs:

- Decisions 1 and 3, the `darkestFirst` helper and the 1 px inset, are
  implementation details that live in a few lines of the card.
- Decision 2, the two greys, is a requirement: the spec names both hex
  values and the contrast they must reach, and a test enforces the contrast.
- Decision 4, the contrast test, is test code.
- Decision 5, the docs wording, is owned by the docs requirements.

The rule that darker means better for observing is a product decision the
night-card spec now states row by row. It is not a fork between technical
approaches, so it gets no record.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core and its verdict document do not change; only the card draws differently.
- [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md): the strip still reads the per-variable timeline sensors as they are; no sensor or attribute changes.
- [ADR-0034](../../../docs/decisions/0034-pierpressure-ships-its-own-dashboard-card-through-hacs.md): the card still only displays published entities. The shades are a display choice and compute no verdict.
- [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md): `docs/night-card.md` stays the one dashboard page, and this change edits it.
- Every other accepted record in `docs/decisions/` (ADR-0002 to ADR-0005, ADR-0007 to ADR-0024, ADR-0027 to ADR-0033, ADR-0036 to ADR-0042) was read and is not affected. ADR-0006 and ADR-0026 are superseded.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
