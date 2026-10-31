## Why

The timeline reaches Home Assistant only through the Cloud cover sensor, so a
chart card can draw one row of the night strip and no more. The dashboard story
(#135) needs a sensor for every row it draws, and the Cloud cover sensor (#133)
has proved the pattern, so this change repeats it for the rest of the timeline.

## What Changes

- Eight new sensors on each pier's device, one per timeline key that has none
  yet (D1): Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency,
  Sun altitude and Moon altitude. Their names match the timeline keys, so each
  entity id ends in its key (D4).
- Each new sensor behaves exactly like Cloud cover (D2): retained discovery,
  available exactly when the process is online, a state that is its own
  variable's value for the current hour or unknown, and attributes `hour` and
  `forecast` judged per variable (D3).
- Units: `%` for the cloud layers, km/h for Wind gust, `°` for the altitudes,
  and no unit for Seeing and Transparency, which publish the timeline's 0 to 1
  values unchanged (D5, D6, D7). No sensor has a device class, so Home Assistant
  never converts a state away from its forecast array's unit.
- The README lists the new entities and topics. `docs/night-timeline.md`
  describes every sensor, explains that an altitude state is for the start of
  the current hour (D8), and names all nine forecast sensors in the recorder
  exclusion example (D10).
- Cloud cover and every other entity, topic and mapping are unchanged (D9). The
  verdict document does not change. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: adds requirements for the eight timeline sensors' discovery,
  attributes and state, following the existing Cloud cover requirements.

## Impact

- **Code:** `pierpressure/delivery/mqtt.py` (topic helpers, discovery builders,
  state and attribute functions, `publish_verdict`); the Cloud cover helpers may
  be generalized so all nine sensors share one path, with Cloud cover's output
  unchanged.
- **Tests:** the MQTT delivery tests, with each new discovery payload validated
  against `SENSOR_SCHEMA` in `pierpressure/delivery/ha_schema.py` (D11).
- **Docs:** `README.md` entity and topic tables; `docs/night-timeline.md`.
- **MQTT surface:** sixteen new retained topics per pier (state and attributes
  for eight sensors) and eight new discovery topics. No existing topic changes.
- **Dependencies:** none.
