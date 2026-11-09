## ADDED Requirements

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

- **WHEN** `open_meteo`, `open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`, `open_meteo_icon`, `open_meteo_gfs` and `open_meteo_air_quality` are each fetched for a pier
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

## REMOVED Requirements

### Requirement: Cloud cover carries a low/mid/high component split

**Reason**: It bundled four behaviors. It is split into "Cloud data carries low, mid and high layers beside the total", "Each cloud layer is marked available on its own" and "The layer split leaves the total cloud cover unchanged", with the same meaning and the same scenarios.

**Migration**: None. Nothing changes for users or code.

### Requirement: Each fetch reports its outcome per provider

**Reason**: It bundled eight behaviors. It is split into "A fetch reports one outcome per provider in order", "A successful outcome carries its data's issue time", "A failed outcome carries a short error description", "A fetch that returns no readings is reported as failed", "A fetch that returns readings is reported as successful", "An outcome's error description is built only from safe parts", "An outcome's error description copies no text from the error or the response" and "Fetch outcomes never reach the verdict", with the same meaning and the same scenarios.

**Migration**: None. Nothing changes for users or code.

### Requirement: A failed computed outcome says which input was missing

**Reason**: It bundled four behaviors. It is split into "The computed outcome carries an error for each variable that computed nothing", "A computed error names the inputs that have no filled series", "A computed error says when no hour has every input" and "A computed error gives the kind of error a derivation raised", with the same meaning and the same scenarios.

**Migration**: None. Nothing changes for users or code.

### Requirement: Each variable is filled from the first provider in order that returned it

**Reason**: It bundled two behaviors. It is split into "The first provider in order that returned a variable fills its series" and "A provider fills a bundle whole or not at all", with the same meaning and the same scenarios.

**Migration**: None. Nothing changes for users or code.

### Requirement: The computed source reports an outcome like a provider

**Reason**: It bundled four behaviors. It is split into "The computed source reports one outcome at its place in the order", "The computed outcome succeeds when a computed hour carries a value", "A successful computed outcome carries the oldest computed issue time" and "A successful computed outcome names the providers each variable read", with the same meaning and the same scenarios.

**Migration**: None. Nothing changes for users or code.

### Requirement: The snapshot keeps alternates beside the filled series

**Reason**: It bundled three behaviors. It is split into "Each later provider that returned a variable leaves an alternate", "A provider that returned nothing or failed leaves no alternate" and "Alternates never change the filled series", with the same meaning and the same scenarios.

**Migration**: None. Nothing changes for users or code.

### Requirement: NWS periods are expanded onto the hourly grid within a 72-hour horizon

**Reason**: It bundled three behaviors. It is split into "Each NWS value is held across every hour its period covers", "An NWS precipitation probability is held one hour after its period's hours" and "NWS keeps only hours within 72 hours of the earliest period start", with the same meaning and the same scenarios.

**Migration**: None. Nothing changes for users or code.

### Requirement: Each Open-Meteo model declares the variables its model returns

**Reason**: It bundled four behaviors. It is split into "HRRR and GFS declare the same variables as Open-Meteo", "ICON declares neither column water vapour nor the seeing column", "HRDPS and RDPS declare no precipitation probability" and "A provider that does not declare the seeing column declares none of its variables", with the same meaning and the same scenarios.

**Migration**: None. Nothing changes for users or code.

### Requirement: Every Open-Meteo request asks for the 4 hours before the fetch and the 72 after

**Reason**: It bundled two behaviors. It is split into "Every Open-Meteo hourly request asks for 4 past hours and 72 forecast hours" and "An Open-Meteo hourly request asks for no forecast days and for UTC times", with the same meaning and the same scenarios. The second gains one scenario, which an existing test already asserts.

**Migration**: None. Nothing changes for users or code.
