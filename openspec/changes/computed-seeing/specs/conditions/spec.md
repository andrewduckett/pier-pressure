## ADDED Requirements

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
column. A layer SHALL be bad when its potential temperature rises by more than
0.5 K per 100 m of geopotential height across it. Potential temperature at a
level SHALL be its temperature in kelvin times `(1000 / p) ^ 0.286`, for the
level's pressure `p` in hPa.

#### Scenario: An inversion is a bad layer

- **WHEN** an hour's column has 850 hPa at 1500 m and 0.0 °C, and 800 hPa at 2000 m and 1.0 °C, and the pier's elevation is 100 m
- **THEN** the layer from 850 to 800 hPa is counted as bad

#### Scenario: A layer cooling at the standard rate is not bad

- **WHEN** an hour's column has 850 hPa at 1500 m and 0.0 °C, and 800 hPa at 2000 m and -3.25 °C
- **THEN** the layer from 850 to 800 hPa is not counted as bad

### Requirement: Bad layers are counted between the pier's ground and the tropopause

A layer SHALL be counted only when the geopotential height of its lower level is
at or above the pier's elevation, and it lies below the tropopause. The
tropopause SHALL be the lowest level at 500 hPa or higher up from which
temperature falls by 2 K per km or less to the next level up. When no level
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

## MODIFIED Requirements

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
- **AND** they include no seeing-column variable

#### Scenario: Plain Open-Meteo still asks for best match

- **WHEN** `open_meteo` is fetched for a pier
- **THEN** its request to Open-Meteo names no model
- **AND** it asks for 48 hourly variables: the twelve it asked for before this change, and the 36 seeing-column variables
- **AND** it asks for the same forecast length and units as before this change

### Requirement: Each Open-Meteo model declares the variables its model returns

The HRRR and GFS model providers SHALL declare the same variables and bundles as
`open_meteo`. The ICON model provider SHALL declare the same variables and the
cloud bundle except `column_water_vapour` and the seeing column, which that
model does not fully supply. The HRDPS and RDPS model providers SHALL declare
the same variables and the cloud bundle except `precipitation_probability`,
`column_water_vapour` and the seeing column, which those models do not fully
supply. A provider that does not declare the seeing column SHALL declare no
seeing-column variable.

#### Scenario: HRRR declares the same variables as Open-Meteo

- **WHEN** the `open_meteo_hrrr` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability` and `column_water_vapour`, then the 36 seeing-column variables
- **AND** it has the cloud bundle and the seeing-column bundle

#### Scenario: GFS declares column water vapour

- **WHEN** the `open_meteo_gfs` provider's declaration is read
- **THEN** it lists `column_water_vapour` and the 36 seeing-column variables

#### Scenario: ICON declares no column water vapour

- **WHEN** the `open_meteo_icon` provider's declaration is read
- **THEN** it lists `precipitation_probability`
- **AND** it lists neither `column_water_vapour` nor any seeing-column variable
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: HRDPS declares no precipitation probability

- **WHEN** the `open_meteo_hrdps` provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed` and `wind_direction`
- **AND** it lists neither `precipitation_probability`, `column_water_vapour` nor any seeing-column variable
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: RDPS declares no seeing column

- **WHEN** the `open_meteo_rdps` provider's declaration is read
- **THEN** it lists no seeing-column variable

#### Scenario: Precipitation probability comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo`, and both return readings for the dark window
- **THEN** the `precipitation_probability` series carries the key `open_meteo`

#### Scenario: Column water vapour comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo_gfs`, and both return readings for the dark window
- **THEN** the `column_water_vapour` series carries the key `open_meteo_gfs`

#### Scenario: The seeing column comes from the next provider that declares it

- **WHEN** the order is `open_meteo_hrdps` then `open_meteo_gfs`, and both return readings for the dark window
- **THEN** every seeing-column series carries the key `open_meteo_gfs`

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

### Requirement: The computed source reports an outcome like a provider

The computed source SHALL report one outcome on each fetch, at its place in the
provider order, naming `computed` and the variables `transparency` and
`seeing`. The outcome SHALL record when the computation ran. When at least one
hour of at least one computed series carries a value, the outcome SHALL be
successful. Otherwise it SHALL be failed.

