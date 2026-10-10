# ha-delivery Specification

## Purpose

The ha-delivery capability publishes a produced verdict document into Home Assistant over MQTT discovery, so per-pier entities appear on a dashboard with no hand-written YAML, stay current from a persistent process, and can be refreshed on demand and used as automation triggers for push notifications. Delivery consumes an already-produced verdict document; it never computes one.

Scenarios below are written against the system's observable MQTT output (topics, retain flags, and payloads), because that is what PierPressure controls and can assert mechanically. Home Assistant's own reaction to a valid discovery payload (actually rendering an entity) is confirmed by a documented manual acceptance check, not asserted as if PierPressure produced it.

## Requirements

### Requirement: Delivery consumes a produced verdict document

The delivery adapter SHALL take an already-produced verdict document as its input and publish it. It SHALL NOT compute, alter, or reinterpret the verdict, score, confidence, or reasons. This keeps the decision core independent of, and testable without, the delivery path.

#### Scenario: Adapter publishes the document it is given

- **WHEN** the adapter is given a verdict document and asked to publish
- **THEN** the values published to the state and attributes topics match the input document's verdict, score, confidence, and reasons exactly

#### Scenario: Verdict production does not depend on delivery

- **WHEN** the delivery path is unavailable
- **THEN** a verdict document can still be produced by the core

### Requirement: Per-pier entity auto-discovery

On publishing, the system SHALL publish MQTT discovery configuration messages for at least a verdict entity, a score entity, and a refresh control for the pier, so Home Assistant auto-creates them without manual configuration. Each discovery payload SHALL conform to Home Assistant's MQTT discovery schema for its entity type (sensor, sensor, button), SHALL be published to the discovery topic derived from the pier identifier, and SHALL be published with the retain flag set. Each entity's unique identity SHALL derive from the pier identifier, so re-publishing for the same pier updates the existing entities rather than creating duplicates.

#### Scenario: Discovery configuration is published on first publish

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration message for a verdict sensor, a score sensor, and a refresh button, each on the discovery topic derived from the pier identifier
- **AND** each discovery payload validates against Home Assistant's MQTT discovery schema for its entity type

#### Scenario: Re-publishing targets the same identities, not duplicates

- **WHEN** the adapter publishes twice for the same pier identifier
- **THEN** both publishes use the same discovery topics and the same entity unique identities
- **AND** no additional verdict, score, or refresh discovery identity is introduced

### Requirement: Verdict state and attributes are exposed

The verdict entity's state SHALL be published as the verdict value (`GO`, `MAYBE`, or `NO-GO`). The reasons, the score, the confidence (band and value), the night window, the pier identifier, and the generation timestamp SHALL be published as a JSON attributes payload so a dashboard card can display them. The score entity's state SHALL be the numeric score. The score entity's discovery configuration SHALL declare availability such that the score is available only when the process is online AND the score is non-null; when the score is null the score entity SHALL resolve to unavailable rather than a numeric value such as `0`.

#### Scenario: Verdict state and attributes are published from the document

- **WHEN** a verdict document with verdict `MAYBE`, a confidence, and a set of reasons is published
- **THEN** `MAYBE` is published to the verdict state topic
- **AND** a JSON attributes payload is published containing the reasons, score, confidence, night window, pier identifier, and generation timestamp

#### Scenario: Null score is published as null, with availability requiring non-null

- **WHEN** a verdict document whose score is null is published
- **THEN** the published attributes payload contains the `score` key explicitly set to null (present, not omitted)
- **AND** the score entity's published discovery payload declares an availability that requires a non-null score, so Home Assistant renders it unavailable rather than as `0`

### Requirement: Persistent operation with periodic republish

The delivery process SHALL run persistently rather than as a one-shot. It SHALL publish a verdict on startup and republish on a configurable interval so the displayed state does not silently go stale as the day and forecast move. Discovery configuration, state, attributes, and availability SHALL be published with the retain flag set, so a Home Assistant restart re-reads the last known verdict and availability without waiting for the next recompute. The process SHALL NOT depend on Home Assistant being available in order to stay current.

#### Scenario: State is published on startup

- **WHEN** the delivery process starts with a valid configuration
- **THEN** it publishes a verdict for the configured pier without any external trigger

