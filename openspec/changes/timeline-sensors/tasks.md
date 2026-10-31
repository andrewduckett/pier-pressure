## 1. Timeline sensors in the MQTT adapter

- [ ] 1.1 [medium] A module-level table in `pierpressure/delivery/mqtt.py` lists the nine timeline sensors (key, name, unit or none, icon), Cloud cover first, with the names, units and icons of design DD7 and the spec; tests assert every key is a `TimelineEntry` field typed `float` or `float | None` once `Annotated` is unwrapped, and every name lower-cased with spaces as underscores equals its key (design DD1, DD4) (verify: uv run pytest tests/test_timeline_sensors.py -q)
- [ ] 1.2 [medium] A generic discovery builder and topic helpers give each table row a retained discovery payload on the pier's device with topic and unique id from the pier id and key, its name and unit, no `device_class`, and availability only on the shared online topic; each of the eight new payloads validates against `{**SENSOR_SCHEMA, "additionalProperties": False}`, Seeing and Transparency carry no `unit_of_measurement`, and the Cloud cover functions become thin delegates whose payload equals its literal pre-change value (design DD2, DD3) (verify: uv run pytest tests/test_timeline_sensors.py tests/test_cloud_cover.py -q)
- [ ] 1.3 [medium] A sensor's state and `hour` come from its own key in the current-hour entry: the current-hour lookup no longer checks `cloud_cover`, a null value for one key publishes `None` and `hour` null for that sensor only (tested over the six nullable keys), and a missing current hour or an empty timeline publishes `None` for all eight, altitudes included (design DD5) (verify: uv run pytest tests/test_timeline_sensors.py tests/test_cloud_cover.py -q)
- [ ] 1.4 [easy] A sensor's attributes are exactly `hour` and `forecast`, one `{datetime, value}` per timeline entry for its own key with nulls kept; with 48 entries every sensor's forecast lines up hour for hour, and with 120 full entries each payload is under 16 KiB (verify: uv run pytest tests/test_timeline_sensors.py -q)
- [ ] 1.5 [medium] `publish_verdict` sends each table row's discovery, state and attributes, retained, in table order at Cloud cover's current place, and a later publish replaces each sensor's forecast; the filter in `test_existing_entities_publish_the_same_topics_and_payloads` widens to the eight new sensors' topics, a new test pins the order and payloads of the nine sensors' messages, and the `mqtt.py` docstring topic table gains the timeline sensor rows with the placeholder `<var>` (design DD6) (verify: uv run pytest tests/test_timeline_sensors.py tests/test_rank_targets.py tests/test_cloud_cover.py -q)

## 2. Documentation [depends-on: 1]

- [ ] 2.1 [easy] The README lists the eight new sensors in one entity row, adds a topic row for them beside Cloud cover's literal row, names the keys in the discovery-topic pattern, writes the eight entries into the "Removing the entities" loop without brace expansion, and says the `timeline` row is delivered on the timeline sensors; `tests/test_timeline_docs.py` checks each, and its Cloud cover checks stay green (design DD8) (verify: uv run pytest tests/test_timeline_docs.py -q)
- [ ] 2.2 [easy] `docs/night-timeline.md` describes all nine timeline sensors in a table of entity ids, units and state meaning; says an altitude state is for the start of the hour, can trail the live sky by up to one hour plus one recompute interval, and shows unknown when no source returned the current hour; names all nine sensors where it said "starting with Cloud cover"; and lists all nine entities in the recorder example with a note that each pier has its own; `tests/test_timeline_docs.py` checks each (design DD8) (verify: uv run pytest tests/test_timeline_docs.py -q)

## 3. Integration [depends-on: 2]

- [ ] 3.1 [easy] The full gate passes: lint, strict types and the whole test suite (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
