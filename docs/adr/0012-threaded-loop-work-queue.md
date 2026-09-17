---
id: adrs-adr0012
date: 2026-09-08
status: accepted
title: 'ADR0012: A threaded MQTT loop with a main-thread work queue and an absolute refresh deadline'
description: Architecture Decision Record for running delivery as an MQTT network thread that enqueues refresh requests onto a single main-thread work queue governed by an absolute deadline, so periodic all-pier recompute and on-demand single-pier refresh share one mechanism without starving each other.
---

# ADR-0012: A threaded MQTT loop with a main-thread work queue and an absolute refresh deadline

## Context

PierPressure recomputes a verdict on three triggers: at startup, on a fixed
interval, and on demand when a user asks to "show me now." Delivery runs over
MQTT, a lightweight message protocol, and an on-demand request arrives as a
message on a per-pier command topic. So the service does two things at once: it
listens for those messages, and it runs the periodic recompute. That is a
concurrency problem. The MQTT client library (paho) runs its own background
network thread and calls a function when a message arrives. Doing real work in
that callback would block the network thread, and it would let two threads publish
at the same time. The periodic and on-demand triggers must also not starve each
other.

## Decision

Use the MQTT client's network thread only to listen. When a command arrives, its
callback does no work: it reads the pier's identity and puts it on a thread-safe
queue. A single main thread owns all recompute and all publishing, and it draws
its work from that queue. The two triggers feed that one thread. An on-demand
request is a pier waiting on the queue. The periodic all-pier recompute fires when
the queue stays empty up to a deadline.

That deadline is the crux: it is absolute — a fixed next-run time, not a fresh
interval counted from each cycle. An absolute deadline stops a burst of on-demand
requests from repeatedly resetting the timer and starving the periodic run. One
thread doing all the publishing means there are never concurrent writes. A queue
that carries the pier's identity means an on-demand refresh knows which pier to
recompute — something a bare signal could not say.

## Consequences

- **Easier:** the periodic and on-demand triggers are one mechanism, not two, so
  they cannot race or duplicate work. One publishing thread means no
  concurrent-write bugs. A refresh that arrives mid-recompute is just the next
  queue item, handled next cycle, never dropped.
- **Easier:** per-pier isolation falls out for free. The queue item names the pier,
  so an on-demand refresh touches only that pier.
- **Harder:** the absolute-deadline logic must be right, and it is not obvious.
  Anyone changing the wait must preserve it, or frequent on-demand refreshes will
  starve the periodic recompute. The model also assumes a recompute is short enough
  to run inline on one thread.

## Alternatives Considered

### Alternative 1: An asyncio client instead of threads
- **Pros**: one event loop, no thread-safety concerns, and a modern async style.
- **Cons**: it pulls an async runtime through the whole service for a workload that
  is really just a timer plus an occasional message.
- **Why not**: the async surface buys nothing here and adds complexity. A single
  worker thread with a queue meets every requirement.

### Alternative 2: Signal the worker with a bare flag instead of a queue
- **Pros**: the simplest possible nudge between threads.
- **Cons**: a flag carries no payload, so it cannot say which pier to refresh, and
  a per-pier on-demand refresh becomes impossible.
- **Why not**: the refresh has to name its pier, and only a queue carries that
  identity.

### Alternative 3: Do the work in the MQTT callback thread
- **Pros**: no queue and no second thread — publish straight from the callback.
- **Cons**: a recompute would block the network thread, and the periodic recompute
  and an incoming command could publish at the same time.
- **Why not**: it blocks the client's network loop and allows concurrent writes,
  the exact hazards the single-worker model removes.
