## Why

Every cloud voice a pier can list today comes through one API, Open-Meteo. The National Weather Service gridpoint forecast carries the National Blend of Models plus the local office's edits, the most informed free source for lake-effect cloud, and it reaches us through a different API. Now that cloud agreement exists, a second opinion on overcast and wind has somewhere to land (#155, #153).

## What Changes

- A new provider, `nws`, fetches the NWS raw gridpoint forecast in two steps, from the pier's coordinates to its grid cell and then to the data (D4). It declares total cloud cover, wind speed, gust and direction, temperature, dew point, humidity and precipitation probability, with no bundle and no API key (D7).
- Variable-length NWS periods are expanded onto the hourly grid, held across their hours, out to 72 hours from the first period (D2).
- The grid cell is remembered per pier in the provider for the life of the process. A failed lookup is not remembered, and a gridpoint 404 forgets the cell (D3). The point request follows NWS's redirect for coordinates with more than four decimal places.
- The issue time is the payload's `updateTime` (D8). A value whose unit code is not the expected one is left absent (D9).
- Every request sends a fixed `User-Agent` of project name, running version and repository URL (D6).
- A pier outside NWS coverage is a failed outcome with a 404, passed over like any failed provider. There is no startup check (D5).
- The fill is tightened: a provider fills a bundle whole or not at all. When an earlier provider already holds a member of a later provider's bundle, that later provider fills none of the remaining members. With `nws` first, the cloud layers stay unavailable and Open-Meteo's total becomes an alternate (D1). This applies to every provider; today only NWS can trigger it.
- The README documents the new key, its coverage, the layer-split trade-off and the two-step lookup. The default provider list is unchanged (D10).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: the catalog gains `nws` with its declaration. The fill's bundle rule becomes whole or not at all. NWS periods are resampled onto the hourly grid with a 72-hour horizon. NWS requests carry the fixed `User-Agent`, the issue time comes from `updateTime`, and an out-of-coverage pier is a failed outcome.

## Impact

- Code: new `pierpressure/conditions/nws.py`; `pierpressure/core/providers.py` (`NWS` spec, `CATALOG`); `pierpressure/conditions/provider.py` (`assemble_snapshot` bundle rule, `build_provider`); `pierpressure/__init__.py` read for the version.
- Tests: a recorded fixture pair for the points and gridpoint responses under `tests/fixtures/`; parser, fetch, catalog, config and fill tests; the golden fixtures that enumerate catalog keys, if any.
- Docs: `README.md` provider list, model section and health topic list; `openspec/specs/conditions/spec.md` through the delta.
- No new dependencies. `httpx` already carries the requests. No change to the verdict document, the MQTT topics or the default configuration.
