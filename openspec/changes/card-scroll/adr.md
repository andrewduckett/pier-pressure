# ADR Review Manifest

- Status: completed
- Review date: 2026-11-07

## Review Summary

ADR review completed for this change. None of design.md's decisions passes the
test. D-1 to D-7 sit inside the card's own source, behind the published
entities, and a later change can replace any of them inside `card/src/` at
little cost: drawing a moved axis rather than native scrolling (D-1) is the
weightiest, and swapping it touches only the strip's drawing and its input
handlers. The change relies on ADR-0034: the card pans only through hours the
published timeline sensors already carry, and fetches nothing. ADR-0025 is
unaffected: the timeline stays evidence beside the verdict, and the card draws
no dusk, dawn or target bar for a night the verdict does not judge. ADR-0001
is unaffected: the core and the verdict document do not change.

## In-Force ADRs Reviewed

- [ADR-0001: Home-Assistant-agnostic core with a JSON verdict contract delivered via a dumb adapter](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md)
- [ADR-0002: Night verdict uses hard gates then a banded score, not a single weighted average](../../../docs/decisions/0002-gates-then-banded-score.md)
- [ADR-0003: Target observability is hard-clamped to astronomical night, regardless of the requested view window](../../../docs/decisions/0003-astronomical-night-hard-clamp.md)
- [ADR-0004: Deterministic offline astronomy via Skyfield with a pinned ephemeris and built-in timescale](../../../docs/decisions/0004-deterministic-offline-astronomy.md)
- [ADR-0005: Weather enters at a provider edge; the core takes a conditions snapshot](../../../docs/decisions/0005-conditions-provider-edge-seam.md)
- [ADR-0007: The horizon is a cyclic set of (az, alt) samples with linear interpolation](../../../docs/decisions/0007-canonical-horizon-representation.md)
- [ADR-0008: The deep-sky object catalog is the full OpenNGC vendored as pinned in-repo data](../../../docs/decisions/0008-vendored-openngc-catalog.md)
- [ADR-0009: The targets field is filled additively with a structured, numbers-only target element](../../../docs/decisions/0009-targets-structured-additive-fill.md)
- [ADR-0010: The ranking score renormalises over the factors whose inputs are known](../../../docs/decisions/0010-ranking-renormalises-over-known-factors.md)
- [ADR-0011: The LLM narrative is delivered as a separate entity, not a verdict-document field](../../../docs/decisions/0011-narrative-separate-entity-not-document-field.md)
- [ADR-0012: A threaded MQTT loop with a main-thread work queue and an absolute refresh deadline](../../../docs/decisions/0012-threaded-loop-work-queue.md)
- [ADR-0013: Release versions are monthly CalVer, and the git tag is their only source](../../../docs/decisions/0013-calver-versions-from-git-tags.md)
- [ADR-0014: The Home Assistant add-on lives in this repository and runs the released image](../../../docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md)
- [ADR-0015: Provider health travels beside the verdict as diagnostic entities, held only in memory](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md)
- [ADR-0016: PierPressure runs on Python 3.14](../../../docs/decisions/0016-python-3-14.md)
- [ADR-0017: Inside an add-on, the broker comes from the config file or the Supervisor, never a mix](../../../docs/decisions/0017-addon-broker-from-supervisor-as-one-source.md)
- [ADR-0018: The MQTT library retries every connection to the broker](../../../docs/decisions/0018-mqtt-library-owns-broker-retries.md)
- [ADR-0019: The replay after a reconnect repairs what an outage missed, not the MQTT client queue](../../../docs/decisions/0019-replay-repairs-outage-publishes.md)
- [ADR-0020: The add-on is set up on a form, and the form is translated into the config file's shape](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md)
- [ADR-0021: Inside an add-on, the config file adds the settings the form leaves unset](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md)
- [ADR-0022: The core is the only place that validates settings, whatever the interface](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md)
- [ADR-0023: Once the night has started, the verdict judges the rest of it](../../../docs/decisions/0023-verdict-judges-the-remaining-night.md)
- [ADR-0024: Self-hosted Renovate owns every dependency update, and Dependabot only raises alerts](../../../docs/decisions/0024-self-hosted-renovate-owns-dependency-updates.md)
- [ADR-0025: The verdict document carries a flat hourly timeline as evidence beside the verdict](../../../docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md)
- [ADR-0027: Conditions are filled variable by variable from an ordered provider list](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md)
- [ADR-0028: Each Open-Meteo model is its own provider](../../../docs/decisions/0028-each-open-meteo-model-is-its-own-provider.md)
- [ADR-0029: Forecast agreement is an input to confidence, never to a gate or the score](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md)
- [ADR-0030: Raw input variables stay out of the verdict document](../../../docs/decisions/0030-raw-input-variables-stay-out-of-the-verdict-document.md)
- [ADR-0031: Computed variables come from a source in the provider order](../../../docs/decisions/0031-computed-variables-are-a-source-in-the-provider-order.md)
- [ADR-0032: Computed transparency estimates extinction and maps it onto 7Timer!'s scale](../../../docs/decisions/0032-computed-transparency-estimates-extinction.md)
- [ADR-0033: Computed seeing subtracts capped penalties for bad layers, the jet stream and the boundary layer](../../../docs/decisions/0033-computed-seeing-sums-capped-penalties.md)
- [ADR-0034: PierPressure ships its own dashboard card, from this repository, through HACS](../../../docs/decisions/0034-pierpressure-ships-its-own-dashboard-card-through-hacs.md)

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
