---
id: adrs-adr0005
date: 2026-09-09
status: accepted
title: 'ADR0005: Weather enters at a provider edge; the core takes a conditions snapshot'
description: Architecture Decision Record for confining all network access to a provider layer outside the pure core, which receives observing conditions as an immutable availability-stamped snapshot, so the verdict stays deterministic while weather is fetched live.
---

# ADR-0005: Weather enters at a provider edge; the core takes a conditions snapshot

## Context

PierPressure computes each night's go/no-go in a pure core. The core does no
I/O, and its output depends only on its inputs. So the same inputs always
produce the same document, and the core can be tested with no network. An
earlier decision (ADR0004) kept the astronomy offline for this reason: the star
and planet data ships bundled with the app. Live weather breaks that pattern. A
real go/no-go needs tonight's cloud, wind, seeing, and transparency, and a
forecast cannot be bundled. It must be fetched close to the time it applies, and
it changes constantly. So the core faces a conflict. It must use live external
data without doing any I/O itself, or it stops being pure and testable. No
single source may be load-bearing either, so a missing forecast must degrade the
verdict rather than crash it.

## Decision

Confine all network access, caching, and fallback to a provider layer outside
`pierpressure/core/`. Have `produce_verdict(pier, clock, conditions)` receive
conditions as an immutable, availability-stamped snapshot, not a fetching
interface. The core only reads the snapshot, so it stays a pure function of its
inputs. Network lives only at the provider edge.

## Consequences

- **Easier:** the core stays byte-identical for a pinned snapshot, so the
  determinism, boundary, and offline-guard tests keep passing. Determinism is now
  a hard wall, not a mocking discipline — a data value cannot fetch. Graceful
  fallback and "no load-bearing source" become pure logic over the snapshot's
  availability flags. The core degrades by reading `absent`, never by catching a
  network error.
- **Easier:** providers are swappable and testable on their own against recorded
  fixtures. A provider outage is buffered by cache and shows up as lower
  confidence, not a crash.
- **Harder:** the snapshot must carry enough provenance — per-field availability
  and per-provider issue time — for the core to judge completeness and freshness
  without touching the clock or network. The service must fetch before it
  computes. Cloud data is required to reach a GO, so losing the base provider
  degrades to a low-confidence MAYBE rather than a clear-sky GO. We accept that as
  the honest behaviour.

## Alternatives Considered

### Alternative 1: Inject a provider interface into the core
- **Pros**: the core pulls exactly the data it needs, when it needs it; one fewer
  intermediate type.
- **Cons**: an interface that can fetch invites lazy fetches, retries, and
  timeouts that blur the seam. Determinism tests must mock the interface instead
  of pinning a value. The offline boundary is no longer statically true.
- **Why not**: it trades a hard, inspectable wall for a discipline that erodes,
  and puts I/O back into the component that must stay pure.

### Alternative 2: The core owns fetching behind an offline cache
- **Pros**: one component owns freshness; no separate provider layer.
- **Cons**: it brings back the runtime-download problem ADR0004 removed, breaks
  the zero-network core boundary test, and couples astronomy and weather freshness
  despite their very different guarantees.
- **Why not**: it violates the offline-core boundary and undoes ADR0004's
  determinism work.

### Alternative 3: Treat weather as another offline, bundled data source
- **Pros**: would keep full offline determinism system-wide.
- **Cons**: impossible in principle. A forecast for tonight cannot ship in the
  image; it must be fetched near the time it applies.
- **Why not**: not achievable — weather is external by nature.
