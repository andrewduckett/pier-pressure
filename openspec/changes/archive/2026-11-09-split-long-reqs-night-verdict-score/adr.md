# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Five set rules that the split requirements specify, and the split keeps each one:
  - [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): one deterministic verdict document is the contract ("A gate-passing night gets a deterministic integer score from 0 to 100", "The targets list is always present, and empty when nothing is rankable").
  - [ADR-0002](../../../docs/decisions/0002-gates-then-banded-score.md): hard gates, then a banded score ("A failed hard gate is the only cause of a NO-GO", "A failed hard gate leaves the score null and names the gate", "The score is the product of four factors", "GO needs a score at the go-threshold, cloud data and no cap").
  - [ADR-0009](../../../docs/decisions/0009-targets-structured-additive-fill.md): the `targets` field is filled additively with a structured element ("Each target carries its identity, ranking and observing fields", "Each target carries its catalog size, magnitude and surface brightness").
  - [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): the core validates settings ("A negative or non-finite dew margin is a configuration error").
  - [ADR-0023](../../../docs/decisions/0023-verdict-judges-the-remaining-night.md): the gates and the score read the scored window ("The overcast gate fails when every part of the scored window with cloud data is overcast", "The wind gate fails when the forecast gust exceeds a configured limit").

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5). Each of the ten added scenarios restates a rule its requirement keeps, and joining the two statements about missing seeing and transparency changes no meaning, so none is a costly fork.
