## 1. The weather variables reach the timeline entry

- [x] 1.1 [easy] `parse_open_meteo` carries `temperature_2m`, `dew_point_2m`, `relative_humidity_2m`, `wind_speed_10m`, `wind_direction_10m` and `precipitation_probability` onto six new optional `SourceReading` fields, unrounded; a null element leaves that hour's field `None`, and an array absent from `hourly` leaves the field `None` for every hour while the others keep their values. Extend `tests/fixtures/open_meteo.json` with the six arrays and their `hourly_units`, including one null (verify: `uv run pytest tests/test_conditions_provider.py -k open_meteo`) (✓ `uv run pytest tests/test_conditions_provider.py -k open_meteo` passed)
- [x] 1.2 [easy] `OpenMeteoProvider.fetch` asks Open-Meteo for the six variables in its `hourly` parameter, with `wind_speed_unit` still `kmh`, proven through a mock HTTP transport that records the request (verify: `uv run pytest tests/test_conditions_provider.py -k fetch`) (✓ `uv run pytest tests/test_conditions_provider.py -k fetch` passed)
- [x] 1.3 [easy] `assemble_snapshot` copies the six reading fields onto six new optional `BaseHour` fields, each `None` when the reading lacks it (verify: `uv run pytest tests/test_conditions_provider.py -k assemble`) (✓ `uv run pytest tests/test_conditions_provider.py -k assemble` passed)
- [ ] 1.4 [medium] `TimelineEntry` carries `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction` and `precipitation_probability` as plain `float | None` after `transparency`, so a serialized entry's keys are the ten existing ones then the six in that order, present when null and unrounded. Extend `TIMELINE_ENTRY_KEY_ORDER` and move the extra-key probe to a key outside the schema (verify: `uv run pytest tests/test_model.py -k timeline_entry`)
- [ ] 1.5 [easy] `produce_verdict` copies the base hour's six weather values onto each entry: unchanged when present, null for a weather value the base source lacks, and all six null for an hour the base source lacks while seeing and transparency stay (verify: `uv run pytest tests/test_producer_timeline.py`)
- [ ] 1.6 [easy] Regenerate the golden documents with `PP_WRITE_GOLDENS=1 uv run pytest tests/test_golden_verdict.py`, and check the diff is exactly six null keys per timeline entry before committing (verify: `uv run pytest tests/test_golden_verdict.py tests/test_determinism.py`)

## 2. The weather variables reach Home Assistant [depends-on: 1]

- [ ] 2.1 [medium] `TIMELINE_SENSORS` gains six rows after Moon altitude, named Temperature, Dew point, Humidity, Wind speed, Wind direction and Precipitation probability, with units `°C`, `°C`, `%`, `km/h`, `°`, `%`, the design's icons and no `device_class`; each publishes discovery, current-hour state and the `forecast` array like the other sensors. Widen `NEW_KEYS`, `NULLABLE_KEYS`, the names-units-icons pin and the unit pin in `tests/test_timeline_sensors.py`, and fill the six fields in `make_timeline` (verify: `uv run pytest tests/test_timeline_sensors.py tests/test_cloud_cover.py tests/test_rank_targets.py tests/test_publish.py`)

## 3. The docs name the six sensors [depends-on: 1]

- [ ] 3.1 [parallel] [easy] `README.md` lists the six sensors with their units in the timeline sensor row, in the discovery-topic pattern, in the timeline topic row and in the "Removing the entities" loop; `docs/night-timeline.md` adds six rows to the sensor table and names the six under "Why the Verdict sensor leaves the timeline out". Extend the key, name and unit guards in `tests/test_timeline_docs.py`, including `°C` (verify: `uv run pytest tests/test_timeline_docs.py tests/test_docs.py`)

## 4. Everything together [depends-on: 2, 3]

- [ ] 4.1 [easy] The whole gate is green: lint, types and the full suite, including the dashboard doc check and the core boundary test (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
