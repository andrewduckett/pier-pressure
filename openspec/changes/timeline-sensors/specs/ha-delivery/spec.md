## ADDED Requirements

### Requirement: Each further timeline variable is exposed as an entity

On publishing, the system SHALL publish retained MQTT discovery configuration for one timeline sensor per pier for each of the keys `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, `sun_altitude` and `moon_altitude`, on the pier's device. Each payload SHALL be a valid Home Assistant sensor discovery payload, with a topic and unique identity derived from the pier identifier and the key.

#### Scenario: A timeline sensor's discovery is published

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration for each of the eight keys, on the pier's device, enabled by default
- **AND** each discovery topic and unique identity derive from the pier identifier and the key
- **AND** each payload validates against Home Assistant's MQTT discovery schema for a sensor

#### Scenario: Existing entities are unchanged by the timeline sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, rank, Cloud cover, narrative, health and refresh entities keep their existing topics, payloads and unique identities
- **AND** re-publishing for the same pier introduces no additional identity for any of the eight sensors

### Requirement: Each timeline sensor has a fixed name and unit

Each timeline sensor SHALL carry the name and unit its key is given in the scenarios below, and no device class, so Home Assistant never converts its state away from the unit of its forecast.

#### Scenario: Names and units follow the key

- **WHEN** the adapter publishes for a pier
- **THEN** the `cloud_low`, `cloud_mid` and `cloud_high` sensors are named Cloud low, Cloud mid and Cloud high, with the unit `%`
- **AND** the `wind_gust` sensor is named Wind gust, with the unit `km/h`
- **AND** the `sun_altitude` and `moon_altitude` sensors are named Sun altitude and Moon altitude, with the unit `°`
- **AND** none of the eight discovery payloads carries a `device_class`

#### Scenario: Seeing and Transparency carry no unit

- **WHEN** the adapter publishes for a pier
- **THEN** the `seeing` and `transparency` sensors are named Seeing and Transparency
- **AND** their discovery payloads carry no `unit_of_measurement`

### Requirement: A timeline sensor's forecast mirrors its variable

The JSON attributes payload of each timeline sensor SHALL carry exactly `hour` and `forecast`. `forecast` SHALL hold one `{datetime, value}` entry per timeline entry, in the timeline's order: `datetime` is the entry's `time` and `value` is that entry's value for the sensor's key as the document emits it, null when null. Every publish SHALL replace the payload.

#### Scenario: The forecast array mirrors the variable's timeline values

- **WHEN** the adapter publishes a document whose timeline holds entries at 20:00 with seeing `0.62` and at 21:00 with seeing null
- **THEN** the Seeing sensor's attributes payload holds `forecast` with exactly two entries in that order: `{datetime: <20:00>, value: 0.62}` and `{datetime: <21:00>, value: null}`

#### Scenario: Every sensor's forecast lines up with the timeline

- **WHEN** the adapter publishes a document whose timeline holds 48 entries
- **THEN** each of the eight sensors' `forecast` holds 48 entries, and the `n`th entry's `datetime` is the `n`th timeline entry's `time` for every sensor

#### Scenario: An empty timeline publishes an empty forecast

- **WHEN** the adapter publishes a document whose timeline is empty
- **THEN** each of the eight sensors' attributes payload holds an empty `forecast` list and `hour` null

#### Scenario: A later publish replaces the forecast

- **WHEN** the adapter publishes a document with 72 timeline entries and then one with 48 for the same pier
- **THEN** each of the eight sensors' retained attributes payload holds exactly the 48 entries of the second document

#### Scenario: The attributes stay under the recorder limit

- **WHEN** the adapter publishes a document whose timeline holds 120 entries with every value present
- **THEN** each of the eight sensors' attributes payload is smaller than 16 KiB

### Requirement: A timeline sensor's hour names the entry its state comes from

Each timeline sensor's `hour` attribute SHALL be the `time` of the timeline entry its state comes from, or null when its state is unknown. It SHALL depend only on the sensor's own key.

#### Scenario: The hour is judged per variable

- **WHEN** the adapter publishes a document generated at 23:30 whose 23:00 entry has cloud low `20.0` and seeing null
- **THEN** the Cloud low sensor's attributes payload has `hour` equal to that entry's `time`
- **AND** the Seeing sensor's attributes payload has `hour` null

### Requirement: A timeline sensor's state is its variable's current-hour value

The state of each timeline sensor SHALL be its key's value in the timeline entry whose hour contains the document's generation timestamp, written as the document emits the number. The state is as fresh as the last recompute, so it can lag by up to one recompute interval. For the Sun altitude and Moon altitude sensors, it is the altitude at the start of that hour, not at the moment of publishing.

#### Scenario: The state is the current hour's value

- **WHEN** the adapter publishes a document generated at 23:30 whose 23:00 entry has wind gust `18.4` and moon altitude `-12.345`
- **THEN** the Wind gust sensor's state is `18.4`
- **AND** the Moon altitude sensor's state is `-12.345`

### Requirement: A timeline sensor with no current-hour value shows unknown and stays available

When no timeline entry has the current hour, or that entry's value for a sensor's key is null, that sensor's state SHALL be published as `None`, which Home Assistant shows as unknown, rather than `0`, an empty value or an earlier value. Each timeline sensor SHALL be available exactly when the process is online, so its `forecast` stays readable when the current hour has no value.

#### Scenario: A null current-hour value renders unknown for that sensor only

- **WHEN** the adapter publishes a document generated at 23:30 whose 23:00 entry has transparency null and cloud high `5.0`
- **THEN** the adapter publishes the retained Transparency state `None`
- **AND** the retained Cloud high state `5.0`

#### Scenario: A missing current hour renders unknown

- **WHEN** the adapter publishes a document generated at 23:30 whose timeline has no entry at 23:00
- **THEN** the adapter publishes the retained state `None` for each of the eight sensors
- **AND** a retained attributes payload for each with `hour` null and a `forecast` entry for every timeline hour
- **AND** each sensor's discovery payload makes it available exactly when the process is online, with no condition on the current hour

#### Scenario: An empty timeline renders unknown

- **WHEN** the adapter publishes a document whose timeline is empty
- **THEN** the adapter publishes the retained state `None` for each of the eight sensors
- **AND** each sensor stays available while the process is online
