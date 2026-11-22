## MODIFIED Requirements

### Requirement: Verdict document structure

The system SHALL produce, for a single configured pier, a verdict document containing at least these fields: a pier identifier, a generation timestamp, a `verdict` value, a `score` value, a `confidence` value, a `reasons` list, a `targets` list, a `dark_window` value, a `moon` value, and a `later_nights` list. The document SHALL be serializable to JSON so downstream adapters and tests can consume it without access to internal state.

#### Scenario: Document contains all required fields

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the resulting document contains a pier identifier, a generation timestamp, a `verdict`, a `score`, a `confidence`, a `reasons` list, a `targets` list, a `dark_window`, a `moon`, and a `later_nights` list
- **AND** the document can be serialized to JSON and read back with the same field values

### Requirement: The document carries the observation

The verdict document SHALL carry an `observation` key, always present, after
`agreement`. It SHALL be null when the pier has no usable observation.
Otherwise it SHALL be an object with `station`, `observed_at`, `cover` and
`clouds`, in that order. Each `clouds` entry SHALL have `cover` and `base_ft`,
in that order, with `base_ft` null when the base is unknown.

#### Scenario: A usable observation fills the object

- **WHEN** a verdict is produced at `2026-11-14T21:30:00Z` for a pier whose observation from `KBOS` was measured at `2026-11-14T20:54:00Z`, with cover `BKN` and layers `FEW` at 3000 ft and `BKN` at 4200 ft
- **THEN** `observation` is `{"station": "KBOS", "observed_at": "2026-11-14T20:54:00Z", "cover": "BKN", "clouds": [{"cover": "FEW", "base_ft": 3000}, {"cover": "BKN", "base_ft": 4200}]}`
- **AND** the only key after `observation` is `later_nights`

#### Scenario: No station gives a null observation

- **WHEN** a verdict is produced for a pier with no `metar_station`
- **THEN** `observation` is null

#### Scenario: A failed fetch gives a null observation

- **WHEN** a verdict is produced for a pier whose METAR fetch failed
- **THEN** `observation` is null
- **AND** the verdict is produced as it would be with no station

### Requirement: The timeline is evidence beside the verdict

The timeline SHALL be filled whether or not a provider returned rows, and whether or not the selected night has a dark window. It SHALL NOT change the verdict, the score, the confidence, the reasons or any other existing field. Only `later_nights`, which counts the timeline's hours, can follow it. It carries no verdict of its own: the verdict judges the one night the dark window names, however far the timeline reaches.

#### Scenario: The timeline fills without a dark window

- **WHEN** a verdict is produced for a pier whose selected night has no dark window and a provider returned rows
- **THEN** the `timeline` holds one entry per returned hour and per hour of the selected night, each hour once
- **AND** the document with `timeline` and `later_nights` removed equals the document produced for the same pier and instant from the empty conditions value

#### Scenario: Hours outside the dark window change no other field

- **WHEN** a verdict is produced twice for the same pier and instant, once with the providers' hours limited to the dark window and once with extra hours before and after it
- **THEN** the two documents differ only in `timeline` and `later_nights`

## ADDED Requirements

### Requirement: The document carries the later nights after the observation

The verdict document SHALL carry a `later_nights` list as its last key, after
`observation`, always present. It SHALL hold one entry per later night, in date
order. Each entry SHALL hold a `dark_window` object with a `start` and an `end`,
in the same shape and precision as the top-level `dark_window`. Tonight's
fields SHALL be unchanged and SHALL NOT be repeated in `later_nights`.

#### Scenario: Each entry holds a dark window

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-11-21T18:00:00Z, with a `cloud_cover` series that covers every hour from 2026-11-21T18:00:00Z to 2026-11-24T17:00:00Z
- **THEN** `later_nights` is the last key of the document
- **AND** each entry of `later_nights` has exactly one key, `dark_window`, whose keys are `start` and `end`, in that order

#### Scenario: No later nights still gives the key

- **WHEN** a verdict is produced from the empty conditions value
- **THEN** the document's last key is `later_nights`, and its value is an empty list

### Requirement: Later nights follow the selected night one local solar day at a time

