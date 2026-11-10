## ADDED Requirements

### Requirement: The verdict, score and refresh entities are announced by discovery

On publishing, the system SHALL publish MQTT discovery configuration messages
for at least a verdict entity, a score entity, and a refresh control for the
pier, so Home Assistant auto-creates them without manual configuration. Each
discovery payload SHALL conform to Home Assistant's MQTT discovery schema for
its entity type (sensor, sensor, button), SHALL be published to the discovery
topic derived from the pier identifier, and SHALL be published with the retain
flag set.

#### Scenario: Discovery configuration is published on first publish

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration message for a verdict sensor, a score sensor, and a refresh button, each on the discovery topic derived from the pier identifier
- **AND** each discovery payload validates against Home Assistant's MQTT discovery schema for its entity type

### Requirement: Re-publishing for a pier updates its verdict, score and refresh entities

The unique identity of the verdict, score and refresh entities SHALL derive from
the pier identifier, so re-publishing for the same pier updates the existing
entities rather than creating duplicates.

#### Scenario: Re-publishing targets the same identities, not duplicates

- **WHEN** the adapter publishes twice for the same pier identifier
- **THEN** both publishes use the same discovery topics and the same entity unique identities
- **AND** no additional verdict, score, or refresh discovery identity is introduced

### Requirement: The verdict entity publishes the verdict and its details

The verdict entity's state SHALL be published as the verdict value (`GO`,
`MAYBE`, or `NO-GO`). The reasons, the score, the confidence (band and value),
the night window, the pier identifier, and the generation timestamp SHALL be
published as a JSON attributes payload so a dashboard card can display them.

#### Scenario: Verdict state and attributes are published from the document

- **WHEN** a verdict document with verdict `MAYBE`, a confidence, and a set of reasons is published
- **THEN** `MAYBE` is published to the verdict state topic
- **AND** a JSON attributes payload is published containing the reasons, score, confidence, night window, pier identifier, and generation timestamp

### Requirement: The verdict attributes leave out only the timeline

The verdict entity's attributes payload SHALL carry every key of the verdict
document except `timeline`, which SHALL be left out so the payload stays under
Home Assistant's recorder limit for state attributes. Every key the payload
carried before the timeline existed SHALL keep its position, value and meaning.

#### Scenario: The attributes payload leaves the timeline out

- **WHEN** a verdict document whose `timeline` holds 120 entries is published
- **THEN** the published attributes payload has no `timeline` key
- **AND** it carries every other key of the document, in the document's order, with the same values

#### Scenario: An empty timeline leaves the attributes payload as it was

- **WHEN** a verdict document whose `timeline` is empty is published
- **THEN** the published attributes payload is byte-identical to the document's JSON with the `timeline` key removed

### Requirement: The score entity shows the numeric score, or unavailable when the score is null

The score entity's state SHALL be the numeric score. The score entity's
discovery configuration SHALL declare availability such that the score is
available only when the process is online AND the score is non-null; when the
score is null the score entity SHALL resolve to unavailable rather than a
numeric value such as `0`.

#### Scenario: Null score is published as null, with availability requiring non-null

- **WHEN** a verdict document whose score is null is published
- **THEN** the published attributes payload contains the `score` key explicitly set to null (present, not omitted)
- **AND** the score entity's published discovery payload declares an availability that requires a non-null score, so Home Assistant renders it unavailable rather than as `0`

### Requirement: The top-target sensor is announced by discovery

On publishing, the system SHALL publish MQTT discovery configuration for a
top-target sensor for the pier, in addition to the existing verdict, score, and
refresh entities. The discovery payload SHALL conform to Home Assistant's MQTT
discovery schema for a sensor, and SHALL be published retained to the discovery
topic derived from the pier identifier.

#### Scenario: Top-target discovery and state are published

- **WHEN** the adapter publishes for a pier whose verdict has a non-empty target list
- **THEN** it publishes a retained discovery configuration for a top-target sensor on the discovery topic derived from the pier identifier
- **AND** the discovery payload validates against Home Assistant's MQTT discovery schema for a sensor
- **AND** the sensor state is the top-ranked target's name, with the full ordered target list published as a JSON attributes payload

