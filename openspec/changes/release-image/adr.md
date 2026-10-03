# ADR Review Manifest

- Status: completed
- Review date: 2026-10-03

## Review Summary

ADR review completed for this change. One decision in design.md meets the bar for
a durable ADR: the version scheme and where the version lives (design D1, plus the
CalVer scheme from the spec). Adopters pin versions, so the scheme is costly to
reverse. An engineer reading only the code could also plausibly put a hard-coded
version back.

The other design decisions do not need ADRs:

- D2 (a tested version script), D3 (the workflow's shape) and D6 (the startup log
  line) are visible in the code and cheap to change.
- D4 (QEMU emulation) can be swapped for native runners without any change that
  adopters can see.
- D5 (the uv pin and range) is tooling configuration that #26 will maintain.

## In-Force ADRs Reviewed

- ADR-0001: core is Home Assistant agnostic and emits one JSON verdict contract
- ADR-0002: gates, then a banded score
- ADR-0003: target windows are hard-clamped to astronomical night
- ADR-0004: deterministic, offline astronomy
- ADR-0005: the conditions provider is an edge seam
- ADR-0007: canonical horizon representation
- ADR-0008: vendored OpenNGC catalogue
- ADR-0009: targets are filled additively in a structured form
- ADR-0010: ranking renormalises over known factors
- ADR-0011: the narrative is a separate entity, not a verdict-document field
- ADR-0012: threaded MQTT loop with a main-thread work queue

ADR-0006 is deprecated and was not treated as in force. This change touches none
of these decisions. The verdict document, the delivery surface and the core stay
as they are. ADR-0004's version-pinned ephemeris is unaffected, because pinning
the build tooling does not touch the data packages in `uv.lock`.

## New Durable ADRs Created

- [ADR-0013: Release versions are monthly CalVer, and the git tag is their only
  source](../../../docs/decisions/0013-calver-versions-from-git-tags.md)
