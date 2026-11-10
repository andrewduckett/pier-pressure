## ADDED Requirements

### Requirement: A horizon is a set of azimuth and altitude samples

A pier's horizon SHALL be represented as an ordered set of `(azimuth, altitude)`
samples. Azimuth SHALL be measured from true north at 0 degrees, increasing clockwise
through east, and SHALL lie in the half-open range 0 to 360 degrees; a supplied value of
exactly 360 is the same direction as 0 and SHALL be normalized to 0. Altitude SHALL be
the angle the terrain rises to above the true horizon, in degrees, in the range 0 to 90.

#### Scenario: A sample at azimuth 360 is held at azimuth 0

- **WHEN** a horizon is given the samples `[0, 20]` and `[360, 20]`
- **THEN** every sample the horizon holds is at azimuth 0

### Requirement: Every horizon source gives the same samples

Every source of a horizon (inline configuration, a flat floor, or an imported file)
SHALL produce the same `(azimuth, altitude)` sample representation, so downstream
behaviour does not depend on where a horizon came from.

#### Scenario: An imported file and the same inline points hold the same samples

- **WHEN** a pier imports a NINA `.hrz` export and another pier configures the export's pairs as inline points
- **THEN** the two horizons hold the same samples in the same order

### Requirement: The horizon interpolates round a closed ring of samples

The samples define the horizon for the **entire** circle, not a partial overlay. The
horizon SHALL return an altitude for every azimuth by linear interpolation between the
two adjacent samples, and the samples SHALL be treated as a closed ring so the segment
from the greatest sampled azimuth back to the least is interpolated across the 360/0
boundary like any other segment.

#### Scenario: A sampled azimuth returns its own altitude

- **WHEN** the horizon is queried at an azimuth that equals one of its samples
- **THEN** the returned altitude equals that sample's altitude

#### Scenario: Altitude between samples is linearly interpolated

- **WHEN** the horizon is queried at an azimuth that lies between two adjacent samples
- **THEN** the returned altitude is the linear interpolation of those two samples' altitudes by azimuth

#### Scenario: Interpolation wraps across the 360/0 boundary

- **WHEN** the horizon is queried at an azimuth in the arc between the greatest sampled azimuth and the least (crossing 360/0)
- **THEN** the returned altitude is the linear interpolation of those two samples across the wrap, not a flat or undefined value

### Requirement: Sparse samples leave no direction open

A sparse sample set does **not** leave the unmentioned directions of a horizon open:
because the samples form a closed ring, those directions interpolate between the nearest
sample on each side. To model a localized obstruction with open sky around it, the
configuration SHALL include low (for example 0-degree) anchor samples bounding the
obstruction.

#### Scenario: Sparse samples interpolate rather than leaving open gaps

- **WHEN** a horizon is configured with only the samples `[170, 40]` and `[190, 40]` and is queried at azimuth 0
- **THEN** the returned altitude is 40, because the wrap segment interpolates across north between the two samples
- **AND** modelling open sky north of that obstruction therefore requires low anchor samples bounding it

### Requirement: A one-sample horizon has one altitude everywhere

A horizon of a single sample — including the flat-floor and default-open-sky cases —
SHALL return that one altitude at every azimuth, with no interpolation, so the
one-sample case is well defined rather than a degenerate division by a zero azimuth
span.

#### Scenario: A single-sample horizon is flat

- **WHEN** a horizon has exactly one sample (or is a flat floor, or is the default open sky) and is queried at any azimuth
- **THEN** the returned altitude is that single altitude, with no interpolation

### Requirement: Horizon altitudes have a fixed precision

Horizon altitudes SHALL be handled at a fixed, defined decimal precision: each sample's
altitude SHALL be rounded to that precision when the horizon is constructed, and the
altitude a query returns SHALL be rounded to it in the query itself. So the same samples
and the same azimuth yield the same altitude — and therefore the same above/below
classification at a grazing boundary — on repeated runs and across platforms,
consistent with the core's determinism guarantee.

#### Scenario: The queried altitude is deterministic to a fixed precision

- **WHEN** the same horizon is queried at the same azimuth on repeated runs
- **THEN** the returned altitude is identical, rounded to the defined precision

### Requirement: A pier may give inline points in any order

A pier MAY configure its horizon as an inline list of `[azimuth, altitude]` pairs. The
pairs need not be in azimuth order: the system SHALL order them.

#### Scenario: Unordered pairs are accepted and ordered

- **WHEN** a pier configures inline points whose pairs are not in azimuth order
- **THEN** the resulting horizon behaves as if the pairs were ordered by azimuth

### Requirement: Inline points lie within the azimuth and altitude ranges

Each azimuth in a pier's inline points SHALL lie from 0 to 360 degrees. An azimuth of
360 SHALL be normalized to 0, as the sample representation requires. Each altitude
SHALL lie from 0 to 90 degrees. A pair outside these ranges SHALL make the pier's
configuration invalid.

#### Scenario: An out-of-range pair is rejected

