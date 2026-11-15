## MODIFIED Requirements

### Requirement: Weather variables are carried as reported and never judged

The weather variables SHALL be carried as the provider reports them, with no
rounding: temperature and dew point in degrees Celsius, humidity and
precipitation probability in percent, wind speed in km/h and wind direction in
degrees. They SHALL NOT be converted, except where a provider's own requirement
names a change of unit. The verdict, the score, the confidence and the reasons
SHALL NOT read them.

#### Scenario: Values are not rounded or converted

- **WHEN** the provider that filled a weather variable reports a temperature of `12.34` and a wind speed of `14.25` for an hour
- **THEN** that hour in the snapshot carries `12.34` and `14.25`

#### Scenario: Weather variables do not change the verdict

- **WHEN** two verdicts are produced for the same pier and instant, from snapshots that differ only in the six weather variables
- **THEN** the two documents differ only in the weather keys of their `timeline` entries

### Requirement: No single provider is load-bearing

The failure of one provider SHALL NOT prevent another provider's data from
being used. A provider whose fetch fails or returns no data SHALL be passed over
for every variable, and a variable no remaining provider returned SHALL be
marked unavailable. A failed or empty fetch SHALL NOT be filled from an earlier
fetch, for the same pier or another. A provider SHALL answer a fetch from an
earlier response only when its own requirement allows it and its source still
calls that response current.

#### Scenario: A failed later provider leaves the earlier provider's data intact

- **WHEN** the order is `open_meteo` then `seven_timer`, 7Timer! cannot be reached and Open-Meteo can
- **THEN** cloud cover and wind gust are available in the snapshot
- **AND** seeing and transparency are marked unavailable

#### Scenario: A failed earlier provider does not fail the whole snapshot

- **WHEN** the order is `open_meteo` then `seven_timer` and Open-Meteo cannot be reached
- **THEN** the snapshot is still produced with cloud cover and wind gust marked unavailable
- **AND** seeing and transparency from 7Timer! remain available

#### Scenario: A failed provider is passed over for a variable the next provider returned

- **WHEN** the first provider in order fails and the second returns `cloud_cover`
- **THEN** the `cloud_cover` series carries the second provider's key and values

#### Scenario: A failed fetch is not filled from an earlier fetch

- **WHEN** a provider's fetch succeeded for a pier earlier, and its next fetch for that pier fails or returns no data
- **THEN** no series in the new snapshot carries that provider's key
- **AND** the snapshot carries no values or issue time from the earlier fetch

#### Scenario: A failed fetch for one pier is not filled from another pier's fetch

- **WHEN** a provider's fetch succeeds for one pier, and its fetch for a second pier then fails or returns no data
- **THEN** no series in the second pier's snapshot carries that provider's key
- **AND** the second pier's snapshot carries no values or issue time from the first pier's fetch

## ADDED Requirements

### Requirement: The catalog offers MET Norway as a provider

The catalog SHALL offer a provider with the key `met_norway` and the display
name `MET Norway`. It SHALL need no key. It SHALL declare `cloud_cover`,
`cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `wind_speed`,
`wind_direction`, `temperature`, `dew_point`, `humidity` and
`precipitation_probability`, with the cloud bundle as its one bundle. It SHALL
be listed, filled, fetched and reported like any other provider, and SHALL NOT
be in the default provider order.

#### Scenario: The catalog offers MET Norway

- **WHEN** the catalog is read
- **THEN** it holds `met_norway` with the display name `MET Norway`, needing no key
- **AND** its declaration lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `wind_speed`, `wind_direction`, `temperature`, `dew_point`, `humidity` and `precipitation_probability`
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: MET Norway alone satisfies the cloud rule

- **WHEN** the configuration lists `providers: [met_norway]`
- **THEN** startup succeeds, because `met_norway` needs no key and supplies cloud cover

#### Scenario: The default order does not include MET Norway

- **WHEN** the configuration has no `conditions` block
- **THEN** the provider order is `open_meteo`, `seven_timer`, `open_meteo_air_quality`, `computed`
- **AND** it does not include `met_norway`

#### Scenario: MET Norway fills cloud with its layers when it comes first

- **WHEN** the order is `met_norway` then `open_meteo`, and both return cloud cover for the dark window
- **THEN** the `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high` series carry the key `met_norway`

### Requirement: MET Norway is asked for the complete forecast at the pier's rounded coordinates

A fetch of `met_norway` SHALL request
`https://api.met.no/weatherapi/locationforecast/2.0/complete` with `lat` and
`lon` set to the pier's latitude and longitude, each rounded to 4 decimal
places. It SHALL send no other parameter.

