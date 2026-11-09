# ADR Review Manifest

- Status: completed
- Review date: 2026-11-08

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Four set rules that `target-ranking` specifies, and the split keeps each one, now as its own requirement:
  - [ADR-0003](../../../docs/decisions/0003-astronomical-night-hard-clamp.md): a target's observable window is clamped to astronomical night ("A target's observable window is clamped to the dark window").
  - [ADR-0008](../../../docs/decisions/0008-vendored-openngc-catalog.md): the catalog is pinned in-repo data. Its two requirements are under the limit and stay as they are.
  - [ADR-0009](../../../docs/decisions/0009-targets-structured-additive-fill.md): each target is a structured set of computed numbers ("Each target carries its observing geometry", "Each target carries its catalog size and brightness").
  - [ADR-0010](../../../docs/decisions/0010-ranking-renormalises-over-known-factors.md): the score renormalises over the factors whose inputs are known ("A factor contributes only when its inputs are known", "Factor weights are renormalised over the contributing factors", "Brightness is judged by surface brightness, else magnitude").

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), and each added scenario restates a SHALL its requirement keeps, which an existing test asserts, so none is a costly fork. Keeping the drifted framing requirement as it is (design Decision 5) defers a fix to a separate change; it decides nothing durable.
