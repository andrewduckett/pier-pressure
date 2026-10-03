---
id: adrs-adr0004
date: 2026-09-09
status: accepted
title: 'ADR0004: Deterministic offline astronomy via Skyfield with pinned data'
description: Architecture Decision Record for computing all astronomy with Skyfield alone, using a version-pinned ephemeris shipped in the image and a fixed rounding rule, so the verdict is byte-identical and needs no runtime network access.
---

# ADR-0004: Deterministic offline astronomy via Skyfield with a pinned ephemeris and built-in timescale

## Context

PierPressure needs real astronomy to compute the dark-night window and the moon's
state. That means its first scientific library dependency. Two project-wide rules
constrain the choice. First, the core must be deterministic: the same inputs,
including a fixed evaluation instant, must always yield a byte-for-byte identical
document. Second, no external data source may be load-bearing: the app must own
its freshness and correctness offline. Astronomy libraries fight both rules by
default. Astropy downloads earth-orientation data — the IERS data that relates
Earth's rotation to time — at runtime, which needs the network and changes over
time. Skyfield's default loader fetches its ephemeris — the table of planet and
moon positions — on first use. Full-precision floating-point results can also
differ in their last digits across platforms and library versions, which breaks
byte-identity.

## Decision

Compute all astronomy with Skyfield alone, not Astroplan or Astropy. Ship a
version-pinned ephemeris inside the image and use Skyfield's built-in timescale,
with no runtime network access. Emit every astronomical number at a fixed decimal
precision, so the output is byte-identical. Deliver the ephemeris as a
lockfile-pinned dependency where possible, or download it at build time under a
SHA-256 checksum. Determinism then rests entirely on the lockfile plus the
rounding rule. An offline test guards it by asserting the core makes no network
access.

## Consequences

- **Easier:** producing a verdict is a pure function of the pier and the clock. It
  runs fully offline, reproduces in CI, and cannot drift as upstream
  earth-orientation data updates. If a version bump shifts a rounded value, a
  determinism test fails and the change gets a deliberate review.
- **Harder:** the image carries a bundled ephemeris of tens of megabytes and a
  data-pinning discipline. Adopting Astropy-based helpers later would mean solving
  the runtime-download problem again. Sub-arcsecond precision is given up on
  purpose; it is unnecessary for twilight-to-the-second and two-decimal angles.

## Alternatives Considered

### Alternative 1: Skyfield plus Astroplan/Astropy (the fuller candidate stack)
- **Pros**: Astroplan offers ready-made twilight and observability helpers, and
  Astropy is the de-facto astronomy toolkit.
- **Cons**: Astropy downloads earth-orientation data at runtime, which breaks both
  determinism and the offline rule, and it adds image size and surface.
- **Why not**: Skyfield can find twilight crossings and moon rise and set on its
  own, so the extra libraries buy precision we do not need at the cost of the two
  rules we must keep.

### Alternative 2: Let the library fetch data at runtime (default loaders or a first-boot cache)
- **Pros**: the smallest image, with no build-time data step.
- **Cons**: the first run, or any cache miss, needs the network, and fetched data
  changes over time.
- **Why not**: it breaks the "no load-bearing external source" and determinism
  rules; it only defers the download instead of removing it.

### Alternative 3: Emit full-precision floats with no rounding rule
- **Pros**: no precision decision to make, and maximum numeric fidelity.
- **Cons**: the last digits can differ across platforms and library versions, so
  byte-identity fails now and then.
- **Why not**: the contract's determinism guarantee is worth more than fidelity
  beyond two decimals, which is more than the verdict needs.
