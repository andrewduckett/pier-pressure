---
id: adrs-adr0007
date: 2026-09-11
status: accepted
title: 'ADR0007: The horizon is a cyclic set of (az, alt) samples with linear interpolation'
description: Architecture Decision Record for representing each pier's horizon mask as an azimuth-sorted, north-zero, cyclic set of (azimuth, altitude) samples with linear interpolation, so every source converts to one shape and later target ranking binds to a stable seam.
---

# ADR-0007: The horizon is a cyclic set of (az, alt) samples with linear interpolation

## Context

A pier is a fixed spot a user images the sky from. Each pier has a horizon mask:
the terrain — trees, buildings, hills — that blocks part of its sky. PierPressure
describes any sky direction by two angles: azimuth, the compass bearing, and
altitude, the height above the horizon. A horizon mask arrives from several
sources: hand-authored config, a flat altitude floor, no horizon at all, and
files exported by other tools (NINA files now, with Stellarium and Telescopius to
follow). These sources disagree on their delimiter, and even on where azimuth zero
points. Two kinds of code bind tightly to whatever internal shape we pick: the
importers that feed it, and the later target-visibility check that reads it.
Changing the shape or its azimuth convention after those exist is expensive. So we
fix it here, rather than leave it implicit in the first parser.

## Decision

Represent a horizon as an azimuth-sorted set of (azimuth, altitude) samples.
Azimuth is measured from true north at 0 degrees, clockwise, in the half-open
range 0 to 360. Altitude runs from 0 to 90 degrees. Close the samples into a ring,
so the arc from the largest azimuth back to the smallest wraps across the 360/0
boundary. The altitude at any azimuth is the straight-line interpolation between
the two nearest samples. Every source normalises to this one shape at its own
edge: each importer converts its source's azimuth convention before its samples
enter the canonical form. A point is above the horizon when its altitude is at
least the interpolated horizon altitude in its direction.

## Consequences

- **Easier:** imports round-trip. This is the shape the tools already store and
  draw as a straight-line polygon, so a user's in-tool preview and PierPressure
  agree.
- **Easier:** one query path serves every source. A flat altitude floor and the
  default open sky are just a single-altitude ring, so the query needs no special
  case — only how the samples are built differs.
- **Easier:** the target-visibility check gets a stable, source-agnostic seam. It
  asks for the altitude at an azimuth and an above-or-below answer, without knowing
  where the horizon came from.
- **Constraint accepted:** the north-zero, clockwise convention is now
  load-bearing. Each importer owns normalising its source's convention — Stellarium
  landscapes are sometimes south-zero — which is why an importer is more than
  delimiter-splitting, and each format needs a real fixture to pin it.
- **Constraint accepted:** the straight-line interpolation and the inclusive
  boundary are pinned, so the same samples and query always classify a point the
  same way. This matches the core's determinism guarantee (ADR-0004). The query
  rounds its interpolated altitude to a fixed decimal precision, so unrounded
  floating-point cannot flip the boundary across platforms.
- **Constraint accepted:** the ring is total. The samples define the horizon for
  every azimuth, not a partial overlay — a sparse set interpolates across the
  directions it does not name, including the wrap segment. So leaving a region as
  open sky needs explicit low anchor samples. A one-sample horizon, like the
  flat-floor and open-sky cases, is a constant altitude everywhere, not a
  degenerate interpolation. An input azimuth of exactly 360 is the same direction
  as 0 and is normalised to it.

## Alternatives Considered

### Alternative 1: A fixed-step altitude array (an altitude every N degrees of azimuth)

- **Pros**: terse to hand-author — one row of numbers, with no repeated azimuths.
- **Cons**: no tool exports this shape, so it cannot hold an imported horizon
  without conversion, and it forces a second internal form beside the sample list.
- **Why not**: it invents a shape the importers would have to convert away from,
  which breaks "one representation every source produces." The same terseness is
  available as config sugar over the sample list, with no separate internal model.

### Alternative 2: Step or nearest-neighbour interpolation between samples

- **Pros**: trivial to define — no interpolation arithmetic and no wrap-seam edge
  case.
- **Cons**: it disagrees with how NINA and Stellarium draw the horizon, which is a
  straight line between points. A target near a slope would then be classified
  differently from what the user saw in the tool.
- **Why not**: matching the tools' own rendering is the whole point of importing
  their files. A mismatch would surface as "PierPressure disagrees with my
  planetarium."

### Alternative 3: Store each source's native azimuth convention and normalise at query time

- **Pros**: the importer stays a plain delimiter parse, with no convention logic in
  adapters.
- **Cons**: the query must then know every source's convention, so the one place
  conventions differ leaks into the hot path and into the visibility check, and a
  horizon's meaning depends on remembering which source it came from.
- **Why not**: normalising once, at the edge, keeps the canonical form
  single-meaning and the query trivial. The convention knowledge belongs in the
  adapter that already knows the format.
