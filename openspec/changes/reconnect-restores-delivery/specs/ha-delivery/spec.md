## ADDED Requirements

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
   attributes, narrative and provider health, exactly as it last published them.
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

This requirement covers an outage during which the process publishes nothing.
What happens to a publish during an outage is outside this requirement.

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
