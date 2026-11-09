# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Five set rules that the split requirements specify, and the split keeps each one:
  - [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): one deterministic verdict document is the contract ("The document carries the scored window beside the dark window", "The moon object carries its illumination and phase").
  - [ADR-0002](../../../docs/decisions/0002-gates-then-banded-score.md): hard gates, then a banded score ("The gates, the score and the completeness part of confidence run over the scored window", "A scored window with some usably clear hours is not gated as overcast", "Less than an hour of dark time caps the verdict at MAYBE").
  - [ADR-0003](../../../docs/decisions/0003-astronomical-night-hard-clamp.md): astronomical night is the sun's centre below -18 degrees ("The dark window is the astronomical night selected from the evaluation instant").
  - [ADR-0004](../../../docs/decisions/0004-deterministic-offline-astronomy.md): offline astronomy from a pinned ephemeris and a built-in timescale ("Astronomical fields are computed offline from bundled data", "Repeated runs on one platform yield byte-identical astronomical values").
  - [ADR-0023](../../../docs/decisions/0023-verdict-judges-the-remaining-night.md): once the night has started, the verdict judges the rest of it ("The verdict judges the scored window", "Once the night has started, the scored window starts at the scoring instant", "Over a narrowed scored window, reasons speak only of the rest of the night").

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), and each of the six added scenarios restates a rule its requirement keeps, so none is a costly fork.