A successful outcome SHALL carry the earliest issue time among the computed
series that carry a value. It SHALL also carry its inputs: for each computed
variable whose series carries a value, the keys of the providers whose filled
series it read, each key once, in the order its inputs are listed above.

#### Scenario: A computed hour makes the outcome successful

- **WHEN** both transparency inputs carry values for at least one hour, and no provider returned the seeing column
- **THEN** the `computed` outcome is reported as successful
- **AND** it carries the time the computation ran and the computed transparency series' issue time

#### Scenario: The outcome's issue time is the oldest computed one

- **WHEN** the computed transparency series carries an issue time of 20:40 and the computed seeing series 21:05
- **THEN** the `computed` outcome carries an issue time of 20:40

#### Scenario: The outcome names the providers each variable read

- **WHEN** `column_water_vapour` was filled by `open_meteo`, `aerosol_optical_depth` by `open_meteo_air_quality`, and the seeing column by `open_meteo_hrrr`, and both computed series carry values
- **THEN** the `computed` outcome's inputs give `transparency` as `open_meteo`, `open_meteo_air_quality`, and `seeing` as `open_meteo_hrrr`

#### Scenario: A provider that fed both transparency inputs is named once

- **WHEN** `column_water_vapour` and `aerosol_optical_depth` were both filled by the same provider, `stub`
- **THEN** the `computed` outcome's inputs give `transparency` as `stub` alone

#### Scenario: A failed variable has no inputs

- **WHEN** computed seeing carries values and computed transparency carries none
- **THEN** the `computed` outcome's inputs give `seeing` and do not give `transparency`

#### Scenario: The outcome sits at the computed source's place in the order

- **WHEN** the order is `open_meteo`, `computed`, `seven_timer`
- **THEN** the outcomes are reported for `open_meteo`, `computed` and `seven_timer`, in that order

### Requirement: A failed computed outcome says which input was missing

The computed source's outcome SHALL carry an error for each computed variable
whose series carries no value, and only for those. Each part SHALL be the
variable key, a colon and a space, then one of these fixed reasons:

- `missing input: <inputs>`, when one or more inputs have no filled series.
  For transparency, `<inputs>` lists each missing input key,
  `column_water_vapour` before `aerosol_optical_depth`, separated by a comma
  and a space. For seeing, `<inputs>` is `seeing column`.
- `no hour has every input`, when every input has a filled series but no hour
  carries a value for all of them.
- the kind of error, when the derivation of that variable raised an error.

The parts SHALL be joined by a semicolon and a space, transparency first. When
every computed variable carries a value, the outcome SHALL carry no error. An
outcome that is successful SHALL still carry the error for a variable that
failed.

#### Scenario: A missing aerosol input is named

- **WHEN** the order is `open_meteo`, `seven_timer`, `computed`, no listed provider returns `aerosol_optical_depth`, and `open_meteo` returns the seeing column
- **THEN** the `computed` outcome is reported as successful with the error `transparency: missing input: aerosol_optical_depth`

#### Scenario: Both missing inputs are named in order

- **WHEN** the order is `open_meteo_hrdps`, `computed`
- **THEN** the `computed` outcome is reported as failed with the error `transparency: missing input: column_water_vapour, aerosol_optical_depth; seeing: missing input: seeing column`

#### Scenario: Inputs that never share a valued hour are reported

- **WHEN** both transparency inputs have a filled series, every hour that carries a value in one is blank or absent in the other, and computed seeing carries values
- **THEN** the `computed` outcome is reported as successful with the error `transparency: no hour has every input`

#### Scenario: A column with a blank in every hour is reported

- **WHEN** the seeing column has a filled series, every hour has at least one blank seeing-column variable, and computed transparency carries values
- **THEN** the `computed` outcome is reported as successful with the error `seeing: no hour has every input`

#### Scenario: A raising derivation fails only its own variable

- **WHEN** the seeing derivation raises a `ValueError`, and computed transparency carries values
- **THEN** the `computed` outcome is reported as successful with the error `seeing: ValueError`
- **AND** the `transparency` series carries the key `computed`

#### Scenario: Both variables computed carry no error

- **WHEN** both computed series carry values
- **THEN** the `computed` outcome is reported as successful with no error
