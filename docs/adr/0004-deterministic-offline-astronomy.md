---
id: adrs-adr0004
date: 2026-09-08
status: accepted
title: 'ADR0004: Deterministic offline astronomy via Skyfield with pinned data'
description: Architecture Decision Record for computing sun/moon astronomy with Skyfield alone, using a version-pinned ephemeris and built-in timescale with no runtime network access, so the verdict stays deterministic and self-contained.
---

# ADR-0004: Deterministic offline astronomy via Skyfield with a pinned ephemeris and built-in timescale

## Context

The sky-and-light milestone introduces the project's first scientific dependency to compute the astronomical-night window and moon information. Two cross-cutting rules constrain how: the core must be deterministic (same inputs, including a pinned instant, yield a byte-identical document) and no external data source may be load-bearing (the container owns its freshness and correctness offline). Astronomy libraries fight both by default — notably Astropy auto-downloads IERS earth-orientation data at runtime, which both changes over time and requires network access, and Skyfield's default loader fetches its ephemeris on first use. Full-precision floating-point results can also differ in their low-order digits across platforms and library patch versions, breaking byte-identity.

## Decision

Compute all astronomy with Skyfield alone (not Astroplan/Astropy), using a version-pinned ephemeris shipped with the image and Skyfield's built-in timescale, with zero runtime network access; and emit astronomical numbers at a fixed decimal precision so output is byte-identical. The ephemeris is delivered as a lockfile-pinned dependency where possible, otherwise downloaded at build time under a SHA-256 checksum. Determinism thus rests entirely on the lockfile plus the rounding rule, and is guarded by an offline test asserting the core makes no network access.

## Consequences

- Easier: verdict production is a pure function of (pier, clock); it runs fully offline, is reproducible in CI, and cannot silently drift as upstream earth-orientation data updates. A version bump that shifts a rounded value fails a determinism test and is reviewed deliberately.
- Harder: the image carries a bundled ephemeris (~tens of MB) and a data-pinning discipline; adopting Astropy-based helpers later would mean re-solving the IERS auto-download problem. Sub-arcsecond precision is deliberately forgone (unnecessary for twilight-to-the-second and 2-dp angles).

## Alternatives Considered

### Alternative 1: Skyfield + Astroplan/Astropy (the full roadmap candidate stack)
- **Pros**: Astroplan offers ready-made twilight/observability helpers; Astropy is the de-facto astronomy toolkit.
- **Cons**: Astropy auto-downloads IERS data at runtime, breaking both determinism and the offline constraint; larger image and more surface.
- **Why not**: Skyfield's `almanac.find_discrete` covers twilight crossings and moon rise/set on its own, so the extra dependency buys precision we do not need at the cost of the two rules we must keep.

### Alternative 2: Let the library fetch data at runtime (default loaders / a first-boot cache volume)
- **Pros**: smallest image; no build-time data step.
- **Cons**: the first run (or every cache miss) requires network; fetched data changes over time.
- **Why not**: directly violates "no load-bearing external source" and determinism; it only defers the download rather than removing it.

### Alternative 3: Emit full-precision floats without a rounding rule
- **Pros**: no precision decision to make; maximal numeric fidelity.
- **Cons**: low-order digits can differ across platforms and library patch versions, so "byte-identical" fails intermittently.
- **Why not**: the contract's determinism guarantee is more valuable than fidelity beyond two decimals, which exceeds what the verdict needs.
