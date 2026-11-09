# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Three set rules that the split requirements specify, and the split keeps each one:
  - [ADR-0020](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md): the form's values become the shape of a config file ("A form pier's horizon_points become its horizon points", "A form pier's equipment fields set its equipment", "A form pier's go_threshold and max_gust pass to the pier").
  - [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md): the file adds only settings the form leaves unset ("A form pier with no horizon field takes its horizon from config.yaml", its equipment twin, and "An unset go_threshold or max_gust on the form comes from config.yaml").
  - [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): the core alone validates values ("Horizon points the core cannot read skip the form pier", "A horizon value beside a set horizon field skips the form pier", and "An equipment value beside an equipment field skips the form pier", where the core, not the add-on, rejects the pier).

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), and no scenario is added, so none is a costly fork.
