## MODIFIED Requirements

### Requirement: Each further timeline variable is exposed as an entity

On publishing, the system SHALL publish one further timeline sensor per pier, on the pier's device, for each of these keys: `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, `sun_altitude`, `moon_altitude`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability`, `cloud_cover_min` and `cloud_cover_max`. Its retained discovery payload SHALL be a valid Home Assistant sensor discovery payload. Its topic and unique identity SHALL derive from the pier identifier and the key.

#### Scenario: A timeline sensor's discovery is published

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration for each of the sixteen keys, on the pier's device, enabled by default
- **AND** each discovery topic and unique identity derive from the pier identifier and the key
- **AND** each payload validates against Home Assistant's MQTT discovery schema for a sensor

#### Scenario: Existing entities are unchanged by the timeline sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, rank, Cloud cover, narrative, health and refresh entities keep their existing topics, payloads and unique identities
- **AND** re-publishing for the same pier introduces no additional identity for any of the sixteen sensors

#### Scenario: The first eight sensors are unchanged by the weather sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, `sun_altitude` and `moon_altitude` sensors keep their existing topics, discovery payloads and unique identities
- **AND** the six weather sensors' messages come after the Moon altitude sensor's in the publish

#### Scenario: The cloud range sensors come last

- **WHEN** the adapter publishes for a pier
- **THEN** the fourteen sensors from `cloud_low` to `precipitation_probability` keep their existing topics, discovery payloads and unique identities
- **AND** the `cloud_cover_min` sensor's messages, then the `cloud_cover_max` sensor's, come after the Precipitation probability sensor's in the publish

### Requirement: Each further timeline sensor has a fixed name and unit

Each further timeline sensor SHALL carry the name and unit that the scenarios below give its key. It SHALL carry no device class, so Home Assistant never converts its state away from the unit of its forecast.

#### Scenario: Names and units follow the key

- **WHEN** the adapter publishes for a pier
- **THEN** the `cloud_low`, `cloud_mid` and `cloud_high` sensors are named Cloud low, Cloud mid and Cloud high, with the unit `%`
- **AND** the `wind_gust` sensor is named Wind gust, with the unit `km/h`
- **AND** the `sun_altitude` and `moon_altitude` sensors are named Sun altitude and Moon altitude, with the unit `°`
- **AND** none of the sixteen discovery payloads carries a `device_class`

#### Scenario: Seeing and Transparency carry no unit

- **WHEN** the adapter publishes for a pier
- **THEN** the `seeing` and `transparency` sensors are named Seeing and Transparency
- **AND** their discovery payloads carry no `unit_of_measurement`

#### Scenario: The weather sensors' names and units follow the key

- **WHEN** the adapter publishes for a pier
- **THEN** the `temperature` and `dew_point` sensors are named Temperature and Dew point, with the unit `°C`
- **AND** the `humidity` and `precipitation_probability` sensors are named Humidity and Precipitation probability, with the unit `%`
- **AND** the `wind_speed` sensor is named Wind speed, with the unit `km/h`
- **AND** the `wind_direction` sensor is named Wind direction, with the unit `°`

#### Scenario: The cloud range sensors' names and units follow the key

- **WHEN** the adapter publishes for a pier
- **THEN** the `cloud_cover_min` and `cloud_cover_max` sensors are named Cloud cover min and Cloud cover max, with the unit `%`
- **AND** Home Assistant gives them the entity ids `sensor.pierpressure_<pier>_cloud_cover_min` and `sensor.pierpressure_<pier>_cloud_cover_max`

### Requirement: A further timeline sensor's forecast mirrors its variable

The JSON attributes payload of each further timeline sensor SHALL carry exactly `hour` and `forecast`. `forecast` SHALL hold one `{datetime, value}` entry per timeline entry, in the timeline's order. `datetime` is the entry's `time`. `value` is the entry's value for the sensor's key as the document emits it, or null. Every publish SHALL replace the payload.

#### Scenario: The forecast array mirrors the variable's timeline values

- **WHEN** the adapter publishes a document whose timeline holds entries at 20:00 with seeing `0.62` and at 21:00 with seeing null
- **THEN** the Seeing sensor's attributes payload holds `forecast` with exactly two entries in that order: `{datetime: <20:00>, value: 0.62}` and `{datetime: <21:00>, value: null}`

