---
id: adrs-adr0006
date: 2026-09-10
status: accepted
title: 'ADR0006: The conditions snapshot is modelled as per-source groups'
description: Architecture Decision Record for shaping the core's conditions input as one self-stamped group per source (cloud, wind, seeing) rather than a flat hourly grid with side-channel issue-times, refining the provider-edge seam of ADR-0005.
---

# ADR-0006: The conditions snapshot is modelled as per-source groups

## Context

ADR-0005 put conditions into the pure core as an immutable, availability-stamped
snapshot handed over at a provider edge. The first M3 implementation shaped that
snapshot as one flat hourly grid — each hour holding every field (cloud, wind,
seeing, transparency) — with two snapshot-level issue times
(`base_issued_at`, `secondary_issued_at`) carried alongside. In practice each
source owns distinct fields on a distinct cadence, so the flat grid pushed
per-source provenance into parallel side-channels and left "which source
contributed what" implicit in which fields happened to be present. This ADR
refines ADR-0005's snapshot shape; it does not change where the network lives.

## Decision

Model the snapshot as a `Conditions` value holding one optional group per source:
a `BaseGroup` (Open-Meteo cloud + wind) and a `SecondaryGroup` (7Timer! seeing +
transparency), each carrying its own `GroupMeta` (source role and issue time) and
its own hourly readings. A source's freshness rides with its own group; a source
that returned no rows is a `None` group; a source that returned rows but left a
field empty yields a present group whose hours carry `None` for that field.

## Consequences

- Easier: the source boundary is explicit and typed; per-source freshness is
  intrinsic to each group rather than a pair of side-channel timestamps; a future
  source can add or omit a group without reshaping a shared grid.
- Easier: graceful degradation reads naturally — "no base group" versus "base group
  present but this hour's cloud absent" are distinct, matching the two absence cases
  the core already handles.
- Easier: freshness stays byte-identical by construction. Today's `base_issued_at`
  survives on any base reading (cloud or wind); grouping both into one base group
  keeps the source's issue time present on any base reading, with no cloud-vs-wind
  presence asymmetry to special-case.
- Constraint accepted: to keep the verdict byte-identical (ADR-0005's determinism
  guarantee), 7Timer!'s 3-hourly seeing stays resampled to hourly in its provider,
  because the seeing score is a per-hour cloud-clarity-weighted mean entangled with
  the hourly grid. Native-cadence seeing is deferred to a science milestone that
  can re-open that number deliberately.

## Alternatives Considered

### Alternative 1: Keep the flat hourly grid with side-channel issue-times
- **Pros**: already shipped and tested; no refactor; one lookup type.
- **Cons**: per-source provenance lives in parallel `*_issued_at` fields; source
  identity is implicit in field presence; adding a source strains the shared grid.
- **Why not**: the seam it presents to the core misrepresents the domain, which is
  per-source; the clarity cost compounds as sources and fields grow.

### Alternative 2: Per-source groups at each source's native cadence
- **Pros**: the cleanest model — no resampling anywhere; each group is exactly what
  its source reported.
- **Cons**: the seeing score's per-hour cloud-clarity weighting is entangled with
  the hourly grid, so native cadence changes the seeing term and the verdict is no
  longer byte-identical; it re-opens scoring science inside a seam refactor.
- **Why not**: this change is a behaviour-preserving refactor; changing the seeing
  number belongs to a deliberate conditions-tuning milestone, not here.

### Alternative 3: Per-field groups (cloud, wind, seeing, transparency each their own)
- **Pros**: fully uniform — one concern, one group; a future source could supply one
  field without its pair.
- **Cons**: duplicates one issue time across the two base fields, and re-creates a
  cloud-vs-wind presence asymmetry — a source can return one base field without the
  other — which is exactly the edge that would break byte-identical freshness unless
  special-cased. Adds more structure than today's model carries.
- **Why not**: the source, not the field, is the unit that fetches, fails, caches,
  and stamps an issue time; grouping by source keeps that atomic and byte-identical,
  and the per-field independent-source case is speculative for the two sources we
  have.
