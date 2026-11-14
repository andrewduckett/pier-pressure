# conditions Specification

## Purpose

The conditions capability obtains observing conditions (cloud, wind, seeing,
transparency) for a pier's dark window from external forecasts and presents them
to the verdict as a single self-contained snapshot, so no single external source
is load-bearing and the verdict computation itself needs no network access.

## Requirements

### Requirement: Conditions cover the dark window at hourly resolution

For a pier whose selected night has a dark window, the system SHALL obtain
observing conditions covering that window — cloud cover, wind gust, seeing, and
transparency — resolved to a per-hour series across the window. Sources that
report at a coarser cadence SHALL be resampled onto the hourly series, so the
verdict consumes one uniform grid regardless of how each source reports.

#### Scenario: Conditions span the dark window hour by hour

- **WHEN** conditions are obtained for a pier whose selected night has a dark window
- **THEN** the result is a per-hour series covering the dark window
- **AND** each hour carries a cloud-cover, wind-gust, seeing, and transparency slot

#### Scenario: A coarser source is resampled to the hourly series

- **WHEN** a source reports at a cadence coarser than one hour
- **THEN** its values are resampled onto the hourly series before the verdict consumes them

### Requirement: The snapshot records when its data was issued

The snapshot SHALL record an issue time on each series: the one its provider
gave for the data it returned on this fetch. Series filled by the same provider
SHALL carry the same issue time, except the computed source's: each computed
series carries the issue time its own inputs give it. Recording it per series
lets downstream trust reflect the age of the data it actually reads, even when
providers refresh on different cadences.

#### Scenario: Each source's issue time reflects the data actually carried

- **WHEN** a snapshot is filled from two providers that gave different issue times
- **THEN** each series carries the issue time of the provider that filled it
- **AND** each recorded issue time is the one that provider gave for the data it returned on this fetch

### Requirement: The snapshot is self-contained so the verdict needs no network

The snapshot SHALL carry everything the verdict needs — the per-hour values,
their availability, and the issue time — so that computing a verdict from a
snapshot requires no further external access. This preserves the deterministic,
offline verdict computation while conditions themselves are fetched live.

#### Scenario: Computing a verdict from a snapshot performs no network access

- **WHEN** a verdict is computed from an already-obtained conditions snapshot
- **THEN** the computation reads only the snapshot
- **AND** it makes no outbound network request

### Requirement: No dark window means conditions are not required

When a pier's selected night has no dark window (continuous non-night), the
system SHALL NOT require conditions to be obtained, because the verdict is
already decided by astronomy alone.

#### Scenario: Continuous non-night needs no conditions

- **WHEN** a pier's selected night has no dark window
- **THEN** obtaining conditions is not required for a verdict to be produced

### Requirement: Weather variables are carried as reported and never judged

The weather variables SHALL be carried as the provider reports them, with no
rounding or conversion: temperature and dew point in degrees Celsius, humidity
and precipitation probability in percent, wind speed in km/h and wind direction
in degrees. The verdict, the score, the confidence and the reasons SHALL NOT
read them.

#### Scenario: Values are not rounded or converted

- **WHEN** the provider that filled a weather variable reports a temperature of `12.34` and a wind speed of `14.25` for an hour
- **THEN** that hour in the snapshot carries `12.34` and `14.25`

#### Scenario: Weather variables do not change the verdict

- **WHEN** two verdicts are produced for the same pier and instant, from snapshots that differ only in the six weather variables
- **THEN** the two documents differ only in the weather keys of their `timeline` entries

### Requirement: Providers are configured as an ordered list

The configuration SHALL accept a `conditions.providers` list of provider keys,
preferred first. When the `conditions` block or the list is absent, the list
SHALL be `[open_meteo, seven_timer, open_meteo_air_quality, computed]`.

#### Scenario: An absent block gives the default order

- **WHEN** the configuration has no `conditions` block
- **THEN** the provider order is `open_meteo`, `seven_timer`, `open_meteo_air_quality`, `computed`

#### Scenario: A configured order is kept as written

- **WHEN** the configuration lists `providers: [seven_timer, open_meteo]`
- **THEN** the provider order is `seven_timer` then `open_meteo`

### Requirement: An invalid provider list stops startup

The system SHALL reject the configuration at startup in four cases: the
provider list is empty, a key names no known provider, a key appears more than
once, or no listed provider is both keyless and declares cloud cover. The error
SHALL name the rule broken. It SHALL carry no value from the configuration
other than the offending key.

#### Scenario: An empty list is rejected

- **WHEN** the configuration lists `providers: []`
- **THEN** startup fails with an error that says the list must name at least one provider

#### Scenario: An unknown key is rejected

- **WHEN** the configuration lists `providers: [open_meteo, weather_wizard]`
- **THEN** startup fails with an error that says `weather_wizard` is not a known provider

#### Scenario: A duplicate key is rejected

- **WHEN** the configuration lists `providers: [open_meteo, seven_timer, open_meteo]`
- **THEN** startup fails with an error that says `open_meteo` is listed more than once

#### Scenario: A list with no keyless cloud-cover provider is rejected

- **WHEN** the configuration lists `providers: [seven_timer]`
- **THEN** startup fails with an error that says the list must include a provider that needs no key and supplies cloud cover

### Requirement: Each provider declares its variables and bundles

Each provider SHALL declare the variables it supplies, named by their variable
keys, and which of them form a bundle. A variable key need not be a timeline
key. A declaration SHALL be fixed: it SHALL NOT change with what a fetch
returned.

#### Scenario: Open-Meteo declares the cloud bundle and the weather variables

- **WHEN** the Open-Meteo provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability` and `column_water_vapour`, then the 36 seeing-column variables
- **AND** it has two bundles: one holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`, and the other holds the 36 seeing-column variables

#### Scenario: 7Timer! declares seeing and transparency

- **WHEN** the 7Timer! provider's declaration is read
- **THEN** it lists `seeing` and `transparency` and no bundle

### Requirement: A series comes whole from one provider

Hours a series' provider did not cover SHALL stay unavailable. The system SHALL
NOT merge hours from two providers into one series.

#### Scenario: A series is whole, never merged per hour

- **WHEN** the first provider in order returns `cloud_cover` for 20:00 to 23:00 only, and the second returns `cloud_cover` for 20:00 to 03:00
- **THEN** the `cloud_cover` series carries the first provider's key and values for 20:00 to 23:00
- **AND** its hours from 00:00 to 03:00 are unavailable

### Requirement: Every listed provider is fetched on every fetch

The system SHALL fetch every provider in the list, in order, each time it
fetches conditions for a pier, and SHALL decide the fill after all fetches.

#### Scenario: Every listed provider is fetched in order

- **WHEN** the order lists three providers and the first returns every variable the other two declare
- **THEN** all three providers are fetched, first to last
- **AND** one fetch outcome is reported for each

### Requirement: No single provider is load-bearing

The failure of one provider SHALL NOT prevent another provider's data from
being used. A provider whose fetch fails or returns no data SHALL be passed over
for every variable, and a variable no remaining provider returned SHALL be
marked unavailable. The system SHALL NOT fill a variable with data from an
earlier fetch, whether for the same pier or another pier.

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

### Requirement: A provider supplies the weather variables

The conditions SHALL carry six weather variables: temperature, dew point,
relative humidity, wind speed, wind direction and precipitation probability.
Each SHALL be its own series, filled by the first provider in order that
returned it, and marked available or unavailable per hour like every other
variable. A provider that reports some or none of them SHALL still yield a
valid snapshot.

