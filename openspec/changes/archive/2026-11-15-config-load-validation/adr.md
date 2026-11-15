# ADR Review Manifest

- Status: completed
- Review date: 2026-11-15

## Review Summary

ADR review completed for this change. Of design.md's decisions, DD1 passes the
test. An engineer could replace the custom reader with `yaml.safe_load` or a
YAML 1.2 library as a tidy-up, and that would change what users' config files
mean. DD2 to DD5 are recoverable from code or are requirements the specs own:
the repeated-id rule is a requirement, not a fork between approaches.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core stays free of Home Assistant code; the reader lives in the core.
- [ADR-0007](../../../docs/decisions/0007-canonical-horizon-representation.md): horizon points still become the one canonical horizon; only how their numbers are read changes.
- [ADR-0020](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md), [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md): the form is translated to the file's shape and combined with the add-on's file; neither step changes.
- [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): the core alone checks settings, so both the number rule and the repeated-id rule live in the core, and the add-on gains no check.
- Every other record in `docs/decisions/` (ADR-0002 to ADR-0006, ADR-0008 to ADR-0019, ADR-0023 to ADR-0040) was read and is not affected.

## New Durable ADRs Created

- [ADR-0041](../../../docs/decisions/0041-config-yaml-reads-padded-integers-as-decimal.md): settings YAML keeps YAML 1.1 rules, except that padded integers are decimal and base-60 values are text (design DD1).
