## Why

The timeline carries cloud, gust, seeing and transparency, but not the weather
a pier owner also reads off a forecast: temperature, dew point, humidity, wind
speed and direction, and the chance of rain. Open-Meteo returns all six free in
the request PierPressure already makes, and the timeline and per-variable
sensor patterns from #133 and #134 make each one a request parameter, a reading
field, a timeline field and a sensor row. Adding them together now keeps the
request and the document in step, and gives the dew-risk and rain work (#98)
its raw material.

## What Changes

- The Open-Meteo request asks for `temperature_2m`, `dew_point_2m`,
  `relative_humidity_2m`, `wind_speed_10m`, `wind_direction_10m` and
  `precipitation_probability`, and the parser maps each onto the base reading
  for that hour, independently optional (D5).
- `SourceReading` and `BaseHour` gain six optional fields; the base group
  carries them to the core as passthrough data. No gate or score reads them (D8).
- Each timeline entry gains six keys after `transparency`, in this order:
  `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`,
  `precipitation_probability` (D2, D6). Values pass through unrounded (D4), in
  °C, °C, %, km/h, ° and % (D3). This is additive growth of the verdict
  document; no existing key moves or changes meaning.
- Six new timeline sensors on the pier device, after Moon altitude: Temperature,
  Dew point, Humidity, Wind speed, Wind direction and Precipitation probability,
  each with the current-hour state and the `forecast` array, a unit and no
  device class (D1, D7).
- README and `docs/night-timeline.md` list the six sensors. The golden verdict
  fixture is regenerated once for the grown document (D9).
- Out of scope: any gate or score term using these values (#98), and rows for
  them on the night dashboard (D8).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: the base source also supplies temperature, dew point,
  humidity, wind speed, wind direction and precipitation probability per hour,
  each stamped available or unavailable like every other field.
- `night-verdict`: the timeline entry's fixed flat shape grows by the six keys,
  and a requirement states their units, source and passthrough rule.
- `ha-delivery`: the further-timeline-sensor requirements cover fourteen keys
  instead of eight, with the six new names and units.

## Impact

- Code: `pierpressure/conditions/open_meteo.py` (request and parser),
  `pierpressure/conditions/provider.py` (`SourceReading`, `assemble_snapshot`),
  `pierpressure/core/conditions.py` (`BaseHour`), `pierpressure/core/model.py`
  (`TimelineEntry`), `pierpressure/core/producer.py` (`_timeline`),
  `pierpressure/delivery/mqtt.py` (`TIMELINE_SENSORS`).
- Contract: six additive keys on every timeline entry; six new retained
  discovery, state and attributes topics per pier. Nothing existing changes.
- Tests: the Open-Meteo fixture and parser tests, the timeline and timeline
  sensor tests, the message-order pin in `tests/test_rank_targets.py`, the
  golden verdict fixture, and the docs guards.
- Docs: `README.md` entity, topic and removal rows; `docs/night-timeline.md`
  sensor table.
- Dependencies: none added. Open-Meteo remains the only source for these fields.
