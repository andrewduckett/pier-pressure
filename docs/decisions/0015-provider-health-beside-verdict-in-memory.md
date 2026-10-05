---
id: adrs-adr0015
date: 2026-10-05
status: accepted
title: 'ADR0015: Provider health travels beside the verdict as diagnostic entities, held only in memory'
description: Architecture Decision Record for weather provider health. Each provider's health is a separate diagnostic Home Assistant entity. It stays outside the verdict document, the verdict never reads it, and it lives only in process memory.
---

# ADR-0015: Provider health travels beside the verdict as diagnostic entities, held only in memory

## Context

PierPressure fetches weather from external providers and turns it into one verdict
document per pier. A pure core builds that document from a snapshot of conditions.
The same inputs always give a byte-identical document. When a provider fails, its
data is simply missing from the snapshot, and the verdict degrades. The verdict
shows that data is missing, but not which provider failed, why, or since when.
Operators need that operational information to notice a broken provider. Where it
lives is a lasting choice, because Home Assistant users bind automations to whatever
entities ship.

## Decision

Report each provider's health as its own diagnostic Home Assistant entity, one per
pier per provider. The fetch layer hands each fetch's outcome to the service beside
the conditions, not inside them. The core never receives health, and the verdict
document gains no health field. The service keeps health in process memory and does
not save it to disk.

## Consequences

- **Easier:** the verdict document stays byte-identical for the same inputs. Health
  cannot change a verdict, score, or confidence, because the code that computes
  them never receives it.
- **Easier:** operators can notify on a failing provider with an ordinary Home
  Assistant automation, the same way they notify on a verdict.
- **Easier:** health has no storage to manage, migrate, or corrupt.
- **Constraint accepted:** health resets on restart. A provider failing since
  before a restart shows "unknown" rather than its true time since the last
  success. Operators treat a long "unknown" as a failure.
- **Constraint accepted:** each provider's health entity joins the delivery surface.
  Consumers that read only the verdict document never see health.

## Alternatives Considered

### Alternative 1: A health field in the verdict document

- **Pros**: one document holds everything about a pier's night.
- **Cons**: the verdict document is a frozen contract about the sky. Health describes
  the system, not the sky. The document would change on every failed fetch, even
  when the verdict does not. Consumers that watch the document for changes would
  then see churn.
- **Why not**: it mixes operational state into the decision contract.

### Alternative 2: Let health lower the verdict's confidence directly

- **Pros**: a failing provider would visibly weaken the verdict.
- **Cons**: missing data already lowers confidence through the snapshot. Counting
  the failure a second time would double-penalise it. It would also make the
  verdict depend on fetch history rather than on the data in hand.
- **Why not**: the snapshot already carries the effect that matters to the verdict.

### Alternative 3: Persist health across restarts

- **Pros**: the time since the last success survives a restart.
- **Cons**: the container gains state to store, version, and recover. A stale file
  could show an old success as current after a long outage.
- **Why not**: the gain is small, because a long "unknown" already signals the
  failure, and stored state would be the first state this container keeps.
