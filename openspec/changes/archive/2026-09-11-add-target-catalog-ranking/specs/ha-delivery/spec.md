## ADDED Requirements

### Requirement: Top target is exposed as an entity

On publishing, the system SHALL publish MQTT discovery configuration for a
top-target sensor for the pier, in addition to the existing verdict, score, and
refresh entities. The sensor's state SHALL be the top-ranked target's name (its
designation when the catalog records no common name). The full ordered target
list, and the top target's fields, SHALL be published as a JSON attributes
payload so a dashboard card can display them. The discovery payload SHALL conform
to Home Assistant's MQTT discovery schema for a sensor, SHALL be published
retained to the discovery topic derived from the pier identifier, and SHALL
derive its unique identity from the pier identifier so re-publishing updates the
existing entity rather than creating a duplicate. When the target list is empty,
the sensor SHALL resolve to unavailable rather than an empty or placeholder
value. This entity is additive: every existing entity, topic, and mapping is
unchanged.

#### Scenario: Top-target discovery and state are published

- **WHEN** the adapter publishes for a pier whose verdict has a non-empty target list
- **THEN** it publishes a retained discovery configuration for a top-target sensor on the discovery topic derived from the pier identifier
- **AND** the discovery payload validates against Home Assistant's MQTT discovery schema for a sensor
- **AND** the sensor state is the top-ranked target's name, with the full ordered target list published as a JSON attributes payload

#### Scenario: Existing entities are unchanged

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, and refresh entities keep their existing topics and unique identities
- **AND** re-publishing for the same pier introduces no additional top-target discovery identity

#### Scenario: Empty target list renders unavailable

- **WHEN** the adapter publishes for a pier whose verdict has an empty target list
- **THEN** the top-target sensor's discovery payload declares an availability that makes it unavailable rather than showing an empty or placeholder value
