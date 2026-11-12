## MODIFIED Requirements

### Requirement: A target must clear the horizon mask for the minimum duration

A candidate SHALL appear in the ranked list only when its remaining window
spans at least a configured minimum duration. Otherwise it SHALL be absent from
the list rather than listed with a low score. This covers a candidate that never
rises above the horizon mask within the scored window, and one that is above it
for less than the minimum duration.

#### Scenario: An object that never clears the mask is absent

- **WHEN** a candidate stays below the pier's horizon mask throughout the dark window
- **THEN** it does not appear in the target list

#### Scenario: A briefly observable object is absent

- **WHEN** a candidate is above the mask within the dark window for less than the minimum duration
- **THEN** it does not appear in the target list

#### Scenario: A target that has set is absent mid-session

- **WHEN** a verdict is produced two hours after `dark_window.start`, and a candidate's only stretch above the mask ended before `generated_at`
- **THEN** it does not appear in the target list

#### Scenario: A target with under the minimum left is absent mid-session

- **WHEN** a verdict is produced inside the dark window, and a candidate is above the mask from `generated_at` until 30 minutes later, then below it until `dark_window.end`
- **THEN** it does not appear in the target list

#### Scenario: The last hour of the night has no targets

- **WHEN** a verdict is produced 30 minutes before `dark_window.end`
- **THEN** the target list is empty

## ADDED Requirements

### Requirement: A target is ranked on its remaining window

A target's **remaining window** SHALL be its longest stretch above the pier's
horizon mask within the scored window. When two stretches are equally long, the
earlier SHALL be used. Once the night has started, the remaining window can be
a different stretch from the target's `window`.

#### Scenario: A target with a second stretch ahead is ranked on it

- **WHEN** a verdict is produced at 22:00, a candidate is above the mask from 20:00 to 21:30 and from 23:00 to 01:00, and the dark window runs from 19:45 to 05:00
- **THEN** the candidate appears in the target list
- **AND** its `window` runs from 20:00 to 21:30
- **AND** its `remaining_window` runs from 23:00 to 01:00

### Requirement: Before astronomical dusk, the remaining window is the observable window

Before astronomical dusk, a target's remaining window SHALL equal its
observable window, so the target list is the same as a whole-night ranking.

#### Scenario: Before dusk, the remaining window equals the window

- **WHEN** a verdict is produced at an evaluation instant before `dark_window.start`
- **THEN** each target's `remaining_window` equals its `window`

#### Scenario: Before dusk, the ranking is unchanged

- **WHEN** two verdicts are produced for the same pier and night, at two different evaluation instants before `dark_window.start`
- **THEN** their target lists are identical

### Requirement: The geometry factors judge the remaining window

The four geometry factors SHALL be measured over the target's remaining window:

- maximum altitude and moon separation at the target's peak within it;
- remaining window length as a share of the scored window;
- transit timing against it.

Brightness and field-of-view fit SHALL NOT depend on the evaluation instant.

#### Scenario: A target past its peak is scored on the altitude still ahead

- **WHEN** a verdict is produced mid-session for a target that peaked at 70° before `generated_at` and reaches at most 40° in its remaining window
- **THEN** its altitude factor is the factor for 40°, not for 70°

#### Scenario: A transit that has passed scores no transit timing

- **WHEN** a verdict is produced mid-session for a target that crossed the meridian before `generated_at`
- **THEN** its transit timing factor is 0

#### Scenario: A target up for the rest of the night has a full window factor

- **WHEN** a verdict is produced mid-session for a target that stays above the mask from `generated_at` to `dark_window.end`
- **THEN** its window length factor is 1

### Requirement: Each target carries its remaining window

Each target SHALL carry a `remaining_window` with a `start` and an `end`: the
remaining window it was ranked on. Its times SHALL be UTC at whole-second
precision and SHALL lie within the scored window. The target's `window`,
`max_altitude`, `transit_time` and `moon_separation` SHALL keep their
whole-night meaning.

#### Scenario: Mid-session, a target already up starts its remaining window now

- **WHEN** a verdict is produced inside the dark window for a target that is above the mask at `generated_at` and stays above it until its `window.end`
- **THEN** its `remaining_window.start` equals `generated_at`
- **AND** its `remaining_window.end` equals its `window.end`
- **AND** its `window.start` is earlier than `generated_at`

#### Scenario: Every remaining window spans the minimum duration

- **WHEN** the target list is produced, before or after dusk
- **THEN** each target's `remaining_window` spans at least the minimum duration

### Requirement: A recompute in the same night matches a fresh ranking

A ranking produced after an earlier ranking of the same pier and night SHALL be
identical to a ranking produced at the same evaluation instant with no earlier
ranking.

#### Scenario: A later recompute matches a fresh ranking

- **WHEN** ranking runs for a pier at 21:00 and again at 23:00 in the same night, and separately runs at 23:00 with no earlier ranking
- **THEN** the two 23:00 target lists are byte-identical
