## ADDED Requirements

### Requirement: A zero-padded azimuth in inline points is a decimal number

An azimuth or altitude in a pier's inline points that is an integer written with
leading zeros SHALL be read as that decimal number. This SHALL hold for points
given as a list and for points written as YAML text.

#### Scenario: A padded azimuth in a list of points

- **WHEN** a pier configures `horizon.points` as the list `[[045, 10], [180, 5]]` in the configuration file
- **THEN** the pier's horizon samples are `(45, 10)` and `(180, 5)`

#### Scenario: A padded azimuth in points text

- **WHEN** a pier configures `horizon.points` as the text `"[[045, 10], [180, 5]]"`
- **THEN** the pier's horizon samples are `(45, 10)` and `(180, 5)`

### Requirement: A base-60 value in inline points is rejected

A pier's configuration SHALL be invalid when an azimuth or altitude in its inline
points is written as numbers joined by colons, such as `1:30`. This SHALL hold
for points given as a list and for points written as YAML text. The error SHALL
name the pier and `horizon.points`.

#### Scenario: A base-60 azimuth in a list of points

- **WHEN** a pier configures `horizon.points` as the list `[[1:30, 20], [180, 5]]` in the configuration file
- **THEN** the pier's configuration is reported as invalid
- **AND** the error names the pier and `horizon.points`

#### Scenario: A base-60 azimuth in points text

- **WHEN** a pier configures `horizon.points` as the text `"[[1:30, 20], [180, 5]]"`
- **THEN** the pier's configuration is reported as invalid
- **AND** the error names the pier and `horizon.points`
