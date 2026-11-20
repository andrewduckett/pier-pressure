<!-- Plain language: Make each record link identify the decision so a reader can find its rationale. Keep this manifest separate from the records themselves. -->

# ADR Review Manifest

- Status: completed
- Review date: 2026-11-20

## Review Summary

ADR review completed for this change. None of design.md's eight decisions
passes the test. Each is cheap to reverse, and the code or the specs show it:

- Decisions 1 and 2, the `data-tip` keys and the text lookup by key, are
  implementation details inside the card. The spec states what counts as the
  same item after a redraw, so a change to the keys that broke it would fail
  a test.
- Decisions 3 and 4, tracking taps on `<ha-card>` apart from the drag and
  closing the box in `panTo` and `onBack`, are event-handling choices inside
  one component. The spec's tap and pan requirements guard the behaviour.
- Decisions 5 and 6, the box's styles and the pure placement function, are
  display choices. Replacing them changes only the box's markup, its styles
  and their tests.
- Decision 7, moving the test helper, and decision 8, the docs wording, are
  owned by the tests and the docs requirement.

Adding tap support in the card, with no tooltip library, follows from
ADR-0034 and adds no dependency, so it is not a new decision.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core and its verdict document do not change; only the card responds to taps.
- [ADR-0034](../../../docs/decisions/0034-pierpressure-ships-its-own-dashboard-card-through-hacs.md): the card still only displays published entities. The box shows text the card already draws, and fetches nothing.
- [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md): `docs/night-card.md` stays the one dashboard page, and this change edits it.
- Every other accepted record in `docs/decisions/` (ADR-0002 to ADR-0005, ADR-0007 to ADR-0025, ADR-0027 to ADR-0033, ADR-0036 to ADR-0042) was checked by its title and description, and none governs the card's interaction. ADR-0006 and ADR-0026 are superseded.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
