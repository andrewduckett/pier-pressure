## ADDED Requirements

### Requirement: The timeline holds every hour of the selected night's solar day

The `timeline` SHALL hold an entry for every clock hour that starts inside the
selected night's local solar day, whatever the providers returned. The solar
day runs from one local solar noon to the next. When the selected night has a
dark window, it is the solar day that holds `dark_window.start`.

#### Scenario: An ordinary night with no provider rows

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, from the empty conditions value
- **THEN** the `timeline` holds 24 entries, one per hour from 2026-09-08T12:00:00Z to 2026-09-09T11:00:00Z, in ascending order

#### Scenario: Continuous polar night

- **WHEN** a verdict is produced from the empty conditions value during continuous polar night, at an evaluation instant inside the dark window
- **THEN** the `timeline` holds one entry for every clock hour that starts inside `dark_window`, and no other entry

### Requirement: The night's hours start at the current hour when that comes first

When the clock hour that holds the evaluation instant starts before the
selected night's solar day, the `timeline` SHALL also hold every clock hour
from that hour up to the solar day.

#### Scenario: A morning after dawn

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-09T06:30:00Z, from the empty conditions value
- **THEN** the `timeline` holds one entry per hour from 2026-09-09T06:00:00Z to 2026-09-10T11:00:00Z, in ascending order

#### Scenario: The current hour inside the solar day adds nothing

- **WHEN** a verdict is produced for the same pier at 2026-09-08T18:00:00Z, from the empty conditions value
- **THEN** the `timeline`'s first entry is 2026-09-08T12:00:00Z

### Requirement: Without a dark window, the solar day is the next one to reach its midpoint

When the selected night has no dark window, its solar day SHALL be the first
local solar day whose midpoint, halfway between its two solar noons, is at or
after the evaluation instant.

#### Scenario: A summer night that never reaches astronomical darkness

- **WHEN** a verdict is produced for a pier at latitude 55.0, longitude −3.0, elevation 0 m, at 2026-06-21T08:00:00Z, from the empty conditions value
- **THEN** `dark_window` is null
- **AND** the `timeline` holds one entry per hour from 2026-06-21T08:00:00Z to 2026-06-22T12:00:00Z, in ascending order

#### Scenario: Before the midpoint the current solar day applies

- **WHEN** a verdict is produced for the same pier at 2026-06-20T22:00:00Z, from the empty conditions value
- **THEN** the `timeline`'s first entry is 2026-06-20T13:00:00Z and its last is 2026-06-21T12:00:00Z

### Requirement: An hour no provider returned carries only its time and altitudes

A timeline entry for an hour that no filled series of a shown variable covers
SHALL carry its `time`, `sun_altitude` and `moon_altitude`, and null for every
other key.

#### Scenario: Every forecast fails

- **WHEN** a verdict is produced from the empty conditions value
- **THEN** every entry's `sun_altitude` and `moon_altitude` are numbers
- **AND** every other key of every entry except `time` is null

#### Scenario: A forecast shorter than the solar day

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-09T05:00:00Z
- **THEN** the `timeline` holds one entry per hour from 2026-09-08T12:00:00Z to 2026-09-09T11:00:00Z
- **AND** the entries before 18:00 and after 05:00 have a null `cloud_cover`

### Requirement: With no provider rows, the timeline carries the selected night's astronomy

The `timeline` list SHALL never be empty or absent. When no provider returned
rows for a variable the timeline shows, it SHALL hold exactly the selected
night's hours, and the verdict SHALL be produced without error.

#### Scenario: No provider rows yield the night's hours

- **WHEN** a verdict is produced with the empty conditions value
- **THEN** the document's `timeline` holds exactly the selected night's hours
- **AND** the verdict is produced without error

## MODIFIED Requirements

### Requirement: The timeline is evidence beside the verdict

The timeline SHALL be filled whether or not a provider returned rows, and whether or not the selected night has a dark window. It SHALL NOT change the verdict, the score, the confidence, the reasons or any other existing field. It carries no verdict of its own: the verdict judges the one night the dark window names, however far the timeline reaches.

#### Scenario: The timeline fills without a dark window

