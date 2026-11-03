## Context

Every provider is a small dataclass in `pierpressure/conditions/` with a `spec` pointing at its `ProviderSpec` in the core catalog, a `fetch(pier)` that returns a `SourceForecast`, and a pure `parse_*` function tested against a recorded fixture under `tests/fixtures/`. `SevenTimerProvider` is the closest template: it parses a coarser cadence and holds each value across its hours in the provider layer, so the core only ever sees an hourly grid. `OpenMeteoProvider` shows the `httpx.Client` injection the fetch tests use with `httpx.MockTransport`.

The fill in `assemble_snapshot` walks variables in `Variable` order and providers in configured order. It decides a bundle once per winning provider, but a comment there lets a later provider fill the members of its bundle that an earlier provider did not take. No shipped provider triggers that path, because every cloud provider declares the same four-variable bundle. NWS declares `cloud_cover` with no layers, so it is the first that can.

NWS facts that shape the code. `GET /points/{lat},{lon}` returns `properties.gridId`, `gridX` and `gridY`, and answers 404 outside coverage. `GET /gridpoints/{gridId}/{gridX},{gridY}` returns `properties.updateTime` and one object per variable with a `uom` unit code and `values[]`, each `{validTime, value}` where `validTime` is an ISO 8601 start and duration such as `2026-11-03T18:00:00+00:00/PT3H`. Both require a `User-Agent`. The running version is `pierpressure.__version__`, read from package metadata.

The constraints that bind: the core stays free of network code; the provider layer owns resampling; `describe_error` is the only path for error text; `mise run check` must stay green; the verdict document, the MQTT topics and the default configuration do not change.

## Goals / Non-Goals

**Goals:**
- One new module, `pierpressure/conditions/nws.py`, on the 7Timer! and Open-Meteo patterns, with parsing separate from fetching.
- A fill rule that keeps a bundle whole without changing any outcome a shipped configuration produces today.
- Tests that need no network, driven by a recorded points and gridpoint fixture pair.

**Non-Goals:**
- Alerts, visibility and mixing height (later computed story).
- Any persistence of the grid cell across restarts.
- Unit conversion. An unexpected unit is dropped, not converted.
- Retry on a failed fetch (#38).

## Test Seams

- **Primary test seam:** `tests/test_conditions_provider.py`. It already drives providers through `fetch(pier)` with an injected `httpx.Client(transport=httpx.MockTransport(...))`, asserts request URLs, params and headers, and drives `assemble_snapshot` and `build_provider` with stub fetchers. Every NWS behaviour, the two-step lookup, the remembered grid, the header, the resample, the units, the issue time, the 404 and the bundle rule, is observable there.
- **Existing seams reused:** `tests/test_provider_catalog.py` for the declaration; `tests/test_config.py` for the provider list scenarios; `tests/test_scoring.py` for the neutral high-cloud term; `tests/test_docs.py` if it checks README provider tables.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** `pierpressure/conditions/` (new module, `provider.py` fill and `build_provider`), `pierpressure/core/providers.py` (catalog entry), README. The fill change touches every configuration, but it is a no-op for every bundle layout that ships today. No change to the verdict document, topics or delivery.

## Decisions

**DD1. The provider reads the raw gridpoint endpoint, not the hourly forecast endpoint.** The hourly forecast endpoint is already on an hourly grid but has no numeric sky cover, only a text summary, and gives wind as strings such as "5 mph". The raw gridpoint endpoint has numeric sky cover and every variable the story names, in SI units, with `updateTime`. Alternative: the hourly endpoint plus text parsing for cloud. Rejected: it would invent a cloud number from prose.

**DD2. Period expansion is a hold, done in the parser, capped at 72 hours from the earliest period start.** Each `validTime` is split into a start and an ISO 8601 duration. The duration parser handles days, hours and minutes, which is all NWS emits. The value is written to every top-of-hour slot from the start for the duration. The horizon is computed once from the minimum start across all variables and applied to every variable (D2). Alternatives: interpolation (rejected, same reason as 7Timer!: it manufactures precision), or no cap (rejected, D2). Python 3.14 has no ISO duration parser in the standard library, so a ten-line regex parser lives in the module rather than a new dependency.

**DD3. The grid cell is a dictionary on the provider instance keyed by `(latitude, longitude)`.** `build_provider` already creates one instance per process, so the instance is the natural lifetime. The points call runs only on a miss; a raised error leaves no entry (D3). Alternative: a module-level cache. Rejected: it would leak between tests and between stacks built with different clients.

**DD4. Units are checked against a fixed mapping from variable to accepted `uom` code.** `wmoUnit:percent` for sky cover, humidity and precipitation probability; `wmoUnit:degC` for temperature and dew point; `wmoUnit:km_h-1` for wind speed and gust; `wmoUnit:degree_(angle)` for direction. A variable whose `uom` differs is skipped whole, so the column is absent (D9). Alternative: convert known units such as knots. Rejected: the spec says carried as reported, never converted, and a silent conversion is the kind of thing that drifts.

**DD5. The `User-Agent` is one module constant built from `__version__` at import.** Format: `PierPressure/<version> (https://github.com/andrewduckett/pier-pressure)`. It is set as a default header on the client the provider creates, and the test injects a client and asserts the header on each captured request (D6).

**DD6. The fill rule becomes: a provider fills a bundle only if no member is already filled.** In `assemble_snapshot`, the branch that fills a bundle checks every member of the provider's declared bundle; if any is already in `series`, the provider fills nothing for that variable, and falls through to become an alternate for the variable when that variable itself is filled. The comment that justified the old carve-out goes. For every shipped configuration this is identical, because every cloud provider declares the same bundle. Alternative: have NWS declare empty layers. Rejected in D1. This decision is cheap to reverse and needs no ADR; ADR-0027 already states the bundle principle, and this is its enforcement.

**DD7. One fixture pair, recorded once.** `tests/fixtures/nws_points.json` and `tests/fixtures/nws_gridpoints.json`, recorded from the live API for a pier near the Great Lakes, trimmed to the first few days. The parser test reads the gridpoint fixture; the fetch test serves both through `MockTransport` by URL path. Recording is a one-off task done by hand with the project's `User-Agent`; nothing in the suite touches the network.

## Risks / Trade-offs

- [NWS changes a `uom` code or renames a property] → the column goes absent rather than wrong; the health sensor still shows success, so the README notes that a missing NWS variable is visible on the timeline, not in health.
- [The points mapping changes for a pier while the process runs] → gridpoint calls fail, the health sensor shows NWS failing, and a restart re-resolves. Rare by NWS's own account.
- [The fill rule has an effect on a configuration we did not foresee] → the existing fill tests all run unchanged; a new test proves `[open_meteo, open_meteo_hrrr]` and `[open_meteo_hrdps, open_meteo]` produce the same snapshot before and after.
- [Golden fixtures that enumerate catalog keys drift] → the catalog test lists keys explicitly, so the new key is added there on purpose, not discovered by a failing golden.
- [NWS rate limits or latency] → one request per fetch after the first, same 10-second timeout as the other providers.

## Migration & Rollback

N/A. No data changes shape. A pier that never lists `nws` sees no difference. Rolling back is reverting the commits.

## Open Questions

- Whether the README's "Choosing Open-Meteo models" section should become "Choosing providers" with NWS as a second subsection, or NWS gets its own section. Decide while writing the README task; it changes no code.
