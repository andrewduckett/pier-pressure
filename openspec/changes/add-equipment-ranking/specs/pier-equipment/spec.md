## Purpose

The pier-equipment capability gives each pier an optional description of one
imaging rig — telescope and camera — and derives the field of view that rig sees,
offline and deterministically, so target ranking can judge how well an object
frames.

## ADDED Requirements

### Requirement: Equipment is an optional per-pier imaging rig

Each pier MAY carry a description of one imaging rig. When present, the rig SHALL
provide a telescope focal length in millimetres, a camera sensor width and height
in millimetres, and MAY provide a focal reducer or barlow factor (default 1.0).
Equipment SHALL be optional: a pier with no rig configured SHALL still produce a
verdict and a ranked target list, without a field-of-view term. A rig SHALL NOT
change any existing configuration field or its meaning.

The focal length, both sensor dimensions, and the reducer factor SHALL each be
strictly positive. A rig with a zero or negative value in any of these SHALL make
the pier's configuration invalid — reported as a configuration error, with no
verdict produced — mirroring the pier configuration validation already applied to
other fields. This keeps the derived field of view well defined, so the derivation
never divides by zero.

#### Scenario: A pier without a rig still ranks targets

- **WHEN** a verdict is produced for a pier that has no rig configured
- **THEN** the verdict and its ranked target list are produced without error
- **AND** no field-of-view term contributes to any target's score

#### Scenario: A rig with a non-positive value is rejected

- **WHEN** a pier configures a rig whose focal length, a sensor dimension, or reducer is zero or negative
- **THEN** loading that configuration fails with a configuration error
- **AND** no verdict is produced for that pier

#### Scenario: A rig is described by optics, not a pre-computed field of view

- **WHEN** a pier configures a rig
- **THEN** the rig is given as a focal length, a sensor width, and a sensor height, with an optional reducer factor
- **AND** the configuration does not require the field of view to be supplied directly

### Requirement: Field of view is derived offline from the rig

The system SHALL derive the rig's field of view from its optics, with no runtime
network access, as a width and a height angle. The derivation SHALL apply the
reducer or barlow factor to the focal length before computing the field of view,
so a reducer below 1.0 widens the field and a barlow above 1.0 narrows it. The
same rig SHALL always yield the same field of view, so ranking stays
deterministic.

#### Scenario: Field of view follows from focal length and sensor size

- **WHEN** a rig's field of view is derived
- **THEN** each axis angle grows as the sensor dimension grows and shrinks as the focal length grows

#### Scenario: The reducer widens the field

- **WHEN** two rigs are identical except that one has a reducer factor below 1.0
- **THEN** the rig with the reducer has the wider field of view

#### Scenario: Field-of-view derivation is deterministic and offline

- **WHEN** the field of view is derived twice for the same rig, with no network available
- **THEN** the two results are identical
