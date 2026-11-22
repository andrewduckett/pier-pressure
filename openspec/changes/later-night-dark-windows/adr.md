# ADR Review Manifest

- Status: completed
- Review date: 2026-11-22

## Review Summary

ADR review completed for this change. Two of design.md's decisions pass the
test, and each gets its own record:

- DD4, the document shape. Someone could fold later nights into a `nights`
  list or into parallel arrays. Undoing either later would reshape the frozen
  document.
- DD5, the delivery. Someone could move later nights into the Verdict
  attributes. That breaks the Verdict sensor once the targets arrive, and the
  three entity names join the frozen delivery surface.

The other decisions are recoverable from code: DD1 and DD2 (sky functions),
DD3 (where the count runs), DD6 (card line keys) and DD7 (docs and goldens).

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core emits one JSON document; `later_nights` grows it additively.
- [ADR-0003](../../../docs/decisions/0003-astronomical-night-hard-clamp.md): each later night's dark window is astronomical night, as tonight's is.
- [ADR-0004](../../../docs/decisions/0004-deterministic-offline-astronomy.md): later nights come from the same pinned, offline ephemeris.
- [ADR-0009](../../../docs/decisions/0009-targets-structured-additive-fill.md), [ADR-0036](../../../docs/decisions/0036-targets-ranked-on-the-remaining-night.md): tonight's targets are unchanged; later-night targets are the next story's.
- [ADR-0011](../../../docs/decisions/0011-narrative-separate-entity-not-document-field.md): the narrative is untouched; its prompt never reads `later_nights`.
- [ADR-0015](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md): the Night sensors follow the health sensors' timestamp state.
- [ADR-0023](../../../docs/decisions/0023-verdict-judges-the-remaining-night.md): the verdict still judges only the selected night.
- [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md): its note that a verdict for later nights would be a separate decision stands; ADR-0043 builds on it and adds no verdict.
- [ADR-0034](../../../docs/decisions/0034-pierpressure-ships-its-own-dashboard-card-through-hacs.md), [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md): the card is where later-night lines are drawn and documented.
- Every other record in `docs/decisions/` (ADR-0002, ADR-0005 to ADR-0008, ADR-0010, ADR-0012 to ADR-0014, ADR-0016 to ADR-0022, ADR-0024, ADR-0026 to ADR-0033, ADR-0037 to ADR-0042) was read and is not affected.

## New Durable ADRs Created

- [ADR-0043](../../../docs/decisions/0043-later-nights-are-a-list-of-per-night-entries-in-the-verdict-document.md): later nights are a list of per-night entries after the document's existing fields (design DD4).
- [ADR-0044](../../../docs/decisions/0044-each-later-night-is-its-own-home-assistant-sensor.md): each later night reaches Home Assistant as its own Night sensor, not through the Verdict attributes (design DD5).
