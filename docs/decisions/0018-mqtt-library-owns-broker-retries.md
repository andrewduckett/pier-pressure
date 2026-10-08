---
id: adrs-adr0018
date: 2026-10-07
status: accepted
title: 'ADR0018: The MQTT library retries every connection to the broker'
description: Architecture Decision Record for broker connection retries. The paho MQTT client retries the first connection and every reconnect. PierPressure only listens to its callbacks and has no retry loop of its own.
---

# ADR-0018: The MQTT library retries every connection to the broker

## Context

PierPressure publishes its verdicts to Home Assistant through an MQTT broker. It
uses paho, the standard Python MQTT client. paho runs a background network thread
that sends and receives messages.

PierPressure must cope with a broker that is not there yet. After Home Assistant
OS restarts, PierPressure can start before the broker accepts connections. It must
also cope with a broker that goes away and comes back while PierPressure runs.

paho can retry in both cases. When a program starts the connection in the
background, paho's thread keeps trying until the broker accepts. It pauses longer
after each failure, up to a limit. The same thread reconnects after an outage.

The broker's answer to a connection attempt arrives on paho's thread. That answer
is the only place that says why the broker refused, for example a wrong password.
paho's blocking connect call returns before that answer arrives. So any design
that stops on a wrong password must listen to paho's connection callbacks.

## Decision

PierPressure lets paho retry every connection to the broker: the first one at
startup, and every reconnect. PierPressure has no retry loop of its own around
the connection. It sets the pauses paho uses, and it listens to paho's connection
callbacks to learn each outcome. Those callbacks only record the outcome for the
main thread, which does all publishing.

This decision covers connecting to the broker only. Inside a Home Assistant
add-on, PierPressure first asks the Supervisor which broker to use. That request
has its own short, bounded wait, because it talks to a different service.

## Consequences

- **Easier:** one mechanism handles a broker that starts late and a broker that
  comes back. Work on reconnect behaviour extends the same callbacks.
- **Easier:** PierPressure sees the broker's reason for each refusal. So it can
  stop on a rejected login, which retrying cannot fix, and retry everything else.
- **Harder:** the behaviour depends on paho's background thread, which its
  documentation describes only briefly. In one rare case, paho's thread can end
  without calling any callback. So PierPressure must also watch that the thread
  is still running, and start it again if it ends. A paho upgrade must be checked against this behaviour.
- **Harder:** tests need a fake client that calls the callbacks, rather than one
  that simply raises an error.

## Alternatives Considered

### Alternative 1: PierPressure's own retry loop around the blocking connect
- **Pros**: easy to read, and easy to test with a fake that fails a set number of
  times. PierPressure already waits this way for the Home Assistant Supervisor.
- **Cons**: PierPressure would have two retry mechanisms, its own for startup and
  paho's for reconnects. To stop on a wrong password, the loop would still need
  paho's connection callbacks.
- **Why not**: two mechanisms can drift apart, and the loop saves no code, because
  it needs the same callbacks anyway.

### Alternative 2: Exit, and let a process supervisor restart PierPressure
- **Pros**: no retry code in PierPressure at all. Docker's restart policy already
  does this.
- **Cons**: the Home Assistant add-on has no restart by default, so it stays
  stopped. It also breaks the rule that PierPressure owns its own freshness.
- **Why not**: it fails in the install most users run.
