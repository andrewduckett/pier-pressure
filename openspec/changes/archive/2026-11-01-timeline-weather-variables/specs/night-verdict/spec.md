## MODIFIED Requirements

### Requirement: A timeline entry has a fixed flat shape

Each timeline entry SHALL carry exactly these keys, always present and in this order: `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability`. `time` SHALL be the top of the hour, emitted like every other document timestamp. The six weather keys come last, so every key that preceded them keeps its position.

#### Scenario: A read-back entry equals the emitted one

- **WHEN** a document with a timeline is serialized to JSON and read back
- **THEN** every entry's keys, order and values are unchanged

#### Scenario: The keys before the weather keys keep their positions

- **WHEN** a document with a timeline is serialized to JSON
- **THEN** each entry's first ten keys are `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, in that order
- **AND** the six weather keys follow them in the order `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability`

## ADDED Requirements

### Requirement: Entry weather values carry the base source's reading for the hour

`temperature` and `dew_point` SHALL be degrees Celsius, `humidity` and `precipitation_probability` percent, `wind_speed` km/h and `wind_direction` degrees, each carried exactly as the base source's reading for that hour, with no rounding or conversion. Each SHALL be null when the base source lacks the hour or the value.

#### Scenario: Weather values pass through unchanged

- **WHEN** the base source reports, for an hour, a temperature of `12.3`, a dew point of `9.8`, a humidity of `85.0`, a wind speed of `14.2`, a wind direction of `230.0` and a precipitation probability of `35.0`
- **THEN** that entry's `temperature` is `12.3`, `dew_point` `9.8`, `humidity` `85.0`, `wind_speed` `14.2`, `wind_direction` `230.0` and `precipitation_probability` `35.0`

#### Scenario: An hour the base source lacks carries null weather values

- **WHEN** an hour is present in the secondary source but absent from the base source
- **THEN** that entry's six weather keys are all null
- **AND** its `seeing` and `transparency` carry the secondary source's values

#### Scenario: A weather value the base source lacks is null on its own

- **WHEN** the base source reports every weather variable but the dew point for an hour
- **THEN** that entry's `dew_point` is null
- **AND** its other five weather keys carry the reported values
