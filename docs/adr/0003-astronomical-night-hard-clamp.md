---
id: adrs-adr0003
date: 2026-09-07
status: accepted
title: 'ADR0003: Target observability is hard-clamped to astronomical night'
description: Architecture Decision Record for always clamping target observability windows to astronomical night, regardless of any user-requested viewing window.
---

# ADR-0003: Target observability is hard-clamped to astronomical night, regardless of the requested view window

## Context

PierPressure recommends deep-sky targets to image from a fixed pier, and it lets a
user set a viewing-session window. Planetarium tools often show a target whenever
it is above the horizon. But imaging these faint objects is only meaningful during
astronomical darkness — when the sun is far enough below the horizon that the sky
is truly dark. Showing targets that are merely "up" during twilight, or honoring a
user window that runs into twilight, would recommend shots that cannot realistically
be taken. Misleading recommendations are the exact failure this product exists to
avoid.

## Decision

Always clamp target observability to astronomical night: the span from
astronomical dusk to astronomical dawn, when the sun is more than 18 degrees below
the horizon. This clamp applies regardless of any user-requested window. The
dark-night span is a first-class part of the verdict, so every downstream step
measures a target against the same honest boundary.

## Consequences

- **Easier:** targets and their ranking are honest about when an object is
  actually observable, and one boundary rule applies everywhere downstream —
  ranking, equipment fit, and the final recommendation.
- **Harder:** a user cannot force a target into view during twilight, even on
  request. And target logic cannot be trusted until reliable astronomical-twilight
  computation exists to draw the boundary.

## Alternatives Considered

### Alternative 1: Honor the user-requested window as-is
- **Pros**: maximally flexible, and it matches how some planetarium tools behave.
- **Cons**: it invites recommending targets that cannot realistically be imaged,
  which undermines trust.
- **Why not**: we choose trustworthiness over flexibility. Coarse but honest beats
  flexible but misleading.

### Alternative 2: Make the darkness level configurable (civil, nautical, or astronomical)
- **Pros**: it would accommodate brighter-sky imaging, such as bright targets or
  narrowband.
- **Cons**: it adds a knob that can quietly widen the window and bring misleading
  results back if misused.
- **Why not**: astronomical night is the safe default and the decision here. A
  later change could add an opt-in relaxation, but the hard clamp stays the
  baseline rather than an arbitrary per-request window.
