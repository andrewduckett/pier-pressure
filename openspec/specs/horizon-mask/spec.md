# horizon-mask Specification

## Purpose

The horizon-mask capability gives each pier a model of the terrain that blocks its
sky — trees, buildings, hills — as a canonical set of `(azimuth, altitude)` samples
with a query that answers how high the terrain rises in any direction, so a later
milestone can rank out targets that never clear it.

## Requirements

### Requirement: Canonical horizon representation

A pier's horizon SHALL be represented as an ordered set of `(azimuth, altitude)`
samples. Azimuth SHALL be measured from true north at 0 degrees, increasing clockwise
through east, and SHALL lie in the half-open range 0 to 360 degrees; a supplied value of
exactly 360 is the same direction as 0 and SHALL be normalized to 0. Altitude SHALL be
the angle the terrain rises to above the true horizon, in degrees, in the range 0 to 90.
Every source of a horizon (inline configuration, a flat floor, or an imported file)
SHALL produce this same representation, so downstream behaviour does not depend on where
a horizon came from.

The samples define the horizon for the **entire** circle, not a partial overlay. The
horizon SHALL return an altitude for every azimuth by linear interpolation between the
two adjacent samples, and the samples SHALL be treated as a closed ring so the segment
from the greatest sampled azimuth back to the least is interpolated across the 360/0
boundary like any other segment. It follows that a sparse sample set does **not** leave
the unmentioned directions open: those directions interpolate between the nearest sample
on each side. To model a localized obstruction with open sky around it, the
configuration SHALL include low (for example 0-degree) anchor samples bounding the
obstruction.

A horizon of a single sample — including the flat-floor and default-open-sky cases —
SHALL return that one altitude at every azimuth, with no interpolation, so the
one-sample case is well defined rather than a degenerate division by a zero azimuth
span.

Altitudes SHALL be handled at a fixed, defined decimal precision: each sample's altitude
SHALL be rounded to that precision when the horizon is constructed, and the altitude a
query returns SHALL be rounded to it in the query itself. So the same samples and the
same azimuth yield the same altitude — and therefore the same above/below classification
at a grazing boundary — on repeated runs and across platforms, consistent with the
core's determinism guarantee. Because sample altitudes are rounded at construction, the
duplicate-azimuth rule below compares rounded altitudes, so two samples that differ only
by sub-precision floating-point noise are treated as equal.

#### Scenario: A sampled azimuth returns its own altitude

- **WHEN** the horizon is queried at an azimuth that equals one of its samples
- **THEN** the returned altitude equals that sample's altitude

#### Scenario: Altitude between samples is linearly interpolated

- **WHEN** the horizon is queried at an azimuth that lies between two adjacent samples
- **THEN** the returned altitude is the linear interpolation of those two samples' altitudes by azimuth

#### Scenario: Interpolation wraps across the 360/0 boundary

- **WHEN** the horizon is queried at an azimuth in the arc between the greatest sampled azimuth and the least (crossing 360/0)
- **THEN** the returned altitude is the linear interpolation of those two samples across the wrap, not a flat or undefined value

#### Scenario: A single-sample horizon is flat

- **WHEN** a horizon has exactly one sample (or is a flat floor, or is the default open sky) and is queried at any azimuth
- **THEN** the returned altitude is that single altitude, with no interpolation

#### Scenario: Sparse samples interpolate rather than leaving open gaps

- **WHEN** a horizon is configured with only the samples `[170, 40]` and `[190, 40]` and is queried at azimuth 0
- **THEN** the returned altitude is 40, because the wrap segment interpolates across north between the two samples
- **AND** modelling open sky north of that obstruction therefore requires low anchor samples bounding it

#### Scenario: The queried altitude is deterministic to a fixed precision

- **WHEN** the same horizon is queried at the same azimuth on repeated runs
- **THEN** the returned altitude is identical, rounded to the defined precision

### Requirement: Terrain-clearance query

The horizon SHALL answer, for any azimuth, the terrain altitude in that direction, and
SHALL classify a point at a given `(azimuth, altitude)` as above the horizon (visible)
or below it (blocked). A point SHALL be considered above the horizon when its altitude
is greater than or equal to the horizon altitude in its direction, so the boundary is
pinned and a grazing target is treated as visible rather than ambiguously excluded.

#### Scenario: A point higher than the terrain is visible

- **WHEN** a point's altitude is greater than the horizon altitude in its direction
- **THEN** the point is classified as above the horizon

#### Scenario: A point lower than the terrain is blocked

- **WHEN** a point's altitude is less than the horizon altitude in its direction
- **THEN** the point is classified as below the horizon

#### Scenario: A point exactly on the terrain is visible

- **WHEN** a point's altitude equals the horizon altitude in its direction
- **THEN** the point is classified as above the horizon

### Requirement: Inline points configuration

A pier MAY configure its horizon as an inline list of `[azimuth, altitude]` pairs. The
pairs need not be given in azimuth order; the system SHALL order them. Each azimuth
SHALL lie in 0 to 360 degrees (360 normalized to 0, per the representation requirement)
and each altitude in 0 to 90 degrees; a pair outside these ranges SHALL make the pier's
configuration invalid. Two pairs at the same azimuth (including one produced by
normalizing 360 to 0) SHALL be deduplicated when their rounded altitudes are equal, and
SHALL make the configuration invalid when their rounded altitudes differ, because a
single direction cannot rise to two altitudes. At least one pair SHALL be given.

