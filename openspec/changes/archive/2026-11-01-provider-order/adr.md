# ADR Review Manifest

- Status: completed
- Review date: 2026-11-01

## Review Summary

ADR review completed for this change. Design decision D1 (the snapshot as
per-variable series filled from an ordered provider list) is a canonical data
model that every later provider binds to, so it gets a record. D2 to D8 follow
from it or are recoverable from the code and get none.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the verdict document is the frozen contract. This change leaves it untouched.
- [ADR-0002](../../../docs/decisions/0002-gates-then-banded-score.md): gates then banded score. Unchanged.
- [ADR-0003](../../../docs/decisions/0003-astronomical-night-hard-clamp.md), [ADR-0004](../../../docs/decisions/0004-deterministic-offline-astronomy.md): astronomy. Unchanged.
- [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md): the provider edge seam. Still in force; amended to drop the role wording.
- [ADR-0007](../../../docs/decisions/0007-canonical-horizon-representation.md) to [ADR-0014](../../../docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md): horizon, catalog, targets, ranking, narrative, loop, versions, add-on. Unchanged.
- [ADR-0015](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md): health beside the verdict, in memory. Unchanged; the attribute set changes, not the placement.
- [ADR-0016](../../../docs/decisions/0016-python-3-14.md) to [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md): toolchain, broker, retries, replay, add-on settings. Unchanged.
- [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): the core validates settings. Design D2 keeps the provider declarations in the core so the new list is validated there.
- [ADR-0023](../../../docs/decisions/0023-verdict-judges-the-remaining-night.md) to [ADR-0026](../../../docs/decisions/0026-night-dashboard-ships-as-yaml-on-plotly-graph-card.md): remaining night, Renovate, timeline, dashboard. Unchanged.

ADR-0006 was already deprecated; this change marks it superseded by ADR-0027.

## New Durable ADRs Created

- [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md): conditions are filled variable by variable from an ordered provider list. Supersedes ADR-0006.
