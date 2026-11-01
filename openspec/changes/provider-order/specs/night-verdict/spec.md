## ADDED Requirements

### Requirement: Freshness follows the cloud-cover series

The freshness that confidence reads SHALL be the issue time of the `cloud_cover`
series: the time the provider that filled cloud cover gave for its data. The
issue time of any other series SHALL NOT change the confidence. When no series
fills cloud cover, freshness SHALL be at its floor.

#### Scenario: A stale seeing series does not lower confidence

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in the issue time of the `seeing` series
- **THEN** the two documents are byte-identical

#### Scenario: A stale cloud series lowers confidence

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in the issue time of the `cloud_cover` series, one issued an hour before the instant and one eleven hours before
- **THEN** the confidence value of the second is lower than the first

### Requirement: Entry weather values carry the filling provider's reading for the hour

`temperature` and `dew_point` SHALL be degrees Celsius, `humidity` and `precipitation_probability` percent, `wind_speed` km/h and `wind_direction` degrees, each carried exactly as its series holds it for that hour, with no rounding or conversion. Each SHALL be null when its series lacks the hour or the value, or no provider filled it.

#### Scenario: Weather values pass through unchanged

- **WHEN** the weather series hold, for an hour, a temperature of `12.3`, a dew point of `9.8`, a humidity of `85.0`, a wind speed of `14.2`, a wind direction of `230.0` and a precipitation probability of `35.0`
- **THEN** that entry's `temperature` is `12.3`, `dew_point` `9.8`, `humidity` `85.0`, `wind_speed` `14.2`, `wind_direction` `230.0` and `precipitation_probability` `35.0`

#### Scenario: An hour the weather series lack carries null weather values

- **WHEN** an hour is present in the `seeing` and `transparency` series but absent from every weather series
- **THEN** that entry's six weather keys are all null
- **AND** its `seeing` and `transparency` carry their series' values

#### Scenario: A weather value the provider lacks is null on its own

- **WHEN** the provider that filled the weather series reports every weather variable but the dew point for an hour
- **THEN** that entry's `dew_point` is null
- **AND** its other five weather keys carry the reported values

## MODIFIED Requirements

### Requirement: The document carries an hourly timeline

The verdict document SHALL carry a `timeline` list: the hourly series of sky and weather for the pier. The list SHALL hold one entry per clock hour across the union of the hours every series in the conditions covers, including hours already past, sorted by hour ascending, with no hour repeated. The list SHALL be empty, never absent, when no provider returned rows.

#### Scenario: The timeline spans the union of both providers' hours

- **WHEN** a verdict is produced with a cloud-cover series covering 00:00 to 23:00 on one day and a seeing series covering 12:00 on that day to 11:00 two days later
- **THEN** the `timeline` holds one entry for every hour from the first day's 00:00 to the third day's 11:00, in ascending order, with no hour repeated

#### Scenario: No provider rows yield an empty timeline

- **WHEN** a verdict is produced with the empty conditions value
- **THEN** the document's `timeline` is an empty list
- **AND** the verdict is produced without error

#### Scenario: Past hours stay in the timeline

- **WHEN** a verdict is produced inside the dark window, with the evaluation instant later than some hours a provider returned
- **THEN** the entries for those earlier hours are present and unchanged
- **AND** the `scored_window` still starts at the evaluation instant

### Requirement: Entry values carry each source's reading for the hour

`cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high` SHALL be percent and `wind_gust` km/h, each carried exactly as its series holds it for that hour, with no rounding, and null when the series lacks the hour or the value, or no provider filled it. `seeing` and `transparency` SHALL be quality in 0 to 1 where 1 is best, from their series for that hour, rounded to two decimal places, each null when the series lacks the hour or the value, or no provider filled it.

#### Scenario: An hour one source lacks carries null for that source's fields

- **WHEN** an hour is present in the `seeing` and `transparency` series but absent from the `cloud_cover`, cloud-layer and `wind_gust` series
- **THEN** that entry's `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high` and `wind_gust` are null
- **AND** its `seeing` and `transparency` carry their series' values
- **AND** its `sun_altitude` and `moon_altitude` are present

#### Scenario: Cloud and wind values pass through unchanged

- **WHEN** the `cloud_cover` series holds `37.0` and the `wind_gust` series `23.4` for an hour
- **THEN** that entry's `cloud_cover` is `37.0` and its `wind_gust` is `23.4`

#### Scenario: Seeing and transparency are emitted at two decimal places

- **WHEN** the `seeing` series holds a quality of four sevenths for an hour
- **THEN** that entry's `seeing` is `0.57`

## REMOVED Requirements

### Requirement: Entry weather values carry the base source's reading for the hour

**Reason**: The base role no longer exists. Each weather value comes from its own
series, filled by the first provider in order that returned it.
**Migration**: The behaviour is restated under "Entry weather values carry the
filling provider's reading for the hour". The document's keys and values are
unchanged.
