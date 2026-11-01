## Context

The path a base-source variable takes is already laid end to end for cloud and
gust. `parse_open_meteo` reads each hourly array index-guarded into a
`SourceReading`; `assemble_snapshot` copies the reading onto a `BaseHour`;
`_timeline` in `pierpressure/core/producer.py` copies the base hour's fields
onto a `TimelineEntry`; `TIMELINE_SENSORS` in `pierpressure/delivery/mqtt.py`
turns each entry key into a sensor through one generic code path (timeline-
sensors DD1). Every step is a flat field copy with `None` for absent.

`TimelineEntry` forbids extra keys and declares its fields in emission order,
so new keys go at the end of the class. `Degrees` and `Quality` are rounding
validators; `cloud_cover` and `wind_gust` are plain `float | None` and pass
through unrounded.

The pins that will move: `tests/test_model.py` holds the entry key order in
`TIMELINE_ENTRY_KEY_ORDER` and probes the extra-key guard with `dew_point`;
`tests/test_timeline_sensors.py` lists the eight further keys and their names,
units and icons, and a literal list of the keys that carry a unit;
`tests/test_timeline_docs.py` lists the keys, names and units the docs must
mention; the golden documents under `tests/fixtures/golden/expected/` hold the
serialized timeline. The message
pin in `tests/test_rank_targets.py` filters by `TIMELINE_SENSORS`, so it
follows the table without an edit. `make_timeline` in `tests/conftest.py`
builds entries with every field filled.

## Goals / Non-Goals

**Goals:**

- Each new variable rides the existing copy chain and the existing sensor
  table. No new mechanism.
- Nothing before the new keys or the new sensors changes: existing entry keys,
  topics, payloads, names and goldens stay as they are, apart from the six
  added keys in each golden entry.

**Non-Goals:**

