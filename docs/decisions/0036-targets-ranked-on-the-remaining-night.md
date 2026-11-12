---
id: adrs-adr0036
date: 2026-11-11
status: accepted
title: 'ADR-0036: Once the night has started, targets are ranked on the rest of it, beside their whole-night window'
description: Architecture Decision Record. After astronomical dusk, target ranking gates and scores each target on its longest stretch above the horizon mask from now to dawn, and each target carries that stretch in a new remaining_window field, while window keeps the whole night.
---

# ADR-0036: Once the night has started, targets are ranked on the rest of it, beside their whole-night window

## Context

PierPressure recomputes each pier's verdict through the night. Since ADR-0023,
the verdict's gates and score judge the scored window: from the scoring instant
(the evaluation instant, to the whole second) to the end of the dark window.
Before dusk, that is the whole night. The target list did not follow. It still
ranked every target over the whole night, so at 22:00 it listed objects that set
at 21:00.

Each target carries an observable `window`: its longest stretch above the pier's
horizon mask during the dark window. The verdict document is a frozen contract.
An existing field never changes meaning, and the document grows only by adding
fields. Any field added here is permanent.

A target can clear an irregular skyline more than once a night. Its `window` is
then the longest stretch, which may already be over while a shorter one is
still ahead.

## Decision

Target ranking judges each target's **remaining window**: its longest stretch
above the horizon mask within the scored window. The minimum-duration gate and
the four geometry factors (altitude, window length, moon separation, transit)
all read that stretch. Window length is measured as a share of the scored
window.

Each target carries the stretch in a new `remaining_window` field, with a
`start` and an `end`. `window`, `max_altitude`, `transit_time` and
`moon_separation` keep their whole-night meaning. Before dusk,
`remaining_window` equals `window`, and the ranking is the same as a whole-night
ranking.

## Consequences

- **Easier:** a mid-session refresh answers "what should I point at now?". A
  target that has set drops out, and a target past its best ranks on what is
  left.
- **Easier:** the verdict and the target list judge the same span, so the "Top
  pick" sentence and the verdict's score no longer describe different nights.
- **Easier:** a consumer can see which stretch was ranked, and can still show
  the whole night from `window`.
- **Harder:** a target's score and the top pick now change through the night,
  so a Home Assistant automation that triggers on the top target can fire more
  than once.
- **Constraint accepted:** in the last hour of the night, no target can meet the
  60-minute minimum, so the list is empty. This matches the verdict, which says
  under an hour is not worth setting up for.
- **Constraint accepted:** in the rare two-stretch case, a listed target's
  `window` can end before `generated_at`. `remaining_window` is the field that
  is always ahead of now.
- **Constraint accepted:** every recompute ranks at a new instant, so a cache of
  final lists would never hit. Only the whole-night scan of the catalog can be
  cached per night.

## Alternatives Considered

### Alternative 1: Keep ranking the whole night

- **Pros**: no change, and the list stays stable through the night.
- **Cons**: mid-session, the list recommends objects that have set, and scores
  the rest on hours that have passed.
- **Why not**: a recommendation for a target you can no longer image is wrong,
  and the verdict already judges the rest of the night.

### Alternative 2: Narrow `window` itself to the remaining stretch

- **Pros**: one window per target, and no new field.
- **Cons**: it changes what an existing field means, mid-night only, which every
  consumer of `window` (the dashboard card's target bars included) would have to
  learn.
- **Why not**: the contract forbids changing an existing field's meaning. The
  document may only grow.

### Alternative 3: Rank on the remaining stretch, but do not publish it

- **Pros**: the document does not grow.
- **Cons**: a consumer cannot tell which stretch a target was ranked on. In the
  two-stretch case, the only window it can see has already ended.
- **Why not**: the numbers-only targets are meant to carry the ranking's own
  evidence, and hiding the stretch it judged defeats that.

### Alternative 4: Take what is left of `window`, not the longest stretch ahead

- **Pros**: `remaining_window` always lies inside `window`, and `window` is
  never wholly in the past for a listed target.
- **Cons**: a target whose remaining stretch is a different one drops out, even
  though it can still be imaged tonight.
- **Why not**: the list answers what to point at for the rest of the night. A
  target that will clear the skyline again belongs on it.