- **WHEN** a verdict is produced for a pier whose selected night has no dark window and a provider returned rows
- **THEN** the `timeline` holds one entry per returned hour and per hour of the selected night, each hour once
- **AND** the document with `timeline` removed equals the document produced for the same pier and instant from the empty conditions value

#### Scenario: Hours outside the dark window change no other field

- **WHEN** a verdict is produced twice for the same pier and instant, once with the providers' hours limited to the dark window and once with extra hours before and after it
- **THEN** the two documents differ only in `timeline`

### Requirement: The timeline holds one entry per hour a shown variable's filled series covers

The verdict document SHALL carry a `timeline` list: the hourly series of sky and
weather for the pier. Beside the selected night's hours, the list SHALL hold one
entry per clock hour that a filled series of a shown variable covers, including
hours already past. A shown variable is one the timeline carries as a key. The
list SHALL be sorted by hour ascending, with no hour repeated.

#### Scenario: The timeline spans the union of both providers' hours

- **WHEN** a verdict is produced with a cloud-cover series covering 00:00 to 23:00 on one day and a seeing series covering 12:00 on that day to 11:00 two days later, and the selected night's hours all fall inside that span
- **THEN** the `timeline` holds one entry for every hour from the first day's 00:00 to the third day's 11:00, in ascending order, with no hour repeated

#### Scenario: Past hours stay in the timeline

- **WHEN** a verdict is produced inside the dark window, with the evaluation instant later than some hours a provider returned
- **THEN** the entries for those earlier hours are present and unchanged
- **AND** the `scored_window` still starts at the evaluation instant

#### Scenario: Provider hours past the night stay in the timeline

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T18:00:00Z
- **THEN** the `timeline` holds one entry per hour from 2026-09-08T12:00:00Z to 2026-09-10T18:00:00Z

### Requirement: Hours only an alternate covers add no timeline entry

Hours only an alternate covers SHALL NOT add a timeline entry, unless they are
among the selected night's hours.

#### Scenario: Hours only an alternate covers add no entry

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, every filled series ends at 2026-09-09T18:00:00Z, and a `cloud_cover` alternate runs to 2026-09-11T18:00:00Z
- **THEN** the `timeline`'s last entry is 2026-09-09T18:00:00Z

### Requirement: A variable the timeline does not show adds no timeline hour

Hours only a series of a variable the timeline does not show covers SHALL NOT
add a timeline entry, unless they are among the selected night's hours.

#### Scenario: Hours only a hidden variable covers add no entry

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, every filled series of a variable the timeline shows ends at 2026-09-09T18:00:00Z, and an `aerosol_optical_depth` series runs to 2026-09-11T18:00:00Z
- **THEN** the `timeline`'s last entry is 2026-09-09T18:00:00Z

### Requirement: Variables the timeline does not show leave the document unchanged

The timeline does not show these variables in the conditions: today,
`aerosol_optical_depth`, `pm2_5`, `column_water_vapour` and the seeing column's
36 variables. The verdict document SHALL NOT depend on them. No gate, score,
reason, confidence, agreement, timeline entry or timeline hour SHALL change with
their presence, absence or values. A value derived from them reaches the
document only as a shown variable's series in the snapshot, such as the computed
source's `transparency` and `seeing`.

#### Scenario: Air-quality series leave the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether `aerosol_optical_depth` and `pm2_5` series are present and in their values
- **THEN** the two serialized documents are byte-identical

#### Scenario: Air-quality series alone yield the empty-conditions document

- **WHEN** a verdict is produced from a snapshot whose only series are `aerosol_optical_depth` and `pm2_5`
- **THEN** the serialized document is byte-identical to the one produced for the same pier and instant from the empty conditions value
- **AND** its `timeline` holds exactly the selected night's hours

#### Scenario: A column water vapour series leaves the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether a `column_water_vapour` series is present and in its values
- **THEN** the two serialized documents are byte-identical

#### Scenario: Seeing-column series leave the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether the seeing column's series are present and in their values
- **THEN** the two serialized documents are byte-identical

## REMOVED Requirements

### Requirement: The timeline is empty, never absent, when no provider returned rows

**Reason**: The timeline now always holds the selected night's hours, so it is never empty.

**Migration**: Read "With no provider rows, the timeline carries the selected night's astronomy". A reader that took an empty timeline to mean "no forecast" checks whether the entries' weather values are null instead.
