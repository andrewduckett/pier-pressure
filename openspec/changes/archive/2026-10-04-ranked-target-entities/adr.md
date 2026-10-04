# ADR Review Manifest

- Status: completed
- Review date: 2026-10-04

## Review Summary

ADR review completed for this change. The design adds ten sensor entities to the
existing MQTT adapter, using the patterns the Top target and Narrative sensors
already use. Its choices are a topic layout, an attributes shape, and a display-name
helper. Each is cheap to reverse and readable from the code, so none meets the ADR bar.

## In-Force ADRs Reviewed

- ADR-0001: Home-Assistant-agnostic core with a JSON verdict contract delivered via a dumb adapter. The rank sensors live in the adapter and read the finished document. The core is untouched.
- ADR-0002: Night verdict uses hard gates then a banded score. Not affected.
- ADR-0003: Target observability is hard-clamped to astronomical night. Not affected. The rank sensors show windows the ranking already clamped.
- ADR-0004: Deterministic offline astronomy via Skyfield. Not affected.
- ADR-0005: Weather enters at a provider edge. Not affected.
- ADR-0007: The horizon is a cyclic set of (az, alt) samples. Not affected.
- ADR-0008: The deep-sky object catalog is the full OpenNGC vendored in-repo. Not affected.
- ADR-0009: The targets field is filled additively with a structured, numbers-only target element. The rank sensors' attributes carry those structured fields unchanged.
- ADR-0010: The ranking score renormalises over the factors whose inputs are known. Not affected.
- ADR-0011: The LLM narrative is delivered as a separate entity. The rank sensors follow the same additive-entity approach and reuse its availability-flag pattern.
- ADR-0012: A threaded MQTT loop with a main-thread work queue. The rank sensors publish on the same main-thread publish path.
- ADR-0013: Release versions are monthly CalVer from git tags. Not affected.
- ADR-0014: The Home Assistant add-on lives in this repository and runs the released image. Not affected.

ADR-0006 is deprecated and was not treated as in force.

## New Durable ADRs Created

- None. This change introduces no major durable architectural decisions.
