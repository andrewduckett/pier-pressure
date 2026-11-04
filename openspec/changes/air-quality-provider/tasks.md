## 1. The core carries raw variables without showing them

- [x] 1.1 [medium] `Conditions.hours(variables)` takes a required list of variables and returns the sorted union of the hours of only those variables' filled series; the existing callers in `tests/test_conditions_model.py` pass their variables explicitly (design DD2) (verify: uv run pytest tests/test_conditions_model.py) (✓ uv run pytest tests/test_conditions_model.py passed)
- [x] 1.2 [medium] `Variable` gains `aerosol_optical_depth` and `pm2_5`, appended last, and `TIMELINE_VARIABLES` lists the thirteen shown variables in timeline order; a test pins `TIMELINE_VARIABLES` to the `TimelineEntry` fields that hold a variable's value (design DD1) (verify: uv run pytest tests/test_conditions_model.py) (✓ uv run pytest tests/test_conditions_model.py passed)
- [x] 1.3 [medium] The timeline takes its keys and its hours from `TIMELINE_VARIABLES` only: an `aerosol_optical_depth` series that runs two days past the shown series adds no entry, a snapshot whose only series are `aerosol_optical_depth` and `pm2_5` serializes byte-identical to the empty-conditions document, and adding or changing those two series leaves any document byte-identical (night-verdict spec) (verify: uv run pytest tests/test_producer_timeline.py) (✓ uv run pytest tests/test_producer_timeline.py passed)

## 2. The air-quality provider [depends-on: 1]

- [x] 2.1 [easy] The catalog offers `open_meteo_air_quality`, display name `Open-Meteo air quality`, needing no key, declaring `aerosol_optical_depth` then `pm2_5` and no bundle; `COLUMNS` maps both, and the pinned count of Open-Meteo specs becomes seven (verify: uv run pytest tests/test_provider_catalog.py tests/test_conditions_provider.py -k "catalog or column") (✓ uv run pytest tests/test_provider_catalog.py tests/test_conditions_provider.py -k "catalog or column" passed)
- [x] 2.2 [easy] Publishing `open_meteo_air_quality`'s health gives a `variables` attribute equal to `["aerosol_optical_depth", "pm2_5"]` (ha-delivery spec) (verify: uv run pytest tests/test_health_delivery.py) (✓ uv run pytest tests/test_health_delivery.py passed)
- [x] 2.3 [medium] An `OpenMeteoProvider` with the air-quality spec requests `https://air-quality-api.open-meteo.com/v1/air-quality`, chosen through `ENDPOINTS` by the spec's key, with `hourly=aerosol_optical_depth,pm2_5`, `forecast_days=2`, `timezone=UTC`, and no `wind_speed_unit` or `models`; the forecast providers' requests are unchanged (design DD3) (verify: uv run pytest tests/test_conditions_provider.py -k air_quality) (✓ uv run pytest tests/test_conditions_provider.py -k air_quality passed)
- [x] 2.4 [medium] Parsing the recorded fixture `tests/fixtures/open_meteo_air_quality.json` (latitude 51.5, longitude -0.12, `forecast_days=2`, `timezone=UTC`, saved as returned) carries each hour's aerosol optical depth and PM2.5 as reported, a blank aerosol value leaves that hour's PM2.5 present, and the issue time is the fetch time (conditions spec) (verify: uv run pytest tests/test_conditions_provider.py -k air_quality) (✓ uv run pytest tests/test_conditions_provider.py -k air_quality passed)
- [ ] 2.5 [easy] `build_provider(["open_meteo_air_quality"])` builds the air-quality fetcher, and a composite fetch through it fills `aerosol_optical_depth` and `pm2_5` series keyed `open_meteo_air_quality` (verify: uv run pytest tests/test_conditions_provider.py -k air_quality)

## 3. Default list and documentation [depends-on: 2]

- [ ] 3.1 [easy] With no `conditions` block or a null `providers`, the order is `open_meteo`, `seven_timer`, `open_meteo_air_quality`, read from one `DEFAULT_PROVIDERS` constant; `[open_meteo_hrrr, open_meteo_air_quality]` is accepted, and `[open_meteo_air_quality]` alone fails the keyless cloud-cover rule (design DD4) (verify: uv run pytest tests/test_config.py)
- [ ] 3.2 [easy] The README names `open_meteo_air_quality` in the provider table and the default list, gives its two variables and their units, and says nothing reads them yet and the timeline does not show them (verify: uv run pytest tests/test_docs.py)
- [ ] 3.3 [easy] `docs/night-timeline.md` says the timeline covers every hour a provider returned for a variable it shows, and that the air-quality variables never add an hour (verify: uv run pytest tests/test_timeline_docs.py)

## 4. Integration [depends-on: 3]

- [ ] 4.1 [medium] The full gate passes with the new default list, including the golden verdicts and the service tests, with no network access (verify: mise run check)

## Deviations Ledger

- 1.2: `TimelineEntry` forbids extra keys, so 1.2 could not stay green with the timeline spreading every `Variable`. The timeline's keys moved to `TIMELINE_VARIABLES` in 1.2; its hours follow in 1.3. The old pin in `tests/test_provider_catalog.py`, that every variable is a timeline key, is removed: the new pin in `tests/test_conditions_model.py` replaces it, and the conditions spec now says a variable key need not be a timeline key.
- 2.1: two pieces of DD3 landed here rather than in 2.3 and 2.5. `build_provider` registers `open_meteo_air_quality`, because `test_each_fetcher_points_at_its_catalog_spec` builds every catalog key. `SourceReading` gains the two fields, because `parse_open_meteo` builds a reading from every `COLUMNS` entry. 2.3 and 2.5 still add their own tests.
- 2.2: the health path reads any spec's variables, so the new test passed on first run once 2.1 had added the spec. It pins the ha-delivery scenario.
- 2.4: the parse is shared and 2.1 added the reading fields, so these tests passed on first run. The fixture was recorded on 2026-11-03 and has no blank values, so the blank-aerosol test blanks one in a copy of it.
