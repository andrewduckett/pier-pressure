# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Four set rules that the split requirements specify, and the split keeps each one:
  - [ADR-0017](../../../docs/decisions/0017-addon-broker-from-supervisor-as-one-source.md): all four connection settings come from one source, and a port or login in the file without a host is an error ("A broker host in config.yaml sets all four connection settings", "With no broker host set, the connection settings come from the Supervisor", "A broker port or login in config.yaml without a host is rejected", "Outside an add-on, the service does not ask the Supervisor for the broker").
  - [ADR-0020](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md): the form's values become the shape of a config file ("The add-on only reads, renames and combines the saved form values").
  - [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md): the file adds only settings the form leaves unset ("The add-on's config.yaml uses the same keys as outside Home Assistant").
  - [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): the core alone validates values, and the add-on passes on what it does not expect ("The core checks each saved setting as it checks config.yaml").

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), and the two added scenarios restate rules the requirements keep, so none is a costly fork.
