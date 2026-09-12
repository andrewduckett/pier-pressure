---
id: adrs-adr0008
date: 2026-09-11
status: accepted
title: 'ADR0008: The deep-sky object catalog is the full OpenNGC vendored as pinned in-repo data'
description: Architecture Decision Record for sourcing target ranking's catalog by committing the upstream OpenNGC data files into the repository and loading them inside the pure core like the ephemeris, rather than adding a package dependency or a catalog-source interface.
---

# ADR-0008: The deep-sky object catalog is the full OpenNGC vendored as pinned in-repo data

## Context

Milestone M5 ranks what to point at from a pier, which needs a catalog of deep-sky
objects with their J2000 coordinates. The core's determinism guarantee (ADR-0004)
requires that the same `(pier, instant)` yield a byte-identical document with no
runtime network access, so the catalog must be offline and version-pinned exactly
as the ephemeris is. The roadmap named "Messier / OpenNGC" as the source. How the
catalog is obtained and pinned is hard to change later: the ranking, the parser,
and every golden fixture bind to whatever objects and coordinates it yields.

## Decision

Commit the upstream OpenNGC data files into the repository as-is, with their
license and attribution, and load them inside a pure-core module via a cached
loader that mirrors the ephemeris loader in `core/sky.py`. The committed bytes are
the version pin. The loader filters to observable deep-sky types and applies the
magnitude cutoff. There is no catalog-source interface: OpenNGC is the one
catalog, and Messier is a view over it (its `M` designation), not a second source.

## Consequences

- Easier: determinism is airtight and reviewable — the exact catalog is in the
  repository diff, and no external package can shift a coordinate between releases.
- Easier: the dependency surface stays lean (no new Python package for data we can
  commit), consistent with the project's small dependency set.
- Easier: loading inside the core, like the ephemeris, keeps `produce_verdict`'s
  signature unchanged; the catalog is static offline data, unlike conditions,
  which are I/O passed in at the provider edge (ADR-0005).
- Constraint accepted: the OpenNGC license (CC-BY-SA-4.0) now governs a vendored
  file, so the repository carries a NOTICE and attribution, and share-alike
  compatibility with the repository's own license is a merge-time check.
- Constraint accepted: the project owns a parser for OpenNGC's format (sexagesimal
  J2000 coordinates, its type vocabulary, blank magnitudes), pinned with real-row
  fixtures including the addendum.
- Constraint accepted: updating the catalog is a deliberate, reviewed commit of new
  data files, not a version bump — which is the intended trade for the pin.

## Alternatives Considered

### Alternative 1: Vendor only a curated Messier subset

- **Pros**: ~110 rows, trivially small and reviewable; a hand-checkable set.
- **Cons**: it under-delivers the milestone's stated ambition, and Messier is
  already derivable as a filter over the full catalog.
- **Why not**: the full catalog is the goal; a subset would force a second
  sourcing effort later for the objects Messier omits.

### Alternative 2: Add the `pyongc` package dependency

- **Pros**: authoritative, maintained, offline, pinned via the lockfile; no parser
  to own.
- **Cons**: adds a dependency for data we can commit, and makes determinism depend
  on the package holding its coordinate values stable across releases; its schema
  becomes ours.
- **Why not**: a committed file is the tighter pin and keeps the dependency surface
  lean; the package's convenience does not outweigh ceding the pin to an external
  release cadence.

### Alternative 3: A catalog-source interface with OpenNGC as one implementation

- **Pros**: symmetry with the conditions provider seam (ADR-0005); an obvious slot
  for future sources.
- **Cons**: there is only one real catalog now, so the interface is abstraction
  ahead of need, and it invites inventing a shape before a second source defines
  it.
- **Why not**: the conditions seam earned its interface because M3 had two genuine
  sources; here a single source does not, and a seam can be extracted later if a
  second source (custom lists, all-sky-camera feeds) ever arrives.
