# ADR Review Manifest

- Status: completed
- Review date: 2026-11-08

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. [ADR-0007](../../../docs/decisions/0007-canonical-horizon-representation.md) sets the horizon representation that `horizon-mask` specifies: north-zero clockwise azimuth, a closed ring of samples, linear interpolation and a fixed precision. The split keeps each of those rules, now as its own requirement. [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md) and [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md) shape how horizon settings reach the core and where they are checked. This change keeps that behavior, and the requirements that state it, as they are.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), and each added scenario restates a SHALL its requirement keeps, which an existing test asserts, so none is a costly fork. Keeping the out-of-date verdict-document requirement as it is (design Decision 5) defers a fix to a separate bug; it decides nothing durable.
