## ADDED Requirements

### Requirement: The document carries an hourly timeline

The verdict document SHALL carry a `timeline` list: the hourly series of sky and weather for the pier. The list SHALL hold one entry per clock hour across the union of the hours the conditions providers returned, including hours already past, sorted by hour ascending, with no hour repeated. The list SHALL be empty, never absent, when no provider returned rows.

#### Scenario: The timeline spans the union of both providers' hours

- **WHEN** a verdict is produced with a base source covering 00:00 to 23:00 on one day and a secondary source covering 12:00 on that day to 11:00 two days later
- **THEN** the `timeline` holds one entry for every hour from the first day's 00:00 to the third day's 11:00, in ascending order, with no hour repeated

#### Scenario: No provider rows yield an empty timeline

- **WHEN** a verdict is produced with the empty conditions value
- **THEN** the document's `timeline` is an empty list
- **AND** the verdict is produced without error

#### Scenario: Past hours stay in the timeline

- **WHEN** a verdict is produced inside the dark window, with the evaluation instant later than some hours a provider returned
- **THEN** the entries for those earlier hours are present and unchanged
- **AND** the `scored_window` still starts at the evaluation instant

### Requirement: A timeline entry has a fixed flat shape

Each timeline entry SHALL carry exactly these keys, always present and in this order: `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`. `time` SHALL be the top of the hour, emitted like every other document timestamp.

#### Scenario: A read-back entry equals the emitted one

- **WHEN** a document with a timeline is serialized to JSON and read back
- **THEN** every entry's keys, order and values are unchanged

### Requirement: Entry values carry each source's reading for the hour

`cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high` SHALL be percent and `wind_gust` km/h, carried exactly as the base source's reading for that hour, with no rounding, each null when the base source lacks the hour or the value. `seeing` and `transparency` SHALL be quality in 0 to 1 where 1 is best, from the secondary source's reading for that hour, rounded to two decimal places, each null when the secondary source lacks the hour or the value.

#### Scenario: An hour one source lacks carries null for that source's fields

- **WHEN** an hour is present in the secondary source but absent from the base source
- **THEN** that entry's `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high` and `wind_gust` are null
- **AND** its `seeing` and `transparency` carry the secondary source's values
- **AND** its `sun_altitude` and `moon_altitude` are present

#### Scenario: Cloud and wind values pass through unchanged

- **WHEN** the base source reports cloud cover `37.0` and a gust of `23.4` for an hour
- **THEN** that entry's `cloud_cover` is `37.0` and its `wind_gust` is `23.4`

#### Scenario: Seeing and transparency are emitted at two decimal places

- **WHEN** the secondary source reports a seeing quality of four sevenths for an hour
- **THEN** that entry's `seeing` is `0.57`

### Requirement: Timeline altitudes are computed offline at fixed precision

Each entry's `sun_altitude` and `moon_altitude` SHALL be the geometric altitude of the body's centre in degrees at the entry's `time`, computed with no network access from the bundled ephemeris, rounded to the document's fixed angle precision, and present for every entry.

#### Scenario: Altitudes are byte-identical across runs

- **WHEN** a verdict is produced twice for the same pier, pinned instant and conditions with no network available
- **THEN** every entry's `sun_altitude` and `moon_altitude` are rounded to the document's fixed angle precision
- **AND** the two serialized timelines are byte-identical

#### Scenario: Altitudes agree with the dark window

- **WHEN** an entry's `time` falls inside the dark window
- **THEN** its `sun_altitude` is at or below minus 18.0 degrees after rounding

#### Scenario: Altitudes agree with the single-instant astronomy

- **WHEN** the sun and moon altitude for an hour are computed for the timeline and again one instant at a time with the same observer
- **THEN** the two agree at the document's fixed angle precision

### Requirement: The timeline is evidence beside the verdict

The timeline SHALL be filled whenever a provider returned rows, whether or not the selected night has a dark window. It SHALL NOT change the verdict, the score, the confidence, the reasons or any other existing field. It carries no verdict of its own: the verdict judges the one night the dark window names, however far the timeline reaches.

#### Scenario: The timeline fills without a dark window

- **WHEN** a verdict is produced for a pier whose selected night has no dark window and a provider returned rows
- **THEN** the `timeline` holds one entry per returned hour
- **AND** the document with `timeline` removed equals the document produced for the same pier and instant from the empty conditions value

#### Scenario: Hours outside the dark window change no other field

- **WHEN** a verdict is produced twice for the same pier and instant, once with the providers' hours limited to the dark window and once with extra hours before and after it
- **THEN** the two documents differ only in `timeline`