- **WHEN** a pier configures an inline pair with an azimuth outside 0 to 360 or an altitude outside 0 to 90
- **THEN** the pier's configuration is reported as invalid

### Requirement: A repeated azimuth in inline points keeps one altitude

An azimuth can repeat in a pier's inline points, including one that comes from
normalizing 360 to 0.

- When the pairs' rounded altitudes are equal, the system SHALL keep one pair.
- When they differ, the pier's configuration SHALL be invalid. One direction cannot
  rise to two altitudes.

Because sample altitudes are rounded when the horizon is constructed, this rule compares
rounded altitudes, so two samples that differ only by sub-precision floating-point noise
are treated as equal.

#### Scenario: A duplicate azimuth is rejected

- **WHEN** a pier configures two inline pairs with the same azimuth and different rounded altitudes
- **THEN** the pier's configuration is reported as invalid

#### Scenario: A repeated pair is deduplicated

- **WHEN** a pier configures two inline pairs with the same azimuth and equal rounded altitudes
- **THEN** the resulting horizon answers queries identically to a pier that gives that pair once

### Requirement: Inline points hold at least one pair

A pier's inline list of `[azimuth, altitude]` pairs SHALL hold at least one pair.

#### Scenario: An empty points list is rejected

- **WHEN** a pier configures `horizon.points` as the empty list `[]`
- **THEN** the pier's configuration is reported as invalid

### Requirement: Inline points may be written as YAML text

A pier MAY instead write its inline list of points as YAML text, such as
`"[[0, 10], [90, 20]]"`. The system SHALL read the text, and SHALL then treat the result
exactly as an inline list.

#### Scenario: Points written as text equal the same list

- **WHEN** a pier configures `horizon.points` as the text `"[[0, 10], [90, 25], [180, 5]]"`
- **THEN** the resulting horizon answers queries identically to a pier whose `horizon.points` is the list `[[0, 10], [90, 25], [180, 5]]`

### Requirement: Points text that gives no list is rejected

The pier's configuration SHALL be invalid when its points text:

- cannot be read as YAML
- does not hold a list of points
- holds nothing, such as empty text, blank text or only a comment

The error SHALL name `horizon.points`. When the error quotes the YAML reader's message,
it SHALL keep that message on one line.

#### Scenario: Unreadable text is rejected

- **WHEN** a pier configures `horizon.points` as the text `"[[0, 10], [90"`
- **THEN** the pier's configuration is reported as invalid
- **AND** the error names `horizon.points`
- **AND** the YAML reader's message in the error is on one line

#### Scenario: Text that holds no list of points is rejected

- **WHEN** a pier configures `horizon.points` as the text `"5"`, as the text `"{a: 1}"`, as empty text, or as the text `"# none"`
- **THEN** the pier's configuration is reported as invalid
- **AND** the error names `horizon.points`

### Requirement: A pier may import a NINA horizon export

A pier MAY reference a NINA `.hrz` horizon export as its horizon source. The system SHALL
parse the export's whitespace-separated `azimuth altitude` pair-per-line text into the
canonical representation, applying the same ordering and duplicate rules as inline
points.

#### Scenario: A valid export imports to the equivalent horizon

- **WHEN** a pier imports a NINA `.hrz` export whose pairs match a set of inline points
- **THEN** the resulting horizon answers queries identically to that inline-points horizon

### Requirement: The NINA importer skips blank and comment lines

In a NINA `.hrz` export, blank lines and comment lines — lines whose first
non-whitespace character is `#` — SHALL be ignored (the exact token is confirmed against
the committed fixture).

#### Scenario: Blank and comment lines are ignored

- **WHEN** a NINA `.hrz` export contains blank lines and comment lines among its pairs
- **THEN** those lines are ignored and the remaining pairs form the horizon

### Requirement: The NINA importer tolerates a 360 azimuth and altitudes below 0

Because real NINA `.hrz` exports close the polygon and carry sub-horizon terrain, the
importer SHALL tolerate two file-specific quirks rather than reject the file: an azimuth
of exactly 360 SHALL be normalized to 0 (and deduplicated against an existing 0 per the
inline-points rule), and an altitude below 0 — terrain below the true horizontal, which
cannot block an observable target — SHALL be clamped to 0.

#### Scenario: A polygon-closing 360 entry and sub-horizon altitude are tolerated

- **WHEN** a pier imports a NINA `.hrz` export whose pairs include an azimuth of exactly 360 and an altitude below 0
- **THEN** the 360 entry is normalized to 0 (deduplicated against any existing 0) and the sub-horizon altitude is clamped to 0
- **AND** the pier's configuration is valid

### Requirement: Malformed NINA content makes the pier's configuration invalid

In a NINA `.hrz` export, malformed content — a line that is neither blank, a comment,
nor a parseable pair — SHALL make the pier's configuration invalid rather than crash the
load.

#### Scenario: A malformed export invalidates only its pier