#### Scenario: State refreshes on the configured interval

- **WHEN** the configured interval elapses with no external trigger
- **THEN** the pier's entities reflect a newer verdict document with a later generation timestamp

#### Scenario: Discovery, state, and availability are published retained

- **WHEN** the adapter publishes for a pier
- **THEN** the discovery configuration, state, attributes, and availability messages are all published with the retain flag set
- **AND** the availability message reflects the process being online

### Requirement: Availability reflects process liveness via last-will

The system SHALL register a retained Last-Will-and-Testament that marks the pier's entities unavailable if the process disconnects unexpectedly, and SHALL publish a retained online availability while running. Because both the online message and the last-will are retained, a subscriber connecting after the process has died SHALL read the offline state rather than a stale online state.

#### Scenario: A retained offline last-will is registered on connect

- **WHEN** the process connects to the broker
- **THEN** it registers a last-will message on the availability topic with an offline payload and the retain flag set

#### Scenario: A retained online availability is published while running

- **WHEN** the process is running and connected
- **THEN** an online availability message has been published to the availability topic with the retain flag set

### Requirement: On-demand refresh via a show-me-now control

The system SHALL publish the refresh control as an actionable Home Assistant entity (a button) and SHALL subscribe to a command topic that the control publishes to. When a message arrives on that command topic, the system SHALL recompute and republish immediately for the pier, producing a verdict document with a current generation timestamp. This gives the user a "show me now" action from the dashboard without waiting for the interval.

#### Scenario: A command on the refresh topic triggers an immediate republish

- **WHEN** a message is received on the pier's refresh command topic
- **THEN** the system recomputes and republishes for the pier
- **AND** the republished document carries a generation timestamp at or after the moment the command was received

#### Scenario: Refresh works independently of the interval

- **WHEN** a refresh command is received before the configured interval has elapsed
- **THEN** the entities update immediately rather than waiting for the next interval tick

#### Scenario: A refresh arriving during a recompute is not lost

- **WHEN** a refresh command arrives while a recompute is already in progress
- **THEN** a further recompute and republish occurs after the in-progress one completes

### Requirement: Verdict is usable as a notification trigger

The published verdict entity SHALL expose the verdict as a discrete, watchable state that distinguishes `NO-GO` from a not-`NO-GO` result, so a Home Assistant automation can trigger a push notification when tonight is worth setting up. Because state is republished on startup, on interval, and on demand, an automation firing at a chosen time reads the current verdict.

#### Scenario: The published verdict state is a discrete value distinguishing no-go

- **WHEN** a verdict document is published
- **THEN** the value published to the verdict state topic is exactly one of `GO`, `MAYBE`, or `NO-GO`
- **AND** the `NO-GO` value is distinct from `GO` and `MAYBE`, so a Home Assistant automation can branch on it by equality

### Requirement: Delivery failures are reported, not swallowed

When the MQTT broker is unreachable or a publish fails, the system SHALL report the failure in its log rather than reporting success. A delivery failure SHALL NOT corrupt or partially publish an entity's state such that a stale value is presented as current without indication.

A failed publish SHALL NOT stop the process. The process SHALL keep running, and SHALL keep its interval and refresh command working.

While the process is disconnected from the broker, its entities show as unavailable through the offline last-will. A publish during that time is held for the replay after the reconnect, as the reconnect requirement describes. The disconnect is already logged, so the process SHALL NOT log each held publish.

When the MQTT client refuses a publish for any other reason, the process SHALL log a warning that names the topic. While refusals continue, the process SHALL log only the first as a warning, until a publish succeeds. The log line SHALL NOT contain the broker password.

When the MQTT client refuses the online availability, the process SHALL publish it again with the next verdict it publishes.

#### Scenario: A refused online availability is published again

- **WHEN** the MQTT client refuses the online availability
- **AND** the process then publishes a verdict for a pier
- **THEN** the process publishes its online availability again, with the retain flag set

#### Scenario: Unreachable broker is reported as a failure

- **WHEN** the adapter attempts to publish and the broker cannot be reached
- **THEN** the log reports that the connection to the broker was lost
- **AND** the process does not report the publish as successful

#### Scenario: A publish during an outage does not stop the process

