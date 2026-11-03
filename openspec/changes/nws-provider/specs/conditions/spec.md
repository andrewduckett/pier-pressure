## ADDED Requirements

### Requirement: The catalog offers the National Weather Service as a provider

The catalog SHALL offer a provider with the key `nws` and the display name
`NWS`. It SHALL need no key. It SHALL declare `cloud_cover`, `wind_gust`,
`wind_speed`, `wind_direction`, `temperature`, `dew_point`, `humidity` and
`precipitation_probability`, and no bundle. It SHALL NOT declare `cloud_low`,
`cloud_mid`, `cloud_high`, `seeing` or `transparency`. It SHALL be listed,
filled, fetched and reported like any other provider, and the default provider
order SHALL NOT change.

#### Scenario: The catalog offers NWS

- **WHEN** the catalog is read
- **THEN** it holds `nws` with the display name `NWS`, needing no key
- **AND** its declaration lists `cloud_cover`, `wind_gust`, `wind_speed`, `wind_direction`, `temperature`, `dew_point`, `humidity` and `precipitation_probability`, and no bundle

#### Scenario: NWS is accepted in the provider list

- **WHEN** the configuration lists `providers: [nws, open_meteo_hrrr, seven_timer]`
- **THEN** startup succeeds and the provider order is `nws`, `open_meteo_hrrr`, `seven_timer`

#### Scenario: NWS alone satisfies the cloud rule

- **WHEN** the configuration lists `providers: [nws]`
- **THEN** startup succeeds, because `nws` needs no key and supplies cloud cover

#### Scenario: The default order does not include NWS

- **WHEN** the configuration has no `conditions` block
- **THEN** the provider order is `open_meteo` then `seven_timer`

### Requirement: NWS is fetched in two steps and the grid cell is remembered per pier

A fetch of `nws` for a pier SHALL first resolve the pier's coordinates to its
forecast office and grid cell, then fetch the raw gridpoint forecast for that
cell. The provider SHALL remember the resolved grid cell for the pier's
coordinates for as long as the process runs, so later fetches for the same pier
make only the gridpoint request. A failed resolution SHALL NOT be remembered.
The point request SHALL follow a redirect, because NWS answers one when the
coordinates carry more than four decimal places. When the gridpoint request
answers status 404, the provider SHALL forget the remembered cell, so the next
fetch resolves the point again. Nothing SHALL be written to disk.

#### Scenario: The first fetch makes two requests

- **WHEN** `nws` is fetched for a pier for the first time since startup
- **THEN** it requests the point for the pier's latitude and longitude, then the gridpoint forecast for the office and cell that answer named
- **AND** it returns readings from the gridpoint forecast

#### Scenario: A later fetch for the same pier makes one request

- **WHEN** `nws` is fetched a second time for the same pier
- **THEN** it requests only the gridpoint forecast for the remembered office and cell

#### Scenario: A failed resolution is retried next fetch

- **WHEN** the point request for a pier fails with status 503, and `nws` is fetched again for that pier
- **THEN** the second fetch requests the point again

#### Scenario: Two piers resolve separately

- **WHEN** `nws` is fetched for two piers at different coordinates
- **THEN** each pier's point is requested once, and each fetch uses its own pier's office and cell

#### Scenario: Coordinates with five decimal places still resolve

- **WHEN** a pier sits at latitude 42.12345 and longitude -87.65432, and NWS answers its point request with status 301 pointing at the four-decimal form
- **THEN** the provider follows the redirect, requests the gridpoint forecast the redirected answer named, and returns readings

#### Scenario: A gridpoint 404 forgets the cell

- **WHEN** the gridpoint request for a remembered cell answers status 404, and `nws` is fetched again for that pier
- **THEN** the first fetch is a failed outcome with the kind of error, `404` and `Not Found`
- **AND** the second fetch requests the point again before the gridpoint forecast

### Requirement: NWS requests carry a fixed User-Agent

Every request to NWS SHALL carry a `User-Agent` header made of the project
name, the running version and the repository URL. The header SHALL NOT carry an
email address, and it SHALL NOT be configurable.

#### Scenario: The header names the project, version and repository

- **WHEN** `nws` makes any request
- **THEN** its `User-Agent` header contains `PierPressure`, the running version and `https://github.com/andrewduckett/pier-pressure`
- **AND** it contains no `@`

### Requirement: NWS periods are expanded onto the hourly grid within a 72-hour horizon

Each NWS value SHALL be held across every clock hour its period covers, so the
result is on the same hourly grid as every other provider. The provider SHALL
keep only hours within 72 hours of the earliest period start in the payload.
Hours past that horizon SHALL be dropped, and hours within it that no period
covers SHALL stay absent.

#### Scenario: A three-hour period is held across its hours

- **WHEN** NWS reports sky cover `45` for the period starting at 21:00 lasting three hours
- **THEN** the readings for 21:00, 22:00 and 23:00 each carry a cloud cover of `45`

#### Scenario: A period spanning days is held across its hours

- **WHEN** NWS reports a wind speed for a period starting at 06:00 lasting one day and six hours
- **THEN** the readings from 06:00 to 11:00 the next day each carry that wind speed

#### Scenario: A period that straddles the horizon is cut at it

- **WHEN** the earliest period in the payload starts at 18:00 on day one, and a sky cover period starts at 16:00 on day four lasting three hours
- **THEN** the readings for 16:00 and 17:00 on day four carry that sky cover
- **AND** no reading exists for 18:00 on day four

#### Scenario: A period that starts past the horizon is dropped

