## ADDED Requirements

### Requirement: The verdict attributes leave out the timeline and the later nights

The verdict entity's attributes payload SHALL carry every key of the verdict
document except `timeline` and `later_nights`, which SHALL be left out so the
payload stays under Home Assistant's recorder limit for state attributes. Every
key the payload carried before the timeline existed SHALL keep its position,
value and meaning.

#### Scenario: The attributes payload leaves the timeline and the later nights out

- **WHEN** a verdict document whose `timeline` holds 120 entries and whose `later_nights` holds three entries is published
- **THEN** the published attributes payload has no `timeline` key and no `later_nights` key
- **AND** it carries every other key of the document, in the document's order, with the same values

#### Scenario: An empty timeline leaves the attributes payload as it was

- **WHEN** a verdict document whose `timeline` and `later_nights` are both empty is published
- **THEN** the published attributes payload is byte-identical to the document's JSON with the `timeline` and `later_nights` keys removed

### Requirement: Each pier has a Night 2, Night 3 and Night 4 sensor

On publishing, the system SHALL publish MQTT discovery configuration for three
Night sensors per pier, named `Night 2`, `Night 3` and `Night 4`, on the pier's
device and enabled by default. Each SHALL be a timestamp sensor. Night 2 SHALL
show the first entry of `later_nights`, Night 3 the second and Night 4 the
third.

#### Scenario: Night discovery is published

- **WHEN** the adapter publishes for a pier with the id `backyard`
- **THEN** it publishes a retained discovery configuration on `<discovery prefix>/sensor/pierpressure_backyard/night_2/config`, and likewise for `night_3` and `night_4`
- **AND** each payload names its sensor `Night 2`, `Night 3` or `Night 4`, has the device class `timestamp`, and belongs to the pier's device
- **AND** each payload validates against Home Assistant's MQTT discovery schema for a sensor

### Requirement: Each Night sensor's discovery is retained and keyed by the pier and the night

Each Night sensor's topics and unique identity SHALL derive from the pier
identifier and the night's number, so re-publishing updates the existing entity
rather than creating a duplicate. The Night sensors are additive: every existing
entity, topic and mapping is unchanged.

#### Scenario: Existing entities are unchanged by the Night sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, rank, timeline, narrative, health and refresh entities keep their existing topics, payloads and unique identities
- **AND** re-publishing for the same pier introduces no additional Night sensor identity

### Requirement: A Night sensor's state is its night's dusk

When `later_nights` has an entry for a Night sensor, the sensor's state SHALL be
that entry's `dark_window.start`, as an ISO 8601 time with a `+00:00` offset, to
the whole second. When that `dark_window.start` is null, or `later_nights` has
no entry for the sensor, the state SHALL be the literal `None`, which Home
Assistant shows as unknown.

#### Scenario: Night 2 shows the next dusk

- **WHEN** the adapter publishes for the pier `backyard` a document whose first `later_nights` entry has the `dark_window` `{"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}`
- **THEN** it publishes `2026-09-09T20:27:57+00:00`, retained, to `<base topic>/backyard/night_2/state`

#### Scenario: A night with no astronomical darkness shows unknown

- **WHEN** the adapter publishes a document whose second `later_nights` entry has the `dark_window` `{"start": null, "end": null}`
- **THEN** it publishes `None`, retained, to the Night 3 state topic
- **AND** the Night 3 attributes mark the night as available

### Requirement: A Night sensor's attributes hold its night's entry

The adapter SHALL publish each Night sensor's attributes as a JSON object. When
`later_nights` has an entry for the sensor, the object SHALL be `available`
true, then `night` with the sensor's number, then the entry's keys with the
document's values. Otherwise it SHALL be `available` false and `night` only.

#### Scenario: A filled night

- **WHEN** the adapter publishes for the pier `backyard` a document whose first `later_nights` entry has the `dark_window` `{"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}`
- **THEN** it publishes `{"available": true, "night": 2, "dark_window": {"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}}`, retained, to `<base topic>/backyard/night_2/attributes`

#### Scenario: A night the forecast does not reach

- **WHEN** the adapter publishes a document whose `later_nights` holds one entry
- **THEN** it publishes `{"available": false, "night": 3}` to the Night 3 attributes topic and `{"available": false, "night": 4}` to the Night 4 attributes topic, each retained

### Requirement: A Night sensor is unavailable only when its night is not in the later nights

Each Night sensor's discovery SHALL declare an availability that needs both
PierPressure's online availability and the `available` flag of its attributes.
So a Night sensor SHALL be unavailable when its night is not in `later_nights`,
and available, with state unknown, when its night has no astronomical darkness.

#### Scenario: An empty list makes every Night sensor unavailable

- **WHEN** the adapter publishes a document whose `later_nights` is empty
- **THEN** the Night 2, Night 3 and Night 4 attributes each carry `"available": false`
- **AND** each Night sensor's discovery payload declares an availability that makes the sensor unavailable while its attributes carry `"available": false`

### Requirement: Every publish updates every Night sensor

Every publish SHALL write the state and attributes of all three Night sensors,
whether or not their night is in `later_nights`. So a Night sensor never keeps
an earlier night after the list shrinks. The Night sensors' messages SHALL come
after the timeline sensors' messages in the publish.

#### Scenario: A shrinking list clears the later Night sensors

- **WHEN** the adapter publishes a document with three later nights and then a document with one later night, for the same pier
- **THEN** the second publish writes `None` to the Night 3 and Night 4 state topics and `"available": false` attributes to both
- **AND** no retained state or attributes for Night 3 or Night 4 still carry their earlier night

#### Scenario: The Night sensors follow the timeline sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the Night 2, Night 3 and Night 4 messages, in that order, come after the Cloud cover max sensor's messages

## REMOVED Requirements

### Requirement: The verdict attributes leave out only the timeline

**Reason**: The attributes now also leave out `later_nights`, so "only the
timeline" is no longer true. The new requirement "The verdict attributes leave
out the timeline and the later nights" replaces it, with the same scenarios
extended to `later_nights`.

**Migration**: None for Home Assistant users: every key the attributes carried
keeps its position, value and meaning. Read a later night's dark window from
its Night sensor.
