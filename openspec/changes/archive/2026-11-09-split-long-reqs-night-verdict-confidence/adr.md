# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Four set rules that the split requirements specify, and the split keeps each one:
  - [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): one deterministic verdict document is the contract ("Confidence is always present with a band and a value from 0 to 100", "The agreement object has a cloud-cover entry only when two providers share a scored hour").
  - [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md): a flat hourly timeline beside the verdict ("The timeline holds one entry per hour a shown variable's filled series covers", "A timeline entry carries exactly eighteen keys in a fixed order").
  - [ADR-0029](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md): agreement feeds confidence, never a gate or the score ("The mean cloud gap weights each hour by its coverage and its clearest reading", "Confidence is multiplied by an agreement factor set by the band", "Agreement changes no gate, score or verdict").
  - [ADR-0030](../../../docs/decisions/0030-raw-input-variables-stay-out-of-the-verdict-document.md): raw variables stay out of the document and reach it only through a shown variable ("Variables the timeline does not show leave the document unchanged"). The tightened wording keeps that last rule.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5). Keeping one requirement whole with tighter wording, and adding one scenario an existing test backs, change no meaning, so neither is a costly fork.
