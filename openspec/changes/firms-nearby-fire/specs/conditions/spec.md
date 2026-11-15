## ADDED Requirements

### Requirement: The configuration may set a FIRMS key for the whole service

The configuration MAY hold a top-level `firms` block with one setting,
`map_key`: a NASA FIRMS MAP_KEY, as text. It SHALL apply to every pier. A
`${VAR}` in it SHALL be expanded from the environment, as elsewhere in the
configuration. With no `firms` block, an empty one, or no `map_key`, the service
SHALL have no FIRMS key.

#### Scenario: A key in the file is read

- **WHEN** `config.yaml` sets `firms.map_key: abc123secret`
- **THEN** the configuration loads with a FIRMS key

#### Scenario: A key from the environment is read

- **WHEN** `config.yaml` sets `firms.map_key: ${FIRMS_KEY}` and the environment sets `FIRMS_KEY` to `abc123secret`
- **THEN** the configuration loads with the FIRMS key `abc123secret`

#### Scenario: No firms block means no key

- **WHEN** `config.yaml` has no `firms` block
- **THEN** the configuration loads with no FIRMS key

### Requirement: A FIRMS key that still holds an unexpanded variable counts as no key

When `firms.map_key` is empty text, or still holds `${` after expansion because
its variable is unset, the service SHALL have no FIRMS key. It SHALL log one
warning that names `firms.map_key` and does not contain its value.

#### Scenario: An unset variable leaves no key

- **WHEN** `config.yaml` sets `firms.map_key: ${FIRMS_KEY}` and the environment has no `FIRMS_KEY`
- **THEN** the configuration loads with no FIRMS key
- **AND** the log has one warning that names `firms.map_key`

### Requirement: An invalid firms block is reported without its values

When the process rejects the `firms` block, the error SHALL name the setting at
fault and SHALL NOT contain any value from the block. A `firms` value that is
not a mapping SHALL be an error that says `firms` must be a mapping of
settings. A key the block does not define SHALL be an error that says the block
holds a setting it does not know, and lists the settings it defines, without
the unknown key's name. The log SHALL hold none of these values or names.

#### Scenario: A key that is not text is rejected without its value

- **WHEN** `config.yaml` sets `firms.map_key` to the number `12345`
- **THEN** the process stops with a configuration error that names `firms.map_key`
- **AND** neither the error nor the log contains `12345`

#### Scenario: An unknown setting is not named

- **WHEN** the `firms` block holds `mapkey: abc123secret`
- **THEN** the process stops with a configuration error that says the `firms` block holds a setting it does not know, and lists `map_key`
- **AND** neither the error nor the log contains `mapkey` or `abc123secret`

#### Scenario: A firms value that is not a mapping is not shown

- **WHEN** `config.yaml` sets `firms: abc123secret`
- **THEN** the process stops with a configuration error that says `firms` must be a mapping of settings
- **AND** neither the error nor the log contains `abc123secret`

### Requirement: The FIRMS key never appears in a log, an error or health

The system SHALL NOT write the FIRMS key, or a request URL that contains it, to
any log line, error, health attribute or MQTT message. Printing or logging the
settings SHALL show the key as a mask.

#### Scenario: A rejected key stays out of the log and health

- **WHEN** the FIRMS key is `abc123secret` and the FIRMS request answers 400 with the body `Invalid MAP_KEY.`
- **THEN** no log line and no published health attribute contains `abc123secret`

#### Scenario: A timeout stays out of the log

- **WHEN** the FIRMS key is `abc123secret` and the FIRMS request times out
- **THEN** no log line contains `abc123secret`

#### Scenario: The settings show a mask

- **WHEN** the configuration sets a FIRMS key and the process prints its settings
- **THEN** the output does not contain the key

### Requirement: Every pier's fire detections are fetched on every fetch while the key is set

While the service has a FIRMS key, every fetch for every pier SHALL make one
request to
`https://firms.modaps.eosdis.nasa.gov/api/area/csv/<key>/VIIRS_NOAA20_NRT/<west>,<south>,<east>,<north>/2`,
where the four bounds are the pier's FIRMS box. The day range of 2 asks for
today and yesterday in UTC, so the 24 hours before any instant are covered. With no key, the system SHALL
make no FIRMS request.

#### Scenario: A pier at 60° north fetches its box

- **WHEN** the FIRMS key is `abc123secret` and the system fetches conditions for a pier at latitude 60.0, longitude 10.0
- **THEN** it makes one request to `https://firms.modaps.eosdis.nasa.gov/api/area/csv/abc123secret/VIIRS_NOAA20_NRT/9.0000,59.5000,11.0000,60.5000/2`

#### Scenario: No key makes no FIRMS request

- **WHEN** the configuration has no FIRMS key and the system fetches conditions for a pier
- **THEN** it makes no request to `firms.modaps.eosdis.nasa.gov`

