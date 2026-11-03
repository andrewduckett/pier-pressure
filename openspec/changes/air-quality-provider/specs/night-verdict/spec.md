## ADDED Requirements

### Requirement: Variables the timeline does not show never change the document

Some variables in the conditions are not shown on the timeline: today,
`aerosol_optical_depth` and `pm2_5`. The verdict document SHALL NOT depend on
them. No gate, score,
reason, confidence, agreement, timeline entry or timeline hour SHALL change
with their presence, absence or values.

#### Scenario: Air-quality series leave the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether `aerosol_optical_depth` and `pm2_5` series are present and in their values
- **THEN** the two serialized documents are byte-identical

#### Scenario: Air-quality series alone yield the empty-conditions document

- **WHEN** a verdict is produced from a snapshot whose only series are `aerosol_optical_depth` and `pm2_5`
- **THEN** the serialized document is byte-identical to the one produced for the same pier and instant from the empty conditions value
- **AND** its `timeline` is an empty list

## MODIFIED Requirements

### Requirement: The document carries an hourly timeline

The verdict document SHALL carry a `timeline` list: the hourly series of sky and weather for the pier. The list SHALL hold one entry per clock hour across the union of the hours covered by every filled series of a variable the timeline shows, including hours already past. Hours only an alternate covers SHALL NOT add an entry, and hours only a series of a variable the timeline does not show covers SHALL NOT add an entry. It SHALL be sorted by hour ascending, with no hour repeated. The list SHALL be empty, never absent, when no provider returned rows for a variable the timeline shows.

#### Scenario: The timeline spans the union of both providers' hours

- **WHEN** a verdict is produced with a cloud-cover series covering 00:00 to 23:00 on one day and a seeing series covering 12:00 on that day to 11:00 two days later
- **THEN** the `timeline` holds one entry for every hour from the first day's 00:00 to the third day's 11:00, in ascending order, with no hour repeated

#### Scenario: No provider rows yield an empty timeline

- **WHEN** a verdict is produced with the empty conditions value
- **THEN** the document's `timeline` is an empty list
- **AND** the verdict is produced without error

#### Scenario: Past hours stay in the timeline

- **WHEN** a verdict is produced inside the dark window, with the evaluation instant later than some hours a provider returned
- **THEN** the entries for those earlier hours are present and unchanged
- **AND** the `scored_window` still starts at the evaluation instant

#### Scenario: Hours only an alternate covers add no entry

- **WHEN** every filled series ends at 03:00 and a `cloud_cover` alternate runs to 03:00 two days later
- **THEN** the `timeline`'s last entry is 03:00 on the first night

#### Scenario: Hours only a hidden variable covers add no entry

- **WHEN** every filled series of a variable the timeline shows ends at 03:00 and an `aerosol_optical_depth` series runs to 03:00 two days later
- **THEN** the `timeline`'s last entry is 03:00 on the first night

### Requirement: The timeline is evidence beside the verdict

The timeline SHALL be filled whenever a provider returned rows for a variable the timeline shows, whether or not the selected night has a dark window. It SHALL NOT change the verdict, the score, the confidence, the reasons or any other existing field. It carries no verdict of its own: the verdict judges the one night the dark window names, however far the timeline reaches.

#### Scenario: The timeline fills without a dark window

- **WHEN** a verdict is produced for a pier whose selected night has no dark window and a provider returned rows
- **THEN** the `timeline` holds one entry per returned hour
- **AND** the document with `timeline` removed equals the document produced for the same pier and instant from the empty conditions value

#### Scenario: Hours outside the dark window change no other field

- **WHEN** a verdict is produced twice for the same pier and instant, once with the providers' hours limited to the dark window and once with extra hours before and after it
- **THEN** the two documents differ only in `timeline`
