## MODIFIED Requirements

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

## ADDED Requirements

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
