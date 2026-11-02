# ADR Review Manifest

- Status: completed
- Review date: 2026-11-02

## Review Summary

ADR review completed for this change. Design decisions D1 to D7 can be read from
the code and cost little to change, so they need no record. Making each model
a separate provider is a real fork. Its keys become configuration values and
health-sensor IDs, so it gets a record.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md)
- [ADR-0007](../../../docs/decisions/0007-canonical-horizon-representation.md) to [ADR-0026](../../../docs/decisions/0026-night-dashboard-ships-as-yaml-on-plotly-graph-card.md)
- [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md): conditions filled per variable from an ordered provider list. The new record builds on it.
- ADR-0006 is superseded by ADR-0027 and was read as history only.

## New Durable ADRs Created

- [ADR-0028](../../../docs/decisions/0028-each-open-meteo-model-is-its-own-provider.md): each Open-Meteo model is its own provider.
