---
id: adrs-adr0010
date: 2026-09-11
status: accepted
title: 'ADR0010: The ranking score renormalises over the factors whose inputs are known'
description: Architecture Decision Record for the M6 equipment ranking model — when a target lacks a size, a brightness, or a rig to frame against, the ranking drops that factor and renormalises the remaining factor weights rather than substituting a neutral value, so a score is always the honest combination of what is known.
---

# ADR-0010: The ranking score renormalises over the factors whose inputs are known

## Context

M5 scored each target from four factors (altitude, window, moon, transit) whose
fixed weights summed to 1.0. M6 adds two suitability factors — brightness and
field-of-view fit — but their inputs are not always available: a pier may have no
rig, an object may have no recorded size, and an object may have no recorded
magnitude or surface brightness. A fixed six-weight sum would then have to invent
a value for every missing factor, and an object missing both new inputs would ride
on two fabricated middles. This milestone must add the factors without guessing and
without breaking the deterministic, banded 0–100 score.

## Decision

For each `(pier, target)` the ranking forms the set of factors whose inputs are
known — the four geometry factors always, brightness only when the object has a
known brightness, field-of-view fit only when a rig is configured and the object
has a known size — renormalises those factors' base weights to sum to 1, and takes
the weighted sum scaled to 0–100. A missing input drops only its own factor; it is
never replaced by a neutral or default value. The brightness factor's input is the
catalog surface brightness where recorded and the integrated magnitude otherwise.

## Consequences

- Graceful degradation is one mechanism: a rig-less pier (five factors) and a
  fully-described target (six factors) use the same code path, and the "no
  equipment" case needs no special handling.
- A score is always honest about what was known — it never smuggles a guessed
  value into the ranking, extending M5's rule that an unknown magnitude is kept as
  a candidate rather than scored.
- Two targets can be scored on different factor sets, so their weight vectors
  differ. This is accepted and documented; the alternative (a neutral fill) would
  make scores look more comparable while resting on invented data.
- Every pier's rankings shift when this lands — even a rig-less pier gains the
  brightness factor — so the change ships with re-baselined golden outputs. The
  score stays deterministic: the live factor set and the renormalised weights are a
  pure function of the inputs.
- The rig becomes an input to ranking, so it joins the per-night ranking cache key.

## Alternatives Considered

### Alternative 1: Fixed six-factor weights with a neutral value for unknowns
- **Pros**: every target scored on the same weight vector, so scores are directly comparable; simplest arithmetic.
- **Cons**: injects a fabricated value for missing size or brightness; an object missing both rides on two neutral middles and can outrank better-known targets on invented data.
- **Why not**: it guesses. The whole point of the milestone is to reward genuine suitability, and a neutral fill quietly rewards missing data instead.

### Alternative 2: Gate out targets that lack the new inputs
- **Pros**: keeps a single fixed weight vector by requiring all inputs to be present.
- **Cons**: discards real, well-placed objects for missing catalog metadata; contradicts M5's "unknown magnitude is kept" rule and would empty the list on sparse nights.
- **Why not**: availability of optional metadata must not decide whether a target can be recommended at all.
