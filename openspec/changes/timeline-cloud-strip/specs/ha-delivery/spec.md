## MODIFIED Requirements

### Requirement: Verdict state and attributes are exposed

The verdict entity's state SHALL be published as the verdict value (`GO`, `MAYBE`, or `NO-GO`). The reasons, the score, the confidence (band and value), the night window, the pier identifier, and the generation timestamp SHALL be published as a JSON attributes payload so a dashboard card can display them. The attributes payload SHALL carry every key of the verdict document except `timeline`, which SHALL be left out so the payload stays under Home Assistant's recorder limit for state attributes. Every key the payload carried before the timeline existed SHALL keep its position, value and meaning. The score entity's state SHALL be the numeric score. The score entity's discovery configuration SHALL declare availability such that the score is available only when the process is online AND the score is non-null; when the score is null the score entity SHALL resolve to unavailable rather than a numeric value such as `0`.

#### Scenario: Verdict state and attributes are published from the document

- **WHEN** a verdict document with verdict `MAYBE`, a confidence, and a set of reasons is published
- **THEN** `MAYBE` is published to the verdict state topic
- **AND** a JSON attributes payload is published containing the reasons, score, confidence, night window, pier identifier, and generation timestamp

#### Scenario: Null score is published as null, with availability requiring non-null

- **WHEN** a verdict document whose score is null is published
- **THEN** the published attributes payload contains the `score` key explicitly set to null (present, not omitted)
- **AND** the score entity's published discovery payload declares an availability that requires a non-null score, so Home Assistant renders it unavailable rather than as `0`

#### Scenario: The attributes payload leaves the timeline out

- **WHEN** a verdict document whose `timeline` holds 72 entries is published
- **THEN** the published attributes payload has no `timeline` key
- **AND** it carries every other key of the document, in the document's order, with the same values

## ADDED Requirements

### Requirement: Cloud cover is exposed as an entity

On publishing, the system SHALL publish MQTT discovery configuration for one Cloud cover sensor per pier, on the pier's device, enabled by default, with a unit of percent. The payload SHALL conform to Home Assistant's MQTT discovery schema for a sensor and be published retained to a discovery topic derived from the pier identifier. Its unique identity SHALL derive from the pier identifier, so re-publishing updates the existing entity. Every existing entity, topic and mapping SHALL be unchanged.

#### Scenario: Cloud cover discovery is published

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration for a Cloud cover sensor on the pier's device, enabled by default, with the unit `%`
- **AND** its discovery topic and unique identity derive from the pier identifier
- **AND** the payload validates against Home Assistant's MQTT discovery schema for a sensor

#### Scenario: Existing entities are unchanged by the Cloud cover sensor

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, rank, narrative, health and refresh entities keep their existing topics, payloads and unique identities
- **AND** re-publishing for the same pier introduces no additional Cloud cover identity

### Requirement: The Cloud cover forecast mirrors the timeline

The Cloud cover sensor's JSON attributes payload SHALL carry a `forecast` list with one entry per timeline entry, in the timeline's order. Each entry SHALL hold `datetime`, the timeline entry's `time`, and `value`, the timeline entry's `cloud_cover`, null when that is null. The list SHALL be empty when the timeline is empty. Every publish SHALL update the payload, so a retained payload never outlives the verdict it came from.

#### Scenario: The forecast array mirrors the timeline

- **WHEN** the adapter publishes a document whose timeline holds entries at 20:00 with cloud cover 37 and at 21:00 with cloud cover null
- **THEN** the sensor's attributes payload holds `forecast` with exactly two entries in that order: `{datetime: <20:00>, value: 37}` and `{datetime: <21:00>, value: null}`

#### Scenario: An empty timeline publishes an empty forecast

- **WHEN** the adapter publishes a document whose timeline is empty
- **THEN** the sensor's attributes payload holds an empty `forecast` list

#### Scenario: A later publish replaces the forecast

- **WHEN** the adapter publishes a document with 72 timeline entries and then one with 48 for the same pier
- **THEN** the retained attributes payload holds exactly the 48 entries of the second document

### Requirement: The Cloud cover state is the current hour's value

The Cloud cover sensor's state SHALL be the `cloud_cover` of the timeline entry whose hour contains the document's generation timestamp. When no entry has that hour, or its `cloud_cover` is null, the sensor SHALL resolve to unavailable rather than `0`, an empty value or an earlier value.

#### Scenario: The state is the current hour's cloud cover

- **WHEN** the adapter publishes a document generated at 23:30 whose timeline has an entry at 23:00 with cloud cover 15
- **THEN** the sensor's state is `15`

#### Scenario: A missing or null current hour renders unavailable

- **WHEN** the adapter publishes a document generated at 23:30 whose timeline has no entry at 23:00, or whose 23:00 entry has a null cloud cover
- **THEN** the adapter publishes a retained attributes payload that marks the sensor as having no current value
- **AND** the sensor's discovery payload declares an availability that makes the sensor unavailable in that case, rather than showing `0`, an empty value or an earlier value

#### Scenario: An empty timeline renders unavailable

- **WHEN** the adapter publishes a document whose timeline is empty
- **THEN** the sensor resolves to unavailable
