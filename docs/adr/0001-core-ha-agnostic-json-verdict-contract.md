---
id: adrs-adr0001
date: 2026-09-07
status: accepted
title: 'ADR0001: Home-Assistant-agnostic core with a JSON verdict contract'
description: Architecture Decision Record for making the decision core a standalone, self-scheduling service that emits a JSON verdict document, with Home Assistant as a dumb, replaceable delivery adapter.
---

# ADR-0001: Home-Assistant-agnostic core with a JSON verdict contract delivered via a dumb adapter

## Context

PierPressure must deliver a night verdict into Home Assistant, and HA integrations are conventionally shipped as in-process custom components (HACS). But the project requires the decision core to be deterministic and testable off Home Assistant, requires that no single external dependency be load-bearing, and requires the verdict to stay correct if Home Assistant restarts. A custom component would drag heavy astronomy dependencies into HA's process and version pins, and entangle the core with HA's async lifecycle, making off-HA testing a constant fight.

## Decision

The decision core is a standalone, pure Python package with zero Home Assistant imports that emits a single JSON verdict document as its contract. It runs as a persistent, self-scheduling service (recompute on startup, on a configurable interval, and on demand) that owns its own freshness. Home Assistant is a dumb, replaceable delivery adapter; the primary adapter publishes via MQTT discovery (REST is an acceptable fallback), and Home Assistant is never load-bearing for freshness or correctness.

## Consequences

- Easier: unit-testing the core with pinned inputs; swapping or extending delivery without touching the core; surviving HA restarts via retained state; hosting the service on any box on the LAN.
- Harder: no one-click "native" HACS install UX; requires a running container and an MQTT broker; entity lifecycle depends on MQTT discovery semantics (retain + Last-Will availability) rather than HA's config-flow.

## Alternatives Considered

### Alternative 1: HACS custom component (in-process integration)
- **Pros**: native UX, config-flow setup, entities without a broker.
- **Cons**: heavy astronomy deps live in HA's venv; core coupled to HA's async loop and version pins; off-HA determinism/testing is hard.
- **Why not**: directly violates the "deterministic and testable off HA" and "HA never load-bearing" requirements.

### Alternative 2: Standalone service that HA reads via REST only
- **Pros**: simplest possible integration; no MQTT.
- **Cons**: manual dashboard YAML; HA polling makes freshness HA-driven rather than self-scheduled.
- **Why not**: MQTT discovery gives auto-created entities and self-scheduled push; REST is retained as a fallback adapter, not the primary path.