- **WHEN** the process loses its connection to the broker
- **AND** the configured interval elapses before the broker accepts a new connection
- **THEN** the process recomputes the verdict for each pier
- **AND** it does not exit

#### Scenario: A refused publish is logged and the process keeps running

- **WHEN** the process is connected to the broker
- **AND** the MQTT client refuses a publish for a reason other than a lost connection
- **THEN** the log has a warning that names the topic
- **AND** the process does not exit
- **AND** the next interval publishes a verdict for each pier

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

- the provider's role (`base` or `secondary`)
- the time health tracking started: the moment the service loop starts, just before
  the startup reset. It stays the same until the process restarts.
- the status of the latest fetch (`ok` or `failed`), or null before the first fetch
- the time of the latest fetch, or null before the first fetch
- the error from the latest failed fetch, or null when the latest fetch succeeded or
  there has been no fetch
- the issue time of the data from the last successful fetch, or null when that fetch
  gave no issue time or there has been no success

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
- **AND** each discovery payload validates against the repository's discovery schema for a sensor

#### Scenario: A successful fetch sets the last-success time

- **WHEN** a provider's fetch for a pier succeeds and the system publishes
- **THEN** that provider's health sensor state is the time of that fetch
- **AND** its attributes give status `ok`, the fetch time, a null error, and the issue time of the returned data

#### Scenario: A failed fetch keeps the earlier success

- **WHEN** a provider's fetch for a pier succeeded earlier, and its next fetch fails
- **THEN** that provider's health sensor state is still the time of the earlier success
- **AND** its attributes give status `failed`, the time of the failed fetch, its error, and the issue time from the earlier success

#### Scenario: Startup clears retained health before going online

- **WHEN** the process starts, and the broker holds a retained health state from before the restart
- **THEN** the system publishes each configured provider's health with no history before it publishes its online availability
- **AND** it does so before it fetches any conditions
- **AND** each health sensor's state is published as unknown, with the tracking start time, and null status, fetch time, error, and issue time

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

### Requirement: The process waits for the broker at startup

When the process starts, it SHALL keep trying to connect to the MQTT broker until
the broker accepts the connection. It SHALL NOT exit because an attempt fails. This
lets the process start before its broker, for example when Home Assistant OS
starts both at once.

This requirement starts once the process knows the broker's settings. Finding the
Supervisor's broker inside the add-on has its own bounded wait, which the
`ha-addon` capability describes.

An attempt fails in one of three ways:

- The process cannot open a network connection to the broker.
- The broker closes the connection before it answers.
- The broker answers with a refusal.

A rejected login is a refusal that says the username or password is wrong, or that
the client is not authorized. Every other failure is a temporary failure.

The process MAY answer two refusals by trying again at once with one detail
changed. When the broker does not support the MQTT version, the process MAY try an
older version. When the broker rejects an empty client identifier, the process MAY
try a generated one. Each of these immediate tries SHALL happen at most once while
the process runs. Each SHALL count as part of the attempt it follows, not as a new
attempt, so it needs no pause and no log line of its own.

After a temporary failure, the process SHALL pause, then try again. No pause SHALL
be shorter than 1 second. The pauses SHALL grow after repeated failures, and no
pause SHALL be longer than 120 seconds.

The process SHALL log each failed attempt. The log line SHALL name the broker's
host and port, and SHALL NOT contain the broker password.

Until the broker accepts the connection, the process SHALL NOT publish anything.
Once the broker accepts it, the process SHALL start as it does when the broker
accepts the first attempt. It publishes the startup health reset, then its online
availability, then a verdict for each pier.

After a rejected login, the process SHALL stop with an error and SHALL NOT try
again. The error SHALL say that the broker rejected the login. The process SHALL
NOT publish its online availability.

#### Scenario: The broker starts after the process

- **WHEN** the process starts, and its first three attempts fail because it cannot open a network connection
- **AND** the broker accepts the fourth attempt
- **THEN** the process publishes the startup health reset, then its online availability
- **AND** it publishes a verdict for each pier
- **AND** it does not exit

#### Scenario: Nothing is published while attempts fail

- **WHEN** the process has started, and every attempt so far has failed
- **THEN** the process has published no message
- **AND** it has not exited

#### Scenario: The pauses grow to a limit

