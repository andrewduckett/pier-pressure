# ADR Review Manifest

- Status: completed
- Review date: 2026-11-08

## Review Summary

ADR review completed for this change. It changes the text of two specs only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. They cover the core, the verdict document, delivery, providers, release and the dashboard. None is about spec structure. ADR-0013 (CalVer) and ADR-0014 (add-on wraps the release image) explain the release behavior that `release-image` states; this change keeps that behavior as it is.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (brainstorm D3), and requirement order carries no meaning, so neither is a costly fork. The heading finding is recorded in epic #230 instead.
