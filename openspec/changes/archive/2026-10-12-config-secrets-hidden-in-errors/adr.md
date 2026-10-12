# ADR Review Manifest

- Status: completed
- Review date: 2026-10-12

## Review Summary

ADR review completed for this change.

No major durable architectural decisions were introduced, and no new
repository-level ADR files were created.

The design's decisions are each cheap to reverse. The specs state the required
behaviour, and the planned tests (design D6) will fail if a decision is undone:

- Holding the two secrets in a type that hides them (design D4) is a local type
  choice. The spec requires the result, and the tests fail if a secret shows.
- Writing block errors from their parts (design D1) and validating `explainer`
  directly (design D2) work around two Pydantic behaviours. A code comment and
  the D6 tests will guard them.

All ADRs from 0001 to 0021 are accepted, and none is superseded. This change
applies these without changing them:

- ADR-0001 keeps the core free of Home Assistant code. The secret handling lives
  in the core, so every interface gets it.
- ADR-0011 keeps the explainer an optional edge that never feeds the verdict.
  This change touches only how its API key is held and reported.
- ADR-0017 takes the add-on's broker from the Supervisor as one source. Its
  password now enters the core's hidden type in the same way as a file's.
- ADR-0020 and ADR-0021 build the add-on's settings in the file's shape, so the
  same core checks cover the add-on's combined settings.

Story #83 will record the wider rule that the core validates every setting,
whatever the interface.

## In-Force ADRs Reviewed

- ADR-0001 to ADR-0021, all accepted. Most relevant: 0001, 0011, 0017, 0020,
  0021.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