- **WHEN** a pier references a NINA `.hrz` export containing an unparseable line
- **THEN** that pier's configuration is reported as invalid
- **AND** other piers still produce verdicts

### Requirement: A relative horizon file path resolves against the configuration file

A relative file reference (for any file-based format) SHALL be resolved against the
directory of the configuration file, not the process working directory, so a horizon
file placed beside `config.yaml` is found regardless of where the service is launched
from.

#### Scenario: A relative file reference resolves against the config file

- **WHEN** a configuration references a horizon file by a relative path and the service is launched from an unrelated working directory
- **THEN** the file is resolved relative to the configuration file's own directory and loaded

### Requirement: A flat floor sets one altitude in every direction

A pier MAY configure a single flat altitude floor instead of terrain samples: the
horizon altitude SHALL then equal that floor in every direction, in the range 0 to 90
degrees.

#### Scenario: A flat floor applies in every direction

- **WHEN** a pier configures a flat altitude floor and the horizon is queried at any azimuth
- **THEN** the returned altitude equals that floor

### Requirement: A pier with no horizon has flat open sky

When a pier configures no horizon at all, its horizon SHALL be flat at 0 degrees — open
sky down to the true horizon, the behaviour before this change, now made explicit.

#### Scenario: No horizon means flat open sky

- **WHEN** a pier configures no horizon
- **THEN** the horizon altitude is 0 degrees at every azimuth

### Requirement: A pier has at most one horizon source

A pier SHALL NOT configure more than one horizon source (inline points, a flat floor, or
an imported file); doing so SHALL make the pier's configuration invalid, so a horizon
has exactly one source.

#### Scenario: Two sources at once are rejected

- **WHEN** a pier configures more than one horizon source (for example inline points together with an imported file, or inline points together with a flat floor)
- **THEN** the pier's configuration is reported as invalid

### Requirement: The horizon mask has no consumer in the verdict document

In this milestone the horizon mask SHALL have no consumer in the verdict document: it is
configuration and a query only. A verdict for a pier with a horizon configured SHALL be
byte-identical to the one for the same pier, instant and conditions with no horizon.
The `targets` list SHALL remain empty and no field, topic, or entity SHALL be added or
changed. This protects the frozen delivery contract until a later milestone gives the
horizon a consumer.

#### Scenario: A configured horizon leaves the verdict document unchanged

- **WHEN** two verdicts are produced for the same pier, instant, and conditions, one with a horizon configured and one without
- **THEN** the two verdict documents are byte-identical
- **AND** the `targets` list is empty in both

## REMOVED Requirements

### Requirement: Canonical horizon representation
**Reason**: It stated six behaviors in more than 500 characters. It is split into "A horizon is a set of azimuth and altitude samples", "Every horizon source gives the same samples", "The horizon interpolates round a closed ring of samples", "Sparse samples leave no direction open", "A one-sample horizon has one altitude everywhere" and "Horizon altitudes have a fixed precision". Its sentence on sub-precision noise moves to "A repeated azimuth in inline points keeps one altitude", the rule it governs. They keep all of its SHALL statements and its scenarios.
**Migration**: None. Nothing changes for users or code: the horizon behaves as before.

### Requirement: Inline points configuration
**Reason**: It stated six behaviors in more than 500 characters. It is split into "A pier may give inline points in any order", "Inline points lie within the azimuth and altitude ranges", "A repeated azimuth in inline points keeps one altitude", "Inline points hold at least one pair", "Inline points may be written as YAML text" and "Points text that gives no list is rejected". They keep all of its SHALL and MAY statements and its scenarios.
**Migration**: None. Nothing changes for users or code: inline points are read and checked as before.

### Requirement: NINA horizon import
**Reason**: It stated five behaviors in more than 500 characters. It is split into "A pier may import a NINA horizon export", "The NINA importer skips blank and comment lines", "The NINA importer tolerates a 360 azimuth and altitudes below 0", "Malformed NINA content makes the pier's configuration invalid" and "A relative horizon file path resolves against the configuration file". They keep all of its SHALL and MAY statements and its scenarios.
**Migration**: None. Nothing changes for users or code: NINA exports and horizon files load as before.

### Requirement: Flat floor and default open sky
**Reason**: It stated three behaviors in more than 500 characters. It is split into "A flat floor sets one altitude in every direction", "A pier with no horizon has flat open sky" and "A pier has at most one horizon source". They keep all of its SHALL and MAY statements and its scenarios.
**Migration**: None. Nothing changes for users or code: flat floors, open sky and the one-source rule behave as before.

### Requirement: The horizon does not change the verdict document
**Reason**: It was more than 500 characters. It is restated in fewer words as "The horizon mask has no consumer in the verdict document", which keeps all of its SHALL statements and its scenario. Its rule that `targets` stays empty is out of date: `target-ranking` and `tests/test_horizon_contract.py` show that the horizon now changes `targets`. Epic #230 changes no meaning, so the restated requirement keeps it, and the pull request reports the drift for a separate fix.
**Migration**: None. Nothing changes for users or code.
