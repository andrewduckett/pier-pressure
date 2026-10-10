## REMOVED Requirements

### Requirement: Equipment is an optional per-pier imaging rig

**Reason**: The entity is renamed from "rig" to "equipment". OpenSpec cannot rename
a scenario, so this requirement is removed and added back as "Equipment is
optional on each pier", with the same behavior and the config key named.
**Migration**: Rename the per-pier config key `rig:` to `equipment:`. The fields
inside it do not change.

### Requirement: Field of view is derived offline from the rig

**Reason**: The entity is renamed from "rig" to "equipment". This requirement is
added back unchanged in meaning as "Field of view is derived offline from the
equipment".
**Migration**: None. The field of view is derived the same way.

## ADDED Requirements

### Requirement: Equipment is optional on each pier

Each pier MAY carry a description of its imaging equipment: one telescope and
one camera. The pier's configuration SHALL give the equipment under the key
`equipment`. When present, the equipment SHALL provide a telescope focal length
in millimetres, a camera sensor width and height in millimetres, and MAY provide
a focal reducer or barlow factor (default 1.0). Equipment SHALL be optional: a
pier with no equipment configured SHALL still produce a verdict and a ranked
target list, without a field-of-view term. Equipment SHALL NOT change any
existing configuration field or its meaning.

The focal length, both sensor dimensions, and the reducer factor SHALL each be
strictly positive. Equipment with a zero or negative value in any of these SHALL
make the pier's configuration invalid. The system SHALL report this as a
configuration error and produce no verdict, as it does for other invalid pier
fields. This keeps the derived field of view well defined, so the derivation
never divides by zero.

#### Scenario: A pier without equipment still ranks targets

- **WHEN** a verdict is produced for a pier that has no equipment configured
- **THEN** the verdict and its ranked target list are produced without error
- **AND** no field-of-view term contributes to any target's score

#### Scenario: Equipment with a non-positive value is rejected

- **WHEN** a pier configures equipment whose focal length, a sensor dimension, or reducer is zero or negative
- **THEN** loading that configuration fails with a configuration error
- **AND** no verdict is produced for that pier

#### Scenario: Equipment is described by optics, not a pre-computed field of view

- **WHEN** a pier configures equipment
- **THEN** the equipment is given as a focal length, a sensor width, and a sensor height, with an optional reducer factor
- **AND** the configuration does not require the field of view to be supplied directly

#### Scenario: Equipment is configured under the `equipment` key

- **WHEN** a pier's configuration gives its focal length and sensor size under the key `equipment`
- **THEN** the configuration loads and the pier ranks targets with a field-of-view term

#### Scenario: The `rig` key is not accepted

- **WHEN** a pier's configuration gives its focal length and sensor size under the key `rig`
- **THEN** loading that configuration fails with the same configuration error as any other unknown key

### Requirement: Field of view is derived offline from the equipment

The system SHALL derive the equipment's field of view from its optics, with no
runtime network access, as a width and a height angle. The derivation SHALL apply
the reducer or barlow factor to the focal length before computing the field of
view, so a reducer below 1.0 widens the field and a barlow above 1.0 narrows it.
The same equipment SHALL always yield the same field of view, so ranking stays
deterministic.

#### Scenario: Field of view follows from focal length and sensor size

- **WHEN** the equipment's field of view is derived
- **THEN** each axis angle grows as the sensor dimension grows and shrinks as the focal length grows

#### Scenario: The reducer widens the field

- **WHEN** two sets of equipment are identical except that one has a reducer factor below 1.0
- **THEN** the equipment with the reducer has the wider field of view

#### Scenario: Field-of-view derivation is deterministic and offline

- **WHEN** the field of view is derived twice for the same equipment, with no network available
- **THEN** the two results are identical
