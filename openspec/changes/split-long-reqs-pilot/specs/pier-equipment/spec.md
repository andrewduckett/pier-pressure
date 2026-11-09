## ADDED Requirements

### Requirement: Equipment is described under the `equipment` key

Each pier MAY carry a description of its imaging equipment: one telescope and
one camera. The pier's configuration SHALL give the equipment under the key
`equipment`. The equipment SHALL provide:

- a telescope focal length in millimetres
- a camera sensor width and height in millimetres
- optionally, a focal reducer or barlow factor (default 1.0)

#### Scenario: Equipment is described by optics, not a pre-computed field of view

- **WHEN** a pier configures equipment
- **THEN** the equipment is given as a focal length, a sensor width, and a sensor height, with an optional reducer factor
- **AND** the configuration does not require the field of view to be supplied directly

#### Scenario: Equipment is configured under the `equipment` key

- **WHEN** a pier's configuration gives its focal length and sensor size under the key `equipment`
- **THEN** the configuration loads and the pier ranks targets with a field-of-view term

#### Scenario: The `rig` key is not accepted

- **WHEN** a pier's configuration gives its focal length and sensor size under the key `rig`
- **THEN** that pier is skipped with a logged configuration error, as for any other unknown key
- **AND** no verdict is produced for that pier, while the other valid piers still produce verdicts

### Requirement: A pier without equipment still produces a verdict

Equipment SHALL be optional. A pier with no equipment configured SHALL still
produce a verdict and a ranked target list, without a field-of-view term. Apart
from the `equipment` key itself, equipment SHALL NOT change any other
configuration field or its meaning.

#### Scenario: A pier without equipment still ranks targets

- **WHEN** a verdict is produced for a pier that has no equipment configured
- **THEN** the verdict and its ranked target list are produced without error
- **AND** no field-of-view term contributes to any target's score

### Requirement: Every equipment value is strictly positive

The focal length, both sensor dimensions, and the reducer factor SHALL each be
strictly positive. Equipment with a zero or negative value in any of these SHALL
make the pier's configuration invalid. The system SHALL report this as a
configuration error and produce no verdict for that pier, as it does for other
invalid pier fields. This keeps the derived field of view well defined, so the
derivation never divides by zero.

#### Scenario: Equipment with a non-positive value is rejected

- **WHEN** a pier configures equipment whose focal length, a sensor dimension, or reducer is zero or negative
- **THEN** loading that configuration fails with a configuration error
- **AND** no verdict is produced for that pier

## REMOVED Requirements

### Requirement: Equipment is optional on each pier

**Reason**: It stated three behaviors in more than 500 characters. It is split into "Equipment is described under the `equipment` key", "A pier without equipment still produces a verdict" and "Every equipment value is strictly positive", which keep all of its SHALL statements and all five of its scenarios.
**Migration**: None. Nothing changes for users or code: the configuration, its validation and the verdict behave as before.
