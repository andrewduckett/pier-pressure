---
id: adrs-adr0019
date: 2026-10-09
status: accepted
title: 'ADR0019: The replay after a reconnect repairs what an outage missed, not the MQTT client queue'
description: Architecture Decision Record for publishes during a broker outage. PierPressure holds messages while it knows it is disconnected and records them, and its replay after the reconnect sends the latest state. It never stops because a publish failed.
---

# ADR-0019: The replay after a reconnect repairs what an outage missed, not the MQTT client queue

## Context

PierPressure publishes its verdicts to Home Assistant through an MQTT broker. It
uses paho, the standard Python MQTT client. Every message PierPressure publishes
is retained: the broker keeps the last one on each topic. And every message
carries a whole state, such as a pier's verdict, never a change to one.

The broker can go away while PierPressure runs. paho reconnects in the
background. While it is disconnected, PierPressure still recomputes on its
interval and on a Refresh press. So it still publishes.

paho offers to keep these messages. It queues a message published while
disconnected, and sends the queue after the reconnect. The queue has no limit by
default. With a limit, paho drops what does not fit.

PierPressure already has a second way to recover. It remembers the last payload
of every retained topic. After each reconnect it publishes them all again, then
marks itself online. This is called the replay.

## Decision

PierPressure relies on the replay, not on paho's queue, to repair what an outage
missed. While PierPressure knows it is disconnected, it records each message for
the replay but does not hand it to paho. It records every message before it
sends it, so the replay always has the latest payload.

A publish never stops PierPressure. When paho refuses a message, PierPressure
logs a warning and keeps running. The next replay or interval repairs the topic.

## Consequences

- **Easier:** an outage of any length costs the same to recover from: one
  replay. paho's queue stays small, and its message IDs cannot run out.
- **Easier:** no message needs a retry loop of its own, including the health
  reset that must reach the broker before PierPressure goes online.
- **Harder:** the replay is now load-bearing. An outage would lose any message
  that PierPressure does not retain or does not record for the replay. So
  PierPressure must record every new topic it publishes.
- **Harder:** PierPressure can learn of a drop after paho does. A few messages
  can still reach paho's queue, and then reach the broker twice. Because each is
  a whole retained state, a duplicate is harmless.
- **Harder:** a publish failure is visible only in the log. PierPressure no
  longer exits to signal it.

## Alternatives Considered

### Alternative 1: Hand every message to paho and cap its queue
- **Pros**: bounded memory, and paho resends in order after the reconnect.
- **Cons**: after a long outage, the queue is full of old messages when the
  broker comes back. The replay and the online message then hit the cap, and
  paho drops them.
- **Why not**: the cap breaks the recovery it was meant to protect.

### Alternative 2: Hand every message to paho with no cap
- **Pros**: no code in PierPressure; paho does it all.
- **Cons**: the queue grows on every interval for as long as the outage lasts.
  After about 65,000 waiting messages, paho's message IDs clash and it drops
  messages anyway. Every queued message is also sent a second time by the replay.
- **Why not**: unbounded growth that the replay makes redundant.

### Alternative 3: Stop on a failed publish and let something restart PierPressure
- **Pros**: the simplest code, and the failure is impossible to miss.
- **Cons**: the Home Assistant add-on does not restart by default, so it stays
  stopped with no verdicts.
- **Why not**: PierPressure owns its own freshness, and this gives that up.
