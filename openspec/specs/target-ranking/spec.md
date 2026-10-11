# target-ranking Specification

## Purpose

Target ranking decides what to point at from a pier tonight. It loads a pinned
deep-sky object catalog, keeps the objects worth imaging, and ranks the ones that
clear the pier's horizon during astronomical night, so the verdict document can
name the best few.

## Requirements

### Requirement: Catalog is loaded from a pinned offline source

The system SHALL load its deep-sky object catalog from data bundled with the
application, with no runtime network access. The catalog SHALL be version-pinned
so the same application version always reads the same objects and coordinates.
Each catalog object SHALL provide a designation, an object type, and J2000
equatorial coordinates; a common name, magnitude, surface brightness, and size
are provided when the source records them.

#### Scenario: Catalog loads without network access

- **WHEN** target ranking runs with no network available
- **THEN** the catalog loads from the bundled data and ranking proceeds

#### Scenario: Same version reads the same catalog

- **WHEN** the catalog is loaded twice from the same application version
- **THEN** the set of objects and their coordinates are identical

#### Scenario: Recorded surface brightness and size are available

- **WHEN** the source records a surface brightness and a size for an object
- **THEN** both are available to ranking
- **AND** an object for which the source records neither is still loaded, with those values absent

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

The system SHALL score each gated target from 0 to 100 by combining six factors.
The four geometry factors are:

- **Maximum altitude:** higher is better.
- **Observable window length:** longer is better.
- **Moon separation:** farther is better. This factor SHALL be neutral when the
  moon is below the horizon at the target's peak, or is unilluminated.
- **Transit timing:** a transit nearer the middle of the observable window is
  better.

The two suitability factors are:

- **Brightness:** a brighter object is better. The system SHALL judge it by
  surface brightness where the catalog records one, and by integrated magnitude
  otherwise. Surface brightness and integrated magnitude are different physical
  scales, so each SHALL be mapped through its own anchors, never one shared curve.
- **Field-of-view fit:** an object that frames well in the pier's equipment is
  better. The system SHALL judge it by the object's size against the **short
  edge** of the derived field of view. An object too small to see and an object
  too large to fit SHALL both be penalised. An object that fills a comfortable
  mid-size band of the frame SHALL score best. An object larger than the field of
  view SHALL be penalised progressively, not dropped to zero at a hard cliff.

Each factor SHALL contribute only when its inputs are known for that target:

- The four geometry factors always contribute.
- Brightness contributes only when the object has a known brightness.
- Field-of-view fit contributes only when the pier has equipment configured and
  the object has a known size.

The system SHALL renormalise the factor weights over the contributing factors
for each target. Missing equipment, an unknown size, or an unknown brightness
then drops only its own factor, instead of substituting a guessed value. The
score stays within 0 to 100.

The list SHALL be ordered by score, highest first, with ties broken by the object
designation so ordering is stable. The list SHALL contain at most the top 10
targets. The same pier and evaluation instant SHALL always yield a byte-identical
target list.

#### Scenario: Higher-quality targets rank first

- **WHEN** two gated targets differ only in maximum altitude
- **THEN** the higher-altitude target has the higher score and sorts first

#### Scenario: A brighter target ranks higher, all else equal

- **WHEN** two gated targets are identical except that one is brighter
- **THEN** the brighter target has the higher score

#### Scenario: A well-framed target ranks higher when equipment is configured

- **WHEN** the pier has equipment configured and two gated targets differ only in how well their size frames in that equipment
- **THEN** the better-framed target has the higher score

#### Scenario: An oversize target is penalised progressively, not cliffed

- **WHEN** the pier has equipment configured and two gated targets are both larger than the field of view, differing only in that one is slightly larger and the other far larger
- **THEN** the slightly-larger target has the higher score
- **AND** the far-larger target is still ranked rather than dropped from the list for exceeding the field of view

#### Scenario: A missing field-of-view factor drops rather than guesses

- **WHEN** a gated target has no known size, or the pier has no equipment configured
- **THEN** the field-of-view factor does not contribute to that target's score
- **AND** the score is the renormalised combination of the target's remaining factors, within 0 to 100

#### Scenario: A missing brightness factor drops rather than guesses

- **WHEN** a gated target has no known magnitude and no known surface brightness
- **THEN** the brightness factor does not contribute to that target's score
- **AND** the score is the renormalised combination of the target's remaining factors, within 0 to 100

#### Scenario: A target with neither brightness nor a framed size scores on geometry alone

- **WHEN** a gated target has no known brightness and (no known size or no equipment configured)
- **THEN** neither the brightness nor the field-of-view factor contributes to that target's score
- **AND** the score is the renormalised combination of the four geometry factors, within 0 to 100