Each later night SHALL belong to one local solar day, from one local solar noon
to the next. The first later night SHALL belong to the solar day after the
selected night's solar day, and each further later night to the solar day after
the one before it. There SHALL be at most three later nights.

#### Scenario: Three nights after a London evening

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-11-21T18:00:00Z, with a `cloud_cover` series that covers every hour from 2026-11-21T18:00:00Z to 2026-11-24T17:00:00Z
- **THEN** the top-level `dark_window` is `{start: 2026-11-21T18:02:27Z, end: 2026-11-22T05:30:58Z}`
- **AND** `later_nights` holds three entries, whose `dark_window` values are `{start: 2026-11-22T18:01:39Z, end: 2026-11-23T05:32:17Z}`, `{start: 2026-11-23T18:00:54Z, end: 2026-11-24T05:33:35Z}` and `{start: 2026-11-24T18:00:11Z, end: 2026-11-25T05:34:52Z}`, in that order

#### Scenario: A longer forecast still gives three

- **WHEN** a verdict is produced for the same pier at 2026-11-21T18:00:00Z, with a `cloud_cover` series that covers every hour from 2026-11-21T18:00:00Z to 2026-11-26T17:00:00Z
- **THEN** `later_nights` holds three entries, and the last one's `dark_window.start` is 2026-11-24T18:00:11Z

### Requirement: A later night counts only while the timeline holds an hour inside its solar day

A later night SHALL be in `later_nights` only when the `timeline` holds an entry
whose hour starts inside that later night's solar day. The first solar day with
no such hour SHALL end the list. The hours of the selected night alone never
reach a later night, so with no provider rows `later_nights` SHALL be empty.

#### Scenario: Every forecast fails

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-11-21T18:00:00Z, from the empty conditions value
- **THEN** the `timeline`'s last entry is 2026-11-22T11:00:00Z
- **AND** `later_nights` is an empty list

#### Scenario: A morning forecast reaches two later nights

- **WHEN** a verdict is produced for the same pier at 2026-11-21T08:00:00Z, with a `cloud_cover` series that covers every hour from 2026-11-21T08:00:00Z to 2026-11-24T07:00:00Z
- **THEN** `later_nights` holds two entries, whose `dark_window.start` values are 2026-11-22T18:01:39Z and 2026-11-23T18:00:54Z

#### Scenario: One hour past the solar noon is enough

- **WHEN** a verdict is produced for the same pier at 2026-11-21T18:00:00Z, with a `cloud_cover` series that covers every hour from 2026-11-21T18:00:00Z to 2026-11-22T12:00:00Z
- **THEN** `later_nights` holds one entry, whose `dark_window` is `{start: 2026-11-22T18:01:39Z, end: 2026-11-23T05:32:17Z}`

### Requirement: A later night's dark window is the whole astronomical night in its solar day

A later night's `dark_window` SHALL run from the astronomical dusk to the
astronomical dawn inside its solar day, however short the night, at
whole-second precision, with `start` strictly before `end`. When the solar day
starts dark, `start` SHALL be the day's start; when it ends dark, `end` SHALL be
the day's end. So continuous astronomical night gives the whole solar day. It
SHALL keep the whole night even where the night runs past the `timeline`.

#### Scenario: The last night runs past the timeline

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-11-21T18:00:00Z, with a `cloud_cover` series that covers every hour from 2026-11-21T18:00:00Z to 2026-11-24T17:00:00Z
- **THEN** the third entry's `dark_window` is `{start: 2026-11-24T18:00:11Z, end: 2026-11-25T05:34:52Z}`, after the `timeline`'s last entry at 2026-11-24T17:00:00Z

#### Scenario: Continuous polar night

- **WHEN** a verdict is produced for a pier at latitude 88.0, longitude 0.0, elevation 0 m, at 2026-12-10T12:00:00Z, with a `cloud_cover` series that covers every hour from 2026-12-10T12:00:00Z to 2026-12-13T11:00:00Z
- **THEN** the top-level `dark_window` is `{start: 2026-12-10T11:52:46Z, end: 2026-12-11T11:53:13Z}`
- **AND** `later_nights` holds two entries, whose `dark_window` values are `{start: 2026-12-11T11:53:13Z, end: 2026-12-12T11:53:41Z}` and `{start: 2026-12-12T11:53:41Z, end: 2026-12-13T11:54:09Z}`

