## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Every Open-Meteo request asks for the 4 hours before the fetch and the 72 after

Every request to Open-Meteo for hourly data SHALL ask for the 4 hours before the
fetch and the 72 hours from the fetch on, whatever the time of day in UTC. This
SHALL hold for `open_meteo`, for each model provider and for
`open_meteo_air_quality`. No such request SHALL ask for a number of forecast
days, because Open-Meteo starts a day's forecast at midnight in the request's
time zone. Each such request SHALL keep asking for times in UTC. A model
provider's metadata request asks for no hours, because the metadata file takes
no parameters.

#### Scenario: Every Open-Meteo provider asks for the same hours

- **WHEN** `open_meteo`, `open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`, `open_meteo_icon`, `open_meteo_gfs` and `open_meteo_air_quality` are each fetched for a pier
- **THEN** each request for hourly data asks for 4 past hours and 72 forecast hours
- **AND** no request asks for a number of forecast days
- **AND** each request for hourly data asks for times in UTC

#### Scenario: The hours asked for do not depend on the time of day

- **WHEN** `open_meteo` is fetched for a pier at 00:05 UTC, and again at 18:05 UTC
- **THEN** both requests ask for 4 past hours and 72 forecast hours

## REMOVED Requirements

### Requirement: A model provider's issue time is its fetch time

**Reason**: The fetch time made a run 6 to 12 hours old look just issued, so
confidence overstated freshness. Each model provider now reads its model's
latest run from Open-Meteo's metadata.

**Migration**: Nothing to configure. A pier whose cloud comes from a model
provider sees confidence reflect the run's real age. Read the issue time as the
run start, or null when the provider could not read it.
