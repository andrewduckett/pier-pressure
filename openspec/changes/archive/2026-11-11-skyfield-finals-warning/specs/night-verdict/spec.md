## ADDED Requirements

### Requirement: Loading the bundled astronomical data raises no expiry warning

Loading the bundled ephemeris and timescale data SHALL raise no warning that
a bundled data file has expired, whatever the current date. Such a warning
tells users to expect computation errors, so it must not appear for data the
system does not read.

#### Scenario: Ephemeris loads with no warning after a bundled file's expiry date

- **WHEN** the bundled ephemeris is loaded on a date after every bundled data file's recorded expiry date
- **THEN** loading succeeds
- **AND** no warning is raised

### Requirement: A verdict outside the bundled ephemeris's range fails with an error

Producing a verdict for an evaluation instant outside the date range the
bundled ephemeris covers SHALL fail with an error that names the covered
range, and SHALL NOT emit a verdict document. The ephemeris's own range,
not a warning, is what guards against computing from data that has run out.

#### Scenario: Evaluation instant after the ephemeris's coverage ends

- **WHEN** a verdict is produced for the pinned evaluation instant 2060-01-01T22:00:00Z
- **THEN** production fails with an error stating the ephemeris covers dates through 2053-10-09
- **AND** no verdict document is returned