#### Scenario: Coordinates are rounded to 4 decimal places

- **WHEN** `met_norway` is fetched for a pier at latitude 59.913868 and longitude 10.752245
- **THEN** its request asks for `lat` `59.9139` and `lon` `10.7522`, and has no other parameter

### Requirement: MET Norway requests carry the fixed User-Agent

Every request to MET Norway SHALL carry the same `User-Agent` header as NWS
requests: the project name, the running version and the repository URL, with
no email address. It SHALL NOT be configurable.

#### Scenario: The header names the project, version and repository

- **WHEN** `met_norway` makes a request
- **THEN** its `User-Agent` header contains `PierPressure`, the running version and `https://github.com/andrewduckett/pier-pressure`
- **AND** it contains no `@`

### Requirement: MET Norway values are read from each step's fields

Each MET Norway step SHALL fill the hour at its time from its instant values:
`cloud_area_fraction` as cloud cover, `cloud_area_fraction_low`,
`cloud_area_fraction_medium` and `cloud_area_fraction_high` as low, mid and high
cloud, `wind_speed_of_gust` as gust, `wind_speed`, `wind_from_direction`,
`air_temperature`, `dew_point_temperature` and `relative_humidity`. A field the
step lacks SHALL leave its variable absent for that hour, with no error.

#### Scenario: A step's instant values fill its hour

- **WHEN** a step at 21:00 UTC reports `cloud_area_fraction` `80`, `cloud_area_fraction_low` `10`, `cloud_area_fraction_medium` `30`, `cloud_area_fraction_high` `75` and `air_temperature` `4.8`
- **THEN** the reading for 21:00 carries a cloud cover of `80`, low cloud `10`, mid cloud `30`, high cloud `75` and a temperature of `4.8`

#### Scenario: A pier outside the Nordic area gets no gust or rain chance

- **WHEN** MET Norway returns steps with no `wind_speed_of_gust` and no `probability_of_precipitation`, and the order is `met_norway` then `open_meteo`
- **THEN** the `met_norway` outcome is successful
- **AND** the `cloud_cover` series carries the key `met_norway`
- **AND** the `wind_gust` and `precipitation_probability` series carry the key `open_meteo`

### Requirement: MET Norway values are carried in their expected units or left absent

Each MET Norway value SHALL be carried as reported when the unit its payload
gives is the expected one: `%` for the cloud fields, humidity and rain chance;
`celsius` for temperature and dew point; `degrees` for wind direction. Wind
speed and gust SHALL be expected in `m/s` and multiplied by 3.6 to give km/h,
unrounded. A variable whose unit is anything else SHALL be left absent in every
hour, with no conversion.

#### Scenario: Wind in metres per second is carried in km/h

- **WHEN** MET Norway reports a `wind_speed` of `5.0` and a `wind_speed_of_gust` of `10.0` for an hour, both in `m/s`
- **THEN** that hour's reading carries a wind speed of `18.0` and a gust of `36.0`

#### Scenario: An unexpected unit leaves the variable absent

- **WHEN** MET Norway gives the unit of `wind_speed` as `knots`
- **THEN** every hour's wind speed is absent
- **AND** the other variables keep their values

### Requirement: MET Norway keeps only its hourly steps within 72 hours

The MET Norway provider SHALL keep only the leading run of steps that are each
one hour after the one before. From the first step that is not, every later
step SHALL be dropped. Of the steps kept, only hours within 72 hours of the
first step SHALL be kept.

#### Scenario: The 6-hourly steps are dropped

- **WHEN** MET Norway returns steps every hour from 00:00 to 12:00 on day one, then at 18:00 on day one and 00:00 on day two
- **THEN** readings exist for every hour from 00:00 to 12:00 on day one
- **AND** no reading exists for 18:00 on day one or 00:00 on day two

#### Scenario: Hourly steps past 72 hours are dropped

- **WHEN** MET Norway returns hourly steps from 00:00 on day one to 06:00 on day four
- **THEN** the latest reading is for 23:00 on day three

### Requirement: A MET Norway precipitation probability is held one hour after its step

Because a MET Norway `next_1_hours` precipitation probability at a step is the
chance for the hour that starts there, and PierPressure's rain chance at an hour
is for the hour that ends there, each value SHALL be held on the hour after its
step. A value whose next hour is not a kept step SHALL be dropped.

#### Scenario: A rain chance moves one hour later

