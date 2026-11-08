## ADDED Requirements

### Requirement: Every Open-Meteo request asks for the 4 hours before the fetch and the 72 after

Every request to Open-Meteo SHALL ask for the 4 hours before the fetch and the
72 hours from the fetch on, whatever the time of day in UTC. This SHALL hold for
`open_meteo`, for each model provider and for `open_meteo_air_quality`. No
request SHALL ask for a number of forecast days, because Open-Meteo starts a
day's forecast at midnight in the request's time zone. Each request SHALL keep
asking for times in UTC.

#### Scenario: Every Open-Meteo provider asks for the same hours

- **WHEN** `open_meteo`, `open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`, `open_meteo_icon`, `open_meteo_gfs` and `open_meteo_air_quality` are each fetched for a pier
- **THEN** each request asks for 4 past hours and 72 forecast hours
- **AND** no request asks for a number of forecast days
- **AND** each request asks for times in UTC

#### Scenario: The hours asked for do not depend on the time of day

- **WHEN** `open_meteo` is fetched for a pier at 00:05 UTC, and again at 18:05 UTC
- **THEN** both requests ask for 4 past hours and 72 forecast hours

## MODIFIED Requirements

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
