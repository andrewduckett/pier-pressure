## ADDED Requirements

### Requirement: A pier that names a METAR station has its latest METAR fetched on every fetch

For each pier that names a METAR station, every fetch SHALL make one request to
`https://aviationweather.gov/api/data/metar?ids=<station>&format=json`, where
`<station>` is the pier's station. A pier that names no station SHALL make no
METAR request.

#### Scenario: A pier with a station fetches its METAR

- **WHEN** the system fetches conditions for a pier whose `metar_station` is `KBOS`
- **THEN** it makes one request to `https://aviationweather.gov/api/data/metar?ids=KBOS&format=json`

#### Scenario: A pier with no station makes no METAR request

- **WHEN** the system fetches conditions for a pier with no `metar_station`
- **THEN** it makes no request to `aviationweather.gov`

### Requirement: METAR requests carry the fixed User-Agent

Every METAR request SHALL carry the same `User-Agent` header as NWS requests:
the project name, the running version and the repository URL, with no email
address. It SHALL NOT be configurable.

#### Scenario: The header names the project, version and repository

- **WHEN** the system makes a METAR request
- **THEN** its `User-Agent` header contains `PierPressure`, the running version and `https://github.com/andrewduckett/pier-pressure`
- **AND** it contains no `@`

### Requirement: METAR is not a provider

METAR SHALL NOT be a provider in the catalog or the provider order. An
observation SHALL NOT fill a variable, and SHALL add no series and no
alternate to the snapshot.

#### Scenario: Listing metar as a provider stops startup

- **WHEN** the configuration lists `providers: [open_meteo, metar]`
- **THEN** startup fails with an error that says `metar` is not a known provider

#### Scenario: An observation leaves the snapshot unchanged

- **WHEN** the system fetches conditions twice for the same pier from the same provider responses, once with a METAR station that reports broken cloud and once with no station
- **THEN** the two snapshots hold the same series and the same alternates

### Requirement: An observation carries its station, time and cloud layers

An observation from a METAR report SHALL carry the station, the time the station
measured it, the report's overall cover code and its cloud layers. The time
SHALL be the report's observation time, not its nominal report time or the fetch
time. Each layer SHALL carry its cover code and its base in feet above ground,
in the order reported.

#### Scenario: A recorded report becomes an observation

- **WHEN** the response for `KBOS` has observation time `2026-11-14T20:54:00Z`, report time `2026-11-14T21:00:00Z`, cover `OVC` and layers `FEW` at 3000, `BKN` at 4200 and `OVC` at 9500
- **THEN** the observation's station is `KBOS` and its time is `2026-11-14T20:54:00Z`
- **AND** its cover is `OVC`
- **AND** its layers are `FEW` at 3000 ft, `BKN` at 4200 ft and `OVC` at 9500 ft, in that order

### Requirement: An observation keeps cover codes as reported and a missing base as unknown

An observation SHALL keep every cover code as the report gives it, including a
code it has no wording for. A layer with no base SHALL be kept, with its base
unknown. A report with no layers SHALL give an observation with an empty list
of layers.

#### Scenario: A layer with no base is kept

- **WHEN** a report has a `BKN` layer with no base
- **THEN** the observation has a `BKN` layer whose base is unknown

#### Scenario: A clear report has no layers

- **WHEN** a report has cover `CLR` and no layers
- **THEN** the observation's cover is `CLR` and its list of layers is empty

### Requirement: A failed METAR fetch leaves the pier with no observation

When the METAR request fails, times out, or returns a body the system cannot
read, the pier SHALL have no observation for that fetch. A response with no
report SHALL count as a failed fetch with the error `no report returned`. A
failed METAR fetch SHALL NOT change the snapshot or fail the fetch of any
provider.

#### Scenario: A server error leaves no observation

- **WHEN** the METAR request for a pier answers with status 503
- **THEN** the pier has no observation for that fetch
- **AND** the snapshot holds the series the providers returned

#### Scenario: An unknown station returns no report

- **WHEN** the METAR request for `KZZZ` answers with an empty list
- **THEN** the pier has no observation for that fetch
- **AND** the METAR fetch is reported as failed with the error `no report returned`

### Requirement: The observation travels beside the snapshot as data

The observation SHALL reach the verdict as a plain data value beside the
snapshot, obtained before the verdict is produced. Producing the verdict SHALL
NOT make a METAR request.

#### Scenario: The verdict is produced with no network

- **WHEN** a verdict is produced for a pier with a pinned observation and no network available
- **THEN** the verdict is produced and makes no network request
