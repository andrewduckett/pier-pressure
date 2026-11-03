<!-- One task is one behavior, its test, and the code that passes it. Test first. -->

## 1. Contract: the declaration and the bundle rule

- [x] 1.1 [easy] The catalog offers `nws`, display name `NWS`, no key, the eight declared variables and no bundle; `[nws, open_meteo_hrrr, seven_timer]` and `[nws]` pass configuration, and the default order is unchanged (verify: `uv run pytest tests/test_provider_catalog.py tests/test_config.py -k nws`) (✓ `uv run pytest tests/test_provider_catalog.py tests/test_config.py -k nws` passed, 5 tests)
- [x] 1.2 [medium] `assemble_snapshot` fills a bundle whole or not at all: with `nws` then `open_meteo`, `cloud_cover` carries `nws` with one `open_meteo` alternate, and `cloud_low`, `cloud_mid`, `cloud_high` have no series and no alternates; every existing fill and alternate test still passes (verify: `uv run pytest tests/test_conditions_provider.py -k "assemble or bundle or alternate"`) (✓ `uv run pytest tests/test_conditions_provider.py -k "assemble or bundle or alternate"` passed, 20 tests)
- [x] 1.3 [parallel] [easy] A snapshot whose `cloud_cover` series carries `nws` and whose `cloud_high` has no series yields score terms with a `None` high-cloud penalty (verify: `uv run pytest tests/test_scoring.py -k high_cloud`) (✓ `uv run pytest tests/test_scoring.py -k high_cloud` passed, 12 tests; the new test passed on first run, as scoring already treats a missing `cloud_high` as neutral)

## 2. The NWS parser [depends-on: 1]

- [x] 2.1 [easy] Record `tests/fixtures/nws_points.json` and `tests/fixtures/nws_gridpoints.json` from the live API for a Great Lakes pier with the project `User-Agent`, trimmed to the first few days, and a test proves both load as JSON with `properties.gridId`, `gridX`, `gridY` and `properties.updateTime` present (verify: `uv run pytest tests/test_conditions_provider.py -k nws_fixture`) (✓ `uv run pytest tests/test_conditions_provider.py -k nws_fixture` passed; recorded 2026-11-03 for MKX 88,65, Milwaukee, four days kept)
- [ ] 2.2 [medium] `parse_nws` holds each period's value across the clock hours it covers: a three-hour sky cover period fills three hours, a one-day-six-hour wind speed period fills thirty hours, and periods for different variables stay independent (verify: `uv run pytest tests/test_conditions_provider.py -k nws_period`)
- [ ] 2.3 [medium] The parser keeps only hours within 72 hours of the earliest period start across all variables: a period straddling the horizon is cut at it, a period starting past it leaves no reading (verify: `uv run pytest tests/test_conditions_provider.py -k nws_horizon`)
- [ ] 2.4 [easy] A variable whose `uom` is not the expected code is absent in every hour, an expected one is carried unrounded, and a `null` value is absent for its hours (verify: `uv run pytest tests/test_conditions_provider.py -k nws_unit`)
- [ ] 2.5 [easy] The forecast's `updateTime` becomes `issued_at`, and a payload without it gives `None` (verify: `uv run pytest tests/test_conditions_provider.py -k nws_issue`)

## 3. The NWS fetch [depends-on: 2]

- [ ] 3.1 [medium] `NwsProvider.fetch` makes the point request then the gridpoint request on the first fetch for a pier, only the gridpoint request on the second, resolves two piers separately, and follows a 301 from the point request (verify: `uv run pytest tests/test_conditions_provider.py -k nws_fetch`)
- [ ] 3.2 [medium] A point 503 is not remembered and the next fetch asks again; a point 404 is a failed outcome `HTTPStatusError: 404 Not Found` and the next provider fills cloud through `CompositeProvider`; a gridpoint 404 forgets the cell so the next fetch asks for the point again (verify: `uv run pytest tests/test_conditions_provider.py -k nws_fail`)
- [ ] 3.3 [easy] Every NWS request carries a `User-Agent` of `PierPressure/<version> (https://github.com/andrewduckett/pier-pressure)` with no `@`, and `build_provider` wires `nws` to `NwsProvider` pointing at its catalog spec (verify: `uv run pytest tests/test_conditions_provider.py -k "nws_user_agent or catalog_spec"`)

## 4. Documentation and the full gate [depends-on: 3]

- [ ] 4.1 [easy] README names `nws` in the configuration table and the health topic list, and a section says it covers the United States only, gives total cloud with no layer split, that listing it first leaves the layers unavailable, how the two-step lookup and the fixed `User-Agent` work, and that a missing NWS variable shows on the timeline rather than in health; the README docs tests pass (verify: `uv run pytest tests/test_docs.py`)
- [ ] 4.2 [easy] The whole gate is green: lint, types and every test (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-03, task 1.1: `test_each_fetcher_points_at_its_catalog_spec` walks the whole catalog, so it skips `nws` until task 3.3 wires `NwsProvider` into `build_provider`. Task 3.3 removes the skip.