### Requirement: The top-target sensor shows the top target's name and the ordered list

The top-target sensor's state SHALL be the top-ranked target's name (its
designation when the catalog records no common name). The full ordered target
list, and the top target's fields, SHALL be published as the sensor's JSON
attributes payload so a dashboard card can display them.

#### Scenario: An unnamed top target shows its designation

- **WHEN** the adapter publishes for a pier whose top-ranked target has no common name in the catalog
- **THEN** the top-target sensor's state is that target's designation

### Requirement: Re-publishing updates the existing top-target sensor

The top-target sensor SHALL derive its unique identity from the pier identifier,
so re-publishing updates the existing entity rather than creating a duplicate.
This entity is additive: every existing entity, topic, and mapping is unchanged.

#### Scenario: Existing entities are unchanged

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, and refresh entities keep their existing topics and unique identities
- **AND** re-publishing for the same pier introduces no additional top-target discovery identity

### Requirement: An empty target list makes the top-target sensor unavailable

When the target list is empty, the top-target sensor SHALL resolve to
unavailable rather than an empty or placeholder value.

#### Scenario: Empty target list renders unavailable

- **WHEN** the adapter publishes for a pier whose verdict has an empty target list
- **THEN** the top-target sensor's discovery payload declares an availability that makes it unavailable rather than showing an empty or placeholder value

### Requirement: Disabled narrative delivery publishes no narrative entity

Narrative delivery is a configurable, off-by-default feature. When it is
**disabled**, the system SHALL NOT publish a narrative entity at all — no
discovery and no state — so a default deployment is unchanged, gains no entity,
and sees no unexpected messages.

#### Scenario: Disabled narrative delivery publishes no entity

- **WHEN** the adapter publishes for a pier and narrative delivery is disabled
- **THEN** no narrative discovery or state is published for the pier
- **AND** the verdict, score, top-target, and refresh entities are published exactly as they are without this feature

### Requirement: A narrative entity left by an earlier configuration is not removed automatically

When narrative delivery is disabled, the system SHALL NOT attempt to auto-remove
a narrative entity that a prior enabled configuration created: it is stateless
across restarts and cannot detect one, and always publishing a removal would
break the "no discovery when disabled" guarantee. Clearing such an orphaned
entity is a documented operator step (clear its retained discovery topic),
outside the publish path.

#### Scenario: A narrative entity from an earlier configuration is left in place

- **WHEN** narrative delivery is disabled, the broker holds a retained narrative discovery configuration from an earlier run with it enabled, and the adapter publishes for the pier
- **THEN** the adapter publishes no message to the pier's narrative discovery topic, not even an empty one

### Requirement: Enabled narrative delivery announces a narrative sensor

When narrative delivery is **enabled**, the system SHALL publish MQTT discovery
configuration for a narrative sensor for the pier, in addition to the existing
verdict, score, top-target, and refresh entities. The discovery payload SHALL
conform to Home Assistant's MQTT discovery schema for a sensor, and SHALL be
published retained to the discovery topic derived from the pier identifier.

#### Scenario: Narrative discovery and state are published when enabled and a narrative exists

- **WHEN** the adapter publishes for a pier with narrative delivery enabled and a narrative is available
- **THEN** it publishes a retained discovery configuration for a narrative sensor on the discovery topic derived from the pier identifier
- **AND** the discovery payload validates against Home Assistant's MQTT discovery schema for a sensor
- **AND** the full narrative prose is published in a JSON attributes payload

### Requirement: The narrative prose is published in the attributes, not the state

Because entity state values are length-limited, the full narrative prose SHALL
be published in the narrative sensor's JSON attributes payload so a dashboard
card can display it, with the entity state carrying a short marker.

#### Scenario: The narrative state does not carry the prose

- **WHEN** the adapter publishes for a pier with narrative delivery enabled and a narrative is available
- **THEN** the narrative sensor's attributes payload carries the full narrative prose
- **AND** the narrative sensor's state does not contain the prose

