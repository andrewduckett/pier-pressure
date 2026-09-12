## Purpose

Target ranking decides what to point at from a pier tonight. It loads a pinned
deep-sky object catalog, keeps the objects worth imaging, and ranks the ones that
clear the pier's horizon during astronomical night, so the verdict document can
name the best few.

## ADDED Requirements

### Requirement: Catalog is loaded from a pinned offline source

The system SHALL load its deep-sky object catalog from data bundled with the
application, with no runtime network access. The catalog SHALL be version-pinned
so the same application version always reads the same objects and coordinates.
Each catalog object SHALL provide a designation, an object type, and J2000
equatorial coordinates; a common name, magnitude, and size are provided when the
source records them.

#### Scenario: Catalog loads without network access

- **WHEN** target ranking runs with no network available
- **THEN** the catalog loads from the bundled data and ranking proceeds

#### Scenario: Same version reads the same catalog

- **WHEN** the catalog is loaded twice from the same application version
- **THEN** the set of objects and their coordinates are identical

### Requirement: Catalog is filtered to observable objects

The system SHALL restrict ranking candidates to observable deep-sky object types
— galaxies, nebulae, and clusters — and SHALL exclude stars, duplicate entries,
and non-existent entries. The system SHALL exclude objects whose recorded
magnitude is fainter than a configured magnitude limit. An object with no
recorded magnitude SHALL be kept as a candidate, so real objects are not dropped
for missing data.

#### Scenario: Non-observable entries are excluded

- **WHEN** the catalog contains stars, duplicate entries, and non-existent entries
- **THEN** none of them appear as ranking candidates

#### Scenario: Faint objects are excluded but unknown magnitudes are kept

- **WHEN** an object is fainter than the configured magnitude limit
- **THEN** it is excluded from candidates
- **AND** an object with no recorded magnitude is kept as a candidate

### Requirement: Targets are gated before ranking

A candidate SHALL appear in the ranked list only when it clears the pier's
horizon mask during astronomical night for at least a configured minimum
duration. A candidate that never rises above the horizon mask within the dark
window, or is observable for less than the minimum duration, SHALL be absent from
the list rather than listed with a low score. Every target that does appear in the
list SHALL have an observable window of at least the minimum duration, measured
from its emitted window. When the selected night has no dark window, the target
list SHALL be empty.

#### Scenario: An object that never clears the mask is absent

- **WHEN** a candidate stays below the pier's horizon mask throughout the dark window
- **THEN** it does not appear in the target list

#### Scenario: A briefly observable object is absent

- **WHEN** a candidate is above the mask within the dark window for less than the minimum duration
- **THEN** it does not appear in the target list

#### Scenario: No dark window yields no targets

- **WHEN** the selected night has no astronomical-night window
- **THEN** the target list is empty

#### Scenario: Every emitted target meets the minimum duration

- **WHEN** the target list is produced
- **THEN** each target's emitted observable window spans at least the minimum duration

### Requirement: Each target carries its computed observing geometry

For each target in the list, the system SHALL compute, against the selected
night and the pier's horizon mask: the observable window (start and end, within
astronomical night and above the mask), the maximum altitude reached during that
window, the meridian transit time, and the angular separation from the moon at
the instant of maximum altitude within the window. The observable window SHALL be
bounded by the dark window: when a target is above the mask at astronomical dusk
or dawn — including a circumpolar target above the mask all night — its window
SHALL be clamped to the dusk or dawn boundary rather than left open. The
`transit_time` SHALL be the meridian crossing for that day and MAY fall outside
the observable window (for example, a daytime transit for a circumpolar target).
Times SHALL be UTC at whole-second precision, consistent with the rest of the
verdict document.

#### Scenario: Geometry fields are present and consistent

- **WHEN** a target appears in the list
- **THEN** it carries an observable window, a maximum altitude, a transit time, and a moon separation
- **AND** the observable window lies within the dark window
- **AND** the maximum altitude is at or above the pier's horizon mask in the target's direction

#### Scenario: A target above the mask all night has a clamped window

- **WHEN** a target stays above the pier's horizon mask throughout astronomical night
- **THEN** its observable window is clamped to the dusk and dawn boundaries
- **AND** ranking completes without error for that target

### Requirement: Targets are scored and ordered deterministically

The system SHALL score each gated target from 0 to 100 by combining four factors:
maximum altitude (higher is better), observable window length (longer is better),
moon separation (farther is better, and neutral when the moon is below the horizon
at the target's peak or unilluminated), and transit timing (a transit nearer the
middle of the observable window is better). The list SHALL be ordered by score,
highest first, with ties broken by the object designation so ordering is stable.
The list SHALL contain at most the top 10 targets. The same pier and evaluation
instant SHALL always yield a byte-identical target list.

#### Scenario: Higher-quality targets rank first

- **WHEN** two gated targets differ only in maximum altitude
- **THEN** the higher-altitude target has the higher score and sorts first

#### Scenario: The list is bounded and stably ordered

- **WHEN** more than 10 targets pass the gates
- **THEN** the list contains exactly the 10 highest-scoring targets
- **AND** targets with equal scores are ordered by designation

#### Scenario: Ranking is deterministic

- **WHEN** ranking runs twice for the same pier and evaluation instant
- **THEN** the two target lists are byte-identical
