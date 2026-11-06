---
id: adrs-adr0031
date: 2026-11-05
status: accepted
title: 'ADR-0031: Computed variables come from a source in the provider order'
description: Architecture decision record for deriving variables such as transparency from other providers' filled series in a computed source that sits in the provider order, runs after every fetch and before the verdict, and fills by the same rule as any provider.
---

# ADR-0031: Computed variables come from a source in the provider order

Builds on ADR-0027.

## Context

The conditions snapshot fills each variable from the first provider in a
configured order that returned it (ADR-0027). Free forecasts now carry raw
inputs, such as column water vapour and aerosol optical depth. From these, the
core can work out indices that an external service such as 7Timer! also
publishes: transparency, and later seeing. A pier owner needs to choose which
one to trust, the computed index or the external one, in the same way they
choose between weather models. The core must stay pure, and raw inputs must
never change the verdict document except through a shown variable
(ADR-0030).

## Decision

A computed source, with the stable key `computed`, sits in the provider order
like a provider. It declares the variables it derives, and has a health
record. It fetches nothing. After every provider has been fetched, the
conditions layer fills the snapshot once without it. A pure core function then
derives its series from the filled inputs only, never from their alternates.
Finally, the fill runs again with the computed series at the computed source's
place in the order. The verdict reads the resulting snapshot and never sees
the raw inputs.

## Consequences

- **Easier:** a pier ranks a computed index against an external one by moving
  one key in its provider list. Alternates, agreement and health need no new
  rules.
- **Easier:** the derivation is pure core math, tested with no network. The
  verdict for a given snapshot stays byte-identical whatever raw inputs it
  carried.
- **Easier:** a new computed variable, such as seeing, is one more derivation
  declared by the same source.
- **Harder:** the fill runs twice on each fetch, and a computed source can't
  derive from another computed variable without a further pass.
- **Harder:** one source holds every computed variable. A pier can't rank
  computed transparency ahead of 7Timer! and computed seeing behind it. The
  fill is per variable, but the order is one list.
- **Harder:** the key `computed` names health topics and entities, so it is
  part of the delivery surface and can't be renamed.

## Alternatives Considered

### Alternative 1: Derive the index inside the verdict computation
- **Pros**: no second fill; the core reads raw inputs where it scores.
- **Cons**: the index can't take part in the provider order, so a pier can't
  prefer it to 7Timer! or fall back to it. Raw inputs would change the
  document directly.
- **Why not**: it breaks the rule that raw inputs reach the document only
  through a shown variable, and it takes away the pier owner's choice.

### Alternative 2: Each provider computes its own index from its own columns
- **Pros**: no new source; each model's index travels with its other variables.
- **Cons**: the inputs come from different providers. Aerosol comes from the
  air-quality forecast, and water vapour from a weather model. No single
  provider holds both.
- **Why not**: the index needs inputs that only exist together after the fill.

### Alternative 3: One computed source per derived variable
- **Pros**: a pier can rank each computed variable separately.
- **Cons**: more keys, health sensors and configuration for a choice no pier
  has asked for yet.
- **Why not**: the cost lands now, for a need that may never come. Splitting
  the source later adds keys, which the document and delivery allow.