#### Scenario: Every weather variable is carried for an hour the provider reports fully

- **WHEN** a provider reports, for one hour, a temperature of `12.3`, a dew point of `9.8`, a humidity of `85`, a wind speed of `14.2`, a wind direction of `230` and a precipitation probability of `35`
- **THEN** that hour in the snapshot carries each of those six values, marked available

#### Scenario: One weather variable can be absent while the others remain present

- **WHEN** the only provider that declares the weather variables reports every one but the dew point for an hour
- **THEN** that hour's dew point is marked unavailable
- **AND** the other five keep their values
- **AND** the absence is not reported as an error

#### Scenario: A provider that reports no weather variables yields a valid snapshot

- **WHEN** the only provider that declares the weather variables reports cloud cover and wind gust but none of the six
- **THEN** the snapshot is returned with cloud cover and wind gust available and all six weather variables marked unavailable

### Requirement: Availability is stamped per variable

Every variable SHALL be marked as available or unavailable for every hour. A
partial snapshot, with some variables present and others absent, SHALL be a
valid result rather than a failure. The verdict then degrades by reading what
is absent, not by handling an error. Any hours of the selected dark window
that a series' provider did not reach SHALL be marked unavailable in that
series rather than filled in, from any provider.

#### Scenario: A partial snapshot is valid

- **WHEN** some variables are obtained and others cannot be
- **THEN** the snapshot is returned with each variable marked available or unavailable
- **AND** the absence of a variable is not reported as an error

#### Scenario: Hours beyond a provider's forecast horizon are unavailable

- **WHEN** the provider that filled a series has a forecast that does not reach part of the dark window
- **THEN** that series is marked unavailable for the hours its forecast does not reach
- **AND** the hours its forecast does reach keep their values

### Requirement: Each Open-Meteo model is its own provider

The catalog SHALL offer six providers, each fetching one named Open-Meteo
model: HRRR, HRDPS, RDPS, ICON, GFS and ECMWF. Each model provider SHALL need
no key, and SHALL be listed, filled, fetched and reported like any other
provider.

#### Scenario: The catalog offers the five model providers

- **WHEN** the catalog is read
- **THEN** it holds these providers, each with this display name, and none needs a key:

  | Key | Display name |
  |---|---|
  | `open_meteo_hrrr` | Open-Meteo HRRR |
  | `open_meteo_hrdps` | Open-Meteo HRDPS |
  | `open_meteo_rdps` | Open-Meteo RDPS |
  | `open_meteo_icon` | Open-Meteo ICON |
  | `open_meteo_gfs` | Open-Meteo GFS |

#### Scenario: The catalog offers the ECMWF model provider

- **WHEN** the catalog is read
- **THEN** it holds `open_meteo_ecmwf`, with the display name `Open-Meteo ECMWF`, and it needs no key

#### Scenario: A model key is accepted in the provider list

- **WHEN** the configuration lists `providers: [open_meteo_hrrr, open_meteo_hrdps, open_meteo_rdps, seven_timer]`
- **THEN** startup succeeds and the provider order is `open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`, `seven_timer`

#### Scenario: A model provider alone satisfies the cloud rule

- **WHEN** the configuration lists `providers: [open_meteo_hrdps]`
- **THEN** startup succeeds, because `open_meteo_hrdps` needs no key and supplies cloud cover

#### Scenario: The model that comes first fills cloud

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo`, and both return cloud cover for the dark window
- **THEN** the `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high` series carry the key `open_meteo_hrdps`

### Requirement: A model provider asks Open-Meteo for its model only

Each model provider SHALL ask Open-Meteo for its one model and no other. It
SHALL ask for the same hours and units as `open_meteo`, and only for the
variables it declares. The `open_meteo` provider SHALL keep fetching
Open-Meteo's best match, and SHALL name no model in its request.

#### Scenario: Each model provider names its own model

- **WHEN** each model provider is fetched for a pier
- **THEN** its request to Open-Meteo names exactly this model and no other:

  | Key | Open-Meteo model |
  |---|---|
  | `open_meteo_hrrr` | `ncep_hrrr_conus` |
  | `open_meteo_hrdps` | `gem_hrdps_continental` |
  | `open_meteo_rdps` | `gem_regional` |
  | `open_meteo_icon` | `icon_seamless` |
  | `open_meteo_gfs` | `gfs_global` |
  | `open_meteo_ecmwf` | `ecmwf_ifs` |

- **AND** each request asks for 4 past hours and 72 forecast hours, with wind speed in km/h

#### Scenario: HRDPS does not ask for precipitation probability

- **WHEN** `open_meteo_hrdps` is fetched for a pier
- **THEN** the hourly variables in its request include neither precipitation probability nor `total_column_integrated_water_vapour`
- **AND** they include no seeing-column variable

#### Scenario: Plain Open-Meteo still asks for best match

- **WHEN** `open_meteo` is fetched for a pier
- **THEN** its request to Open-Meteo names no model
- **AND** it asks for 48 hourly variables: the twelve it asked for before the seeing column was added, and the 36 seeing-column variables
- **AND** it asks for 4 past hours and 72 forecast hours, with wind speed in km/h

### Requirement: ECMWF declares column water vapour but not the seeing column

The ECMWF model provider SHALL declare the same variables and the cloud bundle
as `open_meteo`, except the seeing column, which that model does not fully
supply. It SHALL declare `precipitation_probability` and `column_water_vapour`.

#### Scenario: ECMWF declares every variable but the seeing column

- **WHEN** the `open_meteo_ecmwf` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability` and `column_water_vapour`
- **AND** it lists no seeing-column variable
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: ECMWF does not ask for the seeing column

- **WHEN** `open_meteo_ecmwf` is fetched for a pier
- **THEN** the hourly variables in its request include `precipitation_probability` and `total_column_integrated_water_vapour`
- **AND** they include no seeing-column variable

#### Scenario: Column water vapour can come from ECMWF

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo_ecmwf`, and both return readings for the dark window
- **THEN** the `column_water_vapour` series carries the key `open_meteo_ecmwf`

#### Scenario: The seeing column comes from a later provider than ECMWF

- **WHEN** the order is `open_meteo_ecmwf` then `open_meteo_gfs`, and both return readings for the dark window
- **THEN** the cloud series carry the key `open_meteo_ecmwf`
- **AND** every seeing-column series carries the key `open_meteo_gfs`

#### Scenario: A live ECMWF recording parses

- **WHEN** a recorded `ecmwf_ifs` response from Open-Meteo is parsed
- **THEN** each of its hours has a value for `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `precipitation_probability` and `column_water_vapour`

### Requirement: A model outside its area is not rejected at startup

The system SHALL NOT check a pier's location against a model's area at startup.
A model provider that fails for a pier SHALL be reported and passed over like
any failed provider.

#### Scenario: HRRR for a pier outside its area fails and is passed over

- **WHEN** the order is `open_meteo_hrrr` then `open_meteo`, and Open-Meteo answers the HRRR request with status 400 because it has no data for the pier's location
- **THEN** the `open_meteo_hrrr` outcome is reported as failed, with an error that gives the kind of error, `400` and `Bad Request`
- **AND** the `cloud_cover` series carries the key `open_meteo`

#### Scenario: A model outside its area does not stop startup

- **WHEN** the configuration lists `providers: [open_meteo_hrrr, open_meteo]` for a pier at latitude 51.5 and longitude -0.12
- **THEN** startup succeeds

### Requirement: The catalog offers the National Weather Service as a provider

