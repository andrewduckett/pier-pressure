# ADR Review Manifest

- Status: completed
- Review date: 2026-10-05

## Review Summary

ADR review completed for this change. The design makes one durable decision: provider
health travels beside the verdict as separate entities and is kept only in memory.
That is a system boundary that a later change could reverse at real cost, so it gets
a new ADR. The other design decisions (types, module placement, topic names, error
shortening, and the README automation) can be read from the code and changed cheaply,
so they stay in `design.md`.

## In-Force ADRs Reviewed

- ADR-0001: Home-Assistant-agnostic core with a JSON verdict contract
- ADR-0002: Verdict uses hard gates then a banded score
- ADR-0003: Target observability is hard-clamped to astronomical night
- ADR-0004: Deterministic offline astronomy via Skyfield with pinned data
- ADR-0005: Weather enters at a provider edge; the core takes a conditions snapshot
- ADR-0007: The horizon is a cyclic set of (az, alt) samples with linear interpolation
- ADR-0008: The deep-sky object catalog is the full OpenNGC vendored as pinned in-repo data
- ADR-0009: The targets field is filled additively with a structured, numbers-only target element
- ADR-0010: The ranking score renormalises over the factors whose inputs are known
- ADR-0011: The LLM narrative is delivered as a separate entity, not a verdict-document field
- ADR-0012: A threaded MQTT loop with a main-thread work queue and an absolute refresh deadline
- ADR-0013: Release versions are monthly CalVer, and the git tag is their only source
- ADR-0014: The Home Assistant add-on lives in this repository and runs the released image

ADR-0006 is deprecated and was read only for history. This change follows ADR-0005
(health comes from the provider edge, not the core) and the pattern of ADR-0011 (a
separate entity beside the verdict document).

## New Durable ADRs Created

- `docs/decisions/0015-provider-health-beside-verdict-in-memory.md`
