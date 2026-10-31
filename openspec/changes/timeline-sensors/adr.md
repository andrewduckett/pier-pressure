# ADR Review Manifest

- Status: completed
- Review date: 2026-10-31

## Review Summary

ADR review completed for this change. The change builds on
[ADR-0025](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md),
which already decided that each timeline variable reaches Home Assistant as its
own sensor, and on the separate-entity pattern of ADR-0011 and ADR-0015.

## In-Force ADRs Reviewed

- [ADR0001: Home-Assistant-agnostic core with a JSON verdict contract](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md)
- [ADR0002: Verdict uses hard gates then a banded score](../../../docs/decisions/0002-gates-then-banded-score.md)
- [ADR0003: Target observability is hard-clamped to astronomical night](../../../docs/decisions/0003-astronomical-night-hard-clamp.md)
- [ADR0004: Deterministic offline astronomy via Skyfield with pinned data](../../../docs/decisions/0004-deterministic-offline-astronomy.md)
- [ADR0005: Weather enters at a provider edge; the core takes a conditions snapshot](../../../docs/decisions/0005-conditions-provider-edge-seam.md)
- [ADR0007: The horizon is a cyclic set of (az, alt) samples with linear interpolation](../../../docs/decisions/0007-canonical-horizon-representation.md)
- [ADR0008: The deep-sky object catalog is the full OpenNGC vendored as pinned in-repo data](../../../docs/decisions/0008-vendored-openngc-catalog.md)
- [ADR0009: The targets field is filled additively with a structured, numbers-only target element](../../../docs/decisions/0009-targets-structured-additive-fill.md)
- [ADR0010: The ranking score renormalises over the factors whose inputs are known](../../../docs/decisions/0010-ranking-renormalises-over-known-factors.md)
- [ADR0011: The LLM narrative is delivered as a separate entity, not a verdict-document field](../../../docs/decisions/0011-narrative-separate-entity-not-document-field.md)
- [ADR0012: A threaded MQTT loop with a main-thread work queue and an absolute refresh deadline](../../../docs/decisions/0012-threaded-loop-work-queue.md)
- [ADR0013: Release versions are monthly CalVer, and the git tag is their only source](../../../docs/decisions/0013-calver-versions-from-git-tags.md)
- [ADR0014: The Home Assistant add-on lives in this repository and runs the released image](../../../docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md)
- [ADR0015: Provider health travels beside the verdict as diagnostic entities, held only in memory](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md)
- [ADR0016: PierPressure runs on Python 3.14](../../../docs/decisions/0016-python-3-14.md)
- [ADR0017: Inside an add-on, the broker comes from the config file or the Supervisor, never a mix](../../../docs/decisions/0017-addon-broker-from-supervisor-as-one-source.md)
- [ADR0018: The MQTT library retries every connection to the broker](../../../docs/decisions/0018-mqtt-library-owns-broker-retries.md)
- [ADR0019: The replay after a reconnect repairs what an outage missed, not the MQTT client queue](../../../docs/decisions/0019-replay-repairs-outage-publishes.md)
- [ADR0020: The add-on is set up on a form, and the form is translated into the config file's shape](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md)
- [ADR0021: Inside an add-on, the config file adds the settings the form leaves unset](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md)
- [ADR0022: The core is the only place that validates settings, whatever the interface](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md)
- [ADR0023: Once the night has started, the verdict judges the rest of it](../../../docs/decisions/0023-verdict-judges-the-remaining-night.md)
- [ADR-0024: Self-hosted Renovate owns every dependency update, and Dependabot only raises alerts](../../../docs/decisions/0024-self-hosted-renovate-owns-dependency-updates.md)
- [ADR0025: The verdict document carries a flat hourly timeline as evidence beside the verdict](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md)

ADR-0006 is deprecated, so it was read for context only.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. DD1, DD2 and
  DD4 to DD7 in design.md can be read from the code and are cheap to change.
  DD3's topic and identity scheme repeats the one Cloud cover already uses under
  ADR-0025. The choice of no device class is a requirement, and the ha-delivery
  spec records it with its reason.
