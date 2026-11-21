## MODIFIED Requirements

### Requirement: The verdict gets one framing sentence about the top pick

The system SHALL add one framing sentence about the top pick to the verdict's
`reasons[]`, naming the top pick by its name, else by its designation. It SHALL
add the sentence only when all of these hold:

- The verdict passes its gates, so it has a score.
- The target list is not empty.
- The scored window is at least one hour long (`MIN_USABLE_WINDOW`).
- The pier has equipment configured.
- The top pick is a catalog object with a known size.

The framing sentence SHALL follow the verdict's gate and score terms. Adding it
SHALL NOT change any other reason.

#### Scenario: A pier without equipment gets no framing sentence

- **WHEN** a verdict is produced for a pier with no equipment configured
- **THEN** `reasons[]` contains no framing sentence

#### Scenario: A NO-GO verdict gets no framing sentence

- **WHEN** a verdict fails a gate, so its score is null, and targets are still ranked for the night
- **THEN** `reasons[]` contains no sentence that starts "Top pick"

#### Scenario: A scored window under one hour gets no top-pick sentence

- **WHEN** a gate-passing verdict is produced for a pier with equipment thirty minutes before astronomical dawn, so its scored window is under one hour
- **THEN** `reasons[]` contains no sentence that starts "Top pick"

## ADDED Requirements

### Requirement: A bright top pick gets the bright-target sentence

The system SHALL add "Top pick `<name>` is a bright target." to `reasons[]`,
naming the top pick by its name, else its designation, with or without
equipment, only when all of these hold:

- The verdict passes its gates and has at least one target.
- The scored window lasts at least one hour.
- The top pick is a catalog object that the ranking's own brightness judgment
  counts as bright.

It SHALL come straight after the framing sentence when both appear. It SHALL NOT
change any other reason.

#### Scenario: A bright top pick on a pier without equipment gets only the bright-target sentence

- **WHEN** a gate-passing verdict's top pick is Mel022 (catalog name "Pleiades") and the pier has no equipment configured
- **THEN** the only sentence in `reasons[]` that starts "Top pick" is exactly "Top pick Pleiades is a bright target."

#### Scenario: A bright top pick on a pier with equipment gets the framing sentence, then the bright-target sentence

- **WHEN** a gate-passing verdict's top pick is Pleiades and the pier has equipment configured
- **THEN** `reasons[]` holds the framing sentence for Pleiades, followed straight after by "Top pick Pleiades is a bright target."

#### Scenario: A faint top pick gets no bright-target sentence

- **WHEN** a gate-passing verdict's top pick is NGC0224 (catalog name "Andromeda Galaxy"), whose surface brightness does not count as bright
- **THEN** `reasons[]` contains no sentence that ends "is a bright target."