### Requirement: With no narrative, the enabled narrative sensor is published as unavailable

When narrative delivery is enabled but a publish has no narrative, because its
provider failed or returned nothing, the adapter SHALL actively publish the
narrative sensor's unavailable state on that publish rather than omitting the
update. Because state and attributes are retained, omitting the update would
leave an earlier narrative in place and shown as current; the adapter SHALL
therefore publish so the sensor resolves to unavailable rather than an empty,
placeholder, or stale value.

#### Scenario: A prior retained narrative is not shown as current

- **WHEN** the adapter publishes a narrative for a pier, and a later publish for the same pier has no narrative
- **THEN** the later publish actively updates the narrative entity so it resolves to unavailable
- **AND** the earlier narrative is not left retained and shown as the current explanation

### Requirement: A missing or disabled narrative does not hold back the other entities

The narrative's absence or disablement SHALL NOT block or alter publishing the
verdict, score, top-target, and refresh entities.

#### Scenario: Enabled but missing narrative renders unavailable without blocking the verdict

- **WHEN** the adapter publishes for a pier with narrative delivery enabled and no narrative is available
- **THEN** the adapter publishes so the narrative sensor resolves to unavailable rather than showing an empty or placeholder value
- **AND** the verdict, score, top-target, and refresh entities are still published

### Requirement: Re-publishing updates the existing narrative sensor

The narrative sensor SHALL derive its unique identity from the pier identifier,
so re-publishing updates the existing entity rather than creating a duplicate.
This entity is additive: every existing entity, topic, and mapping is unchanged.

#### Scenario: Existing entities are unchanged

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, and refresh entities keep their existing topics and unique identities
- **AND** re-publishing for the same pier introduces no additional narrative discovery identity

### Requirement: A rank sensor is announced for every rank

On publishing, the system SHALL publish MQTT discovery configuration for one
rank sensor per rank, from rank 1 to the ranking's maximum list length. These
sensors are in addition to the existing entities, and each one belongs to the
pier's device. The adapter SHALL publish each rank sensor as enabled by default.

#### Scenario: Rank discovery is published for every rank

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration for a rank sensor at every rank from 1 to the maximum list length
- **AND** each discovery topic and unique identity derives from the pier identifier and the rank
- **AND** each discovery payload validates against Home Assistant's MQTT discovery schema for a sensor
- **AND** each rank sensor is enabled by default

### Requirement: A filled rank sensor shows its target

When the target list has an entry at a rank sensor's rank, the sensor's state
SHALL be that target's name. When the catalog records no common name, the state
SHALL be the target's catalog id. The adapter SHALL publish that target's rank
and its fields as the sensor's JSON attributes payload.

#### Scenario: A filled rank shows its target

- **WHEN** the adapter publishes for a pier whose target list has an entry at rank 3
- **THEN** the rank 3 sensor's state is that target's name
- **AND** the rank 3 sensor's attributes carry rank 3 and that target's fields

#### Scenario: A filled rank falls back to the catalog id

- **WHEN** the target at a rank has no common name in the catalog
- **THEN** that rank sensor's state is the target's catalog id

### Requirement: A rank with no target renders unavailable

When the target list has no entry at a rank sensor's rank, the sensor SHALL
resolve to unavailable rather than an empty or placeholder value.

#### Scenario: An empty rank renders unavailable

- **WHEN** the adapter publishes for a pier whose target list has fewer entries than the maximum list length
- **THEN** the adapter publishes, for each rank beyond the last entry, a retained attributes payload that marks the rank as having no target
- **AND** each rank sensor's discovery payload declares an availability that makes the sensor unavailable when its rank is marked as having no target, rather than showing an empty or placeholder value

### Requirement: Every publish updates every rank sensor

Every publish SHALL update every rank sensor, including ranks with no target. So
a rank never keeps an earlier target after the list shrinks.

#### Scenario: A shrinking list clears the old ranks

