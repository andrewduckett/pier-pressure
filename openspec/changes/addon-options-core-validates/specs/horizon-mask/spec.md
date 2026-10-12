## MODIFIED Requirements

### Requirement: Inline points configuration

A pier MAY configure its horizon as an inline list of `[azimuth, altitude]` pairs. The
pairs need not be given in azimuth order; the system SHALL order them. Each azimuth
SHALL lie in 0 to 360 degrees (360 normalized to 0, per the representation requirement)
and each altitude in 0 to 90 degrees; a pair outside these ranges SHALL make the pier's
configuration invalid. Two pairs at the same azimuth (including one produced by
normalizing 360 to 0) SHALL be deduplicated when their rounded altitudes are equal, and
SHALL make the configuration invalid when their rounded altitudes differ, because a
single direction cannot rise to two altitudes. At least one pair SHALL be given.

A pier MAY instead write its inline points as text that holds the same list in YAML,
such as `"[[0, 10], [90, 20]]"`. The system SHALL read the text and SHALL then treat
the result exactly as an inline list. The pier's configuration SHALL be invalid, with
an error that names `horizon.points`, when the text cannot be read as YAML, or when
it does not hold a list of points. Text that holds nothing, such as empty text, blank
text or only a comment, does not hold a list of points. Any error SHALL stay on one
line.

#### Scenario: Unordered pairs are accepted and ordered

- **WHEN** a pier configures inline points whose pairs are not in azimuth order
- **THEN** the resulting horizon behaves as if the pairs were ordered by azimuth

#### Scenario: An out-of-range pair is rejected

- **WHEN** a pier configures an inline pair with an azimuth outside 0 to 360 or an altitude outside 0 to 90
- **THEN** the pier's configuration is reported as invalid

#### Scenario: A duplicate azimuth is rejected

- **WHEN** a pier configures two inline pairs with the same azimuth
- **THEN** the pier's configuration is reported as invalid

#### Scenario: Points written as text equal the same list

- **WHEN** a pier configures `horizon.points` as the text `"[[0, 10], [90, 25], [180, 5]]"`
- **THEN** the resulting horizon answers queries identically to a pier whose `horizon.points` is the list `[[0, 10], [90, 25], [180, 5]]`

#### Scenario: Unreadable text is rejected

- **WHEN** a pier configures `horizon.points` as the text `"[[0, 10], [90"`
- **THEN** the pier's configuration is reported as invalid
- **AND** the error names `horizon.points`
- **AND** the error is one line

#### Scenario: Text that holds no list of points is rejected

- **WHEN** a pier configures `horizon.points` as the text `"5"`, as empty text, or as the text `"# none"`
- **THEN** the pier's configuration is reported as invalid
- **AND** the error names `horizon.points`