The catalog SHALL offer a provider with the key `nws` and the display name
`NWS`. It SHALL need no key. It SHALL declare `cloud_cover`, `wind_gust`,
`wind_speed`, `wind_direction`, `temperature`, `dew_point`, `humidity` and
`precipitation_probability`, and no bundle. It SHALL NOT declare `cloud_low`,
`cloud_mid`, `cloud_high`, `seeing` or `transparency`. It SHALL be listed,
filled, fetched and reported like any other provider, and it SHALL NOT be in
the default provider order.

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
- **THEN** the provider order is `open_meteo`, `seven_timer`, `open_meteo_air_quality`, `computed`
- **AND** it does not include `nws`

### Requirement: NWS is fetched in two steps and the grid cell is remembered per pier

A fetch of `nws` for a pier SHALL first resolve the pier's coordinates to its
forecast office and grid cell, then fetch the raw gridpoint forecast for that
cell. The provider SHALL remember the resolved grid cell for the pier's
coordinates for as long as the process runs, so later fetches for the same pier
make only the gridpoint request. A failed resolution SHALL NOT be remembered.
Nothing SHALL be written to disk.

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

### Requirement: NWS's point request follows redirects and a gridpoint 404 forgets the cell

The point request SHALL follow a redirect, because NWS answers one when the
coordinates carry more than four decimal places. When the gridpoint request
answers status 404, the provider SHALL forget the remembered cell, so the next
fetch resolves the point again.

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

### Requirement: The catalog offers Open-Meteo's air-quality forecast as a provider

The catalog SHALL offer a provider with the key `open_meteo_air_quality` and the
display name `Open-Meteo air quality`. It SHALL need no key. It SHALL declare
`aerosol_optical_depth` and `pm2_5`, and no bundle. It SHALL NOT declare cloud
cover or any other variable. It SHALL be listed, filled, fetched and reported
like any other provider.

#### Scenario: The catalog offers the air-quality provider

- **WHEN** the catalog is read
- **THEN** it holds `open_meteo_air_quality` with the display name `Open-Meteo air quality`, needing no key
- **AND** its declaration lists `aerosol_optical_depth` then `pm2_5`, and no bundle

#### Scenario: The air-quality provider is accepted in the provider list

- **WHEN** the configuration lists `providers: [open_meteo_hrrr, open_meteo_air_quality]`
- **THEN** startup succeeds and the provider order is `open_meteo_hrrr` then `open_meteo_air_quality`

#### Scenario: The air-quality provider alone does not satisfy the cloud rule

- **WHEN** the configuration lists `providers: [open_meteo_air_quality]`
- **THEN** startup fails with an error that says the list must include a provider that needs no key and supplies cloud cover

### Requirement: Air-quality variables are carried as reported

The snapshot SHALL carry `aerosol_optical_depth` as the air-quality forecast
reports it, with no unit, and `pm2_5` in micrograms per cubic metre, as
reported, with no rounding or conversion. An hour whose value is blank SHALL
leave that variable unavailable for the hour, and the other variable SHALL be
unaffected.

#### Scenario: Both values are carried for an hour the forecast reports fully

- **WHEN** the air-quality forecast reports an aerosol optical depth of `0.14` and a PM2.5 of `8.8` for an hour
- **THEN** that hour in the snapshot carries `aerosol_optical_depth` `0.14` and `pm2_5` `8.8`, each from `open_meteo_air_quality`

#### Scenario: One blank value leaves the other present

- **WHEN** the air-quality forecast reports a PM2.5 of `8.8` and a blank aerosol optical depth for an hour
- **THEN** that hour's `aerosol_optical_depth` is unavailable
- **AND** that hour's `pm2_5` is `8.8`

### Requirement: The air-quality provider's issue time is its fetch time

The air-quality provider SHALL record the time of its fetch as the issue time of
its data, as `open_meteo` does, because the air-quality response gives none.

#### Scenario: The air-quality provider stamps the fetch time

- **WHEN** `open_meteo_air_quality` is fetched at 21:05 and returns readings
- **THEN** the `aerosol_optical_depth` and `pm2_5` series carry an issue time of 21:05

### Requirement: Column water vapour is carried as reported

The snapshot SHALL carry `column_water_vapour` in kilograms per square metre,
as Open-Meteo's `total_column_integrated_water_vapour` reports it, with no
rounding or conversion. It SHALL fill by ordinary provider order, in no bundle.
An hour whose value is blank SHALL leave the variable unavailable for that hour.

#### Scenario: Column water vapour is carried unrounded

- **WHEN** the provider that filled `column_water_vapour` reports `18.37` for an hour
- **THEN** that hour in the snapshot carries `column_water_vapour` `18.37`

#### Scenario: A blank hour is unavailable

- **WHEN** the provider that filled `column_water_vapour` reports a blank value for an hour
- **THEN** that hour's `column_water_vapour` is unavailable
- **AND** that provider's other variables for the hour are unaffected

### Requirement: The catalog offers the computed source

The catalog SHALL offer an entry with the key `computed` and the display name
`Computed`. It SHALL need no key. It SHALL declare `transparency` then
`seeing`, and no bundle. It SHALL NOT declare cloud cover. It SHALL fetch
nothing from any network. It SHALL be listed in the provider order and accepted
like any provider. Listing it SHALL NOT require any other provider to be listed.

#### Scenario: The catalog offers the computed source

- **WHEN** the catalog is read
- **THEN** it holds `computed` with the display name `Computed`, needing no key
- **AND** its declaration lists `transparency` then `seeing`, and no bundle

#### Scenario: The computed source is accepted in the provider list

- **WHEN** the configuration lists `providers: [open_meteo, computed, seven_timer]`
- **THEN** startup succeeds and the provider order is `open_meteo`, `computed`, `seven_timer`

#### Scenario: The computed source alone does not satisfy the cloud rule

- **WHEN** the configuration lists `providers: [computed, seven_timer]`
- **THEN** startup fails with an error that says the list must include a provider that needs no key and supplies cloud cover

#### Scenario: Listing the computed source without its inputs does not stop startup

- **WHEN** the configuration lists `providers: [open_meteo_hrdps, computed]`
- **THEN** startup succeeds

### Requirement: The computed source derives transparency from water vapour and aerosol

After every listed provider has been fetched, the computed source SHALL derive an
hourly transparency series from the filled `column_water_vapour` and
`aerosol_optical_depth` series. It SHALL read only those filled series, never
their alternates. Each value SHALL lie in `[0, 1]`, where 1 is best. Raising
either input while the other stays the same SHALL NOT raise the value. The
formula SHALL be the one the project's decision record for computed
transparency gives.

#### Scenario: An hour with both inputs gets a transparency value

- **WHEN** the filled `column_water_vapour` and `aerosol_optical_depth` series both carry a value for 22:00
- **THEN** the computed transparency series carries a value in `[0, 1]` for 22:00

#### Scenario: More aerosol never gives better transparency

- **WHEN** two hours carry the same `column_water_vapour`, and the first carries an `aerosol_optical_depth` of `0.05` where the second carries `0.60`
- **THEN** the second hour's computed transparency is not greater than the first's

#### Scenario: More water vapour never gives better transparency

- **WHEN** two hours carry the same `aerosol_optical_depth`, and the first carries a `column_water_vapour` of `5.0` where the second carries `35.0`
- **THEN** the second hour's computed transparency is not greater than the first's

#### Scenario: Only the filled input series are read

- **WHEN** the filled `column_water_vapour` series carries `open_meteo` with `10.0` at 22:00, and an alternate from `open_meteo_gfs` carries `30.0` at 22:00
- **THEN** the computed transparency for 22:00 is the value derived from `10.0`

