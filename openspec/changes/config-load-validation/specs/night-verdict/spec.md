## ADDED Requirements

### Requirement: A pier id repeated in the piers list stops startup

When two or more entries in the piers list have the same text `id`, the system
SHALL report a configuration error that names that id, and SHALL NOT start. An
entry SHALL count whether or not it passes its other checks. Two ids that
differ only in letter case SHALL NOT count as the same id.

#### Scenario: Two piers with one id stop startup

- **WHEN** the piers list holds two entries with the id `backyard`
- **THEN** startup fails with a configuration error that names `backyard`
- **AND** no verdict document is published

#### Scenario: An entry that is otherwise invalid still counts

- **WHEN** the piers list holds a valid pier with the id `backyard`
- **AND** a second entry with the id `backyard` whose latitude is 95
- **THEN** startup fails with a configuration error that names `backyard`

#### Scenario: Ids that differ in letter case are distinct

- **WHEN** the piers list holds one valid pier with the id `backyard` and another with the id `Backyard`
- **THEN** both piers are accepted
- **AND** each produces its own verdict document

### Requirement: The repeated-id error shows only the id

The configuration error for a repeated pier id SHALL be one line. It SHALL show
the repeated id, escaped so that a line break in the id cannot split the line,
and SHALL show no other configuration value.

#### Scenario: An id with a line break stays on one line

- **WHEN** two entries in the piers list have the id `back` followed by a line break and `yard`
- **THEN** the configuration error is a single line that names that id with the line break escaped
- **AND** the error holds no other value from either entry

### Requirement: A zero-padded integer in the configuration file is a decimal number

When a number setting in the configuration file is given an integer written
with one or more leading zeros, with or without a sign, the setting SHALL take
that decimal number.

#### Scenario: A padded go-threshold is read as decimal

- **WHEN** a pier in the configuration file sets `go_threshold: 070`
- **THEN** the pier's go-threshold is 70

#### Scenario: A padded negative number is read as decimal

- **WHEN** a pier in the configuration file sets `longitude: -045`
- **THEN** the pier's longitude is -45

#### Scenario: A padded number with the digit 8 or 9 is read as decimal

- **WHEN** a pier in the configuration file sets `go_threshold: 080`
- **THEN** the pier's go-threshold is 80

### Requirement: A base-60 value in the configuration file is text

The system SHALL read a value in the configuration file that is written as
numbers joined by colons, such as `1:30` or `1:30.5`, as text, not as a number.

#### Scenario: A base-60 number setting is rejected

- **WHEN** a pier in the configuration file sets `go_threshold: 1:05`
- **THEN** that pier is reported as invalid
- **AND** each other valid pier still produces a verdict document

#### Scenario: A base-60 id is text

- **WHEN** a pier in the configuration file sets `id: 1:30`, without quotes
- **THEN** the pier's id is the text `1:30`

### Requirement: Other number forms in the configuration file keep their meaning

The system SHALL read every other number in the configuration file as it did
before zero-padded and base-60 values changed. A hexadecimal value such as
`0x1A` SHALL still read as 26, and a value with underscores such as `1_000`
SHALL still read as 1000.

#### Scenario: Hexadecimal and underscore numbers are unchanged

- **WHEN** a pier in the configuration file sets `elevation_m: 0x1A`
- **AND** another pier sets `elevation_m: 1_000`
- **THEN** the first pier's elevation is 26 metres
- **AND** the second pier's elevation is 1000 metres
