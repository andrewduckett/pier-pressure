---
id: adrs-adr0010
date: 2026-09-11
status: accepted
title: 'ADR0010: The ranking score renormalises over the factors whose inputs are known'
description: Architecture Decision Record for the equipment-aware ranking model — when a target lacks a size, a brightness, or a rig to frame against, the ranking drops that factor and renormalises the remaining weights rather than substituting a neutral value, so a score is always the honest combination of what is known.
---

# ADR-0010: The ranking score renormalises over the factors whose inputs are known

## Context

PierPressure ranks candidate targets with a weighted score. The score began with
four geometry factors — how high the object gets, how long it stays in the dark
window, its distance from the moon, and when it transits — whose fixed weights
summed to one. Two suitability factors are now added: how bright the object is,
and how well it fits the imaging rig's field of view. But their inputs are not
always present. A pier may have no rig configured, an object may have no recorded
size, and an object may have no recorded brightness. A fixed six-weight sum would
then have to invent a value for every missing factor. An object missing both new
inputs would ride on two fabricated middles. The factors must be added without
guessing, and without breaking the deterministic, banded 0-to-100 score.

## Decision

For each pier-and-target pair, the ranking forms the set of factors whose inputs
are known. The four geometry factors always apply. Brightness applies only when
the object has a known brightness. Field-of-view fit applies only when a rig is
configured and the object has a known size. Renormalise the base weights of that
live set to sum to one, then take the weighted sum, scaled to 0-to-100. A missing
input drops only its own factor; it is never replaced by a neutral or default
value. For brightness, use the catalog surface brightness where it is recorded,
and the overall magnitude otherwise.

## Consequences

- **Easier:** graceful degradation is one mechanism. A rig-less pier with five
  factors and a fully-described target with six use the same code path, so the "no
  equipment" case needs no special handling.
- **Honest by construction:** a score never smuggles a guessed value into the
  ranking. This extends the existing rule that an object with unknown brightness
  stays a candidate rather than being scored on a made-up value.
- **Constraint accepted:** two targets can be scored on different factor sets, so
  their weight vectors differ. We accept and document that. The alternative, a
  neutral fill, would make scores look more comparable while resting on invented
  data.
- **Constraint accepted:** every pier's ranking shifts when this lands — even a
  rig-less pier gains the brightness factor — so the change ships with re-baselined
  reference outputs. The score stays deterministic: the live factor set and the
  renormalised weights are a pure function of the inputs.
- **Constraint accepted:** the rig is now an input to ranking, so it joins the
  per-night ranking cache key.

## Alternatives Considered

### Alternative 1: Fixed six-factor weights with a neutral value for unknowns
- **Pros**: every target scored on the same weight vector, so scores are directly
  comparable; the simplest arithmetic.
- **Cons**: it injects a fabricated value for a missing size or brightness; an
  object missing both rides on two neutral middles and can outrank better-known
  targets on invented data.
- **Why not**: it guesses. The whole point is to reward genuine suitability, and a
  neutral fill quietly rewards missing data instead.

### Alternative 2: Gate out targets that lack the new inputs
- **Pros**: keeps a single fixed weight vector by requiring all inputs to be
  present.
- **Cons**: it discards real, well-placed objects for missing catalog metadata,
  contradicts the "keep an unknown-brightness object as a candidate" rule, and
  would empty the list on sparse nights.
- **Why not**: whether a target can be recommended at all must not hinge on the
  availability of optional metadata.