### Requirement: The computed series covers only hours both inputs cover

The computed transparency series SHALL cover only the hours that both input
series cover. An hour SHALL carry a value only when both inputs carry a value
for it. Otherwise the hour SHALL be blank.

#### Scenario: An hour missing one input is blank

- **WHEN** the filled `column_water_vapour` series carries a value for 22:00 and the filled `aerosol_optical_depth` series carries a blank for 22:00
- **THEN** the computed transparency series has 22:00 blank

#### Scenario: The series covers only hours both inputs cover

- **WHEN** the filled `column_water_vapour` series covers 18:00 to 23:00 and the filled `aerosol_optical_depth` series covers 20:00 to 03:00
- **THEN** the computed transparency series covers 20:00 to 23:00 and no other hour

### Requirement: The computed source fills transparency at its place in the order

The computed transparency series SHALL take part in the fill for `transparency`
at the computed source's place in the provider order, exactly as a provider's
series would. It SHALL count as returned when at least one hour carries a
value. When it does not fill `transparency`, it SHALL be kept as an alternate,
as any later provider's series is.

#### Scenario: Listed ahead of 7Timer!, the computed source fills transparency

- **WHEN** the order is `open_meteo`, `open_meteo_air_quality`, `computed`, `seven_timer`, the inputs and 7Timer! both give transparency for the dark window, and Open-Meteo returns no seeing column
- **THEN** the `transparency` series carries the key `computed`
- **AND** `transparency` has one alternate, carrying the key `seven_timer`
- **AND** the `seeing` series carries the key `seven_timer`

#### Scenario: In the default order, 7Timer! fills transparency

- **WHEN** the order is the default, and the inputs and 7Timer! both give transparency for the dark window
- **THEN** the `transparency` series carries the key `seven_timer`
- **AND** `transparency` has one alternate, carrying the key `computed`

#### Scenario: In the default order, the computed source fills transparency when 7Timer! fails

- **WHEN** the order is the default, 7Timer! cannot be reached, Open-Meteo and the air-quality forecast both return their transparency inputs for the dark window, and Open-Meteo returns no seeing column
- **THEN** the `transparency` series carries the key `computed`
- **AND** seeing is unavailable

#### Scenario: A computed series with no values leaves no series and no alternate

- **WHEN** the order is `open_meteo`, `computed`, `seven_timer`, and no listed provider returns `aerosol_optical_depth`
- **THEN** the `transparency` series carries the key `seven_timer`
- **AND** `transparency` has no alternate from `computed`

### Requirement: The computed series carries its oldest input's issue time

Each computed series SHALL carry the earliest issue time among the input series
it read. When none of its input series carries an issue time, it SHALL carry
none. Computed transparency reads `column_water_vapour` and
`aerosol_optical_depth`. Computed seeing reads the seeing column, which comes
from one provider, so it carries that provider's issue time.

#### Scenario: The older input's issue time is used

- **WHEN** the `column_water_vapour` series was issued at 21:05 and the `aerosol_optical_depth` series at 20:40
- **THEN** the computed transparency series carries an issue time of 20:40

#### Scenario: Each computed series keeps its own issue time

- **WHEN** the `column_water_vapour` series was issued at 21:05, the `aerosol_optical_depth` series at 20:40, and the seeing column at 21:05
- **THEN** the computed transparency series carries an issue time of 20:40
- **AND** the computed seeing series carries an issue time of 21:05

### Requirement: The seeing column has 36 variables

The seeing column SHALL be these variables, read from the Open-Meteo hourly
variable beside each: `temperature_<p>hpa` from `temperature_<p>hPa`,
`geopotential_height_<p>hpa` from `geopotential_height_<p>hPa`,
`wind_speed_300hpa` from `wind_speed_300hPa`, and `boundary_layer_height` from
`boundary_layer_height`. `<p>` SHALL be each of these 17 pressure levels, in hPa:
1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100
and 50.

#### Scenario: The column names every level

- **WHEN** the seeing column's variables are listed
- **THEN** there are 36, with `temperature_<p>hpa` and `geopotential_height_<p>hpa` for each of the 17 levels, then `wind_speed_300hpa` and `boundary_layer_height`
- **AND** no level is 70 hPa or 30 hPa

### Requirement: The seeing column is carried as reported

The snapshot SHALL carry the seeing column with no rounding or conversion:
temperatures in °C, geopotential heights in metres, the 300 hPa wind speed in
km/h, and boundary-layer height in metres above ground. An hour whose value is
blank SHALL leave that variable unavailable for that hour.

#### Scenario: A level temperature is carried unrounded

- **WHEN** the provider that filled the seeing column reports `temperature_850hPa` as `-3.27` for an hour
- **THEN** that hour in the snapshot carries `temperature_850hpa` `-3.27`

#### Scenario: The jet-stream wind is carried in km/h

- **WHEN** the provider that filled the seeing column reports `wind_speed_300hPa` as `142.6` for an hour
- **THEN** that hour in the snapshot carries `wind_speed_300hpa` `142.6`

#### Scenario: A blank level is unavailable

- **WHEN** the provider that filled the seeing column reports a blank `geopotential_height_500hPa` for an hour
- **THEN** that hour's `geopotential_height_500hpa` is unavailable
- **AND** that provider's other variables for the hour are unaffected

### Requirement: The seeing column is one bundle

Every provider that declares the seeing column SHALL declare all 36 of its
variables as one bundle, so that the whole column is filled from one provider
or not at all.

#### Scenario: The seeing column comes from one provider

- **WHEN** the order is `open_meteo_hrrr` then `open_meteo_gfs`, and HRRR returns only `boundary_layer_height` for the dark window while GFS returns the whole column
- **THEN** every seeing-column series carries the key `open_meteo_hrrr`
- **AND** `temperature_850hpa` has no value in any hour

#### Scenario: A provider that returned none of the column is passed over

- **WHEN** the order is `open_meteo_hrrr` then `open_meteo_gfs`, and HRRR returns cloud but no seeing-column value, while GFS returns the whole column
- **THEN** every seeing-column series carries the key `open_meteo_gfs`

### Requirement: The computed source derives seeing from the seeing column

After every listed provider has been fetched, the computed source SHALL derive an
hourly seeing series from the filled seeing-column series. It SHALL read only
those filled series, never their alternates. Each value SHALL lie in `[0, 1]`,
where 1 is best. The formula SHALL be the one the project's decision record for
computed seeing gives. It SHALL read only the number of bad layers, the
jet-stream speed `wind_speed_300hpa` and the boundary-layer height
`boundary_layer_height`.

#### Scenario: An hour with the whole column gets a seeing value

- **WHEN** every filled seeing-column series carries a value for 22:00
- **THEN** the computed seeing series carries a value in `[0, 1]` for 22:00

#### Scenario: Only the filled seeing column is read

- **WHEN** the filled seeing column carries `open_meteo` with a `wind_speed_300hpa` of `60.0` at 22:00, and an alternate from `open_meteo_gfs` carries `200.0` at 22:00
- **THEN** the computed seeing for 22:00 is the value derived from `60.0`

### Requirement: A worse column never gives better computed seeing

Adding a bad layer SHALL NOT raise computed seeing. A jet-stream speed between
18 and 126 km/h, which is 5 to 35 m/s, is good, and moving it further outside
that range SHALL NOT raise computed seeing. A deeper boundary layer SHALL NOT
raise computed seeing.

#### Scenario: More bad layers never give better seeing