#### Scenario: Unordered pairs are accepted and ordered

- **WHEN** a pier configures inline points whose pairs are not in azimuth order
- **THEN** the resulting horizon behaves as if the pairs were ordered by azimuth

#### Scenario: An out-of-range pair is rejected

- **WHEN** a pier configures an inline pair with an azimuth outside 0 to 360 or an altitude outside 0 to 90
- **THEN** the pier's configuration is reported as invalid

#### Scenario: A duplicate azimuth is rejected

- **WHEN** a pier configures two inline pairs with the same azimuth
- **THEN** the pier's configuration is reported as invalid

### Requirement: Flat floor and default open sky

A pier MAY configure a single flat altitude floor instead of terrain samples: the
horizon altitude SHALL then equal that floor in every direction, in the range 0 to 90
degrees. When a pier configures no horizon at all, its horizon SHALL be flat at 0
degrees — open sky down to the true horizon, the behaviour before this change, now
made explicit. A pier SHALL NOT configure more than one horizon source (inline points, a
flat floor, or an imported file); doing so SHALL make the pier's configuration invalid,
so a horizon has exactly one source.

#### Scenario: A flat floor applies in every direction

- **WHEN** a pier configures a flat altitude floor and the horizon is queried at any azimuth
- **THEN** the returned altitude equals that floor

#### Scenario: No horizon means flat open sky

- **WHEN** a pier configures no horizon
- **THEN** the horizon altitude is 0 degrees at every azimuth

#### Scenario: Two sources at once are rejected

- **WHEN** a pier configures more than one horizon source (for example inline points together with an imported file, or inline points together with a flat floor)
- **THEN** the pier's configuration is reported as invalid

### Requirement: NINA horizon import

A pier MAY reference a NINA `.hrz` horizon export as its horizon source. The system SHALL
parse the export's whitespace-separated `azimuth altitude` pair-per-line text into the
canonical representation, applying the same ordering and duplicate rules as inline
points. Blank lines and comment lines — lines whose first non-whitespace character is
`#` — SHALL be ignored (the exact token is confirmed against the committed fixture). Because real exports close the
polygon and carry sub-horizon terrain, the importer SHALL tolerate two file-specific
quirks rather than reject the file: an azimuth of exactly 360 SHALL be normalized to 0
(and deduplicated against an existing 0 per the inline-points rule), and an altitude
below 0 — terrain below the true horizontal, which cannot block an observable target —
SHALL be clamped to 0. Malformed content — a line that is neither blank, a comment, nor
a parseable pair — SHALL make the pier's configuration invalid rather than crash the
load.

A relative file reference (for any file-based format) SHALL be resolved against the
directory of the configuration file, not the process working directory, so a horizon
file placed beside `config.yaml` is found regardless of where the service is launched
from.

#### Scenario: A valid export imports to the equivalent horizon

- **WHEN** a pier imports a NINA `.hrz` export whose pairs match a set of inline points
- **THEN** the resulting horizon answers queries identically to that inline-points horizon

#### Scenario: Blank and comment lines are ignored

- **WHEN** a NINA `.hrz` export contains blank lines and comment lines among its pairs
- **THEN** those lines are ignored and the remaining pairs form the horizon

#### Scenario: A malformed export invalidates only its pier

- **WHEN** a pier references a NINA `.hrz` export containing an unparseable line
- **THEN** that pier's configuration is reported as invalid
- **AND** other piers still produce verdicts

#### Scenario: A polygon-closing 360 entry and sub-horizon altitude are tolerated

- **WHEN** a pier imports a NINA `.hrz` export whose pairs include an azimuth of exactly 360 and an altitude below 0
- **THEN** the 360 entry is normalized to 0 (deduplicated against any existing 0) and the sub-horizon altitude is clamped to 0
- **AND** the pier's configuration is valid

#### Scenario: A relative file reference resolves against the config file

- **WHEN** a configuration references a horizon file by a relative path and the service is launched from an unrelated working directory
- **THEN** the file is resolved relative to the configuration file's own directory and loaded

### Requirement: Unsupported formats fail clearly

Stellarium and Telescopius SHALL be recognised horizon format names but SHALL NOT be
supported in this milestone. Configuring a pier with one of them SHALL report a clear
"format not yet supported" configuration error for that pier, rather than silently
falling back to open sky or attempting a wrong parse, so an unimplemented importer can
never yield a silently wrong horizon.

#### Scenario: A recognised-but-unsupported format is a clear error

- **WHEN** a pier configures its horizon source as Stellarium or Telescopius
- **THEN** the pier's configuration is reported as invalid with a message that the format is not yet supported

### Requirement: The horizon does not change the verdict document

In this milestone the horizon mask SHALL have no consumer in the verdict document: it is
configuration and a query only. Producing a verdict for a pier that has a horizon
configured SHALL yield a document byte-identical to the one produced for the same pier,
instant, and conditions with no horizon configured. The `targets` list SHALL remain
empty and no field, topic, or entity SHALL be added or changed. This protects the frozen
delivery contract until a later milestone gives the horizon a consumer.

#### Scenario: A configured horizon leaves the verdict document unchanged

- **WHEN** two verdicts are produced for the same pier, instant, and conditions, one with a horizon configured and one without
- **THEN** the two verdict documents are byte-identical
- **AND** the `targets` list is empty in both
