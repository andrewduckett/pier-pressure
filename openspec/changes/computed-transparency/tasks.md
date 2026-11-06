## 1. Variables and catalog

- [ ] 1.1 [easy] Open-Meteo's `total_column_integrated_water_vapour` parses into a new `column_water_vapour` variable. The variable is appended last to `Variable` and is not in `TIMELINE_VARIABLES`. Values are carried unrounded, in kg/m², and a `null` hour leaves only that variable blank (design DD7). (verify: `uv run pytest tests/test_conditions_provider.py -k water_vapour`)
- [ ] 1.2 [easy] `open_meteo`, `open_meteo_hrrr` and `open_meteo_gfs` declare `column_water_vapour` last. `open_meteo_icon`, `open_meteo_hrdps` and `open_meteo_rdps` don't declare it. Each request asks only for the columns its provider declares: `open_meteo` asks for twelve hourly variables, and HRDPS asks for neither precipitation probability nor water vapour. Update the pinned request test. (verify: `uv run pytest tests/test_provider_catalog.py tests/test_conditions_provider.py -k "declare or request"`)
- [ ] 1.3 [easy] The catalog offers `computed`, named `Computed`. It needs no key and declares `transparency` alone, with no bundle. Configuration accepts `[open_meteo, computed, seven_timer]` and `[open_meteo_hrdps, computed]`. The cloud guard rejects `[computed, seven_timer]`. (verify: `uv run pytest tests/test_provider_catalog.py tests/test_config.py -k computed`)
- [ ] 1.4 [easy] With no `conditions` block, the provider order is `open_meteo`, `seven_timer`, `open_meteo_air_quality`, `computed`. NWS stays out of it. (verify: `uv run pytest tests/test_config.py -k default`)

## 2. Computed transparency in the core [depends-on: 1]

- [ ] 2.1 [medium] A pure `computed_transparency` in `pierpressure/core/computed.py` gives the ADR-0032 values for an hour with both inputs: 1.0 for AOD 0.05 with 10 kg/m², 0.6959 for 0.15 with 30, and 0.0834 for 0.60 with 20. Every value lies in `[0, 1]`, and raising either input never raises the value (design DD3, DD4). (verify: `uv run pytest tests/test_computed.py -k value`)
- [ ] 2.2 [medium] The computed series is keyed `computed`. It covers only the hours both input series cover, with `None` where either input is blank. It carries the earlier of the inputs' issue times that is not `None` (design DD3). (verify: `uv run pytest tests/test_computed.py -k "covers or issue"`)
- [ ] 2.3 [medium] With no hour computed, `computed_transparency` returns the reason instead of a series. One reason is the missing input keys, `column_water_vapour` before `aerosol_optical_depth`. The other is that no hour has both values. The core module imports nothing from the conditions layer or `health` (design DD3). (verify: `uv run pytest tests/test_computed.py tests/test_core_boundary.py`)
- [ ] 2.4 [parallel] [easy] Two verdicts whose snapshots differ only in a `column_water_vapour` series serialize byte-identically (the night-verdict delta). (verify: `uv run pytest tests/test_producer_timeline.py -k water_vapour`)

## 3. The computed source in the provider stack [depends-on: 2]

- [ ] 3.1 [complex] `build_provider` maps `computed` to a `ComputedSource` whose `fetchers` overrides take `Provider | ComputedSource`, and `CompositeProvider.get` fills once without it, derives from the filled inputs only, and fills again with the computed series in its slot (design DD1, DD2). Assert through `build_provider` with stubs: ahead of 7Timer!, `computed` fills transparency and 7Timer! is the alternate; in the default order, 7Timer! fills it and `computed` is the alternate; in the default order, `computed` fills it when 7Timer! fails; a computed series with no values leaves no series and no alternate; an input alternate is never read. (verify: `uv run pytest tests/test_conditions_provider.py -k computed_fill`)
- [ ] 3.2 [medium] `computed` reports one outcome in its slot, naming `computed` and `transparency`, with the time it ran. It is successful with the series' issue time when an hour was computed. It is failed with `missing input: <keys>` or `no hour has every input`, built in `health.py` (design DD6). It is failed with `describe_error`'s kind when the derivation raises, and the snapshot is then built as if `computed` returned nothing (design DD5). (verify: `uv run pytest tests/test_conditions_provider.py tests/test_health.py -k computed_outcome`)

## 4. Documentation and the full gate [depends-on: 3]

- [ ] 4.1 [easy] The README's conditions section names `computed` and its new default place. It explains where to list it: ahead of 7Timer! to prefer it, or after 7Timer! as a fallback. It says the value is uncalibrated and links ADR-0032. The health-topic tables and the clean-up list include `computed`. (verify: `uv run pytest tests/test_docs.py`)
- [ ] 4.2 [easy] The full gate is green. (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
