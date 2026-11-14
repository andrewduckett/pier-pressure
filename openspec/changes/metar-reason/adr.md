# ADR Review Manifest

- Status: completed
- Review date: 2026-11-14

## Review Summary

ADR review completed for this change. Of design.md's decisions, DD1 and DD2
together pass the test. Someone could fold the observation into the conditions
or the provider order. Undoing that later would touch the document contract
and the confidence work that builds on it. The rest (DD3 to DD8) are
recoverable from code or follow existing records.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core emits one JSON document; the new key grows it additively.
- [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md): weather enters at a provider edge; the observation is fetched at the same edge.
- [ADR-0015](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md): METAR health travels beside the verdict, in memory.
- [ADR-0020](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md), [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md), [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): `metar_station` comes from the add-on's config file and is validated only by the core.
- [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md), [ADR-0030](../../../docs/decisions/0030-raw-input-variables-stay-out-of-the-verdict-document.md): the document only grows; the observation is shown evidence, not a raw input.
- [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md), [ADR-0029](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md), [ADR-0031](../../../docs/decisions/0031-computed-variables-are-a-source-in-the-provider-order.md): the fill, agreement and the computed source are unchanged.
- Every other record in `docs/decisions/` (ADR-0002 to ADR-0004, ADR-0007 to ADR-0014, ADR-0016 to ADR-0019, ADR-0023, ADR-0024, ADR-0026, ADR-0028, ADR-0032 to ADR-0036) was read and is not affected.

## New Durable ADRs Created

- [ADR-0037](../../../docs/decisions/0037-observations-are-a-core-input-beside-the-conditions.md): observations are a core input beside the conditions, never a provider (design DD1, DD2).
