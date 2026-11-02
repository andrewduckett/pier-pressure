## 1. Catalog and configuration

- [x] 1.1 [easy] The catalog holds `open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`, `open_meteo_icon` and `open_meteo_gfs`, named "Open-Meteo HRRR" and so on, none needing a key. HRRR, ICON and GFS declare `OPEN_METEO`'s variables; HRDPS and RDPS declare the same without `precipitation_probability`. All share the cloud bundle (design D4) (verify: uv run pytest tests/test_provider_catalog.py) (✓ uv run pytest tests/test_provider_catalog.py passed)
- [x] 1.2 [easy] Configuration accepts the model keys in order. `providers: [open_meteo_hrdps]` alone passes the cloud rule, and `[open_meteo_hrrr, open_meteo]` starts for a pier at 51.5, -0.12 (verify: uv run pytest tests/test_config.py) (✓ uv run pytest tests/test_config.py passed)

## 2. One fetcher for every Open-Meteo provider [depends-on: 1]

- [x] 2.1 [easy] A test pins the `open_meteo` request exactly: the same eleven `hourly` columns in today's order, 2 forecast days, km/h, UTC, and no `models` parameter. It passes before any fetcher change (verify: uv run pytest tests/test_conditions_provider.py -k open_meteo) (✓ uv run pytest tests/test_conditions_provider.py -k open_meteo passed)
- [x] 2.2 [medium] The fetcher builds its `hourly` list from its spec's variables through one variable-to-column map, and `parse_open_meteo` reads its columns through the same map. The pinned `open_meteo` request and every existing parser test still pass (design D3) (verify: uv run pytest tests/test_conditions_provider.py) (✓ uv run pytest tests/test_conditions_provider.py: 41 passed; the one failure is the walk test the ledger names)
- [x] 2.3 [easy] A catalog test checks that every variable each Open-Meteo spec declares has a column in the map, so a missing entry fails a test rather than a fetch (verify: uv run pytest tests/test_conditions_provider.py) (✓ uv run pytest tests/test_conditions_provider.py: 42 passed, and the new test fails with a column removed; the one failure is the walk test the ledger names)
- [x] 2.4 [medium] `OpenMeteoProvider` takes its spec and an optional model as fields (design D2). Built for HRDPS, its request names `models=gem_hrdps_continental` only, asks for 2 days in km/h, and leaves `precipitation_probability` out of `hourly` (verify: uv run pytest tests/test_conditions_provider.py) (✓ uv run pytest tests/test_conditions_provider.py: 44 passed; the one failure is the walk test the ledger names)
- [ ] 2.5 [medium] `build_provider` builds each model key with its model from the key-to-model table and the shared clock (design D1, D5). A test parametrised over the five keys asserts each request's exact `models` value. A model provider fetched at 21:05 stamps 21:05 as the issue time of every series it fills (verify: uv run pytest tests/test_conditions_provider.py)

## 3. Real responses, fill and failure [depends-on: 2]

- [ ] 3.1 [parallel] [medium] One trimmed live recording per model, at the Toronto point (43.65, -79.38), four hours each, kept with its real `null`s and `hourly_units` (design D6). Each parses into readings. HRDPS's and RDPS's precipitation probability is absent, and HRRR's is present (verify: uv run pytest tests/test_conditions_provider.py)
- [ ] 3.2 [parallel] [easy] With `open_meteo_hrdps` then `open_meteo`, cloud and its layers carry `open_meteo_hrdps` and precipitation probability carries `open_meteo`. With `open_meteo_hrrr` answering 400, its outcome fails with `HTTPStatusError: 400 Bad Request`, and cloud carries `open_meteo` (design D7) (verify: uv run pytest tests/test_conditions_provider.py)

## 4. Documentation and the gate [depends-on: 3]

- [ ] 4.1 [easy] The README lists the five keys with each model's identifier, coverage and reach, and keeps the story's Great Lakes order (HRRR, HRDPS, RDPS, then 7Timer!). It explains that hours past the cloud model's reach stay empty, and that a model's issue time is the fetch time. It says every model shares one service, the provider list applies to every pier, and HRRR's precipitation probability is best match's. The entities table, topic tables, health section and removal steps name the new keys, and the removal steps cover a dropped provider's health entity (verify: grep -q open_meteo_hrdps README.md)
- [ ] 4.2 [easy] The full gate passes: lint, types and the whole test suite (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-01, task 1.1: adding the five keys to `CATALOG` makes `test_each_fetcher_points_at_its_catalog_spec` fail until task 2.5 gives `build_provider` a fetcher for each key. That test walks every catalog key, so the commits for tasks 1.1 to 2.4 carry one known failure in `tests/test_conditions_provider.py`.