#### Scenario: Polar night begins

- **WHEN** a verdict is produced for a pier at latitude 88.0, longitude 0.0, elevation 0 m, at 2026-11-20T00:00:00Z, with a `cloud_cover` series that covers every hour from 2026-11-20T00:00:00Z to 2026-11-22T23:00:00Z
- **THEN** the top-level `dark_window` is `{start: 2026-11-19T14:23:06Z, end: 2026-11-20T09:45:15Z}`
- **AND** `later_nights` holds three entries, whose `dark_window` values are `{start: 2026-11-20T13:37:18Z, end: 2026-11-21T11:04:35Z}`, `{start: 2026-11-21T12:19:00Z, end: 2026-11-22T11:46:06Z}` and `{start: 2026-11-22T11:46:06Z, end: 2026-11-23T11:46:23Z}`, in that order
- **AND** the second entry's `end` is the end of its solar day, which has no astronomical dawn

#### Scenario: Polar night ends

- **WHEN** a verdict is produced for the same pier at 2026-01-18T00:00:00Z, with a `cloud_cover` series that covers every hour from 2026-01-18T00:00:00Z to 2026-01-20T23:00:00Z
- **THEN** the top-level `dark_window` is `{start: 2026-01-17T12:10:04Z, end: 2026-01-18T12:10:23Z}`
- **AND** `later_nights` holds three entries, whose `dark_window` values are `{start: 2026-01-18T12:10:23Z, end: 2026-01-19T12:10:42Z}`, `{start: 2026-01-19T12:10:42Z, end: 2026-01-20T12:11:00Z}` and `{start: 2026-01-20T12:11:00Z, end: 2026-01-21T10:41:22Z}`, in that order
- **AND** the third entry's `start` is the start of its solar day, which has no astronomical dusk

### Requirement: A later night with no astronomical darkness has null dark-window bounds

When the sun stays above −18° through a later night's whole solar day, that
later night SHALL still be in `later_nights`, with its `dark_window` `start` and
`end` both null. It SHALL NOT take its dark window from another solar day.

#### Scenario: Darkness returns after the summer

- **WHEN** a verdict is produced for a pier at latitude 55.0, longitude −3.0, elevation 0 m, at 2026-08-03T22:00:00Z, with a `cloud_cover` series that covers every hour from 2026-08-03T22:00:00Z to 2026-08-06T21:00:00Z
- **THEN** the top-level `dark_window` is `{start: null, end: null}`
- **AND** `later_nights` holds three entries, whose `dark_window` values are `{start: null, end: null}`, `{start: 2026-08-05T23:49:40Z, end: 2026-08-06T00:46:51Z}` and `{start: 2026-08-06T23:36:59Z, end: 2026-08-07T00:59:18Z}`, in that order

#### Scenario: Darkness ends in the spring

- **WHEN** a verdict is produced for the same pier at 2026-05-05T22:00:00Z, with a `cloud_cover` series that covers every hour from 2026-05-05T22:00:00Z to 2026-05-08T21:00:00Z
- **THEN** the top-level `dark_window` is `{start: 2026-05-05T23:27:37Z, end: 2026-05-06T00:49:01Z}`
- **AND** `later_nights` holds three entries, whose `dark_window` values are `{start: 2026-05-06T23:40:29Z, end: 2026-05-07T00:36:00Z}`, `{start: null, end: null}` and `{start: null, end: null}`, in that order

### Requirement: The later nights read only the timeline's hours

Which later nights exist SHALL depend only on the pier, the evaluation instant
and the hours the `timeline` holds, never on a forecast value. The later nights
SHALL change no other field of the document.

#### Scenario: Different cloud, the same later nights

- **WHEN** two verdicts are produced for the same pier at the same instant from two conditions values whose `cloud_cover` series cover the same hours, one at 0% in every hour and one at 100% in every hour
- **THEN** both documents have the same `later_nights`
