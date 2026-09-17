## ADDED Requirements

### Requirement: Narrative is exposed as an optional entity

Narrative delivery is a configurable, off-by-default feature. When it is
**disabled**, the system SHALL NOT publish a narrative entity at all — no discovery
and no state — so a default deployment is unchanged, gains no entity, and sees no
unexpected messages. The system SHALL NOT attempt to auto-remove a narrative entity
that a prior enabled configuration created: it is stateless across restarts and
cannot detect one, and always publishing a removal would break the "no discovery
when disabled" guarantee. Clearing such an orphaned entity is a documented operator
step (clear its retained discovery topic), outside the publish path.

When narrative delivery is **enabled**, the system SHALL publish MQTT discovery
configuration for a narrative sensor for the pier, in addition to the existing
verdict, score, top-target, and refresh entities. Because entity state values are
length-limited, the full narrative prose SHALL be published in a JSON attributes
payload so a dashboard card can display it, with the entity state carrying a short
marker. The discovery payload SHALL conform to Home Assistant's MQTT discovery
schema for a sensor, SHALL be published retained to the discovery topic derived
from the pier identifier, and SHALL derive its unique identity from the pier
identifier so re-publishing updates the existing entity rather than creating a
duplicate.

When narrative delivery is enabled but no narrative is available for a publish —
its provider failed or returned nothing — the adapter SHALL actively publish the
narrative sensor's unavailable state on that publish rather than omitting the
update. Because state and attributes are published retained, omitting the update
would leave an earlier retained narrative in place and shown as current; the
adapter SHALL therefore publish so the sensor resolves to unavailable rather than
an empty, placeholder, or stale value. The narrative's absence or disablement SHALL
NOT block or alter publishing the verdict, score, top-target, and refresh entities.
This entity is additive: every existing entity, topic, and mapping is unchanged.

#### Scenario: Disabled narrative delivery publishes no entity

- **WHEN** the adapter publishes for a pier and narrative delivery is disabled
- **THEN** no narrative discovery or state is published for the pier
- **AND** the verdict, score, top-target, and refresh entities are published exactly as they are without this feature

#### Scenario: Narrative discovery and state are published when enabled and a narrative exists

- **WHEN** the adapter publishes for a pier with narrative delivery enabled and a narrative is available
- **THEN** it publishes a retained discovery configuration for a narrative sensor on the discovery topic derived from the pier identifier
- **AND** the discovery payload validates against Home Assistant's MQTT discovery schema for a sensor
- **AND** the full narrative prose is published in a JSON attributes payload

#### Scenario: Enabled but missing narrative renders unavailable without blocking the verdict

- **WHEN** the adapter publishes for a pier with narrative delivery enabled and no narrative is available
- **THEN** the adapter publishes so the narrative sensor resolves to unavailable rather than showing an empty or placeholder value
- **AND** the verdict, score, top-target, and refresh entities are still published

#### Scenario: A prior retained narrative is not shown as current

- **WHEN** the adapter publishes a narrative for a pier, and a later publish for the same pier has no narrative
- **THEN** the later publish actively updates the narrative entity so it resolves to unavailable
- **AND** the earlier narrative is not left retained and shown as the current explanation

#### Scenario: Existing entities are unchanged

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, and refresh entities keep their existing topics and unique identities
- **AND** re-publishing for the same pier introduces no additional narrative discovery identity
