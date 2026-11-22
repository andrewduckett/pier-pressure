## ADDED Requirements

### Requirement: The document carries the later nights

The verdict document SHALL carry a `later_nights` key, always present, after
`observation`. It SHALL be a list with one entry per later night, in date order,
and empty when there are none. A later night is a night after the selected
night, one per local solar day. Every key before `later_nights` SHALL keep its
position, value and meaning.

#### Scenario: Two later nights

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T18:00:00Z
- **THEN** `later_nights` is `[{"dark_window": {"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}}, {"dark_window": {"start": "2026-09-10T20:25:07Z", "end": "2026-09-11T03:30:11Z"}}]`
- **AND** `later_nights` is the last key of the document, straight after `observation`

#### Scenario: No provider rows give an empty list

- **WHEN** a verdict is produced from the empty conditions value
- **THEN** `later_nights` is present and is an empty list

#### Scenario: The document's keys in order

- **WHEN** a verdict is produced for any valid pier
- **THEN** the document's keys, in order, are `pier`, `generated_at`, `verdict`, `score`, `confidence`, `reasons`, `targets`, `dark_window`, `scored_window`, `moon`, `timeline`, `agreement`, `observation` and `later_nights`

### Requirement: Each later night follows the one before by one local solar day

The first later night's local solar day SHALL be the one that starts when the
selected night's solar day ends. Each further later night's solar day SHALL
start when the one before it ends. There SHALL be at most three later nights.

#### Scenario: The forecast reaches six days

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-14T18:00:00Z
- **THEN** `later_nights` holds three entries
- **AND** their `dark_window.start` values are 2026-09-09T20:27:57Z, 2026-09-10T20:25:07Z and 2026-09-11T20:22:18Z, in that order

#### Scenario: A selected night with no dark window

- **WHEN** a verdict is produced for a pier at latitude 55.0, longitude −3.0, elevation 0 m, at 2026-06-21T08:00:00Z, with a `cloud_cover` series that covers 2026-06-21T08:00:00Z to 2026-06-23T18:00:00Z
- **THEN** `dark_window` is null
- **AND** `later_nights` is `[{"dark_window": {"start": null, "end": null}}, {"dark_window": {"start": null, "end": null}}]`, for the solar days that start on 2026-06-22 and 2026-06-23

### Requirement: A later night counts only while the forecast reaches its solar day

A later night SHALL be in `later_nights` only while its solar day starts before
the end of the last hour a filled series of a shown variable covers. Hours only
an alternate covers, and hours only a variable the timeline does not show
covers, SHALL NOT count. With no such hours, `later_nights` SHALL be empty.

#### Scenario: The last hour ends just after the solar noon

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T11:00:00Z, whose last hour ends at 12:00, after the solar noon at 11:57:27
- **THEN** `later_nights` holds two entries

#### Scenario: The last hour ends just before the solar noon

- **WHEN** a verdict is produced for the same pier and instant, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T10:00:00Z, whose last hour ends at 11:00
- **THEN** `later_nights` holds one entry, whose `dark_window.start` is 2026-09-09T20:27:57Z

#### Scenario: Hours only an alternate covers do not count

- **WHEN** a verdict is produced for the same pier and instant, every filled series ends at 2026-09-09T18:00:00Z, and a `cloud_cover` alternate runs to 2026-09-11T18:00:00Z
- **THEN** `later_nights` holds one entry

#### Scenario: Hours only a hidden variable covers do not count

- **WHEN** a verdict is produced for the same pier and instant from a snapshot whose only series is an `aerosol_optical_depth` series that runs to 2026-09-11T18:00:00Z
- **THEN** `later_nights` is an empty list

### Requirement: A later night's dark window is the astronomical night of its solar day

Each later night's `dark_window` SHALL have the top-level `dark_window` shape.
It SHALL be the astronomical night, found by the rules for the selected night's
dark window, whose midpoint falls inside the later night's solar day. In
continuous astronomical night it SHALL run from that solar day's start to its
end. When the solar day holds no such night, its `start` and `end` SHALL both
be null. A non-null window SHALL start strictly before it ends.

#### Scenario: Darkness ends after tonight

