<!-- Plain language: Make each record link identify the decision so a reader can find its rationale. Keep this manifest separate from the records themselves. -->

# ADR Review Manifest

- Status: completed
- Review date: 2026-11-22

## Review Summary

ADR review completed for this change. Of design.md's decisions, only DD7 (how
the verdict document and the Home Assistant delivery carry later nights)
passes the test: it fixes a contract shape that the next story builds on, and
reversing it would change document keys and entities that users rely on. DD1
to DD6 are recoverable from the code and the specs.

## In-Force ADRs Reviewed

Every record in `docs/decisions/` was read. The ones most relevant here are
ADR-0001, ADR-0009, ADR-0011, ADR-0023, ADR-0025 and ADR-0030. These are in
force:

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
- [ADR0020: The add-on is set up on a form, and the form is translated into the config file''s shape](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md)
- [ADR0021: Inside an add-on, the config file adds the settings the form leaves unset](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md)
- [ADR0022: The core is the only place that validates settings, whatever the interface](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md)
- [ADR0023: Once the night has started, the verdict judges the rest of it](../../../docs/decisions/0023-verdict-judges-the-remaining-night.md)
- [ADR-0024: Self-hosted Renovate owns every dependency update, and Dependabot only raises alerts](../../../docs/decisions/0024-self-hosted-renovate-owns-dependency-updates.md)
- [ADR0025: The verdict document carries a flat hourly timeline as evidence beside the verdict](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md)
- [ADR0027: Conditions are filled variable by variable from an ordered provider list](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md)
- [ADR-0028: Each Open-Meteo model is its own provider](../../../docs/decisions/0028-each-open-meteo-model-is-its-own-provider.md)
- [ADR-0029: Forecast agreement is an input to confidence, never to a gate or the score](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md)
- [ADR-0030: Raw input variables stay out of the verdict document](../../../docs/decisions/0030-raw-input-variables-stay-out-of-the-verdict-document.md)
- [ADR-0031: Computed variables come from a source in the provider order](../../../docs/decisions/0031-computed-variables-are-a-source-in-the-provider-order.md)
- [ADR-0032: Computed transparency estimates extinction and maps it onto 7Timer!''s scale](../../../docs/decisions/0032-computed-transparency-estimates-extinction.md)
- [ADR-0033: Computed seeing subtracts capped penalties for bad layers, the jet stream and the boundary layer](../../../docs/decisions/0033-computed-seeing-sums-capped-penalties.md)
- [ADR-0034: PierPressure ships its own dashboard card, from this repository, through HACS](../../../docs/decisions/0034-pierpressure-ships-its-own-dashboard-card-through-hacs.md)
- [ADR-0035: The PierPressure card is the only dashboard PierPressure documents](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md)
- [ADR-0036: Once the night has started, targets are ranked on the rest of it, beside their whole-night window](../../../docs/decisions/0036-targets-ranked-on-the-remaining-night.md)
- [ADR-0037: Observations are a core input beside the conditions, never a provider](../../../docs/decisions/0037-observations-are-a-core-input-beside-the-conditions.md)
- [ADR-0038: An observation can only lower confidence, never raise it or change a gate or the score](../../../docs/decisions/0038-an-observation-only-lowers-confidence.md)
- [ADR-0039: A key that travels in a request URL is masked in every log record](../../../docs/decisions/0039-a-key-in-a-url-is-masked-in-every-log-record.md)
- [ADR0040: A pier''s form fields stay in one flat list, and each label names its section](../../../docs/decisions/0040-addon-pier-fields-stay-flat-with-sectioned-labels.md)
- [ADR0041: Settings YAML keeps YAML 1.1 rules, except that padded integers are decimal and base-60 values are text](../../../docs/decisions/0041-config-yaml-reads-padded-integers-as-decimal.md)
- [ADR0042: In the add-on, the narrative may come from Home Assistant''s AI Task without making Home Assistant load-bearing](../../../docs/decisions/0042-addon-narrative-may-come-from-home-assistant-ai-task.md)

ADR-0006 and ADR-0026 are superseded and were read for history only.

## New Durable ADRs Created

- [ADR-0043: Later nights are entries in the verdict document, delivered one sensor per night](../../../docs/decisions/0043-later-nights-are-document-entries-delivered-one-sensor-per-night.md), building on ADR-0025.
