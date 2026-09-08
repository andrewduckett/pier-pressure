---
id: adrs-adr0003
date: 2026-09-07
status: accepted
title: 'ADR0003: Target observability is hard-clamped to astronomical night'
description: Architecture Decision Record for always clamping target observability windows to astronomical night, regardless of any user-requested viewing window.
---

# ADR-0003: Target observability is hard-clamped to astronomical night, regardless of the requested view window

## Context

Users may set a viewing-session window, and planetarium tools often show a target whenever it is above the horizon. But astrophotography from these piers is only meaningful during astronomical darkness; presenting targets that are "up" during twilight — or honoring a user-requested window that extends into twilight — would produce misleading recommendations, which is exactly the failure mode PierPressure exists to avoid.

## Decision

Target observability windows are always clamped to astronomical night (the sun below -18 degrees, i.e. astronomical dusk to astronomical dawn), regardless of any user-requested view window. The night window is a first-class field (`dark_window`) in the verdict contract, reserved from the walking skeleton onward and filled with real twilight math in the sky-and-light milestone.

## Consequences

- Easier: targets and their ranking are honest about when they are actually observable; a single boundary rule applies everywhere downstream (ranking, FOV-fit, recommendations).
- Harder: users cannot force-view targets during twilight even if they ask to; the system depends on reliable astronomical-twilight computation before target logic can be trusted.

## Alternatives Considered

### Alternative 1: Honor the user-requested view window as-is
- **Pros**: maximally flexible; matches how some planetarium tools behave.
- **Cons**: invites recommending targets that are not realistically imageable, undermining trust.
- **Why not**: trustworthiness is chosen over flexibility; "coarse-but-honest" beats "flexible-but-misleading".

### Alternative 2: Make the twilight level configurable (civil / nautical / astronomical)
- **Pros**: accommodates brighter-sky imaging (e.g. bright targets, narrowband).
- **Cons**: adds a knob that can silently widen the window and reintroduce misleading results if misused.
- **Why not**: astronomical night is the safe default and the decision here; a future change could add an opt-in relaxation, but the hard clamp remains the baseline rule rather than an arbitrary per-request window.
