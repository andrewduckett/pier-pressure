---
id: adrs-adr0028
date: 2026-11-02
status: accepted
title: 'ADR-0028: Each Open-Meteo model is its own provider'
description: Architecture decision record for offering each Open-Meteo weather model as a separate provider in the ordered list, with its own key and health record, rather than as an option on one Open-Meteo provider.
---

# ADR-0028: Each Open-Meteo model is its own provider

## Context

Open-Meteo serves many weather models from one keyless endpoint. A request
names the models it wants with a `models=` parameter, and with no parameter it
returns a "best match" blend. Some models are finer than the blend for a given
region: HRDPS covers Canada and the northern US at 2.5 km, and HRRR covers the
contiguous US at 3 km. A user may want one of these to fill cloud first. The
alternates, the forecasts that lose the fill, are useful too. To say how far
the models agree on tonight's cloud, the core needs each model's forecast as a
separate series with its own provenance. Conditions are already filled variable by variable
from an ordered list of providers, and each provider has a stable key, a fixed
declaration of its variables and a health record (ADR-0027). The key appears
in the configuration and in each health sensor's topics and unique ID.

## Decision

Each Open-Meteo model is a separate provider in the catalog, with its own key
(such as `open_meteo_hrdps`), display name, declaration and health record. The
plain `open_meteo` provider stays the best-match blend. A user picks models by
listing their keys in the ordered provider list, like any other provider.
Whether two model providers share one HTTP request is an implementation
detail, never something the configuration expresses.

## Consequences

- **Easier:** the ordered fill, the configuration check, the per-provider
  fetch outcomes and the health entities all work for models with no new
  concept. A model is a declaration and a request parameter.
- **Easier:** a user can rank models against providers from other services,
  for example HRDPS first, then 7Timer!, then best match.
- **Easier:** every model's forecast arrives as its own series, with its own
  key and issue time, so comparing models needs no new data shape.
- **Easier:** a model that fails, for example because the pier is outside its
  area, shows up on its own health sensor and is passed over without affecting
  the other models.
- **Harder:** each model is one request per recompute until requests are
  shared, so listing five models makes five calls to the same service.
- **Harder:** each key becomes a configuration value and the base of a health
  sensor's topics and unique ID, and each display name fixes that sensor's
  entity ID on a new install. Renaming either breaks users' configurations and
  automations, so both must stay stable even if Open-Meteo renames the model
  behind them.
- **Harder:** the startup rule that a list must hold a keyless provider of
  cloud cover no longer guarantees cloud for every pier. A regional model
  declares cloud cover everywhere but returns it only inside its area. The
  provider list applies to every pier, so a regional model fails on every
  fetch for a pier outside its area, and its health sensor shows that failure
  for good. A list of regional models alone leaves such a pier with no cloud.
- **Harder:** a model's declaration must match what that model actually
  returns, so the catalog has to be checked against the live service when a
  model is added.

## Alternatives Considered

### Alternative 1: One Open-Meteo provider with a configured list of models
- **Pros**: one entry in the provider list, one request, one health sensor.
- **Cons**: the provider would return several forecasts for the same
  variable, so the snapshot would need a second ordering inside one provider.
  A user could not put a provider from another service between two models.
  One model failing would mark the whole provider failed, or need health
  records below the provider level.
- **Why not**: it rebuilds the ordered list inside one provider and loses the
  per-provider health and provenance the core already has.

### Alternative 2: Keep only best match
- **Pros**: nothing to build. Best match already uses HRRR for the first hours
  in the contiguous US.
- **Cons**: the user cannot choose HRDPS or RDPS, and the blend hides which
  model filled which hours. There is one cloud forecast, so there is nothing
  to compare.
- **Why not**: it gives up the finer regional models and the comparison
  between models, which are the reasons for the change.
