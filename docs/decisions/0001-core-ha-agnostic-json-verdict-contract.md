---
id: adrs-adr0001
date: 2026-09-07
status: accepted
title: 'ADR0001: Home-Assistant-agnostic core with a JSON verdict contract'
description: Architecture Decision Record for making the decision core a standalone, self-scheduling service that emits a JSON verdict document, with Home Assistant as a dumb, replaceable delivery adapter.
---

# ADR-0001: Home-Assistant-agnostic core with a JSON verdict contract delivered via a dumb adapter

## Context

Home Assistant is the open-source home-automation hub that PierPressure delivers
its night verdict into. The usual way to extend it is an add-on that runs inside
Home Assistant's own process, often installed through HACS, its community add-on
manager. That path has a cost. The decision core must be deterministic and
testable on its own, no single dependency may be load-bearing, and the verdict
must stay correct when Home Assistant restarts. An in-process add-on works
against all three. It would pull heavy astronomy libraries into Home Assistant's
process and version pins, and tie the core to Home Assistant's async lifecycle.
Testing the core away from Home Assistant would then be a constant fight.

## Decision

Build the decision core as a standalone, pure Python package with no Home
Assistant imports. It emits one JSON verdict document, and that document is its
contract. It runs as a persistent service that schedules itself: it recomputes on
startup, on a set interval, and on demand, so it owns its own freshness. Home
Assistant becomes a dumb, replaceable delivery adapter. The main adapter publishes
over MQTT discovery — a convention where Home Assistant auto-creates entities from
messages on a broker — and a REST endpoint is an acceptable fallback. Home
Assistant is never load-bearing for freshness or correctness.

## Consequences

- **Easier:** the core is unit-tested with pinned inputs. Delivery can be swapped
  or extended without touching it. Retained MQTT state survives Home Assistant
  restarts. The service runs on any box on the local network.
- **Harder:** there is no one-click native install. The setup needs a running
  container and an MQTT broker. Entity lifecycle now depends on MQTT conventions —
  retained messages plus a last-will availability signal — rather than Home
  Assistant's built-in setup flow.

## Alternatives Considered

### Alternative 1: HACS custom component (in-process integration)
- **Pros**: native install and setup; entities without a broker.
- **Cons**: heavy astronomy libraries live in Home Assistant's environment; the
  core is coupled to Home Assistant's async loop and version pins; testing it away
  from Home Assistant is hard.
- **Why not**: it breaks the two rules that matter most — the core must be
  deterministic and testable off Home Assistant, and Home Assistant must never be
  load-bearing.

### Alternative 2: Standalone service that Home Assistant reads over REST only
- **Pros**: the simplest possible integration; no MQTT.
- **Cons**: dashboards must be wired by hand, and Home Assistant polling makes
  freshness depend on Home Assistant rather than the service.
- **Why not**: MQTT discovery auto-creates entities and lets the service push on
  its own schedule; REST stays a fallback, not the main path.
