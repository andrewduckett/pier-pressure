## Why

Today the `open_meteo` provider fetches Open-Meteo's "best match" blend, so a
pier cannot choose a finer regional model. HRDPS at 2.5 km is finer than any
model Astrospheric uses. Making each model its own provider also gives the
coming cloud-agreement story (#153) separate forecasts to compare.

## What Changes

- Five new providers in the catalog, each backed by one Open-Meteo model:
  `open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`, `open_meteo_icon`
  and `open_meteo_gfs` (D2). The identifiers were verified against the live API
  (D1). ICON uses `icon_seamless` and GFS uses `gfs_global` (D3).
- Each model provider declares the variables its model returns. HRDPS and RDPS
  leave out precipitation probability (D4). Each has its own health record.
- A model provider works like `open_meteo` in every other way: 2 days of
  hourly data, issue time taken from the fetch time, and the existing fill and
  forecast-reach rules (D6, D8).
- A pier outside HRRR's or HRDPS's area gets a failed fetch every time, and the
  provider is passed over (D5).
- Plain `open_meteo` still fetches best match. The default list stays
  `open_meteo`, `seven_timer` (D7). Nothing changes for an existing install.
- The README lists the new keys and gives each model's coverage and forecast
  reach. It explains that hours past the cloud model's reach stay empty, and
  suggests an order for a Great Lakes pier: HRRR, HRDPS, RDPS, then 7Timer!.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: the catalog gains the five Open-Meteo model providers, each with
  its declared variables and the model it fetches. A model provider fails for a
  location its model does not cover.

## Impact

- Code: `pierpressure/core/providers.py` (new specs in `CATALOG`),
  `pierpressure/conditions/open_meteo.py` (one fetcher sends a `models=` value
  per spec), `pierpressure/conditions/provider.py` (`build_provider` maps the
  new keys). Config validation in `pierpressure/core/config.py` already reads
  `CATALOG`, so the new keys pass it with no change.
- Tests: one recorded fixture per model under `tests/fixtures/` (D9), plus
  catalog, parser and configuration tests.
- Delivery: a listed model provider gets a health sensor, for example
  `sensor.pierpressure_<pier>_open_meteo_hrrr_health`. The topics, entities and
  verdict document do not change shape.
- Docs: `README.md` configuration and provider-health sections.
- Dependencies and network: none new. Open-Meteo stays keyless.
