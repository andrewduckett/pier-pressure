## MODIFIED Requirements

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

### Requirement: Targets are scored and ordered deterministically

The system SHALL score each gated target from 0 to 100 by combining these
factors: maximum altitude (higher is better), observable window length (longer is
better), moon separation (farther is better, and neutral when the moon is below
the horizon at the target's peak or unilluminated), transit timing (a transit
nearer the middle of the observable window is better), brightness (a brighter
object is better, judged by surface brightness where the catalog records it and by
integrated magnitude otherwise — and because surface brightness and integrated
magnitude are different physical scales, each SHALL be mapped through its own
anchors, never a single shared curve), and field-of-view fit (an object that
frames well in the pier's rig is better, judged by the object's size against the
**short edge** of the derived field of view: an object too small to see and one too
large to fit are both penalised, an object that fills a comfortable mid-size band
of the frame scores best, and an object larger than the field of view SHALL be
penalised progressively rather than dropped to zero at a hard cliff).

Each factor SHALL contribute only when its inputs are known for that target: the
four geometry factors always contribute; brightness contributes only when the
object has a known brightness; field-of-view fit contributes only when the pier
has a rig configured and the object has a known size. The factor weights SHALL be
renormalised over the contributing factors for each target, so a missing rig, an
unknown size, or an unknown brightness drops only its own factor rather than
substituting a guessed value, and the score stays within 0 to 100.

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

#### Scenario: A well-framed target ranks higher when a rig is configured

- **WHEN** the pier has a rig configured and two gated targets differ only in how well their size frames in that rig
- **THEN** the better-framed target has the higher score

#### Scenario: An oversize target is penalised progressively, not cliffed

- **WHEN** the pier has a rig configured and two gated targets are both larger than the field of view, differing only in that one is slightly larger and the other far larger
- **THEN** the slightly-larger target has the higher score
- **AND** the far-larger target is still ranked rather than dropped from the list for exceeding the field of view

#### Scenario: A missing field-of-view factor drops rather than guesses

- **WHEN** a gated target has no known size, or the pier has no rig configured
- **THEN** the field-of-view factor does not contribute to that target's score
- **AND** the score is the renormalised combination of the target's remaining factors, within 0 to 100

#### Scenario: A missing brightness factor drops rather than guesses

- **WHEN** a gated target has no known magnitude and no known surface brightness
- **THEN** the brightness factor does not contribute to that target's score
- **AND** the score is the renormalised combination of the target's remaining factors, within 0 to 100

#### Scenario: A target with neither brightness nor a framed size scores on geometry alone

- **WHEN** a gated target has no known brightness and (no known size or no rig configured)
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

#### Scenario: A rig change changes the ranking

- **WHEN** ranking runs for the same pier and evaluation instant, once with one rig and once with a different rig that frames the candidates differently
- **THEN** the two runs differ in target scores or ordering

## ADDED Requirements

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
