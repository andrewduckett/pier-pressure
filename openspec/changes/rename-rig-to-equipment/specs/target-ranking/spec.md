## MODIFIED Requirements

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
frames well in the pier's equipment is better, judged by the object's size against the
**short edge** of the derived field of view: an object too small to see and one too
large to fit are both penalised, an object that fills a comfortable mid-size band
of the frame scores best, and an object larger than the field of view SHALL be
penalised progressively rather than dropped to zero at a hard cliff).

Each factor SHALL contribute only when its inputs are known for that target: the
four geometry factors always contribute; brightness contributes only when the
object has a known brightness; field-of-view fit contributes only when the pier
has equipment configured and the object has a known size. The factor weights SHALL be
renormalised over the contributing factors for each target, so missing equipment, an
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

#### Scenario: A rig change changes the ranking

- **WHEN** ranking runs for the same pier and evaluation instant, once with one set of equipment and once with different equipment that frames the candidates differently
- **THEN** the two runs differ in target scores or ordering
