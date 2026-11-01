## ADDED Requirements

### Requirement: Providers are configured as an ordered list

The configuration SHALL accept a `conditions.providers` list of provider keys,
preferred first. When the `conditions` block or the list is absent, the list
SHALL be `[open_meteo, seven_timer]`.

#### Scenario: An absent block gives the default order

- **WHEN** the configuration has no `conditions` block
- **THEN** the provider order is `open_meteo` then `seven_timer`

#### Scenario: A configured order is kept as written

- **WHEN** the configuration lists `providers: [seven_timer, open_meteo]`
- **THEN** the provider order is `seven_timer` then `open_meteo`

### Requirement: An invalid provider list stops startup

The system SHALL reject the configuration at startup when the provider list is
empty, when a key names no known provider, when a key appears more than once,
or when no listed provider is both keyless and declares cloud cover. The error
SHALL name the rule broken and SHALL carry no value from the configuration
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

Each provider SHALL declare the variables it supplies, named by their timeline
keys, and which of them form a bundle. A declaration SHALL be fixed: it SHALL
NOT change with what a fetch returned.

#### Scenario: Open-Meteo declares the cloud bundle and the weather variables

- **WHEN** the Open-Meteo provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction` and `precipitation_probability`
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: 7Timer! declares seeing and transparency

- **WHEN** the 7Timer! provider's declaration is read
- **THEN** it lists `seeing` and `transparency` and no bundle

### Requirement: Each variable is filled from the first provider in order that returned it

The snapshot SHALL hold one series per variable, carrying one provider's hourly
values, that provider's key and the issue time of its data. For each variable,
the series SHALL come from the first provider in the configured order that
returned it: at least one hour of its forecast carries a value for it, or for
another variable in the same bundle. The variables of a bundle SHALL come from
the same provider. A variable no provider returned SHALL have no series.

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

#### Scenario: A bundle travels together

- **WHEN** the first provider in order returns `cloud_cover` but no low, mid or high layer, and the second returns all four
- **THEN** the `cloud_cover` series carries the first provider's key
- **AND** the `cloud_low`, `cloud_mid` and `cloud_high` series carry the first provider's key with no values
- **AND** none of the four carries the second provider's values

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

## MODIFIED Requirements

### Requirement: Availability is stamped per field

Every variable SHALL be marked as available or unavailable for every hour. A
partial snapshot — some variables present, others absent — SHALL be a valid
result rather than a failure, so the verdict can degrade by reading what is
absent rather than by handling an error. Any hours of the selected dark window
that a series' provider did not reach SHALL be marked unavailable in that
series rather than filled in, from any provider.

#### Scenario: A partial snapshot is valid

- **WHEN** some variables are obtained and others cannot be
- **THEN** the snapshot is returned with each variable marked available or unavailable
- **AND** the absence of a variable is not reported as an error

#### Scenario: Hours beyond a source's forecast horizon are unavailable

- **WHEN** the provider that filled a series has a forecast that does not reach part of the dark window
- **THEN** that series is marked unavailable for the hours its forecast does not reach
- **AND** the hours its forecast does reach keep their values

### Requirement: The snapshot records when its data was issued

The snapshot SHALL record an issue time on each series: the one its provider
gave for the data it returned on this fetch. Series filled by the same provider
SHALL carry the same issue time. Recording it per series lets downstream trust
reflect the age of the data it actually reads, even when providers refresh on
different cadences.

#### Scenario: Each source's issue time reflects the data actually carried

- **WHEN** a snapshot is filled from two providers that gave different issue times
- **THEN** each series carries the issue time of the provider that filled it
- **AND** each recorded issue time is the one that provider gave for the data it returned on this fetch

### Requirement: Cloud cover carries a low/mid/high component split

For each hour of the dark window, the cloud data SHALL carry, in addition to the
total cloud cover, a split into three layer components — low, mid, and high — so
the verdict can tell a low deck that blocks the view apart from high, thin cirrus
that leaves a near-clear total reading yet degrades transparency. The total and
its three components SHALL form one bundle, filled from the same provider. Each
component SHALL be marked available or unavailable independently, following the
same per-variable availability rule as the rest of the snapshot: one component
may be present while another is absent, and any component may be absent while
the total cloud cover remains present and usable. The component split SHALL be
additive to the existing cloud-cover slot; the meaning of the total cloud-cover
value SHALL NOT change, and a provider that reports only a total SHALL still
yield a valid snapshot with the components marked unavailable.

#### Scenario: Cloud data carries the layer split alongside the total

- **WHEN** conditions are obtained for a pier whose selected night has a dark window and the provider that filled cloud cover reports a low/mid/high cloud split
- **THEN** each hour's cloud data carries a total cloud cover plus low, mid, and high component values
- **AND** each component is marked available

#### Scenario: A component can be absent while others and the total remain present

- **WHEN** the provider reports total cloud cover and some but not all of the low/mid/high components for an hour
- **THEN** the components that were reported are marked available with their values
- **AND** the components that were not reported are marked unavailable
- **AND** the absence of a component is not reported as an error

#### Scenario: A total-only source yields a valid snapshot with components unavailable

- **WHEN** the provider that filled cloud cover reports total cloud cover but no low/mid/high split
- **THEN** the snapshot is returned with total cloud cover available and the low, mid, and high components marked unavailable
- **AND** the total cloud-cover value carries the same meaning as before the split was added

### Requirement: Each fetch reports its outcome per provider

Each time the system fetches conditions for a pier, it SHALL report one outcome for
each provider in the configured order, in that order. An outcome SHALL name the
provider and the variables it declares. It SHALL record when the fetch ran and
whether it succeeded or failed. A failed outcome SHALL carry a short error
description. A successful outcome SHALL carry the issue time the provider gave
for its data, or null when it gave none.

A fetch that returns no readings SHALL be reported as failed, with an error that
says no readings were returned. A fetch that returns readings SHALL be reported as
successful, even when some variables in those readings are blank, and whether or
not the fill used any of them.

The error description SHALL be built only from a fixed set of safe parts:

- the kind of error
- for an HTTP error response, its status code and that code's standard phrase
- fixed messages, such as the one for an empty fetch

It SHALL NOT include any text from the error or from the provider's response. That
includes the reason phrase the provider's server sends. So the description never
contains the request URL or the pier's coordinates.

The outcomes SHALL NOT reach the verdict. The verdict, score, confidence, and
reasons SHALL depend only on the snapshot, never on the outcomes.

#### Scenario: A successful fetch is reported with its issue time

- **WHEN** a provider returns readings for a pier
- **THEN** its outcome for that fetch is reported as successful
- **AND** the outcome carries the time the fetch ran and the issue time of the returned data

#### Scenario: An outcome names the provider's declared variables

- **WHEN** 7Timer! is fetched for a pier
- **THEN** its outcome names `seven_timer` and the variables `seeing` and `transparency`

#### Scenario: A provider the fill passed over still reports success

- **WHEN** a provider returns readings for a pier but an earlier provider in order already filled every variable it declares
- **THEN** its outcome for that fetch is reported as successful

#### Scenario: A failed fetch is reported with a short error

- **WHEN** a provider's fetch for a pier raises an error
- **THEN** its outcome for that fetch is reported as failed
- **AND** the outcome carries the kind of error

#### Scenario: An HTTP error response is reported with its status

- **WHEN** a provider answers a fetch for a pier with an HTTP error status, such as 503
- **THEN** its outcome for that fetch is reported as failed
- **AND** the error gives the kind of error, the status code, and that code's standard phrase

#### Scenario: A server's own reason phrase is never copied

- **WHEN** a provider answers with status 503 and a reason phrase that contains the pier's latitude
- **THEN** the reported error gives the standard phrase for 503
- **AND** it does not contain the latitude

#### Scenario: An empty fetch is reported as failed

- **WHEN** a provider's fetch for a pier completes but returns no readings
- **THEN** its outcome for that fetch is reported as failed
- **AND** its error says that no readings were returned

#### Scenario: Blank fields do not make a fetch fail

- **WHEN** a provider returns readings for a pier and some variables in those readings are blank
- **THEN** its outcome for that fetch is reported as successful

#### Scenario: The error never contains the request URL or coordinates

- **WHEN** a provider's fetch fails with an error whose own message includes the request URL
- **THEN** the reported error contains neither the URL nor the pier's latitude and longitude

#### Scenario: The error never contains coordinates outside a URL

- **WHEN** a provider's fetch fails with an error whose own message includes the pier's latitude, with no URL
- **THEN** the reported error does not contain the latitude

#### Scenario: Outcomes do not change the verdict

- **WHEN** two verdicts are produced for the same pier, instant, and snapshot, with different fetch outcomes
- **THEN** the two verdict documents are byte-identical

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

## REMOVED Requirements

### Requirement: The base source supplies the weather variables

**Reason**: The base role no longer exists. The weather variables are series like
every other variable, filled from the first provider in order that returned them.
**Migration**: The behaviour is restated under "A provider supplies the weather
variables". No configuration or entity changes.

### Requirement: No single source is load-bearing

**Reason**: The base and secondary roles no longer exist. Providers sit in one
ordered list and each variable is filled by the first that returned it.
**Migration**: The behaviour is restated under "No single provider is
load-bearing". No configuration or entity changes.