### Requirement: A pier's FIRMS box holds every point within 50 km

The pier's FIRMS box SHALL run from 0.5° south to 0.5° north of the pier, and
from `0.5 / cos(latitude)` degrees west to the same east of it. It SHALL be
clamped to latitudes from −90 to 90 and longitudes from −180 to 180, and SHALL
span every longitude when the pier is within 0.5° of a pole. Each bound SHALL
have four decimal places.

#### Scenario: A box near the antimeridian is clamped

- **WHEN** the system fetches fire detections for a pier at latitude 0.0, longitude 179.8
- **THEN** the request's box is `179.3000,-0.5000,180.0000,0.5000`

#### Scenario: A box near a pole spans every longitude

- **WHEN** the system fetches fire detections for a pier at latitude 89.8, longitude 10.0
- **THEN** the request's box is `-180.0000,89.3000,180.0000,90.0000`

### Requirement: FIRMS is not a provider

FIRMS SHALL NOT be a provider in the catalog or the provider order. A fire
detection SHALL NOT fill a variable, and SHALL add no series and no alternate
to the snapshot.

#### Scenario: Listing firms as a provider stops startup

- **WHEN** the configuration lists `providers: [open_meteo, firms]`
- **THEN** startup fails with an error that says `firms` is not a known provider

#### Scenario: Fire detections leave the snapshot unchanged

- **WHEN** the system fetches conditions twice for the same pier from the same provider responses, once with a FIRMS response holding detections and once with no FIRMS key
- **THEN** the two snapshots hold the same series and the same alternates

### Requirement: A fire detection carries its place, time and confidence

Each row of a FIRMS response SHALL become one fire detection with its latitude,
its longitude, the time the satellite passed and its confidence. The time SHALL
come from the row's `acq_date` and `acq_time` in UTC, where `acq_time` is hours
and minutes as four digits. The confidence SHALL be the row's `confidence` as
given: `low`, `nominal` or `high`.

#### Scenario: A recorded row becomes a fire detection

- **WHEN** a FIRMS response row has `latitude` 46.76213, `longitude` -71.00217, `acq_date` 2026-11-13, `acq_time` 0554 and `confidence` nominal
- **THEN** the fire detection is at latitude 46.76213, longitude -71.00217, detected at `2026-11-13T05:54:00Z`, with confidence `nominal`

### Requirement: A FIRMS response is read by column name and skips rows it cannot read

The system SHALL find each column of a FIRMS response by its name in the header
row, so a column it does not read, or a change in column order, SHALL NOT change
the result. A row it cannot read SHALL be left out, and the rest kept.

#### Scenario: An extra column changes nothing

- **WHEN** a FIRMS response has an `instrument` column between `satellite` and `confidence`
- **THEN** its rows give the same fire detections as the same rows without that column

#### Scenario: A row with no latitude is left out

- **WHEN** a FIRMS response holds two rows and one has an empty `latitude`
- **THEN** the fetch gives one fire detection

### Requirement: A FIRMS response with only a header has no fire detections

A FIRMS response whose body is the header row alone SHALL be a successful fetch
with no fire detections.

#### Scenario: No fire near the pier

- **WHEN** the FIRMS request answers 200 with the header row and no other row
- **THEN** the pier has no fire detections for that fetch
- **AND** the FIRMS fetch is reported as successful

### Requirement: A failed FIRMS fetch leaves the pier with no fire detections

The pier SHALL have no fire detections for a fetch when the FIRMS request:

- fails or times out;
- answers with a status that is not a success; or
- returns a body whose header row lacks `latitude`, `longitude`, `acq_date`,
  `acq_time` or `confidence`.
 A body with no such header SHALL count as a failed fetch with
the error `unexpected response`. A failed FIRMS fetch SHALL NOT change the
snapshot, the observation, or the fetch of any provider.

#### Scenario: A rejected key leaves no detections

- **WHEN** the FIRMS request answers 400 with the body `Invalid MAP_KEY.`
- **THEN** the pier has no fire detections for that fetch
- **AND** the FIRMS fetch is reported as failed with the error `HTTPStatusError: 400 Bad Request`
- **AND** the snapshot holds the series the providers returned

#### Scenario: A text reply with a success status is a failed fetch

- **WHEN** the FIRMS request answers 200 with the body `Invalid MAP_KEY.`
- **THEN** the pier has no fire detections for that fetch
- **AND** the FIRMS fetch is reported as failed with the error `unexpected response`

### Requirement: Fire detections travel beside the snapshot as data

The fire detections SHALL reach the verdict as plain data beside the snapshot
and the observation, obtained before the verdict is produced. Producing the
verdict SHALL NOT make a FIRMS request.

#### Scenario: The verdict is produced with no network

- **WHEN** a verdict is produced for a pier with pinned fire detections and no network available
- **THEN** the verdict is produced and makes no network request
