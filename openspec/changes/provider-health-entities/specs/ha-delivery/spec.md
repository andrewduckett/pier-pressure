## ADDED Requirements

### Requirement: Provider health is exposed as diagnostic entities

On every publish for a pier, the system SHALL publish one health sensor for each
configured conditions provider. Each sensor SHALL be named after its provider, for
example "Open-Meteo health" and "7Timer! health". The system SHALL publish discovery
for every configured provider, including a provider not tried on this publish.

Each health sensor's discovery configuration SHALL mark it as a diagnostic entity and
as a timestamp sensor. It SHALL conform to Home Assistant's MQTT discovery schema for
a sensor. It SHALL be published retained to the discovery topic derived from the pier
identifier and the provider. Its unique identity SHALL derive from the pier identifier
and the provider, so re-publishing updates the existing entity rather than creating a
duplicate.

The sensor's state SHALL be the time of the provider's last successful fetch for that
pier. When the provider has not succeeded for that pier since the process started,
the sensor SHALL resolve to unknown. It SHALL NOT show a retained time from before the
restart.

On startup, the system SHALL publish every configured provider's health with no
history, for every pier. It SHALL do this before it fetches any conditions or asks
for any narrative. This replaces any retained health from before the restart. If
that publish fails, the process SHALL exit, so its last-will message marks it
offline.

The sensor's JSON attributes SHALL carry:

- the provider's role (`base` or `secondary`)
- the status of the latest fetch (`ok` or `failed`), or null before the first fetch
- the time of the latest fetch, or null before the first fetch
- the error from the latest failed fetch, or null when the latest fetch succeeded or
  there has been no fetch
- the issue time of the data from the last successful fetch, or null when there is none

A failed fetch SHALL leave the last-success time and its issue time unchanged.

The health sensor SHALL be available whenever the process is online. A failing
provider SHALL NOT make its health sensor unavailable. Health SHALL be held in memory
only, and the system SHALL NOT keep it across restarts.

Health travels beside the verdict document, not inside it. The system SHALL NOT add
health to the verdict document. Publishing health SHALL NOT change the verdict,
score, top-target, rank, narrative, or refresh entities. This entity is additive:
every existing entity, topic, and mapping is unchanged.

#### Scenario: Health discovery is published per provider

- **WHEN** the adapter publishes for a pier with two configured conditions providers
- **THEN** it publishes a retained discovery configuration for one health sensor per provider on topics derived from the pier identifier and the provider
- **AND** each discovery payload marks the sensor as diagnostic and as a timestamp
- **AND** each discovery payload validates against Home Assistant's MQTT discovery schema for a sensor

#### Scenario: A successful fetch sets the last-success time

- **WHEN** a provider's fetch for a pier succeeds and the system publishes
- **THEN** that provider's health sensor state is the time of that fetch
- **AND** its attributes give status `ok`, the fetch time, a null error, and the issue time of the returned data

#### Scenario: A failed fetch keeps the earlier success

- **WHEN** a provider's fetch for a pier succeeded earlier, and its next fetch fails
- **THEN** that provider's health sensor state is still the time of the earlier success
- **AND** its attributes give status `failed`, the time of the failed fetch, its error, and the issue time from the earlier success

#### Scenario: Startup clears retained health before any fetch

- **WHEN** the process starts, and the broker holds a retained health state from before the restart
- **THEN** the system publishes each configured provider's health with no history before it fetches any conditions
- **AND** each health sensor's state is published as unknown, with null status, fetch time, error, and issue time

#### Scenario: No success since a restart resolves to unknown

- **WHEN** the process restarts, and a provider's first fetch for a pier fails
- **THEN** the system publishes so that provider's health sensor resolves to unknown
- **AND** no last-success time from before the restart is shown as current

#### Scenario: A failing provider keeps its health sensor available

- **WHEN** the process is online and a provider's fetch fails
- **THEN** that provider's health sensor's discovery declares availability from the process status only
- **AND** the sensor stays available

#### Scenario: Existing entities and the verdict document are unchanged

- **WHEN** the adapter publishes for a pier with provider health
- **THEN** the verdict, score, top-target, rank, narrative, and refresh entities keep their existing topics, unique identities, and payloads
- **AND** the verdict document contains no health fields
