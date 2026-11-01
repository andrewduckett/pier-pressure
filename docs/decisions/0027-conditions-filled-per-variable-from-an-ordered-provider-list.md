---
id: adrs-adr0027
date: 2026-11-01
status: accepted
title: 'ADR0027: Conditions are filled variable by variable from an ordered provider list'
description: Architecture Decision Record for shaping the core's conditions snapshot as one series per variable, each from a single provider, filled from a configured ordered list of providers with declared variables and bundles, in place of fixed base and secondary roles.
---

# ADR-0027: Conditions are filled variable by variable from an ordered provider list

## Context

The pure core receives observing conditions as an immutable snapshot built at a
provider edge, so the verdict stays deterministic and offline. The first shape
of that snapshot gave each of two providers a fixed role: a base source for
cloud, wind and weather, and a secondary source for seeing and transparency
(ADR-0006, since deprecated). The roles worked because the two providers
supplied disjoint variables. A provider that supplies cloud, seeing and
transparency at once fits neither role, and a user who prefers that provider
for cloud still needs the others for wind and weather. The snapshot, the
configuration and the health attributes all named the roles, so adding such a
provider meant reshaping all three. Supersedes ADR-0006.

## Decision

The snapshot holds one series per variable. A series carries one provider's
hourly values, that provider's key and the issue time of its data. Providers
sit in one configured ordered list, preferred first. Each provider declares
the variables it supplies and which of them form a bundle. Each variable, or
bundle, is filled by the first provider in order that returned it: at least
one hour carries a value. A series comes whole from one provider; hours from
two providers are never merged into one series. Every listed provider is
fetched on every recompute, and the fill is decided after all fetches. The
provider declarations are plain data in the core, so the core can validate the
list without importing any network code.

## Consequences

- **Easier:** a new provider is a declaration and a parser. The model, the
  fill, the configuration and the health entities do not change.
- **Easier:** a user chooses a provider by naming it first in the list, and
  the rest of the list still fills what that provider lacks.
- **Easier:** provenance travels with the data. The core reads a variable's
  issue time from its own series, so freshness follows the provider that
  actually filled cloud cover.
- **Easier:** the fill is a pure function of the order and the forecasts, so
  it is tested without a network, and the golden suite pins the document.
- **Harder:** a provider that returns the same variable as an earlier one is
  fetched and then ignored for that variable. The cost is one request per
  recompute per such provider.
- **Harder:** configuration can now be wrong in new ways. The core rejects an
  empty list, an unknown or repeated key, and a list with no keyless provider
  that supplies cloud cover, so a verdict can never silently lose its cloud
  data to a misconfiguration.
- **Harder:** bundles are a rule readers must know: cloud total and its layers
  always come from the same provider, so a provider that gives only a total
  leaves the layers empty even when a later provider has them.

## Alternatives Considered

### Alternative 1: Keep the roles and add a third group for a provider that straddles them
- **Pros**: no change to the existing groups, the goldens or the health
  attributes.
- **Cons**: the third group would overlap both roles, so the core would need
  precedence rules between groups for the same variable, which is the ordered
  fill in disguise, plus three shapes instead of one.
- **Why not**: it keeps a distinction the domain no longer has and still needs
  the fill.

### Alternative 2: Fill per hour, taking each hour's value from the first provider that has it
- **Pros**: the densest possible series; a gap in the preferred provider is
  patched by the next.
- **Cons**: one series would mix two forecast models, so a step between
  providers reads as a change in the weather. The issue time of a series
  would no longer be one time.
- **Why not**: a series that mixes models is not evidence of anything. Hours a
  provider did not cover stay empty, as the horizon rule already says.

### Alternative 3: A provider chosen per variable in the configuration
- **Pros**: fully explicit; no fill rule to learn.
- **Cons**: a configuration entry per variable, which must be kept in step with
  the variables each provider supplies, and a failed provider leaves its
  variables empty with no fallback.
- **Why not**: the ordered list gives the same control with one line and keeps
  the fallback that "no single source is load-bearing" requires.
