---
id: adrs-adr0008
date: 2026-09-11
status: accepted
title: 'ADR0008: The deep-sky object catalog is the full OpenNGC vendored as pinned in-repo data'
description: Architecture Decision Record for sourcing target ranking's catalog by committing the upstream OpenNGC data files into the repository and loading them inside the pure core like the ephemeris, rather than adding a package dependency or a catalog-source interface.
---

# ADR-0008: The deep-sky object catalog is the full OpenNGC vendored as pinned in-repo data

## Context

To rank what to point at from a pier, PierPressure needs a catalog of deep-sky
objects — galaxies, nebulae, and clusters — each with its sky coordinates in the
standard J2000 reference frame. The determinism guarantee (ADR-0004) says the same
pier and instant must yield a byte-identical document with no runtime network
access. So the catalog must be offline and version-pinned, exactly as the bundled
star-and-planet ephemeris already is. OpenNGC is a well-known open catalog that
covers this. How the catalog is obtained and pinned is hard to change later: the
ranking, the parser, and every recorded test fixture bind to whatever objects and
coordinates it yields.

## Decision

Commit the upstream OpenNGC data files into the repository as-is, with their
license and attribution. Load them inside the pure core with a cached loader, the
same pattern the ephemeris already uses. The committed bytes are the version pin.
The loader keeps only observable deep-sky types and applies the brightness cutoff.
There is no catalog-source interface: OpenNGC is the one catalog, and the Messier
list is just a view over it, not a second source.

## Consequences

- **Easier:** determinism is airtight and reviewable — the exact catalog sits in
  the repository diff, and no external package can shift a coordinate between
  releases.
- **Easier:** the dependency surface stays lean, with no new Python package for
  data we can commit, matching the project's small dependency set.
- **Easier:** loading inside the core, like the ephemeris, leaves the core's
  verdict function unchanged. The catalog is static offline data, unlike weather
  conditions, which are fetched and passed in at a provider edge (ADR-0005).
- **Constraint accepted:** the OpenNGC license (CC-BY-SA-4.0) now governs a
  vendored file, so the repository carries a NOTICE and attribution, and
  share-alike compatibility with the repository's own license is a merge-time
  check.
- **Constraint accepted:** the project owns a parser for OpenNGC's format —
  sexagesimal J2000 coordinates, its type vocabulary, and blank magnitudes —
  pinned with real-row fixtures, including the addendum file.
- **Constraint accepted:** updating the catalog is a deliberate, reviewed commit of
  new data files, not a version bump. That is the intended trade for the pin.

## Alternatives Considered

### Alternative 1: Vendor only a curated Messier subset

- **Pros**: about 110 rows — trivially small, reviewable, and hand-checkable.
- **Cons**: it under-delivers the goal, and the Messier list is already derivable
  as a filter over the full catalog.
- **Why not**: the full catalog is the goal; a subset would force a second sourcing
  effort later for the objects Messier leaves out.

### Alternative 2: Add the `pyongc` package dependency

- **Pros**: authoritative, maintained, offline, and pinned through the lockfile,
  with no parser to own.
- **Cons**: it adds a dependency for data we can commit, and it makes determinism
  depend on the package holding its coordinate values stable across releases; its
  schema becomes ours.
- **Why not**: a committed file is the tighter pin and keeps the dependency surface
  lean. The package's convenience does not outweigh handing the pin to an external
  release cadence.

### Alternative 3: A catalog-source interface with OpenNGC as one implementation

- **Pros**: symmetry with the conditions provider seam (ADR-0005), and an obvious
  slot for future sources.
- **Cons**: there is only one real catalog now, so the interface is abstraction
  ahead of need, and it invites inventing a shape before a second source defines
  it.
- **Why not**: the conditions seam earned its interface because weather had two
  genuine sources. A single catalog does not, and a seam can be extracted later if
  a second source — custom lists, all-sky-camera feeds — ever arrives.