- **WHEN** two hours carry the same jet-stream speed and boundary-layer height, and the second hour's column has one more bad layer than the first's
- **THEN** the second hour's computed seeing is not greater than the first's

#### Scenario: A stronger jet never gives better seeing

- **WHEN** two hours carry the same column and boundary-layer height, and the first carries a `wind_speed_300hpa` of `130.0` where the second carries `180.0`
- **THEN** the second hour's computed seeing is not greater than the first's

#### Scenario: A calmer jet below the good range never gives better seeing

- **WHEN** two hours carry the same column and boundary-layer height, and the first carries a `wind_speed_300hpa` of `15.0` where the second carries `5.0`
- **THEN** the second hour's computed seeing is not greater than the first's

#### Scenario: A deeper boundary layer never gives better seeing

- **WHEN** two hours carry the same column and jet-stream speed, and the first carries a `boundary_layer_height` of `200.0` where the second carries `1200.0`
- **THEN** the second hour's computed seeing is not greater than the first's

### Requirement: A bad layer is a strongly stable layer

A layer SHALL be the air between two adjacent pressure levels of the seeing
column. A layer SHALL be bad when, per 100 m of geopotential height across it,
its temperature falls by less than 0.476 K or rises. The test SHALL be the same
at every height.

#### Scenario: An inversion is a bad layer

- **WHEN** an hour's column has 850 hPa at 1500 m and 0.0 °C, and 800 hPa at 2000 m and 1.0 °C, and the pier's elevation is 100 m
- **THEN** the layer from 850 to 800 hPa is counted as bad

#### Scenario: A layer cooling at the standard rate is not bad

- **WHEN** an hour's column has 850 hPa at 1500 m and 0.0 °C, and 800 hPa at 2000 m and -3.25 °C
- **THEN** the layer from 850 to 800 hPa is not counted as bad

#### Scenario: A layer high up cooling at the standard rate is not bad

- **WHEN** an hour's column has 250 hPa at 10400 m and -45.0 °C, and 200 hPa at 11800 m and -54.1 °C
- **THEN** the layer from 250 to 200 hPa is not counted as bad

#### Scenario: A layer cooling slowly is bad

- **WHEN** an hour's column has 700 hPa at 3000 m and -5.0 °C, and 600 hPa at 4200 m and -9.8 °C
- **THEN** the layer from 700 to 600 hPa is counted as bad

### Requirement: Bad layers are counted between the pier's ground and the tropopause

A layer SHALL be counted only when the geopotential height of its lower level is
at or above the pier's elevation, and it lies below the tropopause. The
tropopause SHALL be the lowest level at 500 hPa or higher up from which the
next level up is higher and temperature falls by 2 K per km or less to it. When no level
qualifies, every layer above the pier's ground SHALL be counted.

#### Scenario: A layer below the pier's ground is not counted

- **WHEN** a pier's elevation is 400 m, and an hour's 1000 hPa level is at 120 m with a bad layer from 1000 to 975 hPa
- **THEN** that layer is not counted

#### Scenario: A stable layer above the tropopause is not counted

- **WHEN** an hour's temperature falls by more than 2 K per km in every layer from 500 to 250 hPa, falls by 1 K per km from 250 to 200 hPa, and the layer from 200 to 150 hPa is bad
- **THEN** the layers from 250 to 200 hPa and from 200 to 150 hPa are not counted

### Requirement: The computed seeing series covers only hours with the whole column

The computed seeing series SHALL cover only the hours the filled seeing column
covers. An hour SHALL carry a value only when every seeing-column variable
carries a value for it. Otherwise the hour SHALL be blank.

#### Scenario: An hour missing one level is blank

- **WHEN** the filled seeing column carries every variable for 22:00 except a blank `temperature_300hpa`
- **THEN** the computed seeing series has 22:00 blank

#### Scenario: An hour missing the boundary layer is blank

- **WHEN** the filled seeing column carries every variable for 23:00 except a blank `boundary_layer_height`
- **THEN** the computed seeing series has 23:00 blank

### Requirement: The computed source fills seeing at its place in the order

The computed seeing series SHALL take part in the fill for `seeing` at the
computed source's place in the provider order, exactly as a provider's series
does. A computed seeing series with no value SHALL take no part in the fill.

#### Scenario: Listed ahead of 7Timer!, the computed source fills seeing

- **WHEN** the order is `open_meteo`, `computed`, `seven_timer`, and both the seeing column and 7Timer! give seeing values for the dark window
- **THEN** the `seeing` series carries the key `computed`
- **AND** `seeing` has one alternate, carrying the key `seven_timer`

#### Scenario: In the default order, 7Timer! fills seeing

- **WHEN** the order is the default, and every provider returns readings for the dark window
- **THEN** the `seeing` series carries the key `seven_timer`
- **AND** `seeing` has one alternate, carrying the key `computed`

#### Scenario: In the default order, the computed source fills seeing when 7Timer! fails

- **WHEN** the order is the default, 7Timer! fails, and `open_meteo` returns the seeing column for the dark window
- **THEN** the `seeing` series carries the key `computed`

### Requirement: A model provider's issue time is its model's latest run

Each model provider SHALL record its model's latest run start, as Open-Meteo's
metadata reports it, as the issue time of every series it fills. Its fetch
outcome SHALL carry the same issue time. The `open_meteo` and
`open_meteo_air_quality` providers SHALL keep recording the time of their fetch.

#### Scenario: A model provider carries its run start

- **WHEN** `open_meteo_rdps` is fetched at 21:05, its forecast returns readings, and its metadata reports a latest run that started at 12:00
- **THEN** each series it fills carries an issue time of 12:00
- **AND** its fetch outcome is successful and carries 12:00 as its issue time

#### Scenario: The provider carries the run start, not when the run became available

- **WHEN** a model provider's metadata reports a latest run that started at 18:00 and became available at 21:22
- **THEN** each series that provider fills carries an issue time of 18:00

#### Scenario: Plain Open-Meteo still stamps the fetch time

- **WHEN** `open_meteo` is fetched at 21:05 and returns readings
- **THEN** each series it fills carries an issue time of 21:05
- **AND** no request goes to Open-Meteo's metadata endpoint

### Requirement: A model provider reads its run time from one metadata file

Each model provider SHALL read its run time from Open-Meteo's metadata at
`https://api.open-meteo.com/data/<name>/static/meta.json`, where `<name>` is
fixed per provider. It SHALL read no other metadata file. It SHALL take the
run start from the file's `last_run_initialisation_time`, given in seconds
since the Unix epoch, in UTC.

#### Scenario: Each model provider reads its own metadata file

- **WHEN** each model provider is fetched for a pier
- **THEN** it reads exactly this metadata file and no other:

  | Key | Metadata name |
  |---|---|
  | `open_meteo_hrrr` | `ncep_hrrr_conus` |
  | `open_meteo_hrdps` | `cmc_gem_hrdps` |
  | `open_meteo_rdps` | `cmc_gem_rdps_10km` |
  | `open_meteo_icon` | `dwd_icon` |
  | `open_meteo_gfs` | `ncep_gfs013` |
  | `open_meteo_ecmwf` | `ecmwf_ifs` |

#### Scenario: The epoch time is read as UTC

- **WHEN** a model provider's metadata gives `last_run_initialisation_time` as `1793901600`
- **THEN** each series that provider fills carries an issue time of 2026-11-05 18:00 UTC

### Requirement: A model provider with no run time succeeds with a null issue time

