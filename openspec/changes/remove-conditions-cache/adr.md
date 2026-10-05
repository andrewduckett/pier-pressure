# ADR Review Manifest

- Status: completed
- Review date: 2026-10-04

## Review Summary

ADR review completed for this change. The change removes the conditions cache from
the provider layer. It adds no new architecture. The provider-edge seam in ADR-0005
stays exactly as decided, and only its mention of caching becomes untrue. The user
chose to correct ADR-0005 in place, with a dated note, rather than supersede part of
it (design D4). A task in this change makes that edit.

The other design decisions do not meet the ADR bar. Deleting a class (D1), keeping
a tuning curve (D2), renaming a test case (D3), and not retrying (D5) are each cheap
to reverse and readable from the code or the specs.

## In-Force ADRs Reviewed

- ADR-0001: Home-Assistant-agnostic core with a JSON verdict contract. Not affected. The verdict document and delivery surface keep their shape.
- ADR-0002: Night verdict uses hard gates then a banded score. Not affected. A failed fetch reaches the existing missing-data rules.
- ADR-0003: Target observability is hard-clamped to astronomical night. Not affected.
- ADR-0004: Deterministic offline astronomy via Skyfield. Not affected. The core stays pure and its golden verdicts stay byte-identical.
- ADR-0005: Weather enters at a provider edge. Affected. The seam stays. Its Decision and Consequences sections mention caching, and this change edits those passages in place and adds a dated note.
- ADR-0007: The horizon is a cyclic set of (az, alt) samples. Not affected.
- ADR-0008: The deep-sky object catalog is the full OpenNGC vendored in-repo. Not affected. Its "cached loader" is a different cache.
- ADR-0009: The targets field is filled additively. Not affected.
- ADR-0010: The ranking score renormalises over the factors whose inputs are known. Not affected. A missing source already lowers the known factors.
- ADR-0011: The LLM narrative is delivered as a separate entity. Not affected. The explainer's own cache is a different cache.
- ADR-0012: A threaded MQTT loop with a main-thread work queue. Not affected. Fetches still run on the main thread, now without a cache in front.
- ADR-0013: Release versions are monthly CalVer from git tags. Not affected.
- ADR-0014: The Home Assistant add-on runs the released image. Not affected.

ADR-0006 is deprecated and was not treated as in force. It mentions caching in an
alternative it rejected, and stays as written as a historical record.

## New Durable ADRs Created

- None. This change introduces no major durable architectural decisions. It amends
  ADR-0005 in place instead.
