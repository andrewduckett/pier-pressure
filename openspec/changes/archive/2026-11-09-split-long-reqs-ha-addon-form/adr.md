# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Four set rules that the split requirements specify, and the split keeps each one, now as its own requirement:
  - [ADR-0014](../../../docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md): the add-on wraps the released image and mounts its own config folder ("A relative horizon file path in config.yaml is read from the add-on's config folder").
  - [ADR-0020](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md): the form's values become the shape of a config file, its names follow the file's names, and outside an add-on the form is never read ("The form's setting names match the names in config.yaml", "The add-on builds one set of settings from the form and config.yaml", "Outside an add-on, the service does not read the Configuration form").
  - [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md): the file adds only settings the form leaves unset, a setting in both or an unlisted file pier stops the add-on, some settings count as one, and the form must list a pier ("A pier in config.yaml adds its settings to the form pier with its id", "A setting given on the form and in config.yaml stops the add-on", the two group requirements, "A pier in config.yaml that the form does not list stops the add-on", "A Configuration form with no piers stops the add-on").
  - [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): the core alone validates values, and the Supervisor's save check is a convenience ("Each pier is checked after the file's settings are added to it", and the save checks in the horizon, equipment and gate field requirements. The equipment and gate ones still say "The service then rejects 0").

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), and each added scenario restates a SHALL its requirement keeps, which an existing test asserts, so none is a costly fork.