#### Scenario: A geometry-only target can still reach the top of the range

- **WHEN** a gated target is scored on the four geometry factors alone and each of those factors is ideal
- **THEN** its score can still reach 100
- **AND** dropping the missing factors does not compress its score below the full 0 to 100 range

#### Scenario: The list is bounded and stably ordered

- **WHEN** more than 10 targets pass the gates
- **THEN** the list contains exactly the 10 highest-scoring targets
- **AND** targets with equal scores are ordered by designation

#### Scenario: Ranking is deterministic

- **WHEN** ranking runs twice for the same pier and evaluation instant
- **THEN** the two target lists are byte-identical

#### Scenario: An equipment change changes the ranking

- **WHEN** ranking runs for the same pier and evaluation instant, once with one set of equipment and once with different equipment that frames the candidates differently
- **THEN** the two runs differ in target scores or ordering

### Requirement: Each target carries its size and brightness

For each target in the list, the system SHALL carry the object's angular size, its
integrated magnitude, and its surface brightness as recorded in the catalog, each
null (present, not omitted) when the catalog records no value. These are the raw
catalog facts, carried so downstream consumers see the same numbers the ranking
judged. The carried `magnitude` is the catalog's existing visual-then-blue
magnitude — the same value used as the candidate filter — and is distinct from the
brightness the ranking factor consumes internally (surface brightness where
recorded, else that magnitude); the ranking's internal choice SHALL NOT change any
carried value.

#### Scenario: Recorded size and brightness are carried on the target

- **WHEN** a target appears in the list and the catalog records its size and brightness
- **THEN** the target carries the object's angular size, integrated magnitude, and surface brightness

#### Scenario: Missing catalog values are null on the target

- **WHEN** a target appears in the list and the catalog records no size or no brightness for it
- **THEN** the corresponding value is null (present, not omitted) on the target rather than guessed

### Requirement: The verdict says how the top pick frames

When the pier has equipment, the system SHALL add one framing sentence about the
top pick to the verdict's `reasons[]`. It SHALL add the sentence only when all of
these hold:

- The verdict passes its gates, so it has a score.
- The target list is not empty.
- The pier has equipment configured.
- The top pick is a catalog object with a known size.

The sentence SHALL be the first of these that applies, where `<name>` is the
target's name, or its designation when it has no name:

1. "Top pick `<name>` frames well in your field of view." The object frames well
   by the same field-of-view fit the ranking uses.
2. "Top pick `<name>` is larger than your field of view." The object's size
   exceeds the short edge of the field of view.
3. "Top pick `<name>` is small in your field of view." The object's size is at or
   below the lower edge of the band that scores best.
4. "Top pick `<name>` fills most of your field of view." None of the above
   applies.

The framing sentence SHALL follow the verdict's gate and score terms. Adding it
SHALL NOT change any other reason.

#### Scenario: A well-framed top pick gets the exact framing sentence

- **WHEN** a gate-passing verdict is produced for a pier with equipment, and the top pick NGC0224 (catalog name "Andromeda Galaxy") frames well in that equipment
- **THEN** `reasons[]` contains exactly "Top pick Andromeda Galaxy frames well in your field of view."

#### Scenario: A small top pick gets the small sentence

- **WHEN** a gate-passing verdict's top pick, Andromeda Galaxy, is at or below the lower edge of the best-scoring band in the pier's field of view, and does not frame well
- **THEN** `reasons[]` contains exactly "Top pick Andromeda Galaxy is small in your field of view."

#### Scenario: A top pick that nearly fills the frame gets the fills-most sentence

- **WHEN** a gate-passing verdict's top pick, Andromeda Galaxy, nearly fills the pier's field of view without exceeding it, and does not frame well
- **THEN** `reasons[]` contains exactly "Top pick Andromeda Galaxy fills most of your field of view."

#### Scenario: An oversize top pick gets the larger-than sentence

- **WHEN** a gate-passing verdict's top pick, Andromeda Galaxy, is larger than the short edge of the pier's field of view, and does not frame well
- **THEN** `reasons[]` contains exactly "Top pick Andromeda Galaxy is larger than your field of view."

#### Scenario: A pier without equipment gets no framing sentence

- **WHEN** a verdict is produced for a pier with no equipment configured
- **THEN** `reasons[]` contains no framing sentence

#### Scenario: A NO-GO verdict gets no framing sentence

- **WHEN** a verdict fails a gate, so its score is null, and targets are still ranked for the night
- **THEN** `reasons[]` contains no sentence that starts "Top pick"