When a model provider's forecast returns readings but it cannot read a run
time, the fetch SHALL succeed with a null error, and a null issue time on its
outcome and every series it fills. It cannot read a run time when the metadata
request fails, the body is not a JSON object, or `last_run_initialisation_time`
is missing, not a whole number, or outside the range of a date. A forecast that
fails, or returns no readings, SHALL fail the fetch as for any provider.

#### Scenario: The metadata request fails

- **WHEN** `open_meteo_gfs` is fetched, its forecast returns readings, and its metadata request answers with status 503
- **THEN** each series it fills carries a null issue time
- **AND** its fetch outcome is successful, with a null error and a null issue time

#### Scenario: The metadata gives no run time

- **WHEN** `open_meteo_icon` is fetched, its forecast returns readings, and its metadata response has no `last_run_initialisation_time`
- **THEN** each series it fills carries a null issue time
- **AND** its fetch outcome is successful, with a null error and a null issue time

#### Scenario: The metadata body is not JSON

- **WHEN** `open_meteo_hrdps` is fetched, its forecast returns readings, and its metadata request answers with status 200 and an HTML page
- **THEN** each series it fills carries a null issue time
- **AND** its fetch outcome is successful, with a null error and a null issue time

#### Scenario: The forecast fails while the metadata answers

- **WHEN** `open_meteo_hrrr` is fetched, its forecast request answers with status 500, and its metadata reports a run that started at 02:00
- **THEN** its fetch outcome is failed, with the error kind and `500`, and a null issue time
- **AND** it fills no series

### Requirement: Cloud data carries low, mid and high layers beside the total

For each hour of the dark window, the cloud data SHALL carry, in addition to the
total cloud cover, a split into three layer components — low, mid, and high — so
the verdict can tell a low deck that blocks the view apart from high, thin cirrus
that leaves a near-clear total reading yet degrades transparency. The total and
its three components SHALL form one bundle, filled from the same provider.

#### Scenario: Cloud data carries the layer split alongside the total

- **WHEN** conditions are obtained for a pier whose selected night has a dark window and the provider that filled cloud cover reports a low/mid/high cloud split
- **THEN** each hour's cloud data carries a total cloud cover plus low, mid, and high component values
- **AND** each component is marked available

### Requirement: Each cloud layer is marked available on its own

Each of the low, mid and high cloud components SHALL be marked available or
unavailable independently, following the same per-variable availability rule as
the rest of the snapshot: one component may be present while another is absent,
and any component may be absent while the total cloud cover remains present and
usable.

#### Scenario: A component can be absent while others and the total remain present

- **WHEN** the provider reports total cloud cover and some but not all of the low/mid/high components for an hour
- **THEN** the components that were reported are marked available with their values
- **AND** the components that were not reported are marked unavailable
- **AND** the absence of a component is not reported as an error

### Requirement: The layer split leaves the total cloud cover unchanged

The low, mid and high component split SHALL be additive to the existing
cloud-cover slot. The meaning of the total cloud-cover value SHALL NOT change,
and a provider that reports only a total SHALL still yield a valid snapshot with
the components marked unavailable.

#### Scenario: A total-only source yields a valid snapshot with components unavailable

- **WHEN** the provider that filled cloud cover reports total cloud cover but no low/mid/high split
- **THEN** the snapshot is returned with total cloud cover available and the low, mid, and high components marked unavailable
- **AND** the total cloud-cover value carries the same meaning as before the split was added

### Requirement: A fetch reports one outcome per provider in order

Each time the system fetches conditions for a pier, it SHALL report one outcome for
each provider in the configured order, in that order. An outcome SHALL name the
provider and the variables it declares. It SHALL record when the fetch ran and
whether it succeeded or failed.

#### Scenario: An outcome names the provider's declared variables

- **WHEN** 7Timer! is fetched for a pier
- **THEN** its outcome names `seven_timer` and the variables `seeing` and `transparency`

### Requirement: A successful outcome carries its data's issue time

A successful outcome SHALL carry the issue time the provider gave for its data,
or null when it gave none.

#### Scenario: A successful fetch is reported with its issue time

- **WHEN** a provider returns readings for a pier
- **THEN** its outcome for that fetch is reported as successful
- **AND** the outcome carries the time the fetch ran and the issue time of the returned data

### Requirement: A failed outcome carries a short error description

A failed outcome SHALL carry a short error description.

#### Scenario: A failed fetch is reported with a short error

- **WHEN** a provider's fetch for a pier raises an error
- **THEN** its outcome for that fetch is reported as failed
- **AND** the outcome carries the kind of error

### Requirement: A fetch that returns no readings is reported as failed

A fetch that returns no readings SHALL be reported as failed, with an error that
says no readings were returned.

#### Scenario: An empty fetch is reported as failed

- **WHEN** a provider's fetch for a pier completes but returns no readings
- **THEN** its outcome for that fetch is reported as failed
- **AND** its error says that no readings were returned

### Requirement: A fetch that returns readings is reported as successful

A fetch that returns readings SHALL be reported as successful, even when some
variables in those readings are blank, and whether or not the fill used any of
them.

#### Scenario: A provider the fill passed over still reports success

- **WHEN** a provider returns readings for a pier but an earlier provider in order already filled every variable it declares
- **THEN** its outcome for that fetch is reported as successful

#### Scenario: Blank fields do not make a fetch fail

- **WHEN** a provider returns readings for a pier and some variables in those readings are blank
- **THEN** its outcome for that fetch is reported as successful

### Requirement: An outcome's error description is built only from safe parts

An outcome's error description SHALL be built only from a fixed set of safe parts:

- the kind of error
- for an HTTP error response, its status code and that code's standard phrase
- fixed messages, such as the one for an empty fetch

#### Scenario: An HTTP error response is reported with its status

- **WHEN** a provider answers a fetch for a pier with an HTTP error status, such as 503
- **THEN** its outcome for that fetch is reported as failed
- **AND** the error gives the kind of error, the status code, and that code's standard phrase

### Requirement: An outcome's error description copies no text from the error or the response

An outcome's error description SHALL NOT include any text from the error or from
the provider's response. That includes the reason phrase the provider's server
sends. So the description never contains the request URL or the pier's
coordinates.

#### Scenario: A server's own reason phrase is never copied

- **WHEN** a provider answers with status 503 and a reason phrase that contains the pier's latitude
- **THEN** the reported error gives the standard phrase for 503
- **AND** it does not contain the latitude

#### Scenario: The error never contains the request URL or coordinates

- **WHEN** a provider's fetch fails with an error whose own message includes the request URL
- **THEN** the reported error contains neither the URL nor the pier's latitude and longitude

#### Scenario: The error never contains coordinates outside a URL

- **WHEN** a provider's fetch fails with an error whose own message includes the pier's latitude, with no URL
- **THEN** the reported error does not contain the latitude

### Requirement: Fetch outcomes never reach the verdict

The fetch outcomes SHALL NOT reach the verdict. The verdict, score, confidence,
and reasons SHALL depend only on the snapshot, never on the outcomes.

#### Scenario: Outcomes do not change the verdict

- **WHEN** two verdicts are produced for the same pier, instant, and snapshot, with different fetch outcomes
- **THEN** the two verdict documents are byte-identical

### Requirement: The computed outcome carries an error for each variable that computed nothing

The computed source's outcome SHALL carry an error for each computed variable
whose series carries no value, and only for those. Each such variable's part
SHALL be its key, a colon and a space, then a fixed reason that says why it
computed nothing. The parts SHALL be joined by a semicolon and a space,
transparency first. When every computed variable carries a value, the outcome
SHALL carry no error. An outcome that is successful SHALL still carry the error
for a variable that failed.

