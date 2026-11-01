## ADDED Requirements

### Requirement: The base source supplies the weather variables

For each hour the base source returns, the conditions SHALL carry, beside cloud
and gust, six weather variables: temperature, dew point, relative humidity,
wind speed, wind direction and precipitation probability. Each SHALL be marked
available or unavailable independently, following the same per-field
availability rule as the rest of the snapshot. A source that reports some or
none of them SHALL still yield a valid snapshot.

#### Scenario: Every weather variable is carried for an hour the source reports fully

- **WHEN** the base source reports, for one hour, a temperature of `12.3`, a dew point of `9.8`, a humidity of `85`, a wind speed of `14.2`, a wind direction of `230` and a precipitation probability of `35`
- **THEN** that hour in the snapshot carries each of those six values, marked available

#### Scenario: One weather variable can be absent while the others remain present

- **WHEN** the base source reports every weather variable but the dew point for an hour
- **THEN** that hour's dew point is marked unavailable
- **AND** the other five keep their values
- **AND** the absence is not reported as an error

#### Scenario: A source that reports no weather variables yields a valid snapshot

- **WHEN** the base source reports cloud cover and wind gust but none of the six weather variables
- **THEN** the snapshot is returned with cloud cover and wind gust available and all six weather variables marked unavailable

### Requirement: Weather variables are carried as reported and never judged

The weather variables SHALL be carried as the source reports them, with no
rounding or conversion: temperature and dew point in degrees Celsius, humidity
and precipitation probability in percent, wind speed in km/h and wind direction
in degrees. The verdict, the score, the confidence and the reasons SHALL NOT
read them.

#### Scenario: Values are not rounded or converted

- **WHEN** the base source reports a temperature of `12.34` and a wind speed of `14.25` for an hour
- **THEN** that hour in the snapshot carries `12.34` and `14.25`

#### Scenario: Weather variables do not change the verdict

- **WHEN** two verdicts are produced for the same pier and instant, from snapshots that differ only in the six weather variables
- **THEN** the two documents differ only in the weather keys of their `timeline` entries
