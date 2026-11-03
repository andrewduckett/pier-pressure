# ADR Review Manifest

- Status: completed
- Review date: 2026-11-02

## Review Summary

ADR review completed for this change. Design decisions DD1, DD2, DD5, DD6 and
DD7 can be read from the code and cost little to change, so they need no record.
DD3 and DD4 together are one real fork: where forecast agreement enters the
verdict, and that alternates are measured rather than blended. The document
shape becomes contract on first release, so it gets a record.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md)
- [ADR-0002](../../../docs/decisions/0002-gates-then-banded-score.md): gates then a banded score. The new record builds on it.
- [ADR-0007](../../../docs/decisions/0007-canonical-horizon-representation.md) to [ADR-0028](../../../docs/decisions/0028-each-open-meteo-model-is-its-own-provider.md)
- ADR-0006 is superseded by ADR-0027 and was read as history only.

## New Durable ADRs Created

- [ADR-0029](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md): forecast agreement is an input to confidence, never to a gate or the score.
