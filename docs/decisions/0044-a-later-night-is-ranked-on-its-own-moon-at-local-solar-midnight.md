---
id: adrs-adr0044
date: 2026-11-22
status: accepted
title: 'ADR-0044: A later night is ranked over its whole dark window, on its own moon taken at local solar midnight'
description: Architecture decision record for ranking each later night's targets with tonight's ranking over that night's whole dark window, and for computing a later night's moon illumination and phase at the middle of its local solar day.
---

# ADR-0044: A later night is ranked over its whole dark window, on its own moon taken at local solar midnight

Builds on ADR-0043.

## Context

The verdict document lists up to three later nights after the selected night,
one per local solar day. A local solar day runs from one solar noon to the
next. Each later night's entry holds its own fields, in the same shapes as the
selected night's top-level fields. This decision gives each entry a `moon` and
a `targets` list. The document is a frozen contract, so what these fields mean
is permanent once published.

The selected night's moon illumination and phase are taken at the evaluation
instant, and its targets are ranked on the rest of the night from that instant
once the night has started. A later night has no evaluation instant inside it:
the instant is always before its dusk. The moon's illumination changes by up
to about 11 points a day, and the ranking's moon factor reads it, so the
instant chosen changes which targets a later night lists.

## Decision

Each later night's targets are ranked by the same ranking as the selected
night's, with the later night's dark window and its own moon. The ranking runs
over the later night's whole dark window, so each target's `remaining_window`
equals its `window`.

A later night's moon illumination and phase are computed at the middle of its
local solar day, floored to the whole second. This is its local solar
midnight. Its rise, set and up-during-dark are found within its own dark
window, by the selected night's rules, and are null when it has no dark window.

## Consequences

- Easier: every night is ranked by one code path, so a fix to the ranking
  reaches every night.
- Easier: the moon instant exists for every later night, with or without
  astronomical darkness, so the rule has no special case for a night with no
  darkness.
- Easier: a later night's list does not change between recomputes during the
  day, because neither its window nor its moon instant depends on the
  evaluation instant.
- Harder: a later night's illumination is not tonight's rule. A reader who
  compares the two must know they are taken at different kinds of instant.
- Harder: when that later night becomes the selected night, its moon is taken
  at the evaluation instant instead, so its illumination and its list can
  shift a little.
- Harder: each later night costs a catalog scan, about 5 s, the first time it
  is ranked.

## Alternatives Considered

### Alternative 1: The later night's dusk

- **Pros**: it is the start of the hours being ranked.
- **Cons**: a later night with no astronomical darkness has no dusk, so it
  needs a second rule.
- **Why not**: a rule that changes with the night's darkness is harder to
  explain and to test, and dusk sits at one end of the ranked hours rather
  than near their middle.

### Alternative 2: The evaluation instant plus one, two or three days

- **Pros**: it follows tonight's rule.
- **Cons**: it falls in daylight whenever the evaluation runs in the day, and
  it moves with every recompute.
- **Why not**: a later night's list would change between recomputes for no
  change in its sky, and the instant often lies far from the hours it judges.

### Alternative 3: Reuse tonight's moon and targets on every later night

- **Pros**: no extra computation.
- **Cons**: the moon can go from a crescent to nearly full in three nights.
- **Why not**: ranked one night at a time, London's nights of 2026-11-21 to
  24, with the moon at 87% to 100%, gave a fourth night whose top ten shared
  no target with the first night's. Tonight's list would point the user at the
  wrong objects.
