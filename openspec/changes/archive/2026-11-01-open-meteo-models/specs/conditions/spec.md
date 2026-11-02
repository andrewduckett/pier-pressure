## ADDED Requirements

### Requirement: Each Open-Meteo model is its own provider

The catalog SHALL offer five providers, each fetching one named Open-Meteo
model: HRRR, HRDPS, RDPS, ICON and GFS. Each model provider SHALL need no key,
and SHALL be listed, filled, fetched and reported like any other provider.

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
SHALL ask for the same forecast length and units as `open_meteo`, and only for
the variables it declares. The `open_meteo` provider SHALL keep fetching
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

- **AND** each request asks for 2 forecast days, with wind speed in km/h

#### Scenario: HRDPS does not ask for precipitation probability

- **WHEN** `open_meteo_hrdps` is fetched for a pier
- **THEN** the hourly variables in its request do not include precipitation probability

#### Scenario: Plain Open-Meteo still asks for best match

- **WHEN** `open_meteo` is fetched for a pier
- **THEN** its request to Open-Meteo names no model
- **AND** it asks for the same eleven hourly variables, forecast length and units as before this change

### Requirement: A model provider's issue time is its fetch time

Each model provider SHALL record the time of its fetch as the issue time of its
data, as `open_meteo` does, because the forecast response gives none.

#### Scenario: A model provider stamps the fetch time

- **WHEN** `open_meteo_rdps` is fetched at 21:05 and returns readings
- **THEN** each series it fills carries an issue time of 21:05

### Requirement: Each Open-Meteo model declares the variables its model returns

The HRRR, ICON and GFS model providers SHALL declare the same variables and
bundle as `open_meteo`. The HRDPS and RDPS model providers SHALL declare the
same variables and bundle except `precipitation_probability`, which those models
do not supply.

#### Scenario: HRRR declares the same variables as Open-Meteo

- **WHEN** the `open_meteo_hrrr` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction` and `precipitation_probability`
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: HRDPS declares no precipitation probability

- **WHEN** the `open_meteo_hrdps` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed` and `wind_direction`
- **AND** it does not list `precipitation_probability`
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: Precipitation probability comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo`, and both return readings for the dark window
- **THEN** the `precipitation_probability` series carries the key `open_meteo`

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