- **WHEN** the adapter publishes a target list with 5 entries and then publishes a list with 2 entries for the same pier
- **THEN** the second publish overwrites the retained attributes for ranks 3 to 5 with payloads that mark each rank as having no target
- **AND** no retained state or attributes for ranks 3 to 5 still carry their earlier targets

### Requirement: Each rank sensor's discovery is retained and keyed by the pier and the rank

Each rank sensor's discovery payload SHALL conform to Home Assistant's MQTT
discovery schema for a sensor. The adapter SHALL publish each one retained to a
discovery topic derived from the pier identifier and the rank. Each rank sensor
SHALL derive its unique identity from the pier identifier and the rank, so
re-publishing updates the existing entity rather than creating a duplicate.
These entities are additive: every existing entity, topic, and mapping is
unchanged.

#### Scenario: Existing entities are unchanged by the rank sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, and refresh entities keep their existing topics, payloads, and unique identities
- **AND** re-publishing for the same pier introduces no additional rank sensor identity

### Requirement: Each configured provider has a health sensor named after it

On every publish for a pier, the system SHALL publish one health sensor for each
configured conditions provider. Each sensor SHALL be named after its provider,
for example "Open-Meteo health" and "7Timer! health". The system SHALL publish
discovery for every configured provider, including a provider not tried on this
publish.

#### Scenario: Each health sensor is named after its provider

- **WHEN** the system publishes health for a pier whose configured providers are `open_meteo` and `seven_timer`
- **THEN** it publishes one health sensor named "Open-Meteo health" and one named "7Timer! health"

### Requirement: A health sensor's discovery marks it as a diagnostic timestamp sensor

Each health sensor's discovery configuration SHALL mark it as a diagnostic
entity and as a timestamp sensor. It SHALL conform to the repository's discovery
schema for a sensor. It SHALL be published retained to the discovery topic
derived from the pier identifier and the provider. Its unique identity SHALL
derive from the pier identifier and the provider, so re-publishing updates the
existing entity rather than creating a duplicate.

#### Scenario: Health discovery is published per provider

- **WHEN** the adapter publishes for a pier with two configured conditions providers
- **THEN** it publishes a retained discovery configuration for one health sensor per provider on topics derived from the pier identifier and the provider
- **AND** each discovery payload marks the sensor as diagnostic and as a timestamp
- **AND** each discovery payload validates against the repository's discovery schema for a sensor

### Requirement: A health sensor's state is its provider's last success since the process started

A health sensor's state SHALL be the time of the provider's last successful
fetch for that pier. When the provider has not succeeded for that pier since the
process started, the sensor SHALL resolve to unknown. It SHALL NOT show a
retained time from before the restart while the process is online. Health SHALL
be held in memory only, and the system SHALL NOT keep it across restarts.

#### Scenario: A successful fetch sets the last-success time

- **WHEN** a provider's fetch for a pier succeeds and the system publishes
- **THEN** that provider's health sensor state is the time of that fetch
- **AND** its attributes give status `ok`, the fetch time, a null error, and the issue time of the returned data

#### Scenario: No success since a restart resolves to unknown

- **WHEN** the process restarts, and a provider's first fetch for a pier fails
- **THEN** the system publishes so that provider's health sensor resolves to unknown
- **AND** no last-success time from before the restart is shown as current

### Requirement: On startup, provider health is reset before the process goes online

On startup, the system SHALL publish every configured provider's health with no
history, for every pier. It SHALL do this before it publishes its online
availability, and before it fetches any conditions or asks for any narrative.
This replaces any retained health from before the restart.

#### Scenario: Startup clears retained health before going online

- **WHEN** the process starts, and the broker holds a retained health state from before the restart
- **THEN** the system publishes each configured provider's health with no history before it publishes its online availability
- **AND** it does so before it fetches any conditions
- **AND** each health sensor's state is published as unknown, with the tracking start time and the provider's variables, and null status, fetch time, error, and issue time
- **AND** the `computed` health sensor's `inputs` is null

### Requirement: A startup health reset cut off by a dropped connection is published again

