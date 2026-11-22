## RENAMED Requirements

- FROM: `### Requirement: The verdict attributes leave out only the timeline`
- TO: `### Requirement: The verdict attributes leave out the timeline and the later nights`

## MODIFIED Requirements

### Requirement: The verdict attributes leave out the timeline and the later nights

The verdict entity's attributes payload SHALL carry every key of the verdict
document except `timeline` and `later_nights`. Both SHALL be left out so the
payload stays under Home Assistant's recorder limit for state attributes. Every
key the payload carried before the timeline existed SHALL keep its position,
value and meaning.

#### Scenario: The attributes payload leaves the timeline out

- **WHEN** a verdict document whose `timeline` holds 120 entries is published
- **THEN** the published attributes payload has no `timeline` key
- **AND** it carries every other key of the document except `later_nights`, in the document's order, with the same values

#### Scenario: The attributes payload leaves the later nights out

- **WHEN** a verdict document whose `later_nights` holds three entries is published
- **THEN** the published attributes payload has no `later_nights` key

#### Scenario: An empty timeline leaves the attributes payload as it was

- **WHEN** a verdict document whose `timeline` and `later_nights` are both empty is published
- **THEN** the published attributes payload is byte-identical to the document's JSON with the `timeline` and `later_nights` keys removed

## ADDED Requirements

### Requirement: A Night sensor is announced for each of Night 2 to Night 4

On publishing, the system SHALL publish MQTT discovery configuration for three
Night sensors per pier, named `Night 2`, `Night 3` and `Night 4`, on the pier's
device. Night 2 is the first later night, Night 3 the second and Night 4 the
third. Each SHALL be a timestamp sensor, enabled by default.

#### Scenario: Night discovery is published for every night

- **WHEN** the adapter publishes for a pier with id `backyard`
- **THEN** it publishes a retained discovery configuration for the sensors `Night 2`, `Night 3` and `Night 4`
- **AND** each discovery payload marks the sensor as a timestamp and validates against the repository's discovery schema for a sensor
- **AND** Home Assistant names them `sensor.pierpressure_backyard_night_2`, `sensor.pierpressure_backyard_night_3` and `sensor.pierpressure_backyard_night_4`

### Requirement: Each Night sensor's discovery is retained and keyed by the pier and the night

The adapter SHALL publish each Night sensor's discovery retained, to a topic
derived from the pier identifier and the night number. Each Night sensor SHALL
derive its unique identity from the pier identifier and the night number, so
re-publishing updates the existing entity. These entities are additive: every
existing entity, topic and mapping is unchanged.

#### Scenario: Re-publishing keeps the same Night sensors

- **WHEN** the adapter publishes twice for the same pier
- **THEN** both publishes use the same Night sensor discovery topics and unique identities
- **AND** the verdict, score, top-target, rank, timeline, health and refresh entities keep their existing topics, payloads and unique identities

### Requirement: A Night sensor's state is its night's dusk

When `later_nights` has an entry for a Night sensor's night, the sensor's state
SHALL be that entry's `dark_window.start`, in UTC ISO 8601 with a `+00:00`
offset, to the whole second.

#### Scenario: Night 2 shows tomorrow's dusk

- **WHEN** the adapter publishes a document whose first `later_nights` entry has the `dark_window` `{start: 2026-11-22T18:01:39Z, end: 2026-11-23T05:32:17Z}`
- **THEN** the Night 2 sensor's state is `2026-11-22T18:01:39+00:00`

### Requirement: A Night sensor's attributes hold its night's entry

When `later_nights` has an entry for a Night sensor's night, the adapter SHALL
publish a JSON attributes payload holding `available: true`, the night number
as `night`, and then every key of that entry with the document's values.

#### Scenario: Night 2's attributes

- **WHEN** the adapter publishes a document whose first `later_nights` entry has the `dark_window` `{start: 2026-11-22T18:01:39Z, end: 2026-11-23T05:32:17Z}`
- **THEN** the Night 2 sensor's attributes payload is `{"available": true, "night": 2, "dark_window": {"start": "2026-11-22T18:01:39Z", "end": "2026-11-23T05:32:17Z"}}`

### Requirement: A Night sensor whose night has no astronomical darkness shows unknown

When a Night sensor's night is in `later_nights` with a null `dark_window.start`,
the sensor SHALL resolve to unknown and stay available. Its attributes SHALL
still hold the entry, with the null bounds.

#### Scenario: A night that never gets dark

- **WHEN** the adapter publishes a document whose second `later_nights` entry has the `dark_window` `{start: null, end: null}`
- **THEN** the Night 3 sensor resolves to unknown, not unavailable
- **AND** its attributes payload is `{"available": true, "night": 3, "dark_window": {"start": null, "end": null}}`

### Requirement: A Night sensor whose night is not in the later nights is unavailable

When `later_nights` has no entry for a Night sensor's night, the sensor SHALL
resolve to unavailable rather than an empty or placeholder value. Its
attributes payload SHALL be `{"available": false, "night": <n>}`.

#### Scenario: Only one later night

- **WHEN** the adapter publishes a document whose `later_nights` holds one entry
- **THEN** the Night 3 and Night 4 sensors resolve to unavailable
- **AND** their attributes payloads are `{"available": false, "night": 3}` and `{"available": false, "night": 4}`
- **AND** each Night sensor's discovery payload declares an availability that makes it unavailable when its attributes mark it as not available

#### Scenario: Every forecast fails

- **WHEN** the adapter publishes a document whose `later_nights` is empty
- **THEN** the Night 2, Night 3 and Night 4 sensors all resolve to unavailable

### Requirement: Every publish updates every Night sensor

Every publish SHALL update the state and attributes of all three Night
sensors, including those whose night is not in `later_nights`, so a Night
sensor never keeps an earlier night after the list shrinks.

#### Scenario: A shrinking list clears the old nights

- **WHEN** the adapter publishes a document with three later nights and then one with one later night, for the same pier
- **THEN** the second publish overwrites the retained attributes of Night 3 and Night 4 with payloads that mark each as not available
- **AND** no retained state or attributes for Night 3 or Night 4 still carry their earlier nights