- **WHEN** many attempts in a row fail
- **THEN** no pause between attempts is shorter than 1 second
- **AND** later pauses are longer than the first
- **AND** no pause is longer than 120 seconds

#### Scenario: Each failed attempt is logged

- **WHEN** an attempt fails for any of the three reasons
- **THEN** the log has a line for that attempt that names the broker's host and port
- **AND** the log does not contain the broker password

#### Scenario: A broker that is not ready is tried again

- **WHEN** the broker refuses the connection because it is not ready to serve clients
- **THEN** the process tries again after a pause
- **AND** it does not exit

#### Scenario: A broker that closes the connection is tried again

- **WHEN** the broker closes the connection before it answers
- **THEN** the process tries again after a pause
- **AND** it does not exit

#### Scenario: A failure during an immediate try is tried again

- **WHEN** the broker refuses the connection because it does not support the MQTT version
- **AND** the immediate try with an older version cannot open a network connection
- **THEN** the log has a line for that attempt that names the broker's host and port
- **AND** the process tries again after a pause
- **AND** it does not exit

#### Scenario: A wrong username or password stops the process

- **WHEN** the broker refuses the connection because the username or password is wrong
- **THEN** the process exits with an error
- **AND** its log says the broker rejected the login, and tells the user to check the MQTT username and password
- **AND** it has not published its online availability

#### Scenario: An unauthorized client stops the process

- **WHEN** the broker refuses the connection because the client is not authorized
- **THEN** the process exits with an error
- **AND** its log says the broker rejected the login, and tells the user to check the MQTT user's permissions on the broker
- **AND** it has not published its online availability

### Requirement: The process restores delivery after a reconnect

When the process loses its connection to the MQTT broker while it runs, it SHALL
keep trying to reconnect. Once the broker accepts a new connection, the process
SHALL restore its delivery without a restart. A reconnect is any accepted
connection after the first one.

The process SHALL try to reconnect with the same pauses as at startup. No pause
SHALL be shorter than 1 second or longer than 120 seconds. The process SHALL keep
trying for as long as it runs, whichever way an attempt fails. This includes a
failure during an immediate try with one detail changed, as the startup
requirement describes.

After each reconnect, the process SHALL do three things:

1. Subscribe again to every pier's refresh command topic.
2. For each pier, publish again its last discovery configs, verdict state,
   attributes, narrative and provider health, each with the latest payload the
   process produced for it. This includes a payload the process held during the
   outage.
3. Then publish its retained online availability.

In this requirement, to publish a message means to hand it to the MQTT client for
sending. A published message is not proof that the broker received it.

The process SHALL publish the online availability only after it has published the
state in step 2. A pier the process has not yet published has nothing to publish
again in step 2.

This order covers the messages the process publishes after the reconnect. The
MQTT client MAY first send again a message it was still sending when the
connection dropped, such as an earlier online availability. The process does not
hold such a message back.

This requirement assumes that the broker lets the process subscribe to the same
topics after a reconnect as before. When the broker refuses a subscription, or the
MQTT client cannot send it, the process SHALL log a warning that names the topic.
This applies at startup and after each reconnect.

A reconnect SHALL NOT trigger a new verdict. The process SHALL NOT compute a
verdict or fetch conditions because of a reconnect. The configured interval and
the refresh command keep the verdict fresh, as before.

The first accepted connection is not a reconnect. A reconnect SHALL NOT change the
startup order: the startup health reset, then the online availability, then a
verdict for each pier.

The process SHALL log when it loses the connection, each failed attempt to
reconnect, and each reconnect. Each log line SHALL name the broker's host and
port, and SHALL NOT contain the broker password.

When the broker rejects the login during a reconnect, the process SHALL NOT exit.
It SHALL log an error that says the broker rejected the login, with the same
advice it gives for a rejected login at startup. It SHALL keep trying to
reconnect, with the same pauses.

The process MAY publish during an outage: on the interval, after a refresh
command, or for the startup health reset. While the process knows it is
disconnected, it SHALL hold each such message for step 2 instead of handing it to
the MQTT client. It SHALL also hold its online availability, which step 3 then
publishes. The process learns of a drop only after the MQTT client detects it.
The MQTT client MAY send a message it received before then again after the
reconnect, before or after step 2. When it comes after, that topic shows the
older payload until the process next publishes it.

