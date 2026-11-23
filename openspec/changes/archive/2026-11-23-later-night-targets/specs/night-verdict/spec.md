<!-- Plain language: Name the actor, condition and observable result. Explain necessary domain terms using the agreed glossary. Keep requirement and scenario headings and WHEN/THEN syntax exactly as required. -->

## ADDED Requirements

### Requirement: A later night entry holds its dark window, moon and targets

Each `later_nights` entry SHALL be an object with exactly the keys
`dark_window`, `moon` and `targets`, in that order. `moon` SHALL have the shape
of the top-level `moon`, and `targets` the shape of the top-level `targets`. A
later night SHALL carry no verdict, score, confidence or reasons of its own.
The later nights' moon and targets SHALL change no other field of the document.

#### Scenario: An entry's keys

- **WHEN** a verdict is produced with at least one later night
- **THEN** every `later_nights` entry has exactly the keys `dark_window`, `moon` and `targets`, in that order

#### Scenario: Later nights leave tonight's fields as they were

- **WHEN** two verdicts are produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, one with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T18:00:00Z and one with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-09T06:00:00Z
- **THEN** the first has two later nights and the second has none
- **AND** the two documents have the same `verdict`, `score`, `reasons`, `targets`, `dark_window`, `scored_window` and `moon`

### Requirement: A later night's moon illumination and phase are taken at its local solar midnight

A later night's `moon.illumination` and `moon.phase` SHALL be computed at the
middle of its local solar day, floored to the whole second, by the same rules as
the top-level `moon`. Its `up_during_dark`, `rise` and `set` SHALL describe the
moon within the later night's own `dark_window`, by the rules of the top-level
`moon`, and SHALL be null when that window is null.

#### Scenario: The next night's moon

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T18:00:00Z
- **THEN** the first later night's solar day runs from 2026-09-09T11:57:48Z to 2026-09-10T11:57:27Z, and its `moon` illumination and phase are those at 2026-09-09T23:57:37Z
- **AND** the first later night's `moon` is `{"illumination": 0.02, "phase": "new", "up_during_dark": false, "rise": null, "set": null}`
- **AND** the top-level `moon.illumination` is 0.07

#### Scenario: A moon up all through a later night

- **WHEN** a verdict is produced for the same pier at 2026-11-21T12:00:00Z, with a `cloud_cover` series that covers 2026-11-21T12:00:00Z to 2026-11-23T18:00:00Z
- **THEN** the first later night's `moon` is `{"illumination": 0.96, "phase": "waxing gibbous", "up_during_dark": true, "rise": null, "set": null}`

#### Scenario: A later night with no astronomical darkness

- **WHEN** a verdict is produced for a pier at latitude 52.0, longitude 0.0, elevation 0 m, at 2026-05-19T15:00:00Z, with a `cloud_cover` series that covers 2026-05-19T15:00:00Z to 2026-05-21T18:00:00Z
- **THEN** the first later night's `moon` is `{"illumination": 0.24, "phase": "waxing crescent", "up_during_dark": null, "rise": null, "set": null}`

### Requirement: A later night's targets are present, and empty when nothing is rankable

A later night's `targets` SHALL always be present as a list, ordered by score
and holding at most 10 targets, by the rules of the top-level `targets`. It
SHALL be empty when the later night's `dark_window` is null.

#### Scenario: A later night with no astronomical darkness has no targets

- **WHEN** a verdict is produced for a pier at latitude 52.0, longitude 0.0, elevation 0 m, at 2026-05-19T15:00:00Z, with a `cloud_cover` series that covers 2026-05-19T15:00:00Z to 2026-05-21T18:00:00Z
- **THEN** each of the two later nights has `targets` present as an empty list

#### Scenario: A dark later night holds ten targets

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T18:00:00Z
- **THEN** each of the two later nights has 10 targets, ordered by score from highest to lowest

## MODIFIED Requirements

### Requirement: The document carries the later nights

The verdict document SHALL carry a `later_nights` key, always present, after
`observation`. It SHALL be a list with one entry per later night, in date order,
and empty when there are none. A later night is a night after the selected
night, one per local solar day. Every key before `later_nights` SHALL keep its
position, value and meaning.

#### Scenario: Two later nights

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T18:00:00Z
- **THEN** `later_nights` holds two entries, whose `dark_window` values are `{"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}` and `{"start": "2026-09-10T20:25:07Z", "end": "2026-09-11T03:30:11Z"}`, in that order
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
- **AND** `later_nights` holds two entries, for the solar days that start on 2026-06-22 and 2026-06-23, and each entry's `dark_window` is `{"start": null, "end": null}`

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
- **AND** `later_nights` holds two entries, and each entry's `dark_window` is `{"start": null, "end": null}`

#### Scenario: Continuous polar night

- **WHEN** a verdict is produced for a pier at latitude 88.0, longitude 0.0, elevation 0 m, at 2026-12-10T12:00:00Z, with a `cloud_cover` series that covers 2026-12-10T12:00:00Z to 2026-12-14T12:00:00Z
- **THEN** `later_nights` holds three entries
- **AND** each entry's `dark_window` runs from its solar day's start to its end, at whole seconds, and the three windows follow one another with no gap and no overlap

## REMOVED Requirements

### Requirement: A later night entry holds only its dark window

**Reason**: Each later night now carries its own moon and ranked targets beside
its dark window.

**Migration**: Read the new requirement "A later night entry holds its dark
window, moon and targets". A reader that took `dark_window` from each entry
still finds it, as the first key, unchanged.
