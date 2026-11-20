<!-- Plain language: Make each record link identify the decision so a reader can find its rationale. Keep this manifest separate from the records themselves. -->

# ADR Review Manifest

- Status: completed
- Review date: 2026-11-19

## Review Summary

ADR review completed for this change. None of design.md's eleven decisions
passes the test. Each is cheap to reverse and recoverable from the code or
the specs:

- Decisions 1, 2, 4, 9 and 10, where the chart's model and markup live, the
  hover areas as cells, the extra grid row and the removed rows, are
  implementation details inside the card.
- Decision 3, percent coordinates on SVG `<line>` and `<circle>` elements,
  is a drawing technique. Swapping it for a stretched `viewBox` changes only
  the chart's markup and its tests.
- Decisions 5, 6 and 7, the track height, the label cell layout and the two
  colours, are display choices the night-card spec now states as
  requirements, with tests behind them.
- Decision 8, keeping the card size, keeps an existing requirement.
- Decision 11, the docs wording, is owned by the docs requirements.

Drawing the chart in the card, with no charting library, follows from
ADR-0034 and adds no dependency, so it is not a new decision.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core and its verdict document do not change; only the card draws differently.
- [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md): the chart reads the existing temperature and dew point timeline sensors as they are; no sensor or attribute changes.
- [ADR-0034](../../../docs/decisions/0034-pierpressure-ships-its-own-dashboard-card-through-hacs.md): the card still only displays published entities. The chart computes no verdict and fetches nothing.
- [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md): `docs/night-card.md` stays the one dashboard page, and this change edits it.
- Every other accepted record in `docs/decisions/` (ADR-0002 to ADR-0005, ADR-0007 to ADR-0024, ADR-0027 to ADR-0033, ADR-0036 to ADR-0042) was checked by its title and description, and none governs the card's drawing. ADR-0006 and ADR-0026 are superseded.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
