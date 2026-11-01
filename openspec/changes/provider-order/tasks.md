<!-- Ten tasks. One task is one behavior, its test, and the code that passes it.
     Each task is one line: - [ ] X.Y [tags] <behavior> (verify: <command>)
     Tags: [easy|medium|complex], [parallel]. A section heading may carry [depends-on: <section>]. -->

## 1. Core contracts: declarations, the series model, its readers, the config block

- [x] 1.1 [medium] A `ProviderSpec` catalog in the pure core declares `open_meteo` and `seven_timer` as the conditions spec's "Each provider declares its variables and bundles" scenarios state: eleven variables with the cloud bundle for Open-Meteo, `seeing` and `transparency` with no bundle for 7Timer!, both keyless; the core boundary test stays green (verify: uv run pytest tests/test_provider_catalog.py tests/test_core_boundary.py) (✓ uv run pytest tests/test_provider_catalog.py tests/test_core_boundary.py passed)
- [x] 1.2 [complex] `Conditions` holds one `Series` per variable (provider key, issue time, values over every hour the provider returned, `None` for blanks) and answers `value_at`, `issued_at` and the sorted union `hours()`; `Conditions()` is the empty value; `BaseGroup`, `SecondaryGroup`, `GroupMeta`, `BaseHour` and `SecondaryHour` are gone; `tests/conftest.py`'s `make_conditions` builds series with one issue time for all (verify: uv run pytest tests/test_conditions_model.py) (✓ uv run pytest tests/test_conditions_model.py passed; full suite 1588 passed)
- [ ] 1.3 [complex] Scoring reads every variable through `value_at`, the atmosphere functions read `seeing` and `transparency` directly, and `confidence` reads freshness from the `cloud_cover` series' issue time: a stale `seeing` series leaves the document byte-identical and a `cloud_cover` series issued eleven hours before the instant gives a lower confidence than one issued an hour before (verify: uv run pytest tests/test_scoring.py tests/test_verdict_eval.py)
- [ ] 1.4 [easy] The timeline holds one entry per hour in the union of every series' hours, each key read from its series, and is empty for the empty value (verify: uv run pytest tests/test_producer_timeline.py)
- [ ] 1.5 [medium] `AppConfig.conditions.providers` defaults to `[open_meteo, seven_timer]` when the block is absent, keeps a configured order, and `build_config` raises `Invalid conditions configuration: ...` naming the rule for an empty list, an unknown key, a duplicate key, and a list with no keyless cloud-cover provider, with no other configuration value in the message (verify: uv run pytest tests/test_config.py)

## 2. Health carries variables [depends-on: 1]

- [ ] 2.1 [medium] `Role` is removed; `ProviderInfo`, `FetchOutcome` and `ProviderHealth` carry `variables`; `health_attributes` emits `variables` as a list of timeline keys where `role` was, with every other key and its order unchanged, and the startup reset publishes it; `Service` seeds health from `ProviderInfo` without a role (verify: uv run pytest tests/test_health.py tests/test_health_delivery.py tests/test_service.py tests/test_service_reconnect.py tests/test_reconnect.py tests/test_replay.py tests/test_night_dashboard_doc.py)

## 3. The provider layer fills per variable [depends-on: 2]

- [ ] 3.1 [complex] `assemble_snapshot(fills)` takes ordered `(spec, forecast)` pairs and fills each variable from the first provider that returned it: the earlier provider wins a variable both returned, an all-blank column falls through, a bundle travels together with its empty members staying on the winner, a series is whole and never merged per hour, and a failed or empty forecast is passed over (verify: uv run pytest tests/test_conditions_provider.py -k assemble)
- [ ] 3.2 [medium] `CompositeProvider` holds an ordered sequence, fetches every provider in order on every `get`, reports one `FetchOutcome` per provider naming its declared variables, success for a provider the fill passed over, and fills after all fetches; `build_provider(keys, ...)` builds the fetchers from the catalog in the configured order and `__main__` passes `config.conditions.providers` (verify: uv run pytest tests/test_conditions_provider.py tests/test_main.py tests/test_integration.py)

## 4. Documentation and the whole gate [depends-on: 3]

- [ ] 4.1 [easy] [parallel] The README's configuration table gains a `conditions` row with the default list and the four rejected cases, "Watching provider health" describes `variables` in place of `role` and drops the base/secondary wording, "How it is built" says providers sit in an ordered list, and the module docstrings of `pierpressure/conditions/__init__.py`, `provider.py` and `pierpressure/core/conditions.py` describe the series model (verify: uv run pytest tests/test_docs.py)
- [ ] 4.2 [medium] The golden suite's `_verdict_json` passes the recorded forecasts as ordered `(spec, forecast)` pairs and every expected JSON file is byte-identical with no regeneration; the determinism test passes; the full gate is green (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-01, task 1.2: removing the group types breaks every reader at import, and
  the pre-commit mypy hook checks the whole package. So 1.2 also moved scoring,
  the producer's timeline and the service fallback onto `value_at`, `issued_at` and
  `hours()`, ported the test builders that used the groups, and gave
  `assemble_snapshot(base, secondary)` a transitional body that builds series. Tasks
  1.3 and 1.4 then add their own scenarios as tests; 3.1 replaces the transitional
  `assemble_snapshot`. No behaviour or guarantee changes.
