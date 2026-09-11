---
id: adrs-adr0007
date: 2026-09-11
status: accepted
title: 'ADR0007: The horizon is a cyclic set of (az, alt) samples with linear interpolation'
description: Architecture Decision Record for representing each pier's horizon mask as an azimuth-sorted, north-zero, cyclic set of (azimuth, altitude) samples with linear interpolation, so every source converts to one shape and later target ranking binds to a stable seam.
---

# ADR-0007: The horizon is a cyclic set of (az, alt) samples with linear interpolation

## Context

Milestone M4 gives each pier a horizon mask — the terrain (trees, buildings, hills)
that blocks parts of its sky. That horizon arrives from several sources: hand-authored
config, a flat altitude floor, no horizon at all, and exported files (NINA `.hrz` now;
Stellarium and Telescopius to follow). These sources disagree on delimiter and even on
azimuth reference. Two later consumers bind tightly to whatever internal shape we pick:
the importers that feed it and M5's target-visibility test that reads it. Changing the
representation or its azimuth convention after those exist is expensive, so it is fixed
here rather than left implicit in the first parser.

## Decision

Represent a horizon as an azimuth-sorted set of `(azimuth, altitude)` samples — azimuth
measured from true north at 0 degrees, clockwise, in the half-open range 0 to 360; and
altitude in 0 to 90 degrees — closed into a ring so the arc from the greatest azimuth
back to the least wraps across the 360/0 boundary. The altitude at any azimuth is the
linear interpolation of the two bracketing samples. Every source normalises to this one
shape at its own edge (each importer converts its source's azimuth convention before its
samples enter the canonical form). A point at `(azimuth, altitude)` is above the horizon
when its altitude is greater than or equal to the interpolated horizon altitude in its
direction.

## Consequences

- Easier: imports round-trip, because this is the shape the tools already store and draw
  as a linear polygon; a user's in-tool preview and PierPressure agree.
- Easier: one query path serves every source. A flat `min_altitude` floor and the
  default open sky (flat 0) are the degenerate single-altitude ring, so there is no
  special case in the query — only in how samples are built.
- Easier: M5 gets a stable, source-agnostic seam (altitude at an azimuth; above/below
  classification) it can consume without knowing where the horizon came from.
- Constraint accepted: the north-zero-clockwise convention is now load-bearing. Each
  importer owns normalising its source's convention (Stellarium landscapes are sometimes
  south-zero), which is why an importer is more than delimiter-splitting and each format
  needs a real fixture to pin.
- Constraint accepted: the linear-interpolation and inclusive (`>=`) boundary choices are
  pinned so the same samples and query yield the same classification deterministically,
  consistent with the core's determinism guarantee (ADR-0004). The query rounds its
  interpolated altitude to a fixed decimal precision (mirroring the existing
  `_round_fraction` idiom) so unrounded floating-point cannot flip the boundary across
  platforms.
- Constraint accepted: the ring is total and complete. The samples define the horizon for
  every azimuth, not a partial overlay — a sparse set interpolates across the directions
  it does not name, including the wrap segment — so leaving a region open sky requires
  explicit low anchor samples. A one-sample horizon (and the flat-floor and open-sky
  cases) is a constant altitude everywhere, not a degenerate interpolation. An input
  azimuth of exactly 360 is the same direction as 0 and is normalized to it.

## Alternatives Considered

### Alternative 1: A fixed-step altitude array (altitudes every N degrees of azimuth)

- **Pros**: terse to hand-author — one row of numbers, no repeated azimuths.
- **Cons**: it is a shape no tool exports, so it cannot represent an imported horizon
  without conversion, and it forces a second internal form alongside the pair list.
- **Why not**: it invents a new shape the importers would have to convert away from,
  violating "one representation every source produces"; the same terseness is available
  as config sugar over the pair list without a distinct internal model.

### Alternative 2: Step or nearest-neighbour interpolation between samples

- **Pros**: trivially defined; no interpolation arithmetic; no wrap-seam edge case.
- **Cons**: it disagrees with how NINA and Stellarium draw the horizon (a straight line
  between consecutive points), so a target near a slope would be classified differently
  from what the user saw in the tool they built the horizon in.
- **Why not**: matching the tools' own rendering is the whole point of importing their
  files; a mismatch would surface as "PierPressure disagrees with my planetarium."

### Alternative 3: Store each source's native azimuth convention; normalise at query time

- **Pros**: the importer stays a pure delimiter parse; no convention logic in adapters.
- **Cons**: the query must then know every source's convention, so the one place
  conventions differ leaks into the hot path and into M5, and a horizon's meaning depends
  on remembering which source it came from.
- **Why not**: normalising once, at the edge, keeps the canonical form single-meaning and
  the query trivial; the convention knowledge belongs in the adapter that already knows
  the format.
