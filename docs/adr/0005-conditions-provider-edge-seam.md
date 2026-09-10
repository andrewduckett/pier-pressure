---
id: adrs-adr0005
date: 2026-09-09
status: accepted
title: 'ADR0005: Weather enters at a provider edge; the core takes a conditions snapshot'
description: Architecture Decision Record for confining all network access to a provider layer outside the pure core, which receives observing conditions as an immutable availability-stamped snapshot, so the verdict stays deterministic while weather is fetched live.
---

# ADR-0005: Weather enters at a provider edge; the core takes a conditions snapshot

## Context

The conditions milestone (M3) turns the stubbed decision fields into a real
go/no-go, which requires live observing conditions (cloud, wind, seeing,
transparency) from external forecasts. This collides head-on with two
established rules: the core is a deterministic, offline-testable pure function
(ADR0004), and no single external source may be load-bearing. Astronomy could
honour both because an ephemeris ships as data; a weather forecast cannot — it
is irreducibly external and changes over time. The design must admit the network
without letting it reach into the core, or determinism and the offline core
boundary (guarded by tests) both break.

## Decision

Confine all network access, caching, and fallback to a provider layer outside
`pierpressure/core/`, and have `produce_verdict(pier, clock, conditions)` receive
observing conditions as an immutable, availability-stamped data snapshot rather
than a fetching interface. The core only reads the snapshot, so it stays a pure
function of its inputs and network lives solely at the provider edge.

## Consequences

- Easier: the core stays byte-identical for a pinned snapshot, so the existing
  determinism, boundary, and offline-guard tests keep passing unchanged;
  determinism is a hard wall (a data value cannot fetch) rather than a mocking
  discipline. Graceful fallback and "no load-bearing source" become pure logic
  over the snapshot's availability flags — the core degrades by reading
  `absent`, never by catching a network error.
- Easier: providers are swappable and independently testable against recorded
  fixtures; a provider outage is buffered by cache and expressed as lowered
  confidence, not a crash.
- Harder: the snapshot must carry enough provenance (per-field availability,
  per-provider issue time) for the core to compute completeness and freshness
  without touching the clock or network; the service must fetch before it
  computes. Cloud data is functionally required to reach a GO verdict, so total
  loss of the base provider degrades to a low-confidence MAYBE rather than a
  clear-sky GO — accepted as the honest behaviour.

## Alternatives Considered

### Alternative 1: Inject a provider interface into the core
- **Pros**: the core can pull exactly the data it needs, when it needs it; one
  fewer intermediate data type.
- **Cons**: an interface that can fetch invites lazy fetches, retries, and
  timeouts to blur the seam; determinism tests must mock the interface rather
  than pin a value; the offline boundary is no longer statically true.
- **Why not**: it trades a hard, inspectable wall for a discipline that erodes,
  and reintroduces I/O into the component that must stay pure.

### Alternative 2: The core owns fetching behind an offline cache
- **Pros**: a single component owns freshness; no separate provider layer.
- **Cons**: reintroduces the runtime-download problem ADR0004 removed, breaks the
  zero-network core boundary test, and couples astronomy and weather freshness
  into one place with very different guarantees.
- **Why not**: directly violates the offline-core boundary and undoes ADR0004's
  determinism work.

### Alternative 3: Treat weather as another offline, bundled data source
- **Pros**: would preserve full offline determinism system-wide.
- **Cons**: impossible in principle — a forecast for tonight cannot be shipped in
  the image; it must be fetched near the time it applies.
- **Why not**: not achievable; weather is irreducibly external.