#### Scenario: Both variables computed carry no error

- **WHEN** both computed series carry values
- **THEN** the `computed` outcome is reported as successful with no error

### Requirement: A computed error names the inputs that have no filled series

When one or more inputs of a computed variable have no filled series, the
reason in that variable's error part SHALL be `missing input: <inputs>`. For
transparency, `<inputs>` lists each missing input key, `column_water_vapour`
before `aerosol_optical_depth`, separated by a comma and a space. For seeing,
`<inputs>` is `seeing column`.

#### Scenario: A missing aerosol input is named

- **WHEN** the order is `open_meteo`, `seven_timer`, `computed`, no listed provider returns `aerosol_optical_depth`, and `open_meteo` returns the seeing column
- **THEN** the `computed` outcome is reported as successful with the error `transparency: missing input: aerosol_optical_depth`

#### Scenario: Both missing inputs are named in order

- **WHEN** the order is `open_meteo_hrdps`, `computed`
- **THEN** the `computed` outcome is reported as failed with the error `transparency: missing input: column_water_vapour, aerosol_optical_depth; seeing: missing input: seeing column`

### Requirement: A computed error says when no hour has every input

When every input of a computed variable has a filled series but no hour carries
a value for all of them, the reason in that variable's error part SHALL be
`no hour has every input`.

#### Scenario: Inputs that never share a valued hour are reported

- **WHEN** both transparency inputs have a filled series, every hour that carries a value in one is blank or absent in the other, and computed seeing carries values
- **THEN** the `computed` outcome is reported as successful with the error `transparency: no hour has every input`

#### Scenario: A column with a blank in every hour is reported

- **WHEN** the seeing column has a filled series, every hour has at least one blank seeing-column variable, and computed transparency carries values
- **THEN** the `computed` outcome is reported as successful with the error `seeing: no hour has every input`

### Requirement: A computed error gives the kind of error a derivation raised

When the derivation of a computed variable raised an error, the reason in that
variable's error part SHALL be the kind of error.

#### Scenario: A raising derivation fails only its own variable

- **WHEN** the seeing derivation raises a `ValueError`, and computed transparency carries values
- **THEN** the `computed` outcome is reported as successful with the error `seeing: ValueError`
- **AND** the `transparency` series carries the key `computed`

### Requirement: The first provider in order that returned a variable fills its series

The snapshot SHALL hold one series per variable, carrying one provider's hourly
values, that provider's key and the issue time of its data. For each variable,
the series SHALL come from the first provider in the configured order that
returned it. A provider returned a variable when at least one hour of its
forecast carries a value for it, or for another variable in the same bundle.
A variable no provider filled SHALL have no series.

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

### Requirement: A provider fills a bundle whole or not at all

The variables of a bundle SHALL come from the same provider. A provider SHALL
fill a bundle whole or not at all. When an earlier provider already holds any
member of the bundle as this provider declares it, this provider fills none of
the bundle's members.

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

### Requirement: The computed source reports one outcome at its place in the order

The computed source SHALL report one outcome on each fetch, at its place in the
provider order, naming `computed` and the variables `transparency` and
`seeing`. The outcome SHALL record when the computation ran.

#### Scenario: The outcome sits at the computed source's place in the order

- **WHEN** the order is `open_meteo`, `computed`, `seven_timer`
- **THEN** the outcomes are reported for `open_meteo`, `computed` and `seven_timer`, in that order

### Requirement: The computed outcome succeeds when a computed hour carries a value

When at least one hour of at least one computed series carries a value, the
computed source's outcome SHALL be successful. Otherwise it SHALL be failed.

#### Scenario: A computed hour makes the outcome successful

- **WHEN** both transparency inputs carry values for at least one hour, and no provider returned the seeing column
- **THEN** the `computed` outcome is reported as successful
- **AND** it carries the time the computation ran and the computed transparency series' issue time

### Requirement: A successful computed outcome carries the oldest computed issue time

A successful outcome of the computed source SHALL carry the earliest issue time
among the computed series that carry a value.

#### Scenario: The outcome's issue time is the oldest computed one

- **WHEN** the computed transparency series carries an issue time of 20:40 and the computed seeing series 21:05
- **THEN** the `computed` outcome carries an issue time of 20:40

### Requirement: A successful computed outcome names the providers each variable read

A successful outcome of the computed source SHALL carry its inputs: for each
computed variable whose series carries a value, the keys of the providers whose
filled series it read, each key once, in the order of that variable's inputs.
For transparency, the provider of `column_water_vapour` comes before the
provider of `aerosol_optical_depth`.

#### Scenario: The outcome names the providers each variable read

- **WHEN** `column_water_vapour` was filled by `open_meteo`, `aerosol_optical_depth` by `open_meteo_air_quality`, and the seeing column by `open_meteo_hrrr`, and both computed series carry values
- **THEN** the `computed` outcome's inputs give `transparency` as `open_meteo`, `open_meteo_air_quality`, and `seeing` as `open_meteo_hrrr`

#### Scenario: A provider that fed both transparency inputs is named once

- **WHEN** `column_water_vapour` and `aerosol_optical_depth` were both filled by the same provider, `stub`
- **THEN** the `computed` outcome's inputs give `transparency` as `stub` alone

#### Scenario: A failed variable has no inputs

- **WHEN** computed seeing carries values and computed transparency carries none
- **THEN** the `computed` outcome's inputs give `seeing` and do not give `transparency`

### Requirement: Each later provider that returned a variable leaves an alternate

For each variable, the snapshot SHALL keep as alternates the series of every
provider after the filling one, in configured order, that returned the variable:
at least one hour of its forecast carries a value for it, or for another
variable in the same bundle. An alternate SHALL carry that provider's hourly
values, its key and the issue time of its data, exactly as a filled series does.

#### Scenario: A later provider's cloud becomes an alternate

- **WHEN** the order is `open_meteo` then `open_meteo_hrrr`, both return `cloud_cover` for the dark window, and the first gives `40` for 21:00 where the second gives `70`
- **THEN** the `cloud_cover` series carries `open_meteo` and `40` at 21:00
- **AND** `cloud_cover` has one alternate, carrying `open_meteo_hrrr`, its issue time and `70` at 21:00

#### Scenario: Alternates keep the configured order

- **WHEN** three providers in order each return `cloud_cover`
- **THEN** `cloud_cover` has two alternates, the second provider's first and the third provider's second

#### Scenario: A losing bundle becomes alternates member by member

- **WHEN** the first provider in order returns `cloud_cover` but no layer, and the second returns `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`
- **THEN** each of the four variables has one alternate carrying the second provider's key
- **AND** the filled `cloud_low`, `cloud_mid` and `cloud_high` series still carry the first provider's key with no values

### Requirement: A provider that returned nothing or failed leaves no alternate

A provider that returned nothing for a variable, or whose fetch failed, SHALL
leave no alternate for it.

#### Scenario: A provider that returned nothing leaves no alternate

- **WHEN** the second provider in order returns rows whose `cloud_cover` is blank in every hour
- **THEN** `cloud_cover` has no alternate from that provider

#### Scenario: A failed provider leaves no alternate

- **WHEN** the second provider in order fails to fetch
- **THEN** no variable has an alternate from that provider
- **AND** the snapshot is otherwise the same as if that provider were not listed

### Requirement: Alternates never change the filled series

The filled series, the hours it covers and the value it gives for each hour
SHALL be the same as they would be with no alternates.

#### Scenario: An alternate never fills an hour the filled series lacks

