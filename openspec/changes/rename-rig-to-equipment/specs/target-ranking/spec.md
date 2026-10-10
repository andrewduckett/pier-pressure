## MODIFIED Requirements

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

## ADDED Requirements

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
