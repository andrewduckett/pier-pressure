# ADR Review Manifest

- Status: completed
- Review date: 2026-10-12

## Review Summary

ADR review completed for this change.

No major durable architectural decisions were introduced, and no new
repository-level ADR files were created.

The design applies three in-force ADRs without changing them, and none is
superseded:

- ADR-0002 sets the verdict model: hard gates, then a banded score. The form
  sets two existing knobs of that model, the GO threshold and the wind gate. It
  adds no gate and changes no meaning.
- ADR-0020 turns the form into the config file's shape. The two fields keep the
  file's names, so they need no rebuilding.
- ADR-0021 lets `config.yaml` add the settings the form leaves unset. Dropping
  an empty field at the edge (design D1) keeps that rule working for the two
  new fields.

ADR-0001 keeps the core free of Home Assistant code. This change does not touch
the core.

Dropping an unset value for two named fields (design D1) is cheap to reverse and
visible in the code, so it does not need an ADR.

ADR-0006 is deprecated and was not considered.

## In-Force ADRs Reviewed

- ADR-0001: Home-Assistant-agnostic core with a JSON verdict contract (`docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md`)
- ADR-0002: Verdict uses hard gates then a banded score (`docs/decisions/0002-gates-then-banded-score.md`)
- ADR-0003: Target observability is hard-clamped to astronomical night (`docs/decisions/0003-astronomical-night-hard-clamp.md`)
- ADR-0004: Deterministic offline astronomy via Skyfield with pinned data (`docs/decisions/0004-deterministic-offline-astronomy.md`)
- ADR-0005: Weather enters at a provider edge; the core takes a conditions snapshot (`docs/decisions/0005-conditions-provider-edge-seam.md`)
- ADR-0007: The horizon is a cyclic set of (az, alt) samples with linear interpolation (`docs/decisions/0007-canonical-horizon-representation.md`)
- ADR-0008: The deep-sky object catalog is the full OpenNGC vendored as pinned in-repo data (`docs/decisions/0008-vendored-openngc-catalog.md`)
- ADR-0009: The targets field is filled additively with a structured, numbers-only target element (`docs/decisions/0009-targets-structured-additive-fill.md`)
- ADR-0010: The ranking score renormalises over the factors whose inputs are known (`docs/decisions/0010-ranking-renormalises-over-known-factors.md`)
- ADR-0011: The LLM narrative is delivered as a separate entity, not a verdict-document field (`docs/decisions/0011-narrative-separate-entity-not-document-field.md`)
- ADR-0012: A threaded MQTT loop with a main-thread work queue and an absolute refresh deadline (`docs/decisions/0012-threaded-loop-work-queue.md`)
- ADR-0013: Release versions are monthly CalVer, and the git tag is their only source (`docs/decisions/0013-calver-versions-from-git-tags.md`)
- ADR-0014: The Home Assistant add-on lives in this repository and runs the released image (`docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md`)
- ADR-0015: Provider health travels beside the verdict as diagnostic entities, held only in memory (`docs/decisions/0015-provider-health-beside-verdict-in-memory.md`)
- ADR-0016: PierPressure runs on Python 3.14 (`docs/decisions/0016-python-3-14.md`)
- ADR-0017: Inside an add-on, the broker comes from the config file or the Supervisor, never a mix (`docs/decisions/0017-addon-broker-from-supervisor-as-one-source.md`)
- ADR-0018: The MQTT library retries every connection to the broker (`docs/decisions/0018-mqtt-library-owns-broker-retries.md`)
- ADR-0019: The replay after a reconnect repairs what an outage missed, not the MQTT client queue (`docs/decisions/0019-replay-repairs-outage-publishes.md`)
- ADR-0020: The add-on is set up on a form, and the form is translated into the config file's shape (`docs/decisions/0020-addon-form-translated-to-config-file-shape.md`)
- ADR-0021: Inside an add-on, the config file adds the settings the form leaves unset (`docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md`)

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
