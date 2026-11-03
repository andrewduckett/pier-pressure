# ADR Review Manifest

- Status: completed
- Review date: 2026-11-03

## Review Summary

ADR review completed for this change. None of the seven design decisions is a
fork that is costly to reverse. DD1 to DD5 and DD7 are provider internals that
the code and the spec state outright: the endpoint, the hold and horizon, the
in-memory grid cell, the unit check, the `User-Agent` and the fixture. DD6, a
bundle is filled whole or not at all, enforces the bundle principle that
ADR-0027 already records; it is a few lines in the fill and a spec scenario,
and the spec is the place that owns it.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md): the provider edge seam is where NWS lives.
- [ADR-0007](../../../docs/decisions/0007-canonical-horizon-representation.md) to [ADR-0026](../../../docs/decisions/0026-night-dashboard-ships-as-yaml-on-plotly-graph-card.md)
- [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md): the ordered fill and bundles. DD6 enforces its bundle rule.
- [ADR-0028](../../../docs/decisions/0028-each-open-meteo-model-is-its-own-provider.md): one key and health record per provider. NWS follows it.
- [ADR-0029](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md): agreement reads alternates. NWS's cloud total becomes one.
- ADR-0006 is superseded by ADR-0027 and was read as history only.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
