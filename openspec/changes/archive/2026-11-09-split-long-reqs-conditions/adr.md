# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Six set rules that the split requirements specify, and the split keeps each one, now as its own requirement:
  - [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md): providers sit at the edge, and the core reads only the snapshot ("Fetch outcomes never reach the verdict").
  - [ADR-0015](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md): provider health is kept beside the verdict, never in it ("A fetch reports one outcome per provider in order", "An outcome's error description is built only from safe parts", "An outcome's error description copies no text from the error or the response").
  - [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md): each variable is filled from the first provider in order, bundles travel together, and later providers' series are kept as alternates ("The first provider in order that returned a variable fills its series", "A provider fills a bundle whole or not at all", "Each later provider that returned a variable leaves an alternate").
  - [ADR-0028](../../../docs/decisions/0028-each-open-meteo-model-is-its-own-provider.md): each Open-Meteo model is its own provider and declares only what it supplies ("HRRR and GFS declare the same variables as Open-Meteo", "ICON declares neither column water vapour nor the seeing column", "HRDPS and RDPS declare no precipitation probability").
  - [ADR-0029](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md): the core reads alternates only to measure agreement ("Alternates never change the filled series").
  - [ADR-0031](../../../docs/decisions/0031-computed-variables-are-a-source-in-the-provider-order.md): the computed source takes a place in the provider order and reports like a provider ("The computed source reports one outcome at its place in the order" and the three computed-outcome requirements after it).

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), and the one added scenario restates a SHALL its requirement keeps, which an existing test asserts, so none is a costly fork.