- **WHEN** the step at 21:00 reports a `next_1_hours` precipitation probability of `40` and a cloud cover of `80`
- **THEN** the reading for 22:00 carries a precipitation probability of `40`
- **AND** the reading for 21:00 carries a cloud cover of `80` and no precipitation probability from that step

#### Scenario: A rain chance on the last kept step is dropped

- **WHEN** the last kept step, at 12:00, reports a `next_1_hours` precipitation probability of `30`
- **THEN** no reading exists for 13:00

### Requirement: MET Norway's issue time is the forecast's update time

Each series filled by `met_norway` SHALL carry the payload's `updated_at` time,
in UTC, as its issue time. When the payload gives no update time, the issue
time SHALL be null.

#### Scenario: The update time becomes the issue time

- **WHEN** the payload's `updated_at` is `2026-11-14T19:17:36Z`
- **THEN** each series `met_norway` fills carries an issue time of 2026-11-14 19:17:36 UTC
- **AND** the fetch outcome carries that time as its issue time

#### Scenario: No update time gives a null issue time

- **WHEN** the payload has no `updated_at`
- **THEN** each series `met_norway` fills carries a null issue time

### Requirement: MET Norway is not asked again before its response expires

The provider SHALL remember, for each rounded pair of coordinates and for as
long as the process runs, its last good forecast and that response's `Expires`
and `Last-Modified` times. A fetch before the remembered `Expires` time SHALL
make no request and SHALL return the remembered forecast, as a successful
outcome with its remembered issue time. Nothing SHALL be written to disk.

#### Scenario: A fetch before Expires makes no request

- **WHEN** a fetch for a pier returns a forecast whose response expires at 20:30 UTC, and the provider is fetched again for that pier at 20:10 UTC
- **THEN** the second fetch makes no request to MET Norway
- **AND** its outcome is successful and it fills the same series, with the same issue time, as the first

#### Scenario: Two piers are remembered separately

- **WHEN** `met_norway` is fetched for two piers at different coordinates before either response expires
- **THEN** each pier's forecast is requested once, and each fetch returns its own pier's forecast

### Requirement: MET Norway is asked with If-Modified-Since after its response expires

A fetch at or after the remembered `Expires` time SHALL send a request with an
`If-Modified-Since` header set to the remembered `Last-Modified` value. A 304
answer SHALL return the remembered forecast as a successful outcome and
remember the 304's `Expires` time. A response with no `Expires` header SHALL
let the next fetch request again. A response with no `Last-Modified` header
SHALL leave the next request without `If-Modified-Since`.

#### Scenario: An expired response is asked for with If-Modified-Since

- **WHEN** the remembered response gave `Last-Modified` `Sat, 14 Nov 2026 23:20:27 GMT` and has expired
- **THEN** the next fetch requests the forecast with `If-Modified-Since` `Sat, 14 Nov 2026 23:20:27 GMT`

#### Scenario: A 304 returns the remembered forecast

- **WHEN** MET Norway answers that request with status 304
- **THEN** the outcome is successful and the fetch fills the same series, with the same issue time, as the remembered forecast

### Requirement: A failed MET Norway request forgets the remembered response

A MET Norway request that fails, or answers any error status, SHALL fail the
fetch like any provider, so the next provider fills. It SHALL forget the
remembered response for those coordinates, so the next fetch makes a request
with no `If-Modified-Since` header. A status 203 SHALL be a success, and the
provider SHALL log a warning that the product version is deprecated.

#### Scenario: A 429 fails the fetch and the next provider fills

- **WHEN** the order is `met_norway` then `open_meteo`, and MET Norway answers with status 429
- **THEN** the `met_norway` outcome is failed, with an error that gives the kind of error, `429` and `Too Many Requests`
- **AND** the `cloud_cover` series carries the key `open_meteo`

#### Scenario: A failure forgets the remembered response

- **WHEN** an expired remembered response is asked for again and MET Norway answers with status 500, and the provider is fetched again for that pier
- **THEN** the second request carries no `If-Modified-Since` header

#### Scenario: A 203 is a success with a warning

- **WHEN** MET Norway answers a request with status 203 and a forecast
- **THEN** the outcome is successful, and a warning that the product version is deprecated is logged

### Requirement: A live MET Norway recording parses

A recorded MET Norway `complete` response for a pier in the Nordic area SHALL
parse into readings with values for every variable `met_norway` declares.

#### Scenario: A live Oslo recording parses

- **WHEN** a recorded `complete` response for Oslo is parsed
- **THEN** each of its hours has a value for `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `wind_speed`, `wind_direction`, `temperature`, `dew_point` and `humidity`
- **AND** each hour after its first has a value for `precipitation_probability`
