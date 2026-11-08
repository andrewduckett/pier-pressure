---
id: adrs-adr0026
date: 2026-10-31
status: superseded by ADR-0034 and ADR-0035
title: 'ADR0026: The night dashboard ships as YAML in the docs, on core cards plus plotly-graph-card'
description: Architecture Decision Record for delivering the night strip dashboard as documented YAML that readers paste in, built on Home Assistant core cards and the community plotly-graph-card, with no JavaScript card of PierPressure's own.
---

# ADR-0026: The night dashboard ships as YAML in the docs, on core cards plus plotly-graph-card

> **Superseded in part on 2026-11-06 by ADR-0034, and fully on 2026-11-08 by
> ADR-0035.** ADR-0034 made PierPressure ship its own dashboard card, so the
> sentence "PierPressure adds no JavaScript card of its own" no longer holds.
> ADR-0035 removed the YAML dashboard from the docs, so nothing of this decision
> stands. The PierPressure card is the only dashboard PierPressure documents.

## Context

PierPressure publishes each timeline variable as its own Home Assistant sensor,
with the hourly values in a `forecast` attribute array (ADR-0025). The night
strip is a heatmap: hours across, one row per variable, each row shaded on its
own scale, with dusk, dawn, the moon and each target's window drawn on the same
time axis. Home Assistant's core cards cannot draw a heatmap. PierPressure is a
container and an add-on that publishes over MQTT. It ships no frontend code, and
Home Assistant is never load-bearing for the verdict. Readers paste a dashboard
into their own Home Assistant, so whichever card it uses becomes part of every
reader's setup, and changing it later means every reader rebuilds their
dashboard.

## Decision

The night dashboard ships as one YAML block in the docs. It uses Home
Assistant's core cards, plus plotly-graph-card from HACS for the strip.
PierPressure adds no JavaScript card of its own. Any logic the strip needs
lives in short expressions inside that YAML, which plotly-graph-card
evaluates.

## Consequences

- **Easier:** PierPressure stays a backend. No frontend build, no card release,
  and no compatibility promise to the Home Assistant frontend.
- **Easier:** readers can see and change everything the dashboard does, in YAML
  they already know how to edit.
- **Easier:** plotly-graph-card passes plotly traces through unchanged, so the
  strip can use a heatmap per row, bars for windows and shapes for lines,
  without waiting for a card to add a feature.
- **Harder:** readers must install a community card through HACS before the
  dashboard works.
- **Harder:** the expressions in the YAML are JavaScript that PierPressure's
  test suite does not run. A test checks that the YAML reads only entities and
  attributes PierPressure publishes, and how it renders is checked in a real
  Home Assistant by hand.
- **Harder:** a breaking plotly-graph-card release can break readers'
  dashboards. The docs name the version the YAML was checked against.

## Alternatives Considered

### Alternative 1: apexcharts-card
- **Pros**: popular, already used in the docs for a single cloud cover chart,
  and good at column and line charts.
- **Cons**: it has no heatmap chart type, and its annotations are fixed values
  in the YAML, so dusk, dawn and target windows cannot follow the published
  entities.
- **Why not**: it cannot draw the strip. A heatmap faked from stacked columns
  loses the gap for a missing hour and the per-row shading.

### Alternative 2: A bespoke PierPressure card
- **Pros**: the best possible strip, one install, and no YAML to paste.
- **Cons**: PierPressure would ship and maintain frontend code, a release
  process for it, and compatibility with each Home Assistant frontend release.
- **Why not**: it is the most expensive option. The YAML dashboard proves the
  strip first. A bespoke card can follow later, built on the same published
  entities, without changing anything decided here.

### Alternative 3: Core cards only
- **Pros**: nothing to install.
- **Cons**: no core card draws a heatmap or places lines from entity attributes
  on a time axis.
- **Why not**: it cannot show the strip. A text fallback is a different view,
  not this one.
