## ADDED Requirements

### Requirement: Each rank of the target list is exposed as an entity

On publishing, the system SHALL publish MQTT discovery configuration for one rank
sensor per rank, from rank 1 to the ranking's maximum list length. These sensors
are in addition to the existing entities, and each one belongs to the pier's device.
The adapter SHALL publish each rank sensor as enabled by default.

When the target list has an entry at a sensor's rank, the sensor's state SHALL be
that target's name. When the catalog records no common name, the state SHALL be
the target's catalog id. The adapter SHALL publish that target's rank and its
fields as the sensor's JSON attributes payload.

When the target list has no entry at a sensor's rank, the sensor SHALL resolve to
unavailable rather than an empty or placeholder value.

Every publish SHALL update every rank sensor, including ranks with no target. So a
rank never keeps an earlier target after the list shrinks.

Each discovery payload SHALL conform to Home Assistant's MQTT discovery schema for
a sensor. The adapter SHALL publish each one retained to a discovery topic derived from
the pier identifier and the rank. Each SHALL derive its unique identity from the pier
identifier and the rank, so re-publishing updates the existing entity rather than
creating a duplicate. These entities are additive: every existing entity, topic,
and mapping is unchanged.

#### Scenario: Rank discovery is published for every rank

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration for a rank sensor at every rank from 1 to the maximum list length
- **AND** each discovery topic and unique identity derives from the pier identifier and the rank
- **AND** each discovery payload validates against Home Assistant's MQTT discovery schema for a sensor
- **AND** each rank sensor is enabled by default

#### Scenario: A filled rank shows its target

- **WHEN** the adapter publishes for a pier whose target list has an entry at rank 3
- **THEN** the rank 3 sensor's state is that target's name
- **AND** the rank 3 sensor's attributes carry rank 3 and that target's fields

#### Scenario: A filled rank falls back to the catalog id

- **WHEN** the target at a rank has no common name in the catalog
- **THEN** that rank sensor's state is the target's catalog id

#### Scenario: An empty rank renders unavailable

- **WHEN** the adapter publishes for a pier whose target list has fewer entries than the maximum list length
- **THEN** the adapter publishes, for each rank beyond the last entry, a retained attributes payload that marks the rank as having no target
- **AND** each rank sensor's discovery payload declares an availability that makes the sensor unavailable when its rank is marked as having no target, rather than showing an empty or placeholder value

#### Scenario: A shrinking list clears the old ranks

- **WHEN** the adapter publishes a target list with 5 entries and then publishes a list with 2 entries for the same pier
- **THEN** the second publish overwrites the retained attributes for ranks 3 to 5 with payloads that mark each rank as having no target
- **AND** no retained state or attributes for ranks 3 to 5 still carry their earlier targets

#### Scenario: Existing entities are unchanged by the rank sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, and refresh entities keep their existing topics, payloads, and unique identities
- **AND** re-publishing for the same pier introduces no additional rank sensor identity