#### Scenario: Refresh works again after a reconnect

- **WHEN** the process loses its connection to the broker while it runs
- **AND** the broker accepts a new connection
- **AND** a message then arrives on a pier's refresh command topic
- **THEN** the system recomputes and republishes for that pier

#### Scenario: Entities come back online after a reconnect

- **WHEN** the process loses its connection, and the broker publishes the offline last-will
- **AND** the broker accepts a new connection
- **THEN** the process publishes its online availability to the availability topic with the retain flag set

#### Scenario: The last state is published again before online

- **WHEN** the process has published a verdict for each pier
- **AND** it loses its connection, and the broker accepts a new connection
- **THEN** for each pier, the process publishes the same discovery configs, verdict state, attributes, narrative and provider health it last published, each retained
- **AND** it publishes its online availability only after all of them

#### Scenario: A message still being sent at the drop does not change the order

- **WHEN** the process publishes its online availability, and the connection drops before the broker acknowledges it
- **AND** the broker accepts a new connection
- **THEN** after the reconnect, the process publishes the state for each pier, then its online availability
- **AND** it does not withhold or remove the message the MQTT client was still sending

#### Scenario: A refused subscription is logged

- **WHEN** the broker accepts a new connection
- **AND** it refuses the subscription to a pier's refresh command topic
- **THEN** the log has a warning that names that topic
- **AND** the process keeps running

#### Scenario: A broker that lost its retained messages gets them back

- **WHEN** the broker restarts without keeping its retained messages
- **AND** the process reconnects
- **THEN** before the next interval, the process publishes every discovery config and state topic it had published for each pier
- **AND** each of those publishes has the payload it last had and the retain flag set

#### Scenario: A reconnect computes no new verdict

- **WHEN** the process reconnects
- **THEN** it fetches no conditions and computes no verdict because of the reconnect
- **AND** each republished verdict carries the same generation timestamp as before the outage

#### Scenario: The first connection is not a reconnect

- **WHEN** the broker accepts the process's first connection
- **THEN** the process publishes the startup health reset, then its online availability, then a verdict for each pier
- **AND** it publishes its online availability only once at startup

#### Scenario: A reconnect during startup keeps the startup order

- **WHEN** the broker accepts the first connection
- **AND** the connection drops and the broker accepts a new one, before the process publishes the startup health reset
- **THEN** the process publishes the startup health reset, then its online availability, then a verdict for each pier
- **AND** it then publishes that same health and those verdicts again, then its online availability again

#### Scenario: A failed immediate try during a reconnect is tried again

- **WHEN** the process loses its connection while it runs
- **AND** the broker refuses the next attempt because it does not support the MQTT version
- **AND** the immediate try with an older version cannot open a network connection
- **THEN** the log has a line for that attempt that names the broker's host and port
- **AND** the process tries again after a pause
- **AND** it restores its delivery once the broker accepts a connection

#### Scenario: The outage is logged

- **WHEN** the process loses its connection, fails two attempts to reconnect, and then reconnects
- **THEN** the log has a line for the lost connection, a line for each failed attempt, and a line for the reconnect
- **AND** each line names the broker's host and port
- **AND** the log does not contain the broker password

#### Scenario: A login rejected during a reconnect does not stop the process

- **WHEN** the broker rejects the login during a reconnect
- **THEN** the log has an error that says the broker rejected the login, with the advice the process gives at startup
- **AND** the process does not exit
- **AND** it tries to reconnect again after a pause
- **AND** it publishes its online availability once the broker accepts a connection

#### Scenario: State published during an outage is restored after the reconnect

- **WHEN** the process loses its connection to the broker
- **AND** the configured interval elapses, and the process recomputes the verdict for each pier
- **AND** the broker accepts a new connection
- **THEN** for each pier, the process publishes the verdict state and attributes from that recompute, each retained
- **AND** it publishes its online availability only after all of them
- **AND** it has not exited

#### Scenario: Nothing is handed to the MQTT client while the process knows it is disconnected

- **WHEN** the process has logged that it lost its connection
- **AND** it recomputes the verdict for a pier before the broker accepts a new connection
- **THEN** it hands no message for that pier to the MQTT client until the broker accepts a new connection
