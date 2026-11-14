## ADDED Requirements

### Requirement: A pier may name a METAR station

A pier configuration MAY set `metar_station`: the code of one airport weather
station, four characters, each a letter or a digit, the first a letter. The
system SHALL accept it in any case and store it in upper case. It is not a
tuning knob. A pier that omits it has no station.

#### Scenario: A lower-case station is stored in upper case

- **WHEN** a pier configuration sets `metar_station: kbos`
- **THEN** the pier's METAR station is `KBOS`

#### Scenario: A station with a digit is accepted

- **WHEN** a pier configuration sets `metar_station: K1V4`
- **THEN** the pier's METAR station is `K1V4`

### Requirement: An invalid METAR station is a configuration error

A `metar_station` that is not four letters or digits starting with a letter
SHALL be a configuration error that names `metar_station`, so the pier is
skipped as any invalid pier is.

#### Scenario: A short station is rejected

- **WHEN** a pier configuration sets `metar_station: KBO`
- **THEN** loading the pier fails with an error that names `metar_station`

#### Scenario: A station starting with a digit is rejected

- **WHEN** a pier configuration sets `metar_station: 1BOS`
- **THEN** loading the pier fails with an error that names `metar_station`

### Requirement: The document carries the observation

The verdict document SHALL carry an `observation` key, always present, after
`agreement`. It SHALL be null when the pier has no usable observation.
Otherwise it SHALL be an object with `station`, `observed_at`, `cover` and
`clouds`, in that order. Each `clouds` entry SHALL have `cover` and `base_ft`,
in that order, with `base_ft` null when the base is unknown.

#### Scenario: A usable observation fills the object

- **WHEN** a verdict is produced at `2026-11-14T21:30:00Z` for a pier whose observation from `KBOS` was measured at `2026-11-14T20:54:00Z`, with cover `BKN` and layers `FEW` at 3000 ft and `BKN` at 4200 ft
- **THEN** `observation` is `{"station": "KBOS", "observed_at": "2026-11-14T20:54:00Z", "cover": "BKN", "clouds": [{"cover": "FEW", "base_ft": 3000}, {"cover": "BKN", "base_ft": 4200}]}`
- **AND** `observation` is the last key of the document

#### Scenario: No station gives a null observation

- **WHEN** a verdict is produced for a pier with no `metar_station`
- **THEN** `observation` is null

#### Scenario: A failed fetch gives a null observation

- **WHEN** a verdict is produced for a pier whose METAR fetch failed
- **THEN** `observation` is null
- **AND** the verdict is produced as it would be with no station

### Requirement: An observation more than 90 minutes old or from the future is not used

An observation SHALL be usable when it was measured at most 90 minutes before
the evaluation instant, and not after it. An observation that is not usable
SHALL give a null `observation` and no observation reason line.

#### Scenario: An observation exactly 90 minutes old is used

- **WHEN** a verdict is produced at `2026-11-14T22:24:00Z` from an observation measured at `2026-11-14T20:54:00Z`
- **THEN** `observation.observed_at` is `2026-11-14T20:54:00Z`

#### Scenario: An observation 91 minutes old is ignored

- **WHEN** a verdict is produced at `2026-11-14T22:25:00Z` from an observation measured at `2026-11-14T20:54:00Z`
- **THEN** `observation` is null
- **AND** no reason line begins with `At 2026-11-14T20:54:00Z`

#### Scenario: An observation measured after the evaluation instant is ignored

- **WHEN** a verdict is produced at `2026-11-14T20:50:00Z` from an observation measured at `2026-11-14T20:54:00Z`
- **THEN** `observation` is null

### Requirement: A usable observation adds one reason line that names its layers

When `observation` is not null, `reasons` SHALL carry exactly one line `At
<time>, <station> reported <layers>.`. `<time>` is `observed_at`. `<layers>`
names each layer lowest first as `<cover> at <base> ft`, joined by `, ` with
` and ` before the last. `<base>` has a comma between thousands, or the layer
says `at an unknown height`. When `observation` is null, no such line SHALL
appear.

#### Scenario: Two layers are named lowest first

- **WHEN** `observation` is from `KBOS` at `2026-11-14T20:54:00Z` with layers `FEW` at 3000 ft and `BKN` at 4200 ft
- **THEN** `reasons` contains `At 2026-11-14T20:54:00Z, KBOS reported few cloud at 3,000 ft and broken cloud at 4,200 ft.`

#### Scenario: Three layers are joined with commas

- **WHEN** `observation` is from `KBOS` at `2026-11-14T20:54:00Z` with layers `FEW` at 3000 ft, `BKN` at 4200 ft and `OVC` at 9500 ft
- **THEN** `reasons` contains `At 2026-11-14T20:54:00Z, KBOS reported few cloud at 3,000 ft, broken cloud at 4,200 ft and overcast cloud at 9,500 ft.`

