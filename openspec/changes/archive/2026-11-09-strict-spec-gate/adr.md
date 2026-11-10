# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It adds one task to the development checks. No record in force covers what `mise run check` runs, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. Only one bears on this change:
  - [ADR-0024](../../../docs/decisions/0024-self-hosted-renovate-owns-dependency-updates.md): Renovate moves the OpenSpec pin in `mise.toml` with the other tools. So the spec check runs whichever OpenSpec version Renovate last moved to, and the contract test (design decision 3) checks each new version on its update pull request. This change keeps the record as it is.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. Adding the spec check is a requirement (`dev-checks`), not a fork between approaches, and removing one task reference undoes it. The task's name, its place in `check` and the test's setup can be read from the code and changed at no cost.