#### Scenario: A weather sensor's forecast mirrors its timeline values

- **WHEN** the adapter publishes a document whose timeline holds entries at 20:00 with temperature `12.3` and at 21:00 with temperature null
- **THEN** the Temperature sensor's attributes payload holds `forecast` with exactly two entries in that order: `{datetime: <20:00>, value: 12.3}` and `{datetime: <21:00>, value: null}`

#### Scenario: A cloud range sensor's forecast mirrors its timeline values

- **WHEN** the adapter publishes a document whose timeline holds entries at 20:00 with cloud cover min `40.0` and cloud cover max `70.0`, and at 21:00 with both null
- **THEN** the Cloud cover min sensor's attributes payload holds `forecast` with exactly two entries in that order: `{datetime: <20:00>, value: 40.0}` and `{datetime: <21:00>, value: null}`
- **AND** the Cloud cover max sensor's holds `{datetime: <20:00>, value: 70.0}` and `{datetime: <21:00>, value: null}`

#### Scenario: Every sensor's forecast lines up with the timeline

- **WHEN** the adapter publishes a document whose timeline holds 48 entries
- **THEN** each of the sixteen sensors' `forecast` holds 48 entries, and the `n`th entry's `datetime` is the `n`th timeline entry's `time` for every sensor

#### Scenario: An empty timeline publishes an empty forecast

- **WHEN** the adapter publishes a document whose timeline is empty
- **THEN** each of the sixteen sensors' attributes payload holds an empty `forecast` list and `hour` null

#### Scenario: A later publish replaces the forecast

- **WHEN** the adapter publishes a document with 72 timeline entries and then one with 48 for the same pier
- **THEN** each of the sixteen sensors' retained attributes payload holds exactly the 48 entries of the second document

#### Scenario: The attributes stay under the recorder limit

- **WHEN** the adapter publishes a document whose timeline holds 120 entries with every value present
- **THEN** each of the sixteen sensors' attributes payload is smaller than 16 KiB

### Requirement: A further timeline sensor with no current-hour value shows unknown and stays available

When no timeline entry has the current hour, or that entry's value for a sensor's key is null, the adapter SHALL publish that sensor's state as `None`, which Home Assistant shows as unknown. It SHALL NOT publish `0`, an empty value or an earlier value instead. Each further timeline sensor SHALL be available exactly when the process is online, so its `forecast` stays readable.

#### Scenario: A null current-hour value renders unknown for that sensor only

- **WHEN** the adapter publishes a document generated at 23:30 whose 23:00 entry has transparency null and cloud high `5.0`
- **THEN** the adapter publishes the retained Transparency state `None`
- **AND** the retained Cloud high state `5.0`

#### Scenario: A null current-hour weather value renders unknown for that sensor only

- **WHEN** the adapter publishes a document generated at 23:30 whose 23:00 entry has dew point null and temperature `12.3`
- **THEN** the adapter publishes the retained Dew point state `None`
- **AND** the retained Temperature state `12.3`

#### Scenario: An hour with one cloud forecast renders the cloud range unknown

- **WHEN** the adapter publishes a document generated at 23:30 whose 23:00 entry has cloud cover `40.0` and cloud cover min and max null
- **THEN** the adapter publishes the retained Cloud cover min and Cloud cover max states `None`
- **AND** the retained Cloud cover state `40.0`

#### Scenario: A missing current hour renders unknown

- **WHEN** the adapter publishes a document generated at 23:30 whose timeline has no entry at 23:00
- **THEN** the adapter publishes the retained state `None` for each of the sixteen sensors, including Sun altitude and Moon altitude
- **AND** a retained attributes payload for each with `hour` null and a `forecast` entry for every timeline hour
- **AND** each sensor's discovery payload makes it available exactly when the process is online, with no condition on the current hour

#### Scenario: An empty timeline renders unknown

- **WHEN** the adapter publishes a document whose timeline is empty
- **THEN** the adapter publishes the retained state `None` for each of the sixteen sensors
- **AND** each sensor stays available while the process is online