If the connection drops before the startup health reset reaches the broker, the
process SHALL NOT exit. It SHALL publish the reset health again after the
reconnect, before it publishes its online availability.

#### Scenario: A failed startup reset does not go online

- **WHEN** the broker accepts the first connection
- **AND** the connection drops before the process publishes the startup health reset
- **AND** the broker accepts a new connection
- **THEN** the process does not exit
- **AND** after the reconnect, it publishes each configured provider's health with no history before it publishes its online availability

### Requirement: A health sensor's attributes name its provider, its variables and when tracking started

Each health sensor's JSON attributes SHALL carry:

- the provider's name
- `variables`: the variables the provider declares, as a list of variable keys
  in the provider's declared order. A variable key need not be a timeline key.
  It is the same on every publish. There is no `role` attribute.
- the time health tracking started: the moment the service loop starts, just
  before the startup reset. It stays the same until the process restarts.

#### Scenario: The attributes list the provider's variables

- **WHEN** the system publishes 7Timer!'s health for a pier
- **THEN** the attributes carry `variables` equal to `["seeing", "transparency"]`
- **AND** the attributes carry no `role` key

#### Scenario: The air-quality provider lists variables the timeline does not show

- **WHEN** the system publishes `open_meteo_air_quality`'s health for a pier
- **THEN** the attributes carry `variables` equal to `["aerosol_optical_depth", "pm2_5"]`

### Requirement: A health sensor's attributes describe its latest fetch

Each health sensor's JSON attributes SHALL carry:

- the status of the latest fetch (`ok` or `failed`), or null before the first
  fetch
- the time of the latest fetch, or null before the first fetch
- the error from the latest fetch, or null when it carried none or there has
  been no fetch. A failed fetch always carries one. A successful fetch carries
  one only from the computed source, when one of its variables failed and
  another did not

#### Scenario: A partly failed computation is ok and keeps its error

- **WHEN** the computed source's outcome is successful with the error `transparency: missing input: aerosol_optical_depth`, and the system publishes
- **THEN** the `computed` health sensor's state is the time of that computation
- **AND** its attributes give status `ok`, the error `transparency: missing input: aerosol_optical_depth`, and `inputs` with `seeing` alone

### Requirement: A health sensor's attributes give the issue time of the last success

Each health sensor's JSON attributes SHALL carry the issue time of the data from
the last successful fetch, or null when that fetch gave no issue time or there
has been no success.

#### Scenario: A failed fetch keeps the earlier success

- **WHEN** a provider's fetch for a pier succeeded earlier, and its next fetch fails
- **THEN** that provider's health sensor state is still the time of the earlier success
- **AND** its attributes give status `failed`, the time of the failed fetch, its error, and the issue time from the earlier success

### Requirement: The computed source's health attributes name its inputs

For the computed source only, the health sensor's JSON attributes SHALL carry
`inputs`: the inputs of the last successful computation, as the conditions
capability defines them. It is an object that maps each computed variable that
carried a value to a list of provider keys, or null when there has been no
success. No other provider's attributes carry `inputs`.

#### Scenario: The computed source's health names its inputs

- **WHEN** the computed source succeeds for a pier, with transparency read from `open_meteo` and `open_meteo_air_quality`, and seeing read from `open_meteo_hrrr`, and the system publishes
- **THEN** the `computed` health sensor's attributes carry `inputs` equal to `{"transparency": ["open_meteo", "open_meteo_air_quality"], "seeing": ["open_meteo_hrrr"]}`
- **AND** they give status `ok` and a null error

#### Scenario: Other providers carry no inputs

- **WHEN** the system publishes 7Timer!'s health for a pier
- **THEN** the attributes carry no `inputs` key

### Requirement: A failed fetch leaves the last success's details unchanged

A failed fetch SHALL leave a health sensor's last-success time, its issue time
and the computed source's `inputs` unchanged.

#### Scenario: A failed computation keeps the earlier inputs