- **WHEN** the earliest period in the payload starts at 18:00 on day one, and a period starts at 19:00 on day four
- **THEN** no reading exists for 19:00 on day four

#### Scenario: Periods for different variables stay independent

- **WHEN** NWS reports sky cover for 21:00 to 23:00 and temperature for 21:00 only
- **THEN** the readings for 22:00 and 23:00 carry a cloud cover and no temperature

### Requirement: NWS values are carried in their expected units or left absent

Each NWS value SHALL be carried as reported when its unit code is the expected
one. The expected codes are: percent for sky cover, humidity and precipitation
probability; degrees Celsius for temperature and dew point; kilometres per hour
for wind speed and gust; degrees for wind direction. A variable whose unit code
is anything else SHALL be left absent in every hour, with no conversion. A
`null` value SHALL be left absent for its hours.

#### Scenario: Expected units are carried as reported

- **WHEN** NWS reports a temperature of `12.34` in degrees Celsius and a wind speed of `14.25` in kilometres per hour for an hour
- **THEN** that hour's reading carries `12.34` and `14.25`

#### Scenario: An unexpected unit leaves the variable absent

- **WHEN** NWS reports wind speed with a unit code of knots
- **THEN** every hour's wind speed is absent
- **AND** the other variables keep their values

#### Scenario: A null value is absent

- **WHEN** NWS reports a `null` dew point for a period
- **THEN** the dew point is absent for that period's hours
- **AND** the absence is not reported as an error

### Requirement: NWS's issue time is the forecast's update time

Each series filled by `nws` SHALL carry the gridpoint forecast's update time as
its issue time. When the payload gives no update time, the issue time SHALL be
null.

#### Scenario: The update time becomes the issue time

- **WHEN** the gridpoint forecast reports an update time of 20:35 UTC
- **THEN** each series `nws` fills carries an issue time of 20:35 UTC
- **AND** the fetch outcome carries 20:35 UTC as its issue time

### Requirement: A pier outside NWS coverage fails and is passed over

The system SHALL NOT check a pier's location against NWS coverage at startup.
When NWS answers the point request with status 404, the `nws` outcome SHALL be
reported as failed with the kind of error, `404` and `Not Found`, and `nws`
SHALL be passed over like any failed provider.

#### Scenario: A pier outside the United States fails and the next provider fills cloud

- **WHEN** the order is `nws` then `open_meteo` for a pier at latitude 51.5 and longitude -0.12, and NWS answers the point request with status 404
- **THEN** the `nws` outcome is reported as failed, with an error that gives the kind of error, `404` and `Not Found`
- **AND** the `cloud_cover` series carries the key `open_meteo`

#### Scenario: A pier outside coverage does not stop startup

- **WHEN** the configuration lists `providers: [nws, open_meteo]` for a pier at latitude 51.5 and longitude -0.12
- **THEN** startup succeeds

## MODIFIED Requirements

### Requirement: Each variable is filled from the first provider in order that returned it

The snapshot SHALL hold one series per variable, carrying one provider's hourly
values, that provider's key and the issue time of its data. For each variable,
the series SHALL come from the first provider in the configured order that
returned it. A provider returned a variable when at least one hour of its
forecast carries a value for it, or for another variable in the same bundle.
The variables of a bundle SHALL come from the same provider. A provider SHALL
fill a bundle whole or not at all. When an earlier provider already holds any
member of the bundle as this provider declares it, this provider fills none of
the bundle's members. A variable no provider filled SHALL have no series.

#### Scenario: The default order gives cloud to Open-Meteo and seeing to 7Timer!

- **WHEN** the order is `open_meteo` then `seven_timer`, Open-Meteo returns cloud cover and gust for the dark window and 7Timer! returns seeing and transparency
- **THEN** the `cloud_cover` and `wind_gust` series carry Open-Meteo's values and key
- **AND** the `seeing` and `transparency` series carry 7Timer!'s values and key

#### Scenario: A provider earlier in the order wins a variable both returned

- **WHEN** two providers both return `cloud_cover` for the dark window and the first in order gives `40` for 21:00 where the second gives `70`
- **THEN** the `cloud_cover` series carries the first provider's key and `40` at 21:00

#### Scenario: An empty column falls through to the next provider

- **WHEN** the first provider in order returns rows whose `cloud_cover` is blank in every hour, and the second returns `cloud_cover` for the dark window
- **THEN** the `cloud_cover` series carries the second provider's key and values

#### Scenario: A bundle travels together

- **WHEN** the first provider in order declares the four-variable cloud bundle and returns `cloud_cover` but no low, mid or high layer, and the second returns all four
- **THEN** the `cloud_cover` series carries the first provider's key
- **AND** the `cloud_low`, `cloud_mid` and `cloud_high` series carry the first provider's key with no values
- **AND** none of the four carries the second provider's values

#### Scenario: A later provider's bundle is not split around an earlier winner

- **WHEN** the order is `nws` then `open_meteo`, NWS returns `cloud_cover` for the dark window, and Open-Meteo returns `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`
- **THEN** the `cloud_cover` series carries the key `nws`
- **AND** `cloud_low`, `cloud_mid` and `cloud_high` have no series and no alternates
- **AND** `cloud_cover` has one alternate, carrying the key `open_meteo`

#### Scenario: A split bundle leaves the high-cloud penalty neutral

- **WHEN** a verdict is produced from a snapshot whose `cloud_cover` series carries `nws` and whose `cloud_high` has no series
- **THEN** the score carries no high-cloud penalty term
