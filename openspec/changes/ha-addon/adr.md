# ADR Review Manifest

- Status: completed
- Review date: 2026-10-03

## Review Summary

ADR review completed for this change. One decision in design.md meets the bar for
a durable ADR. Users will add this repository's URL in Home Assistant, so where
the add-on lives, and how it gets its image, is costly to reverse (design D1, D2
and D5 together).

The other design decisions do not need ADRs:

- D3 (the config folder and environment variable) and D4 (Docker's default init)
  are add-on settings that the code shows and that are cheap to change.
- D6 (the two image labels) and D7 (the drift test) can change without users
  noticing.
- D8 (proving the add-on before merge) is a verification step, not a fork.

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
- ADR-0013: release versions are monthly CalVer, and the git tag is their only
  source

ADR-0006 is deprecated and was not treated as in force. This change keeps
ADR-0001: the add-on is packaging around the same service, and the core gains no
Home Assistant code. It keeps ADR-0013: the release still commits nothing, and
the add-on version update arrives as a pull request.

## New Durable ADRs Created

- [ADR-0014: The Home Assistant add-on lives in this repository and runs the
  released image](../../../docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md)
