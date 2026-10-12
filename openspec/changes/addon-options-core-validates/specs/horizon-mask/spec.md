## MODIFIED Requirements

### Requirement: Inline points configuration

A pier MAY configure its horizon as an inline list of `[azimuth, altitude]` pairs.
The list SHALL follow these rules:

- **Order:** the pairs need not be in azimuth order. The system SHALL order them.
- **Ranges:** each azimuth SHALL lie from 0 to 360 degrees. An azimuth of 360 SHALL
  be normalized to 0, as the representation requirement says. Each altitude SHALL lie
  from 0 to 90 degrees. A pair outside these ranges SHALL make the pier's configuration
  invalid.
- **Repeated azimuths:** an azimuth can repeat, including one that comes from
  normalizing 360 to 0.
  - When the pairs' rounded altitudes are equal, the system SHALL keep one pair.
  - When they differ, the pier's configuration SHALL be invalid. One direction cannot
    rise to two altitudes.
- **Size:** the list SHALL hold at least one pair.

A pier MAY instead write the list as YAML text, such as `"[[0, 10], [90, 20]]"`. The
system SHALL read the text, and SHALL then treat the result exactly as an inline list.

The pier's configuration SHALL be invalid when the text:

- cannot be read as YAML
- does not hold a list of points
- holds nothing, such as empty text, blank text or only a comment

The error SHALL name `horizon.points`. When the error quotes the YAML reader's message,
it SHALL keep that message on one line.

#### Scenario: Unordered pairs are accepted and ordered

- **WHEN** a pier configures inline points whose pairs are not in azimuth order
- **THEN** the resulting horizon behaves as if the pairs were ordered by azimuth

#### Scenario: An out-of-range pair is rejected

- **WHEN** a pier configures an inline pair with an azimuth outside 0 to 360 or an altitude outside 0 to 90
- **THEN** the pier's configuration is reported as invalid

#### Scenario: A duplicate azimuth is rejected

- **WHEN** a pier configures two inline pairs with the same azimuth and different rounded altitudes
- **THEN** the pier's configuration is reported as invalid

#### Scenario: A repeated pair is deduplicated

- **WHEN** a pier configures two inline pairs with the same azimuth and equal rounded altitudes
- **THEN** the resulting horizon answers queries identically to a pier that gives that pair once

#### Scenario: Points written as text equal the same list

- **WHEN** a pier configures `horizon.points` as the text `"[[0, 10], [90, 25], [180, 5]]"`
- **THEN** the resulting horizon answers queries identically to a pier whose `horizon.points` is the list `[[0, 10], [90, 25], [180, 5]]`

#### Scenario: Unreadable text is rejected

- **WHEN** a pier configures `horizon.points` as the text `"[[0, 10], [90"`
- **THEN** the pier's configuration is reported as invalid
- **AND** the error names `horizon.points`
- **AND** the YAML reader's message in the error is on one line

#### Scenario: Text that holds no list of points is rejected

- **WHEN** a pier configures `horizon.points` as the text `"5"`, as the text `"{a: 1}"`, as empty text, or as the text `"# none"`
- **THEN** the pier's configuration is reported as invalid
- **AND** the error names `horizon.points`
