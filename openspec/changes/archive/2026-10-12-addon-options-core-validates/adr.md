# ADR Review Manifest

- Status: completed
- Review date: 2026-10-12

## Review Summary

ADR review completed for this change.

The change makes one durable decision: the core is the only place that validates
settings, whatever the interface (design D2 to D5). It meets the bar for an ADR.
An engineer reading only the add-on code could add a "helpful" check back into
the interface layer. That would make interfaces disagree again, and undoing it
later means finding every copy.

The other decisions are cheap to reverse and are guarded by specs and tests:

- Parsing text in `horizon.points` with a before-validator (design D1) is a
  local choice. The `horizon-mask` delta spec requires the behaviour.
- Using `is_set` to decide when a `horizon` or `equipment` value keeps the set
  flat fields in place (design D2, D3) matches an existing rule, and tests cover
  it.

This change applies these ADRs without changing them:

- ADR-0001 keeps the core free of Home Assistant code. Text horizon points are a
  general config format, not a Home Assistant concept.
- ADR-0007 sets the canonical horizon. Text points convert to the same canonical
  horizon as a list.
- ADR-0020 translates the form into the config file's shape. This change narrows
  the translation to renaming.
- ADR-0021 lets the config file add settings the form leaves unset. Its rule
  against a setting given in both stays in the add-on, because it is about
  combining two sources.

## In-Force ADRs Reviewed

- ADR-0001 to ADR-0005 and ADR-0007 to ADR-0021, all accepted. ADR-0006 is
  deprecated. No ADR supersedes another. Most relevant: 0001, 0007, 0020, 0021.

## New Durable ADRs Created

- [ADR-0022: The core is the only place that validates settings, whatever the
  interface](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md)