- **WHEN** the computed source succeeded earlier with `inputs` `{"seeing": ["open_meteo"]}`, and its next computation fails
- **THEN** the `computed` health sensor's attributes give status `failed` and still carry `inputs` `{"seeing": ["open_meteo"]}`

### Requirement: A health sensor stays available while the process is online

The health sensor SHALL be available whenever the process is online. A failing
provider SHALL NOT make its health sensor unavailable.

#### Scenario: A failing provider keeps its health sensor available

- **WHEN** the process is online and a provider's fetch fails
- **THEN** that provider's health sensor's discovery declares availability from the process status only
- **AND** the sensor stays available

### Requirement: Provider health travels beside the verdict document, not inside it

Health travels beside the verdict document, not inside it. The system SHALL NOT
add health to the verdict document. Publishing health SHALL NOT change the
verdict, score, top-target, rank, narrative, or refresh entities. This entity is
additive: every existing entity, topic, and mapping is unchanged.

#### Scenario: Existing entities and the verdict document are unchanged

- **WHEN** the adapter publishes for a pier with provider health
- **THEN** the verdict, score, top-target, rank, narrative, and refresh entities keep their existing topics, unique identities, and payloads
- **AND** the verdict document contains no health fields

### Requirement: The Cloud cover sensor's state is the current-hour cloud cover

The Cloud cover sensor's state SHALL be the `cloud_cover` of the timeline entry
whose hour contains the document's generation timestamp, written as the document
emits the number. The state is as fresh as the last recompute: it can lag by up
to one recompute interval, and `hour` says which hour it belongs to.

#### Scenario: The state is the current hour's cloud cover

- **WHEN** the adapter publishes a document generated at 23:30 whose timeline has an entry at 23:00 with cloud cover `15.0`
- **THEN** the sensor's state is `15.0`

### Requirement: With no current-hour value, the Cloud cover sensor shows unknown and stays available

When no timeline entry has the hour that contains the document's generation
timestamp, or that entry's `cloud_cover` is null, the Cloud cover sensor's state
SHALL be published as `None`, which Home Assistant shows as unknown, rather than
`0`, an empty value or an earlier value. The sensor SHALL be available exactly
when the process is online, so its attributes, including `forecast`, stay
readable when the current hour has no value.

#### Scenario: A missing or null current hour renders unknown

- **WHEN** the adapter publishes a document generated at 23:30 whose timeline has no entry at 23:00, or whose 23:00 entry has a null cloud cover
- **THEN** the adapter publishes the retained state `None`, rather than `0`, an empty value or an earlier value
- **AND** a retained attributes payload with `hour` null and a `forecast` entry for every timeline hour
- **AND** the sensor's discovery payload makes it available exactly when the process is online, with no condition on the current hour

#### Scenario: An empty timeline renders unknown

- **WHEN** the adapter publishes a document whose timeline is empty
- **THEN** the adapter publishes the retained state `None`
- **AND** the sensor stays available while the process is online

### Requirement: A further timeline sensor is published for each of sixteen keys

On publishing, the system SHALL publish one further timeline sensor per pier, on
the pier's device, for each of these keys: `cloud_low`, `cloud_mid`,
`cloud_high`, `wind_gust`, `seeing`, `transparency`, `sun_altitude`,
`moon_altitude`, `temperature`, `dew_point`, `humidity`, `wind_speed`,
`wind_direction`, `precipitation_probability`, `cloud_cover_min` and
`cloud_cover_max`.

#### Scenario: A timeline sensor's discovery is published

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration for each of the sixteen keys, on the pier's device, enabled by default
- **AND** each discovery topic and unique identity derive from the pier identifier and the key
- **AND** each payload validates against Home Assistant's MQTT discovery schema for a sensor

#### Scenario: The first eight sensors are unchanged by the weather sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, `sun_altitude` and `moon_altitude` sensors keep their existing topics, discovery payloads and unique identities
- **AND** the six weather sensors' messages come after the Moon altitude sensor's in the publish

#### Scenario: The cloud range sensors come last

