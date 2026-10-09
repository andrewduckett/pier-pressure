## MODIFIED Requirements

### Requirement: Delivery failures are reported, not swallowed

When the MQTT broker is unreachable or a publish fails, the system SHALL report the failure in its log rather than reporting success. A delivery failure SHALL NOT corrupt or partially publish an entity's state such that a stale value is presented as current without indication.

A failed publish SHALL NOT stop the process. The process SHALL keep running, and SHALL keep its interval and refresh command working.

While the process is disconnected from the broker, its entities show as unavailable through the offline last-will. A publish during that time is held for the replay after the reconnect, as the reconnect requirement describes. The disconnect is already logged, so the process SHALL NOT log each held publish.

When the MQTT client refuses a publish for any other reason, the process SHALL log a warning that names the topic. The log line SHALL NOT contain the broker password.

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
reconnect, before step 2.

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
