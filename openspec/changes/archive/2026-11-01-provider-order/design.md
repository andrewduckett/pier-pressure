## Context

The core's conditions input is two typed groups, `BaseGroup` (cloud, wind and
weather) and `SecondaryGroup` (seeing, transparency), each with its own issue
time. The provider layer builds them in `assemble_snapshot` from exactly two
providers, fetched by `CompositeProvider`. Scoring already reads one variable
at a time through small accessors, and the timeline builder reads both groups
by hour. Freshness reads the base group's issue time. Health carries a `Role`
literal on `ProviderInfo`, `FetchOutcome` and `ProviderHealth`, and the MQTT
adapter emits it as the `role` attribute.

Constraints that shape the approach:

- The core stays pure: no network library, no Home Assistant import. A test
  enforces it. The core is also the only place that validates settings
  (ADR 0022), and the add-on's combined settings go through the same path.
- The verdict document is frozen. The golden suite drives recorded Open-Meteo
  and 7Timer! payloads through the provider layer into `produce_verdict` and
  asserts byte-identity, including the degraded cases. Those goldens are the
  oracle and are not regenerated.
- No compatibility code: the `role` attribute goes, and Andrew is the only
  user.
- Astrospheric (#131) must later join as a provider only: a declaration and a
  parser, with no change to the model, the fill or health.

## Goals / Non-Goals

**Goals:**

- One snapshot shape that any number of providers can fill, variable by
  variable, with provenance on each series.
- The fill is a pure function of the configured order and the fetched
  forecasts, testable without the network.
- Config validation of the provider list runs in the core, with no network
  import.

**Non-Goals:**

- Native-cadence seeing, retry, caching or any fetch cadence rule. Those stay
  as they are or belong to later stories in the epic.
- Any change to timeline keys, score terms or gate rules.
- An add-on form option for the provider list.

## Test Seams

- **Primary test seam:** `assemble_snapshot` in the provider layer, now taking
  the ordered declarations and their forecasts. The fill rules are asserted on
  the `Conditions` value it returns, with stub forecasts and no network: first
  provider wins, bundles travel together, a series is whole, an empty column
  falls through, a failed provider is passed over.
- **Existing seams reused:** the golden suite (`tests/test_golden_verdict.py`),
  which already routes recorded payloads through `assemble_snapshot` and pins
  the document. Its `_verdict_json` helper changes to pass the two recorded
  forecasts as `[(open_meteo_spec, base), (seven_timer_spec, secondary)]`; the
  expected JSON files do not change. The determinism test; `tests/test_conditions_provider.py` for
  `CompositeProvider` and outcomes; `tests/test_health_delivery.py` for the
  attributes; `tests/test_config.py` for the list's validation;
  `tests/test_producer_timeline.py` and `tests/test_scoring.py` through the
  `make_conditions` helper in `tests/conftest.py`, which is rewritten once to
  build series.

## Scrutiny Tier & Blast Radius

- **Tier:** high
- **Blast radius:** the core's conditions model and every reader of it
  (scoring, producer, config), the provider layer and both providers, health
  and the MQTT health attributes, the service's health seeding, `__main__`,
  and the test helper every conditions test builds on. The verdict document,
  topics and entities are untouched.

## Decisions

### D1. The snapshot is a mapping from variable to series

`Conditions` holds `series: Mapping[Variable, Series]`. A `Series` carries
`provider` (the key), `issued_at`, and `values: Mapping[datetime, float | None]`
over every hour its provider returned, `None` where that hour's value was
blank. `Conditions` offers `value_at(variable, time)`, `issued_at(variable)`
and `hours()` (the sorted union of every series' hours). `Conditions()` with
no series is the empty value. `Variable` is a `Literal` of the thirteen
timeline variable keys, defined once in the core: the sixteen timeline entry
keys without `time`, `sun_altitude` and `moon_altitude`.

Alternatives considered. Keep two groups and add a third for Astrospheric:
rejected, the roles are the problem. A per-hour grid with a provider on every
cell: rejected, it invites per-hour merging, which the epic forbids. Series
that hold only non-null values: rejected, per-hour nulls and the timeline's
hour union must survive, so a series keeps every hour its provider covered.

This is costly to reverse: it is the seam every later provider builds on. It
gets a decision record, superseding the deprecated ADR 0006.

### D2. Provider declarations are core data; fetchers live outside

A `ProviderSpec` (key, display name, `needs_key`, `variables` in declared
order, `bundles` as frozensets) is a frozen value in the core, and a catalog
maps the known keys to their specs. `OpenMeteoProvider` and
`SevenTimerProvider` each point at their spec. The core's `ConditionsConfig`
validates the list against the catalog, so ADR 0022 holds and the core imports
nothing from the provider layer.

Alternatives considered. Declarations as class attributes on the fetchers:
rejected, the core cannot import them without pulling in `httpx`. A registry
injected into `build_config`: rejected, it is a second validation path, and
the add-on's combined settings would need it too.

### D3. The fill is a pure function in the provider layer

`assemble_snapshot(fills)` takes the ordered `(spec, forecast)` pairs and
returns `Conditions`. For each variable, in declared order, it takes the first
spec that declares it and returned it. Returned means the forecast has at
least one non-null value for the variable or for a bundle mate (brainstorm
D2). A bundle is decided once, by
that rule, and every member series gets the same provider, issue time and hour
set. A failed or empty forecast is an empty `SourceForecast`, so it is passed
over without a special case.

Alternative: fill inside `CompositeProvider.get` (rejected: the golden suite
and the fill tests need the fill without a fetch).

### D4. Every listed provider is fetched, in order, then the fill runs

`CompositeProvider` becomes an ordered sequence of providers. `get` fetches
each in order through the existing guarded `_safe_fetch`, collects one
`FetchOutcome` per provider, then calls `assemble_snapshot`. `build_provider`
takes the configured keys and builds the fetchers from the catalog; tests pass
stubs keyed the same way.

### D5. Freshness reads the cloud-cover series

`confidence` calls `conditions.issued_at("cloud_cover")`. The accessors in
scoring become `conditions.value_at(variable, slot)`. The atmosphere functions
that take a `SecondaryHour` today (`_optional_term`, `optional_term_mean`,
`_hour_atmosphere`, `atmosphere_mean` and the `_ATMOSPHERE_TERMS` selectors)
read `value_at("seeing", slot)` and `value_at("transparency", slot)` instead,
so `SecondaryHour` can go. No formula, weight or rounding changes, which is
what keeps the goldens byte-identical.

### D6. Health carries the declared variables

`Role` is deleted. `ProviderInfo`, `FetchOutcome` and `ProviderHealth` carry
`variables: tuple[str, ...]`, copied from the spec. `health_attributes` emits
`variables` as a JSON list where `role` was, keeping the other keys and their
order. The service seeds health from `ProviderInfo` as today.

### D7. The config block

`ConditionsConfig(providers: list[str])` with the default list, validated in
this order: non-empty, every key known, no duplicates, at least one keyless
provider that declares `cloud_cover`. `AppConfig.conditions` defaults to it.
`build_config` validates the raw block like `recompute`, and the error reads
`Invalid conditions configuration: <rule>`, naming the offending key when
there is one and never another value.

### D8. The timeline reads the union of series hours

`_timeline` iterates `conditions.hours()` and reads each key with `value_at`.
The seeing and transparency rounding stays where it is.

## Risks / Trade-offs

- [A golden differs after the refactor] → The goldens are the oracle. A
  difference means the model or the fill is wrong, and is fixed there; the
  goldens are not regenerated in this change.
- [The timeline's hour union shrinks for a provider that returned rows but
  won no variable] → That is the spec as rewritten: a provider with no series
  contributes no hours. With today's two providers it cannot happen without
  every value being blank, and the goldens cover the blank-column cases.
- [Config validation drifts from the fetchers] → One catalog in the core is
  the single source; a test asserts each fetcher's spec is in it under its key.
- [An automation reads the `role` attribute] → It disappears with no
  deprecation, by decision. The README's health section documents
  `variables` and the automation example is checked.
- [Iteration order leaks into the document] → The fill walks variables in the
  fixed `Variable` order and providers in config order, and `hours()` sorts,
  so the output is a function of its inputs only.

## Migration & Rollback

No data migration. Config files without a `conditions` block keep today's
behaviour. The health sensor's `role` attribute disappears on the first publish
after upgrade; `variables` appears. Rollback is reverting the pull request; the
retained health attributes return to `role` on the next publish.
