# ADR Review Manifest

- Status: completed
- Review date: 2026-11-15

## Review Summary

ADR review completed for this change. Of the design's decisions, only DD8
passes the test: whether calling Home Assistant for the narrative breaks the
rule that Home Assistant is never load-bearing. The others (the provider's
module, the request body, the error type, the config field, the wiring table,
the add-on files, the time bound) can be read from the code and changed
cheaply. The new record follows this repository's file naming,
`NNNN-<slug>.md`, rather than the schema's `ADR-NNN-<slug>.md`.

## In-Force ADRs Reviewed

Every accepted record in `docs/decisions/`, ADR-0001 to ADR-0041, except the
superseded ADR-0006 and ADR-0026. These bear on this change:

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core is Home Assistant-agnostic; Home Assistant is a delivery adapter.
- [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md): network access stays at the edge, outside the core.
- [ADR-0011](../../../docs/decisions/0011-narrative-separate-entity-not-document-field.md): the narrative is its own entity, never a field of the verdict document.
- [ADR-0020](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md): the add-on form is translated to the config file's shape.
- [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md): the file adds settings the form leaves unset; a setting in both is an error.
- [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): only the core checks a setting's value.
- [ADR-0039](../../../docs/decisions/0039-a-key-in-a-url-is-masked-in-every-log-record.md): secrets are kept out of every log record.

## New Durable ADRs Created

- [ADR-0042](../../../docs/decisions/0042-addon-narrative-may-come-from-home-assistant-ai-task.md): in the add-on, the narrative may come from Home Assistant's AI Task without making Home Assistant load-bearing. It builds on ADR-0011.
