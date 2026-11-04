# ADR Review Manifest

- Status: completed
- Review date: 2026-11-03

## Review Summary

ADR review completed for this change. Of the design's five decisions, only the
rule behind DD1 qualifies: whether a raw input becomes part of the frozen
document cannot be reversed once published. DD2 to DD5 are local to one module
each and cheap to change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the verdict document is the frozen contract
- [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md): providers sit at the edge of the core
- [ADR-0015](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md): provider health travels beside the verdict
- [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md): the hourly timeline; built on by ADR-0030
- [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md): the per-variable fill from an ordered list
- [ADR-0028](../../../docs/decisions/0028-each-open-meteo-model-is-its-own-provider.md): each Open-Meteo model is its own provider
- [ADR-0029](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md): agreement is a confidence input
- ADR-0002 to ADR-0004, ADR-0007 to ADR-0014, ADR-0016 to ADR-0024 and ADR-0026: checked by title. None concerns conditions, providers or the document's shape. ADR-0006 is superseded and was not reviewed.

## New Durable ADRs Created

- [ADR-0030](../../../docs/decisions/0030-raw-input-variables-stay-out-of-the-verdict-document.md): raw input variables stay out of the verdict document
