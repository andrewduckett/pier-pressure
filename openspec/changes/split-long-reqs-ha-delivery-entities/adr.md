# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. ADR-0034 is superseded only in part, by ADR-0035. None is about spec structure. Five set rules that the split requirements specify, and the split keeps each one:
  - [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): a dumb adapter delivers the verdict contract over MQTT discovery ("The verdict, score and refresh entities are announced by discovery", "The verdict entity publishes the verdict and its details").
  - [ADR-0011](../../../docs/decisions/0011-narrative-separate-entity-not-document-field.md): the narrative is its own entity, not a document field ("Disabled narrative delivery publishes no narrative entity", "The narrative prose is published in the attributes, not the state", "With no narrative, the enabled narrative sensor is published as unavailable").
  - [ADR-0015](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md): provider health travels beside the verdict and is held only in memory ("A health sensor's state is its provider's last success since the process started", "Provider health travels beside the verdict document, not inside it").
  - [ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md): the timeline travels per variable on its own sensors, not in the verdict attributes ("The verdict attributes leave out only the timeline", "A further timeline sensor is published for each of sixteen keys", "The Cloud cover sensor's state is the current-hour cloud cover").
  - [ADR-0031](../../../docs/decisions/0031-computed-variables-are-a-source-in-the-provider-order.md): the computed source has a health record like a provider ("The computed source's health attributes name its inputs").

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), and each of the four added scenarios restates a rule its requirement keeps, so none is a costly fork.
