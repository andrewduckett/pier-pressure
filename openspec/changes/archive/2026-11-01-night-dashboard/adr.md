# ADR Review Manifest

- Status: completed
- Review date: 2026-10-31

## Review Summary

ADR review completed for this change. Of the design's decisions, only the choice of dashboard card passes the test: someone could swap the card without knowing why it was chosen, and every reader would then have to rebuild their dashboard. The other decisions (DD1 to DD5, DD7 to DD9) are inside the YAML, the test or the dev harness. They are cheap to change, and the code shows them.

## In-Force ADRs Reviewed

These records are the ones that bear on this change. ADR-0006 is deprecated and was not used. The rest of `docs/decisions/` (0002, 0003, 0005, 0007 to 0010, 0012 to 0014, 0016 to 0024) was read and does not bear on a docs-only dashboard.

- [ADR-0001: core is Home Assistant agnostic and emits one JSON verdict contract](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the dashboard reads the published contract and changes none of it.
- [ADR-0004: deterministic offline astronomy](../../../docs/decisions/0004-deterministic-offline-astronomy.md): the sun and moon rows come from the core's altitudes, not from Home Assistant.
- [ADR-0011: the narrative is a separate entity, not a document field](../../../docs/decisions/0011-narrative-separate-entity-not-document-field.md): the precedent for per-entity delivery that the dashboard reads.
- [ADR-0015: provider health beside the verdict, in memory](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md): the health chips read these sensors.
- [ADR-0025: the hourly timeline is evidence beside the verdict](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md): the strip's rows read the per-variable sensors this record defines.

## New Durable ADRs Created

- [ADR-0026: the night dashboard ships as YAML in the docs, on core cards plus plotly-graph-card](../../../docs/decisions/0026-night-dashboard-ships-as-yaml-on-plotly-graph-card.md)