- No gate, score or confidence term reads the new fields (#98).
- No dashboard rows, no change to `docs/night-dashboard.md`.
- No unit conversion or user unit setting.
- No change to `forecast_days` or any other request parameter.

## Test Seams

- **Primary test seam:** `MqttDelivery.publish_verdict` on `FakeMqttClient`,
  read back through the published topics, in `tests/test_timeline_sensors.py`
  with the six keys added to its parametrized key lists.
- **Existing seams reused:** `parse_open_meteo` against
  `tests/fixtures/open_meteo.json` and `assemble_snapshot` in
  `tests/test_conditions_provider.py`; `TimelineEntry` in `tests/test_model.py`
  for the entry keys and their order; `produce_verdict` in
  `tests/test_producer_timeline.py` for the passthrough from a `BaseHour`;
  `tests/test_golden_verdict.py` for the regenerated goldens;
  `tests/test_timeline_docs.py` for the docs guards.

## Scrutiny Tier & Blast Radius

- **Tier:** medium. Every step follows an established pattern, but the change
  adds keys to the frozen document and entities and topics to the frozen
  delivery surface, so names and order cannot change once released.
- **Blast radius:** `pierpressure/conditions/open_meteo.py`,
  `pierpressure/conditions/provider.py`, `pierpressure/core/conditions.py`,
  `pierpressure/core/model.py`, `pierpressure/core/producer.py`,
  `pierpressure/delivery/mqtt.py`; `tests/test_model.py` and the other test
  pins named in Context; the golden fixtures; `README.md` and
  `docs/night-timeline.md`. The scoring, ranking and astronomy modules are
  untouched.

## Decisions

### DD1: The request and parser grow by six arrays, read like the cloud components

The Open-Meteo `hourly` parameter gains `temperature_2m`, `dew_point_2m`,
`relative_humidity_2m`, `wind_speed_10m`, `wind_direction_10m` and
`precipitation_probability`. `wind_speed_unit=kmh`, already set for gusts,
makes wind speed km/h; the other units are Open-Meteo's defaults (D3). The
parser reads each array index-guarded and `None`-tolerant, exactly as it reads
`cloud_cover_low`, so a short or null array leaves that field absent for the
hour and nothing else (D5).

- **Alternative:** a second request for the weather variables. Rejected: one
  more failure mode and issue time for data that comes free in the same call.

### DD2: Six optional fields appended to `SourceReading`, `BaseHour` and `TimelineEntry`

Each class gains `temperature`, `dew_point`, `humidity`, `wind_speed`,
`wind_direction` and `precipitation_probability`, all `float | None = None`,
appended after the existing fields in that order (D2, D6). `assemble_snapshot`
and `_timeline` copy them field by field like `cloud_low`. On `TimelineEntry`
they are plain `float | None`, not `Degrees`, because the values pass through
unrounded (D4); `Degrees` would round wind direction to the angle precision.

- **Alternative:** a nested `weather` object on the entry. Rejected: the entry
  is flat by design so a sensor can read any variable by key (timeline-sensors
  DD4), and a nested object would need a second code path in the adapter.
- **Alternative:** carry the fields only from the reading to the entry, skipping
  `BaseHour`. Rejected: `BaseHour` is the only input the pure core sees, and the
  timeline is built inside the core.

### DD3: Six rows appended to `TIMELINE_SENSORS`

After the Moon altitude row, in this order:

| key | name | unit | icon |
|---|---|---|---|
| `temperature` | Temperature | `°C` | `mdi:thermometer` |
| `dew_point` | Dew point | `°C` | `mdi:thermometer-water` |
| `humidity` | Humidity | `%` | `mdi:water-percent` |
| `wind_speed` | Wind speed | `km/h` | `mdi:weather-windy` |
| `wind_direction` | Wind direction | `°` | `mdi:compass` |
| `precipitation_probability` | Precipitation probability | `%` | `mdi:weather-rainy` |

Each name slugs to its key, so the entity id is
`sensor.pierpressure_<pier>_<key>`. No `device_class` (D1); the generic builder
never sets one. Appending keeps the first nine sensors' publish positions
(timeline-sensors DD6). Icons are cosmetic.

### DD4: The recorded parser fixture gains the six arrays; the golden input does not

`tests/fixtures/open_meteo.json` gains the six hourly arrays and their
`hourly_units`, including a null value, so the parser tests prove the null
path. A further parser test feeds a payload with one weather array absent from
`hourly`, and asserts that field is `None` for every hour while the others keep
their values, so the index guard is proven for the absent-array case too. `tests/fixtures/golden/open_meteo_full.json` stays as
recorded, so the regenerated goldens carry the six keys as null in every entry.
The passthrough of real values is proven in `tests/test_producer_timeline.py`,
with a `BaseHour` built in the test.

- **Alternative:** add the arrays to the golden input too. Rejected: it is a
  recording, and invented values would make the goldens less honest than
  nulls that say the recording lacked them.

### DD5: Goldens are regenerated once, and the diff is checked by eye

Run `PP_WRITE_GOLDENS=1 uv run pytest tests/test_golden_verdict.py` after the
core change. The reviewer checks that each expected document differs only by
six null keys per timeline entry.

### DD6: Test pins widen to the fourteen keys

- `tests/test_model.py`: `TIMELINE_ENTRY_KEY_ORDER` gains the six keys in
  order, which pins the modified fixed-shape scenario. The extra-key probe in
  `test_timeline_entry_rejects_unknown_keys` moves from `dew_point` to a key
  outside the schema, such as `pressure`.
- `tests/test_timeline_sensors.py`: `NEW_KEYS` gains the six keys and
  `NULLABLE_KEYS` includes them, so every parametrized scenario, including the
  null-value ones, runs over them. The names-units-icons pin gains six rows,
  and the unit pin `test_a_timeline_discovery_carries_its_unit` gains the six
  key-unit pairs.
- `tests/test_timeline_docs.py`: its key and name lists gain the six, and the
  unit check gains `°C`.
- `tests/conftest.py`: `make_timeline` fills the six fields, so size and
  forecast-length scenarios run with every value present.

### DD7: Documentation

- `README.md`: the combined timeline sensor row adds the six sensors with
  their units; the discovery-topic pattern and the timeline topic row list the
  six keys; the "Removing the entities" loop gains six entries.
- `docs/night-timeline.md`: six rows in the sensor table; the list of sensors
  under "Why the Verdict sensor leaves the timeline out" names them.
- The `mqtt.py` module docstring needs no change: its topic table uses `<var>`.

## Risks / Trade-offs

- [Adding a key to `TimelineEntry` in the wrong place reorders the frozen
  entry] → `TIMELINE_ENTRY_KEY_ORDER` in `tests/test_model.py` pins the first
  ten keys and the six after them.
- [Open-Meteo omits an array for a location or model, such as
  `precipitation_probability` outside its coverage] → The index guard leaves
  that field `None`; the sensor shows unknown and its forecast is all null.
- [Each recompute sends 18 more retained messages per pier] → Each is under
  the 16 KiB limit the spec scenario checks, once per recompute interval.
- [A dashboard that reads `forecast` by position assumes the first ten keys]
  → The entry stays a map, not a list; the forecast arrays are per sensor.
- [Wind direction's forecast array charts poorly as a line] → Accepted. The
  story delivers the data; a card is a later choice.

## Migration & Rollback

No data changes shape. On the first publish after upgrade, Home Assistant
creates the six sensors from their retained discovery messages, and the
verdict document carries six more keys per timeline entry that any reader of
the old shape can ignore. To roll back, deploy the earlier image; the six
retained discovery messages stay on the broker, so the entities stay too.
They share the process's availability topic, so they stay available and show
their last retained state and forecast, which no longer update. Clear them
with the README's "Removing the entities" loop.
