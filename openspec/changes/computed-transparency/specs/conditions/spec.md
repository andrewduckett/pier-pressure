## MODIFIED Requirements

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

### Requirement: Each provider declares its variables and bundles

Each provider SHALL declare the variables it supplies, named by their variable
keys, and which of them form a bundle. A variable key need not be a timeline
key. A declaration SHALL be fixed: it SHALL NOT change with what a fetch
returned.

#### Scenario: Open-Meteo declares the cloud bundle and the weather variables

- **WHEN** the Open-Meteo provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability` and `column_water_vapour`
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: 7Timer! declares seeing and transparency

- **WHEN** the 7Timer! provider's declaration is read
- **THEN** it lists `seeing` and `transparency` and no bundle

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
- **THEN** the hourly variables in its request include neither precipitation probability nor `total_column_integrated_water_vapour`

#### Scenario: Plain Open-Meteo still asks for best match

- **WHEN** `open_meteo` is fetched for a pier
- **THEN** its request to Open-Meteo names no model
- **AND** it asks for twelve hourly variables: the eleven it asked for before this change, and `total_column_integrated_water_vapour`
- **AND** it asks for the same forecast length and units as before this change

### Requirement: Each Open-Meteo model declares the variables its model returns

The HRRR and GFS model providers SHALL declare the same variables and bundle as
`open_meteo`. The ICON model provider SHALL declare the same variables and
bundle except `column_water_vapour`, which that model does not supply. The
HRDPS and RDPS model providers SHALL declare the same variables and bundle
except `precipitation_probability` and `column_water_vapour`, which those
models do not supply.

#### Scenario: HRRR declares the same variables as Open-Meteo

- **WHEN** the `open_meteo_hrrr` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability` and `column_water_vapour`
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: GFS declares column water vapour

- **WHEN** the `open_meteo_gfs` provider's declaration is read
- **THEN** it lists `column_water_vapour`

#### Scenario: ICON declares no column water vapour

- **WHEN** the `open_meteo_icon` provider's declaration is read
- **THEN** it lists `precipitation_probability`
- **AND** it does not list `column_water_vapour`

#### Scenario: HRDPS declares no precipitation probability

- **WHEN** the `open_meteo_hrdps` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed` and `wind_direction`
- **AND** it lists neither `precipitation_probability` nor `column_water_vapour`
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: Precipitation probability comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo`, and both return readings for the dark window
- **THEN** the `precipitation_probability` series carries the key `open_meteo`

#### Scenario: Column water vapour comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo_gfs`, and both return readings for the dark window
- **THEN** the `column_water_vapour` series carries the key `open_meteo_gfs`

## ADDED Requirements

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
`Computed`. It SHALL need no key. It SHALL declare `transparency`, and no
bundle. It SHALL NOT declare cloud cover. It SHALL fetch nothing from any
network. It SHALL be listed in the provider order and accepted like any
provider. Listing it SHALL NOT require any other provider to be listed.

#### Scenario: The catalog offers the computed source

- **WHEN** the catalog is read
- **THEN** it holds `computed` with the display name `Computed`, needing no key
- **AND** its declaration lists `transparency` alone, and no bundle

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

- **WHEN** the order is `open_meteo`, `open_meteo_air_quality`, `computed`, `seven_timer`, and the inputs and 7Timer! both give transparency for the dark window
- **THEN** the `transparency` series carries the key `computed`
- **AND** `transparency` has one alternate, carrying the key `seven_timer`
- **AND** the `seeing` series carries the key `seven_timer`

#### Scenario: In the default order, 7Timer! fills transparency

- **WHEN** the order is the default, and the inputs and 7Timer! both give transparency for the dark window
- **THEN** the `transparency` series carries the key `seven_timer`
- **AND** `transparency` has one alternate, carrying the key `computed`

#### Scenario: In the default order, the computed source fills transparency when 7Timer! fails

- **WHEN** the order is the default, 7Timer! cannot be reached, and Open-Meteo and the air-quality forecast both return their inputs for the dark window
- **THEN** the `transparency` series carries the key `computed`
- **AND** seeing is unavailable

#### Scenario: A computed series with no values leaves no series and no alternate

- **WHEN** the order is `open_meteo`, `computed`, `seven_timer`, and no listed provider returns `aerosol_optical_depth`
- **THEN** the `transparency` series carries the key `seven_timer`
- **AND** `transparency` has no alternate from `computed`

### Requirement: The computed series carries its oldest input's issue time

The computed transparency series SHALL carry the earlier of the issue times of
the two input series it read. When neither input series carries an issue
time, it SHALL carry none. When only one does, it SHALL carry that one.

#### Scenario: The older input's issue time is used

- **WHEN** the `column_water_vapour` series was issued at 21:05 and the `aerosol_optical_depth` series at 20:40
- **THEN** the computed transparency series carries an issue time of 20:40

### Requirement: The computed source reports an outcome like a provider

The computed source SHALL report one outcome on each fetch, at its place in the
provider order, naming `computed` and the variable `transparency`. The outcome
SHALL record when the computation ran. When at least one hour carries a value,
the outcome SHALL be successful and carry the computed series' issue time.
Otherwise it SHALL be failed.

#### Scenario: A computed hour makes the outcome successful

- **WHEN** both inputs carry values for at least one hour
- **THEN** the `computed` outcome is reported as successful
- **AND** it carries the time the computation ran and the computed series' issue time

#### Scenario: The outcome sits at the computed source's place in the order

- **WHEN** the order is `open_meteo`, `computed`, `seven_timer`
- **THEN** the outcomes are reported for `open_meteo`, `computed` and `seven_timer`, in that order

### Requirement: A failed computed outcome says which input was missing

A failed outcome from the computed source SHALL carry one of two fixed errors:

- `missing input: <variables>`, when one or both inputs have no filled series.
  `<variables>` lists each missing input key, `column_water_vapour` before
  `aerosol_optical_depth`, separated by a comma and a space.
- `no hour has every input`, when both inputs have a filled series but no hour
  carries a value for both.

#### Scenario: A missing aerosol input is named

- **WHEN** the order is `open_meteo`, `seven_timer`, `computed`, and no listed provider returns `aerosol_optical_depth`
- **THEN** the `computed` outcome is reported as failed with the error `missing input: aerosol_optical_depth`

#### Scenario: Both missing inputs are named in order

- **WHEN** the order is `open_meteo_hrdps`, `computed`
- **THEN** the `computed` outcome is reported as failed with the error `missing input: column_water_vapour, aerosol_optical_depth`

#### Scenario: Inputs that never share a valued hour are reported

- **WHEN** both inputs have a filled series, and every hour that carries a value in one is blank or absent in the other
- **THEN** the `computed` outcome is reported as failed with the error `no hour has every input`
