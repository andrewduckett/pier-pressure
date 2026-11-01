## Why

Conditions today come from two providers with fixed roles: a base source for
cloud and wind and a secondary source for seeing and transparency. Those roles
were an artefact of two providers with disjoint variables. Astrospheric, the
next provider (#131), supplies cloud, seeing and transparency at once, so it
fits neither role. This change replaces the roles with an ordered provider list
and a per-variable fill before Astrospheric arrives, so that story is only a
provider. The verdict stays byte-identical for the same fetched data.

## What Changes

- **Provider order in config.** A `conditions.providers` list, preferred first,
  default `[open_meteo, seven_timer]`. Four mistakes stop startup with a plain
  configuration error: an empty list, an unknown key, a duplicate key, and a
  list with no keyless provider that supplies cloud cover (D5, D9).
- **Providers declare their variables and bundles.** Each provider names the
  variables it supplies and which travel together. The only bundle today is
  cloud total with its low, mid and high layers (D7).
- **Per-variable fill.** The snapshot becomes one series per variable, each
  carrying its provider's key and issue time. A variable, or a bundle, is filled
  by the first provider in order that returned it: at least one hour carries a
  value (D2). A series comes whole from one provider; hours it did not cover
  stay empty.
- **Every listed provider is fetched on every recompute, in order,** and the
  fill is decided after all fetches. One fetch outcome per provider, every
  time (D3).
- **Freshness reads the cloud series' issue time.** Confidence's freshness
  factor follows the provider that filled cloud cover. Today that is Open-Meteo,
  as before (D8).
- **BREAKING: the health sensor's `role` attribute is replaced by `variables`,**
  a fixed-order list of the provider's declared variables, named by their
  timeline keys (D4). No compatibility code: the attribute is removed, not
  deprecated.
- **The `BaseGroup` / `SecondaryGroup` model and the `Role` type are removed**
  from the core, the provider layer and health.
- **Specs say "provider" and "variable"** where the conditions spec said
  "source" and "field" (D6). The night-verdict timeline requirements get a
  wording-only delta (D1).
- **Documentation.** The README's configuration table and health section, the
  glossary (already committed), and a decision record superseding the
  deprecated ADR 0006.

Out of scope: any new provider, any change to the verdict document's shape or
values, the gates, or the score weights.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: "No single source is load-bearing" is rewritten for the ordered
  fill; the per-provider issue time becomes a per-series issue time; "Each fetch
  reports its outcome per provider" drops the role; the two "base source"
  requirements for cloud layers and weather variables are restated per provider;
  a new requirement covers the provider list's validation.
- `ha-delivery`: the health sensor's attributes carry the provider's variables
  instead of its role.
- `night-verdict`: wording only, in the three timeline requirements. "The base
  source's reading" becomes the reading of the provider that filled that
  series. Scenario values are unchanged.

## Impact

- **Core (pure):** `pierpressure/core/conditions.py` (the snapshot model),
  `pierpressure/core/scoring.py` (variable accessors and `freshness_factor`'s
  input), `pierpressure/core/producer.py` (timeline assembly),
  `pierpressure/core/config.py` (the `conditions` block).
- **Provider layer:** `pierpressure/conditions/provider.py` (`Provider`,
  `assemble_snapshot`, `CompositeProvider`, `build_provider`), the two providers'
  declarations, `pierpressure/__main__.py`.
- **Health and delivery:** `pierpressure/health.py` (`Role`, `ProviderInfo`,
  `FetchOutcome`, `ProviderHealth`), `pierpressure/delivery/mqtt.py`
  (`health_attributes`), `pierpressure/service.py`.
- **Tests:** the golden suite and the determinism test must pass unchanged;
  model, provider, health, delivery, service and config tests follow the new
  shape.
- **Docs:** README, a new ADR, amendments to ADR 0005 and ADR 0015 where they
  name roles.
- **Home Assistant:** the health sensor's `role` attribute disappears. Any
  automation reading it must switch to `variables`. Entities, topics and the
  verdict document are unchanged.
- No new dependencies. No network behaviour changes beyond the fetch order.