- **WHEN** the first provider in order returns `cloud_cover` for 20:00 to 23:00 only, and the second returns `cloud_cover` for 20:00 to 03:00
- **THEN** the `cloud_cover` value for 01:00 is unavailable
- **AND** the alternate carries the second provider's values for 20:00 to 03:00

#### Scenario: Alternates do not change the verdict's cloud reading

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in whether a `cloud_cover` alternate is present
- **THEN** the two documents have the same `verdict`, `score`, `scored_window` and `timeline` cloud-cover values

### Requirement: Each NWS value is held across every hour its period covers

Each NWS value SHALL be held across every clock hour its period covers, so the
result is on the same hourly grid as every other provider. Precipitation
probability is the exception, as its own requirement says. Hours within the
provider's 72-hour horizon that no period covers SHALL stay absent.

#### Scenario: A three-hour period is held across its hours

- **WHEN** NWS reports sky cover `45` for the period starting at 21:00 lasting three hours
- **THEN** the readings for 21:00, 22:00 and 23:00 each carry a cloud cover of `45`

#### Scenario: A period spanning days is held across its hours

- **WHEN** NWS reports a wind speed for a period starting at 06:00 lasting one day and six hours
- **THEN** the readings from 06:00 to 11:00 the next day each carry that wind speed

#### Scenario: Periods for different variables stay independent

- **WHEN** NWS reports sky cover for 21:00 to 23:00 and temperature for 21:00 only
- **THEN** the readings for 22:00 and 23:00 carry a cloud cover and no temperature

### Requirement: An NWS precipitation probability is held one hour after its period's hours

Because an NWS precipitation probability value at an hour is the chance for the
hour that ends there, each precipitation probability value SHALL be held on the
clock hours one hour after each hour its period covers.

#### Scenario: A precipitation probability period is held on the hours that end within it

- **WHEN** NWS reports a precipitation probability of `40` for the period starting at 18:00 lasting six hours
- **THEN** the readings for 19:00, 20:00, 21:00, 22:00, 23:00 and 00:00 the next day each carry a precipitation probability of `40`
- **AND** the reading for 18:00, if one exists, carries no precipitation probability

#### Scenario: Precipitation probability moves and the other variables do not

- **WHEN** NWS reports sky cover `45` and a precipitation probability of `20`, each for the period starting at 21:00 lasting one hour
- **THEN** the reading for 21:00 carries a cloud cover of `45` and no precipitation probability
- **AND** the reading for 22:00 carries a precipitation probability of `20` and no cloud cover

### Requirement: NWS keeps only hours within 72 hours of the earliest period start

The NWS provider SHALL keep only hours within 72 hours of the earliest period
start in the payload. Hours past that horizon SHALL be dropped, precipitation
probability hours included.

#### Scenario: A period that straddles the horizon is cut at it

- **WHEN** the earliest period in the payload starts at 18:00 on day one, and a sky cover period starts at 16:00 on day four lasting three hours
- **THEN** the readings for 16:00 and 17:00 on day four carry that sky cover
- **AND** no reading exists for 18:00 on day four

#### Scenario: A precipitation probability hour at the horizon is cut

- **WHEN** the earliest period in the payload starts at 18:00 on day one, and a precipitation probability period starts at 16:00 on day four lasting two hours
- **THEN** the reading for 17:00 on day four carries that precipitation probability
- **AND** no reading exists for 18:00 on day four

#### Scenario: A period that starts past the horizon is dropped

- **WHEN** the earliest period in the payload starts at 18:00 on day one, and a period starts at 19:00 on day four
- **THEN** no reading exists for 19:00 on day four

### Requirement: HRRR and GFS declare the same variables as Open-Meteo

The HRRR and GFS model providers SHALL declare the same variables and bundles as
`open_meteo`.

#### Scenario: HRRR declares the same variables as Open-Meteo

- **WHEN** the `open_meteo_hrrr` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability` and `column_water_vapour`, then the 36 seeing-column variables
- **AND** it has the cloud bundle and the seeing-column bundle

#### Scenario: GFS declares column water vapour

- **WHEN** the `open_meteo_gfs` provider's declaration is read
- **THEN** it lists `column_water_vapour` and the 36 seeing-column variables

### Requirement: ICON declares neither column water vapour nor the seeing column

The ICON model provider SHALL declare the same variables and the cloud bundle as
`open_meteo`, except `column_water_vapour` and the seeing column, which that
model does not fully supply.

#### Scenario: ICON declares no column water vapour

- **WHEN** the `open_meteo_icon` provider's declaration is read
- **THEN** it lists `precipitation_probability`
- **AND** it lists neither `column_water_vapour` nor any seeing-column variable
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

### Requirement: HRDPS and RDPS declare no precipitation probability

The HRDPS and RDPS model providers SHALL declare the same variables and the
cloud bundle as `open_meteo`, except `precipitation_probability`,
`column_water_vapour` and the seeing column, which those models do not fully
supply.

#### Scenario: HRDPS declares no precipitation probability

- **WHEN** the `open_meteo_hrdps` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed` and `wind_direction`
- **AND** it lists neither `precipitation_probability`, `column_water_vapour` nor any seeing-column variable
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: Precipitation probability comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo`, and both return readings for the dark window
- **THEN** the `precipitation_probability` series carries the key `open_meteo`

#### Scenario: Column water vapour comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo_gfs`, and both return readings for the dark window
- **THEN** the `column_water_vapour` series carries the key `open_meteo_gfs`

### Requirement: A provider that does not declare the seeing column declares none of its variables

A provider that does not declare the seeing column SHALL declare no
seeing-column variable.

#### Scenario: RDPS declares no seeing column

- **WHEN** the `open_meteo_rdps` provider's declaration is read
- **THEN** it lists no seeing-column variable

#### Scenario: The seeing column comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo_gfs`, and both return readings for the dark window
- **THEN** every seeing-column series carries the key `open_meteo_gfs`

### Requirement: Every Open-Meteo hourly request asks for 4 past hours and 72 forecast hours

Every request to Open-Meteo for hourly data SHALL ask for the 4 hours before the
fetch and the 72 hours from the fetch on, whatever the time of day in UTC. This
SHALL hold for `open_meteo`, for each model provider and for
`open_meteo_air_quality`. A model provider's metadata request asks for no hours,
because the metadata file takes no parameters.

#### Scenario: Every Open-Meteo provider asks for the same hours

- **WHEN** `open_meteo`, `open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`, `open_meteo_icon`, `open_meteo_gfs`, `open_meteo_ecmwf` and `open_meteo_air_quality` are each fetched for a pier
- **THEN** each request for hourly data asks for 4 past hours and 72 forecast hours
- **AND** no request asks for a number of forecast days
- **AND** each request for hourly data asks for times in UTC

#### Scenario: The hours asked for do not depend on the time of day

- **WHEN** `open_meteo` is fetched for a pier at 00:05 UTC, and again at 18:05 UTC
- **THEN** both requests ask for 4 past hours and 72 forecast hours

### Requirement: An Open-Meteo hourly request asks for no forecast days and for UTC times

No request to Open-Meteo for hourly data SHALL ask for a number of forecast
days, because Open-Meteo starts a day's forecast at midnight in the request's
time zone. Each such request SHALL keep asking for times in UTC.

#### Scenario: A request just after midnight asks for no forecast days and for UTC

- **WHEN** any Open-Meteo provider is fetched for a pier at 00:05 UTC
- **THEN** its request for hourly data asks for no number of forecast days
- **AND** it asks for times in UTC