#### Scenario: A layer with no base says its height is unknown

- **WHEN** `observation` is from `KBOS` at `2026-11-14T20:54:00Z` with one layer `BKN` whose `base_ft` is null
- **THEN** `reasons` contains `At 2026-11-14T20:54:00Z, KBOS reported broken cloud at an unknown height.`

### Requirement: The observation line words each cover code

The observation line SHALL word the cover codes this way: `FEW` as `few cloud`,
`SCT` as `scattered cloud`, `BKN` as `broken cloud`, `OVC` as `overcast cloud`,
and `OVX` as `an obscured sky`. It SHALL give any other code as it is reported.

#### Scenario: An obscured sky is worded

- **WHEN** `observation` is from `KBOS` at `2026-11-14T20:54:00Z` with one layer `OVX` at 300 ft
- **THEN** `reasons` contains `At 2026-11-14T20:54:00Z, KBOS reported an obscured sky at 300 ft.`

#### Scenario: An unknown code is given as reported

- **WHEN** `observation` is from `KBOS` at `2026-11-14T20:54:00Z` with one layer `VV` at 200 ft
- **THEN** `reasons` contains `At 2026-11-14T20:54:00Z, KBOS reported VV at 200 ft.`

### Requirement: An observation with no layers reports no cloud below what a station can see

When `observation.clouds` is empty, the line SHALL name no cloud below the
height the report covers: `no cloud below 5,000 ft` when `observation.cover` is
`CAVOK`, else `no cloud below 12,000 ft`, because an automated station sees no
higher.

#### Scenario: A clear automated report

- **WHEN** `observation` is from `EGLL` at `2026-11-14T21:20:00Z` with cover `CLR` and no layers
- **THEN** `reasons` contains `At 2026-11-14T21:20:00Z, EGLL reported no cloud below 12,000 ft.`

#### Scenario: A CAVOK report

- **WHEN** `observation` is from `LFPG` at `2026-11-14T21:00:00Z` with cover `CAVOK` and no layers
- **THEN** `reasons` contains `At 2026-11-14T21:00:00Z, LFPG reported no cloud below 5,000 ft.`

### Requirement: The observation line follows the core's other lines on every verdict

The observation line SHALL appear on every verdict with a usable observation,
a gated `NO-GO` and a night with no dark window included. It SHALL come after
every other line the core emits for the verdict, the dew line included, and
before the equipment notes about the top pick.

#### Scenario: The line follows the dew line

- **WHEN** a verdict is `GO` with a `Dew likely from` line and a usable observation, for a pier with no equipment
- **THEN** the last two reasons are the `Dew likely from` line and the observation line, in that order

#### Scenario: The line comes before the equipment notes

- **WHEN** a verdict is `GO` with a usable observation, for a pier with equipment and a top pick
- **THEN** the observation line comes before every equipment note

#### Scenario: A gated NO-GO keeps the line

- **WHEN** a verdict is `NO-GO` for an overcast dark window, with a usable observation
- **THEN** `reasons` names the overcast gate first
- **AND** its last line is the observation line

### Requirement: The observation changes no gate, score or confidence

The observation SHALL NOT change the verdict, the score, the confidence, the
agreement or the timeline.

#### Scenario: Two verdicts differ only in the observation

- **WHEN** two verdicts are produced for the same pier, instant and snapshot, one with a usable observation and one with none
- **THEN** their `verdict`, `score`, `confidence`, `agreement` and `timeline` are identical
- **AND** their `reasons` differ only by the observation line

## MODIFIED Requirements

### Requirement: The dew line is last and changes nothing else

The dew or frost line SHALL come after every other line the core emits for the verdict, including any cap line and the agreement line, so every existing line keeps its position. Only the observation line comes after it. On a gated `NO-GO` no such line SHALL appear. The line SHALL NOT change the verdict, the score or the confidence.

#### Scenario: The line follows the agreement line and is last

- **WHEN** a verdict is `GO` with `agreement.cloud_cover` present, a scored hour under the margin and no usable observation
- **THEN** the core's last three reasons are the `Score N/100.` line, the `Cloud agreement` line and the `Dew likely from` line, in that order

#### Scenario: The line follows a cap line and the agreement line

- **WHEN** a verdict is `MAYBE` because wind data does not cover the scored window, `agreement.cloud_cover` is present, and a scored hour is under the margin
- **THEN** the `Dew likely from` line comes after both the wind-unavailable line and the `Cloud agreement` line

#### Scenario: A gated NO-GO carries no dew line

- **WHEN** a verdict is `NO-GO` for an overcast dark window and every scored hour's spread is 1 °C
- **THEN** no reason line begins with `Dew` or `Frost`

#### Scenario: The line changes nothing else

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in temperature and dew point
- **THEN** their `verdict`, `score` and `confidence` are identical
- **AND** their `reasons` differ at most by one `Dew likely from` or `Frost likely from` line