- **WHEN** a verdict is produced for a pier at latitude 52.0, longitude 0.0, elevation 0 m, at 2026-05-19T15:00:00Z, with a `cloud_cover` series that covers 2026-05-19T15:00:00Z to 2026-05-21T18:00:00Z
- **THEN** `dark_window` is `{"start": "2026-05-19T23:42:13Z", "end": "2026-05-20T00:10:20Z"}`
- **AND** `later_nights` is `[{"dark_window": {"start": null, "end": null}}, {"dark_window": {"start": null, "end": null}}]`

#### Scenario: Continuous polar night

- **WHEN** a verdict is produced for a pier at latitude 88.0, longitude 0.0, elevation 0 m, at 2026-12-10T12:00:00Z, with a `cloud_cover` series that covers 2026-12-10T12:00:00Z to 2026-12-14T12:00:00Z
- **THEN** `later_nights` holds three entries
- **AND** each entry's `dark_window` runs from its solar day's start to its end, at whole seconds, and the three windows follow one another with no gap and no overlap

### Requirement: A later night entry holds only its dark window

Each `later_nights` entry SHALL be an object with exactly one key,
`dark_window`. A later night SHALL carry no verdict, score, confidence, reasons
or targets of its own, and SHALL change no other field of the document.

#### Scenario: An entry's keys

- **WHEN** a verdict is produced with at least one later night
- **THEN** every `later_nights` entry has exactly the key `dark_window`

## MODIFIED Requirements

### Requirement: The document carries the observation

The verdict document SHALL carry an `observation` key, always present, after
`agreement`. It SHALL be null when the pier has no usable observation.
Otherwise it SHALL be an object with `station`, `observed_at`, `cover` and
`clouds`, in that order. Each `clouds` entry SHALL have `cover` and `base_ft`,
in that order, with `base_ft` null when the base is unknown.

#### Scenario: A usable observation fills the object

- **WHEN** a verdict is produced at `2026-11-14T21:30:00Z` for a pier whose observation from `KBOS` was measured at `2026-11-14T20:54:00Z`, with cover `BKN` and layers `FEW` at 3000 ft and `BKN` at 4200 ft
- **THEN** `observation` is `{"station": "KBOS", "observed_at": "2026-11-14T20:54:00Z", "cover": "BKN", "clouds": [{"cover": "FEW", "base_ft": 3000}, {"cover": "BKN", "base_ft": 4200}]}`
- **AND** `observation` is followed only by `later_nights`

#### Scenario: No station gives a null observation

- **WHEN** a verdict is produced for a pier with no `metar_station`
- **THEN** `observation` is null

#### Scenario: A failed fetch gives a null observation

- **WHEN** a verdict is produced for a pier whose METAR fetch failed
- **THEN** `observation` is null
- **AND** the verdict is produced as it would be with no station

### Requirement: Variables the timeline does not show leave the document unchanged

The timeline does not show these variables in the conditions: today,
`aerosol_optical_depth`, `pm2_5`, `column_water_vapour` and the seeing column's
36 variables. The verdict document SHALL NOT depend on them. No gate, score,
reason, confidence, agreement, timeline entry, timeline hour or later night
SHALL change with their presence or values. A value derived from them
reaches the document only as a shown variable's series, such as the computed
source's `transparency` and `seeing`.

#### Scenario: Air-quality series leave the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether `aerosol_optical_depth` and `pm2_5` series are present and in their values
- **THEN** the two serialized documents are byte-identical

#### Scenario: Air-quality series alone yield the empty-conditions document

- **WHEN** a verdict is produced from a snapshot whose only series are `aerosol_optical_depth` and `pm2_5`
- **THEN** the serialized document is byte-identical to the one produced for the same pier and instant from the empty conditions value
- **AND** its `timeline` holds exactly the selected night's hours
- **AND** its `later_nights` is an empty list

#### Scenario: A column water vapour series leaves the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether a `column_water_vapour` series is present and in its values
- **THEN** the two serialized documents are byte-identical

#### Scenario: Seeing-column series leave the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether the seeing column's series are present and in their values
- **THEN** the two serialized documents are byte-identical
