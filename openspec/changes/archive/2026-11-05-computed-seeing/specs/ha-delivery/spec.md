## MODIFIED Requirements

### Requirement: Provider health is exposed as diagnostic entities

On every publish for a pier, the system SHALL publish one health sensor for each
configured conditions provider. Each sensor SHALL be named after its provider, for
example "Open-Meteo health" and "7Timer! health". The system SHALL publish discovery
for every configured provider, including a provider not tried on this publish.

Each health sensor's discovery configuration SHALL mark it as a diagnostic entity and
as a timestamp sensor. It SHALL conform to the repository's discovery schema for a
sensor. It SHALL be published retained to the discovery topic derived from the pier
identifier and the provider. Its unique identity SHALL derive from the pier identifier
and the provider, so re-publishing updates the existing entity rather than creating a
duplicate.

The sensor's state SHALL be the time of the provider's last successful fetch for that
pier. When the provider has not succeeded for that pier since the process started,
the sensor SHALL resolve to unknown. It SHALL NOT show a retained time from before the
restart while the process is online.

On startup, the system SHALL publish every configured provider's health with no
history, for every pier. It SHALL do this before it publishes its online
availability, and before it fetches any conditions or asks for any narrative. This
replaces any retained health from before the restart. If the connection drops
before the reset reaches the broker, the process SHALL NOT exit. It SHALL publish
the reset health again after the reconnect, before it publishes its online
availability.

The sensor's JSON attributes SHALL carry:

- the provider's name
- `variables`: the variables the provider declares, as a list of variable keys in
  the provider's declared order. A variable key need not be a timeline key. It is the same on every publish. There is no
  `role` attribute.
- the time health tracking started: the moment the service loop starts, just before
  the startup reset. It stays the same until the process restarts.
- the status of the latest fetch (`ok` or `failed`), or null before the first fetch
- the time of the latest fetch, or null before the first fetch
- the error from the latest fetch, or null when it carried none or there has been no
  fetch. A failed fetch always carries one. A successful fetch carries one only from
  the computed source, when one of its variables failed and another did not
- the issue time of the data from the last successful fetch, or null when that fetch
  gave no issue time or there has been no success
- for the computed source only, `inputs`: the inputs of the last successful
  computation, as the conditions capability defines them. It is an object that maps
  each computed variable that carried a value to a list of provider keys, or null
  when there has been no success. No other provider's attributes carry `inputs`.

A failed fetch SHALL leave the last-success time, its issue time and the computed
source's `inputs` unchanged.

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
- **AND** each discovery payload validates against the repository's discovery schema for a sensor

#### Scenario: The attributes list the provider's variables

- **WHEN** the system publishes 7Timer!'s health for a pier
- **THEN** the attributes carry `variables` equal to `["seeing", "transparency"]`
- **AND** the attributes carry no `role` key

#### Scenario: The air-quality provider lists variables the timeline does not show

- **WHEN** the system publishes `open_meteo_air_quality`'s health for a pier
- **THEN** the attributes carry `variables` equal to `["aerosol_optical_depth", "pm2_5"]`

#### Scenario: A successful fetch sets the last-success time

- **WHEN** a provider's fetch for a pier succeeds and the system publishes
- **THEN** that provider's health sensor state is the time of that fetch
- **AND** its attributes give status `ok`, the fetch time, a null error, and the issue time of the returned data

#### Scenario: The computed source's health names its inputs

- **WHEN** the computed source succeeds for a pier, with transparency read from `open_meteo` and `open_meteo_air_quality`, and seeing read from `open_meteo_hrrr`, and the system publishes
- **THEN** the `computed` health sensor's attributes carry `inputs` equal to `{"transparency": ["open_meteo", "open_meteo_air_quality"], "seeing": ["open_meteo_hrrr"]}`
- **AND** they give status `ok` and a null error

#### Scenario: A partly failed computation is ok and keeps its error

- **WHEN** the computed source's outcome is successful with the error `transparency: missing input: aerosol_optical_depth`, and the system publishes
- **THEN** the `computed` health sensor's state is the time of that computation
- **AND** its attributes give status `ok`, the error `transparency: missing input: aerosol_optical_depth`, and `inputs` with `seeing` alone

#### Scenario: A failed computation keeps the earlier inputs

- **WHEN** the computed source succeeded earlier with `inputs` `{"seeing": ["open_meteo"]}`, and its next computation fails
- **THEN** the `computed` health sensor's attributes give status `failed` and still carry `inputs` `{"seeing": ["open_meteo"]}`

#### Scenario: Other providers carry no inputs

- **WHEN** the system publishes 7Timer!'s health for a pier
- **THEN** the attributes carry no `inputs` key

#### Scenario: A failed fetch keeps the earlier success

- **WHEN** a provider's fetch for a pier succeeded earlier, and its next fetch fails
- **THEN** that provider's health sensor state is still the time of the earlier success
- **AND** its attributes give status `failed`, the time of the failed fetch, its error, and the issue time from the earlier success

#### Scenario: Startup clears retained health before going online

- **WHEN** the process starts, and the broker holds a retained health state from before the restart
- **THEN** the system publishes each configured provider's health with no history before it publishes its online availability
- **AND** it does so before it fetches any conditions
- **AND** each health sensor's state is published as unknown, with the tracking start time and the provider's variables, and null status, fetch time, error, and issue time
- **AND** the `computed` health sensor's `inputs` is null

#### Scenario: A failed startup reset does not go online

- **WHEN** the broker accepts the first connection
- **AND** the connection drops before the process publishes the startup health reset
- **AND** the broker accepts a new connection
- **THEN** the process does not exit
- **AND** after the reconnect, it publishes each configured provider's health with no history before it publishes its online availability

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
