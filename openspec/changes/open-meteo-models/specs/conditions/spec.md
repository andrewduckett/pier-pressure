## ADDED Requirements

### Requirement: Each Open-Meteo model is its own provider

The catalog SHALL offer five providers, each fetching one named Open-Meteo
model: HRRR, HRDPS, RDPS, ICON and GFS. Each model provider SHALL need no key,
and SHALL be listed, filled, fetched and reported like any other provider.

#### Scenario: The catalog offers the five model providers

- **WHEN** the catalog is read
- **THEN** it holds these providers, each with this display name and Open-Meteo model, and none needs a key:

  | Key | Display name | Open-Meteo model |
  |---|---|---|
  | `open_meteo_hrrr` | Open-Meteo HRRR | `ncep_hrrr_conus` |
  | `open_meteo_hrdps` | Open-Meteo HRDPS | `gem_hrdps_continental` |
  | `open_meteo_rdps` | Open-Meteo RDPS | `gem_regional` |
  | `open_meteo_icon` | Open-Meteo ICON | `icon_seamless` |
  | `open_meteo_gfs` | Open-Meteo GFS | `gfs_global` |

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

Each model provider SHALL ask Open-Meteo for its one model and no other, with
the same forecast length and units as `open_meteo`. The `open_meteo` provider
SHALL keep fetching Open-Meteo's best match, and SHALL name no model in its
request.

#### Scenario: A model provider asks for its model only

- **WHEN** `open_meteo_hrdps` is fetched for a pier
- **THEN** its request to Open-Meteo names the model `gem_hrdps_continental` and no other model
- **AND** it asks for 2 forecast days, with wind speed in km/h

#### Scenario: Plain Open-Meteo still asks for best match

- **WHEN** `open_meteo` is fetched for a pier
- **THEN** its request to Open-Meteo names no model

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

### Requirement: A model that does not cover the pier fails its fetch

When Open-Meteo answers a model provider's request with an HTTP error because
the model has no data for the pier's location, the system SHALL report that
fetch as failed, with the kind of error, the status code and that code's
standard phrase. The provider SHALL be passed over for every variable, as any
failed provider is. The system SHALL NOT reject such a provider at startup.

#### Scenario: HRRR for a pier outside its area fails and is passed over

- **WHEN** the order is `open_meteo_hrrr` then `open_meteo`, and Open-Meteo answers the HRRR request with status 400 because it has no data for the pier's location
- **THEN** the `open_meteo_hrrr` outcome is reported as failed, with an error that gives the kind of error, `400` and `Bad Request`
- **AND** the `cloud_cover` series carries the key `open_meteo`

#### Scenario: A model outside its area does not stop startup

- **WHEN** the configuration lists `providers: [open_meteo_hrrr, open_meteo]` for a pier at latitude 51.5 and longitude -0.12
- **THEN** startup succeeds