- **WHEN** the adapter publishes for a pier
- **THEN** the fourteen sensors from `cloud_low` to `precipitation_probability` keep their existing topics, discovery payloads and unique identities
- **AND** the `cloud_cover_min` sensor's messages, then the `cloud_cover_max` sensor's, come after the Precipitation probability sensor's in the publish

### Requirement: A further timeline sensor's discovery is retained and keyed by the pier and the key

Each further timeline sensor's retained discovery payload SHALL be a valid Home
Assistant sensor discovery payload. Its topic and unique identity SHALL derive
from the pier identifier and the key.

#### Scenario: Existing entities are unchanged by the timeline sensors

- **WHEN** the adapter publishes for a pier
- **THEN** the verdict, score, top-target, rank, Cloud cover, narrative, health and refresh entities keep their existing topics, payloads and unique identities
- **AND** re-publishing for the same pier introduces no additional identity for any of the sixteen sensors

## REMOVED Requirements

### Requirement: Per-pier entity auto-discovery

**Reason**: It bundled two behaviors. It is split into "The verdict, score and
refresh entities are announced by discovery" and "Re-publishing for a pier
updates its verdict, score and refresh entities". Its 2 scenarios move word for
word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Verdict state and attributes are exposed

**Reason**: It bundled three behaviors. It is split into "The verdict entity
publishes the verdict and its details", "The verdict attributes leave out only
the timeline" and "The score entity shows the numeric score, or unavailable when
the score is null". Its 4 scenarios move word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Top target is exposed as an entity

**Reason**: It bundled four behaviors. It is split into "The top-target sensor
is announced by discovery", "The top-target sensor shows the top target's name
and the ordered list", "Re-publishing updates the existing top-target sensor"
and "An empty target list makes the top-target sensor unavailable". Its 3
scenarios move word for word. One scenario is added, so each new requirement has
one.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Narrative is exposed as an optional entity

**Reason**: It bundled seven behaviors. It is split into "Disabled narrative
delivery publishes no narrative entity", "A narrative entity left by an earlier
configuration is not removed automatically", "Enabled narrative delivery
announces a narrative sensor", "The narrative prose is published in the
attributes, not the state", "With no narrative, the enabled narrative sensor is
published as unavailable", "A missing or disabled narrative does not hold back
the other entities" and "Re-publishing updates the existing narrative sensor".
Its 5 scenarios move word for word. Two scenarios are added, so each new
requirement has one.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Each rank of the target list is exposed as an entity

**Reason**: It bundled five behaviors. It is split into "A rank sensor is
announced for every rank", "A filled rank sensor shows its target", "A rank with
no target renders unavailable", "Every publish updates every rank sensor" and
"Each rank sensor's discovery is retained and keyed by the pier and the rank".
Its 6 scenarios move word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Provider health is exposed as diagnostic entities

**Reason**: It bundled twelve behaviors. It is split into "Each configured
provider has a health sensor named after it", "A health sensor's discovery marks
it as a diagnostic timestamp sensor", "A health sensor's state is its provider's
last success since the process started", "On startup, provider health is reset
before the process goes online", "A startup health reset cut off by a dropped
connection is published again", "A health sensor's attributes name its provider,
its variables and when tracking started", "A health sensor's attributes describe
its latest fetch", "A health sensor's attributes give the issue time of the last
success", "The computed source's health attributes name its inputs", "A failed
fetch leaves the last success's details unchanged", "A health sensor stays
available while the process is online" and "Provider health travels beside the
verdict document, not inside it". Its 14 scenarios move word for word. One
scenario is added, so each new requirement has one.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The Cloud cover state is the current hour's value

**Reason**: It bundled two behaviors. It is split into "The Cloud cover sensor's
state is the current-hour cloud cover" and "With no current-hour value, the
Cloud cover sensor shows unknown and stays available". Its 3 scenarios move word
for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Each further timeline variable is exposed as an entity

**Reason**: It bundled two behaviors. It is split into "A further timeline
sensor is published for each of sixteen keys" and "A further timeline sensor's
discovery is retained and keyed by the pier and the key". Its 4 scenarios move
word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.
