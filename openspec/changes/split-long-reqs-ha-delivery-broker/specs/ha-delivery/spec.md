## ADDED Requirements

### Requirement: The process publishes a verdict at startup and on an interval

The delivery process SHALL run persistently rather than as a one-shot. It SHALL
publish a verdict on startup and republish on a configurable interval so the
displayed state does not silently go stale as the day and forecast move. The
process SHALL NOT depend on Home Assistant being available in order to stay
current.

#### Scenario: State is published on startup

- **WHEN** the delivery process starts with a valid configuration
- **THEN** it publishes a verdict for the configured pier without any external trigger

#### Scenario: State refreshes on the configured interval

- **WHEN** the configured interval elapses with no external trigger
- **THEN** the pier's entities reflect a newer verdict document with a later generation timestamp

### Requirement: Discovery, state, attributes and availability are published retained

Discovery configuration, state, attributes, and availability SHALL be published
with the retain flag set, so a Home Assistant restart re-reads the last known
verdict and availability without waiting for the next recompute.

#### Scenario: Discovery, state, and availability are published retained

- **WHEN** the adapter publishes for a pier
- **THEN** the discovery configuration, state, attributes, and availability messages are all published with the retain flag set
- **AND** the availability message reflects the process being online

### Requirement: The process registers a retained offline last-will

The system SHALL register a retained Last-Will-and-Testament on the availability
topic. The last-will marks the pier's entities unavailable if the process
disconnects unexpectedly.

Both the online message and the last-will are retained. So after the process
dies unexpectedly, a subscriber that connects later SHALL read the offline state
rather than a stale online state.

#### Scenario: A retained offline last-will is registered on connect

- **WHEN** the process connects to the broker
- **THEN** it registers a last-will message on the availability topic with an offline payload and the retain flag set

### Requirement: The process publishes a retained online availability while running

The system SHALL publish a retained online availability while running.

#### Scenario: A retained online availability is published while running

- **WHEN** the process is running and connected
- **THEN** an online availability message has been published to the availability topic with the retain flag set

### Requirement: A planned stop publishes a retained offline availability

A clean disconnect does not trigger the last-will, so a planned stop SHALL
attempt to publish the offline state itself. A planned stop is an interrupt, a
termination signal, or an unexpected error in the service loop, at any time after
the broker accepts the connection.

When the process stops on purpose while connected, it SHALL attempt a retained
offline availability publish at QoS 1 before it disconnects.

#### Scenario: A planned stop publishes a retained offline before disconnecting

- **WHEN** the process stops on purpose while connected to the broker
- **THEN** it publishes an offline availability message to the availability topic at QoS 1 with the retain flag set
- **AND** it publishes that message before it disconnects

#### Scenario: A termination signal stops the process cleanly

- **WHEN** the process receives a termination signal at any time after the broker accepts the connection
- **THEN** it publishes a retained offline availability at QoS 1, disconnects, and exits with status 0

### Requirement: A planned stop waits at most two seconds for the offline message

When the process stops on purpose while connected, it SHALL wait at most two
seconds for the broker to confirm the offline message. The process SHALL then disconnect and
exit, whether or not the broker confirmed the message.

The offline publish is a best effort. If the broker never receives it, the
broker keeps the last availability it holds.

#### Scenario: An unconfirmed offline message does not block the stop

- **WHEN** the process stops on purpose and the broker does not confirm the offline message
- **THEN** the process waits at most two seconds for the confirmation
- **AND** it disconnects and exits

### Requirement: A planned stop while disconnected publishes no offline message

When the process stops on purpose while its connection is down, it SHALL NOT
publish the offline message. The broker sends the last-will when it notices the
lost connection.

#### Scenario: A stop while disconnected publishes nothing

- **WHEN** the process stops on purpose while its connection to the broker is down
- **THEN** it publishes no availability message
- **AND** it exits

### Requirement: A delivery failure is logged, not reported as success

When the MQTT broker is unreachable or a publish fails, the system SHALL report
the failure in its log rather than reporting success. A delivery failure SHALL
NOT corrupt or partially publish an entity's state such that a stale value is
presented as current without indication.

#### Scenario: Unreachable broker is reported as a failure

- **WHEN** the adapter attempts to publish and the broker cannot be reached
- **THEN** the log reports that the connection to the broker was lost
- **AND** the process does not report the publish as successful

### Requirement: A failed publish does not stop the process

A failed publish SHALL NOT stop the process. The process SHALL keep running, and
SHALL keep its interval and refresh command working.

#### Scenario: A publish during an outage does not stop the process

- **WHEN** the process loses its connection to the broker
- **AND** the configured interval elapses before the broker accepts a new connection
- **THEN** the process recomputes the verdict for each pier
- **AND** it does not exit

### Requirement: A publish held while disconnected is not logged

While the process is disconnected from the broker, its entities show as
unavailable through the offline last-will. A publish during that time is held
for the replay after the reconnect, as the requirement
"While disconnected, the process holds its publishes for the replay" describes.
The disconnect is already logged, so the process SHALL NOT log each held publish.

#### Scenario: A publish held during an outage logs no warning

- **WHEN** the process is disconnected from the broker
- **AND** it publishes a verdict for a pier and its online availability before the broker accepts a new connection
- **THEN** the log has no warning for those publishes

### Requirement: A refused publish is logged once as a warning

When the MQTT client refuses a publish for a reason other than a lost
connection, the process SHALL log a warning that names the topic. While
refusals continue, the process SHALL log only the first as a warning, until a
publish succeeds. The log line SHALL NOT contain the broker password.

#### Scenario: A refused publish is logged and the process keeps running

- **WHEN** the process is connected to the broker
- **AND** the MQTT client refuses a publish for a reason other than a lost connection
- **THEN** the log has a warning that names the topic
- **AND** the process does not exit
- **AND** the next interval publishes a verdict for each pier

### Requirement: A refused online availability is sent again with the next verdict

When the MQTT client refuses the online availability, the process SHALL publish
it again with the next verdict it publishes.

#### Scenario: A refused online availability is published again

- **WHEN** the MQTT client refuses the online availability
- **AND** the process then publishes a verdict for a pier
- **THEN** the process publishes its online availability again, with the retain flag set

### Requirement: The process keeps trying to connect to the broker at startup

When the process starts, it SHALL keep trying to connect to the MQTT broker until
the broker accepts the connection. It SHALL NOT exit because an attempt fails.
This lets the process start before its broker, for example when Home Assistant
OS starts both at once.

This requirement starts once the process knows the broker's settings. Finding
the Supervisor's broker inside the add-on has its own bounded wait, which the
`ha-addon` capability describes.

#### Scenario: The broker starts after the process

- **WHEN** the process starts, and its first three attempts fail because it cannot open a network connection
- **AND** the broker accepts the fourth attempt
- **THEN** the process publishes the startup health reset, then its online availability
- **AND** it publishes a verdict for each pier
- **AND** it does not exit

### Requirement: After a temporary failure at startup, the process pauses and tries again

An attempt to connect to the broker fails in one of three ways:

- The process cannot open a network connection to the broker.
- The broker closes the connection before it answers.
- The broker answers with a refusal.

A rejected login is a refusal that says the username or password is wrong, or
that the client is not authorized. Every other failure is a temporary failure.
After a temporary failure, the process SHALL pause, then try again.

#### Scenario: A broker that is not ready is tried again

- **WHEN** the broker refuses the connection because it is not ready to serve clients
- **THEN** the process tries again after a pause
- **AND** it does not exit

#### Scenario: A broker that closes the connection is tried again

- **WHEN** the broker closes the connection before it answers
- **THEN** the process tries again after a pause
- **AND** it does not exit

### Requirement: The pauses between connection attempts grow from 1 to 120 seconds

No pause between connection attempts SHALL be shorter than 1 second. The pauses
SHALL grow after repeated failures, and no pause SHALL be longer than 120
seconds.

#### Scenario: The pauses grow to a limit

- **WHEN** many attempts in a row fail
- **THEN** no pause between attempts is shorter than 1 second
- **AND** later pauses are longer than the first
- **AND** no pause is longer than 120 seconds

### Requirement: The process may try once more at once with one detail changed

The process MAY answer two refusals by trying again at once with one detail
changed. When the broker does not support the MQTT version, the process MAY try
an older version. When the broker rejects an empty client identifier, the
process MAY try a generated one. Each of these immediate tries SHALL happen at
most once while the process runs. Each SHALL count as part of the attempt it
follows, not as a new attempt, so it needs no pause and no log line of its own.

#### Scenario: A failure during an immediate try is tried again

- **WHEN** the broker refuses the connection because it does not support the MQTT version
- **AND** the immediate try with an older version cannot open a network connection
- **THEN** the log has a line for that attempt that names the broker's host and port
- **AND** the process tries again after a pause
- **AND** it does not exit

### Requirement: Each failed connection attempt is logged without the password

The process SHALL log each failed attempt to connect. The log line SHALL name the
broker's host and port, and SHALL NOT contain the broker password.

#### Scenario: Each failed attempt is logged

- **WHEN** an attempt fails for any of the three reasons
- **THEN** the log has a line for that attempt that names the broker's host and port
- **AND** the log does not contain the broker password

### Requirement: The process publishes only once the broker accepts the connection

Until the broker accepts the connection, the process SHALL NOT publish anything.
Once the broker accepts it, the process SHALL start as it does when the broker
accepts the first attempt. It publishes the startup health reset, then its
online availability, then a verdict for each pier.

#### Scenario: Nothing is published while attempts fail

- **WHEN** the process has started, and every attempt so far has failed
- **THEN** the process has published no message
- **AND** it has not exited

### Requirement: A rejected login at startup stops the process

After a rejected login at startup, the process SHALL stop with an error and
SHALL NOT try again. The error SHALL say that the broker rejected the login. The
process SHALL NOT publish its online availability.

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

### Requirement: The process keeps trying to reconnect while it runs

When the process loses its connection to the MQTT broker while it runs, it SHALL
keep trying to reconnect. The process SHALL try to reconnect with the same pauses as at startup. No
pause SHALL be shorter than 1 second or longer than 120 seconds. The process
SHALL keep trying for as long as it runs, whichever way an attempt fails. This
includes a failure during an immediate try, which the requirement
"The process may try once more at once with one detail changed" describes.

#### Scenario: A failed immediate try during a reconnect is tried again

- **WHEN** the process loses its connection while it runs
- **AND** the broker refuses the next attempt because it does not support the MQTT version
- **AND** the immediate try with an older version cannot open a network connection
- **THEN** the log has a line for that attempt that names the broker's host and port
- **AND** the process tries again after a pause
- **AND** it restores its delivery once the broker accepts a connection

### Requirement: After a reconnect, the process subscribes again and republishes its last state

Once the broker accepts a new connection, the process SHALL restore its delivery
without a restart. After each reconnect, the process SHALL do three things:

1. Subscribe again to every pier's refresh command topic.
2. For each pier, publish again its last discovery configs, verdict state,
   attributes, narrative and provider health, each with the latest payload the
   process produced for it. This includes a payload the process held during the
   outage.
3. Then publish its retained online availability.

#### Scenario: Refresh works again after a reconnect

- **WHEN** the process loses its connection to the broker while it runs
- **AND** the broker accepts a new connection
- **AND** a message then arrives on a pier's refresh command topic
- **THEN** the system recomputes and republishes for that pier

#### Scenario: Entities come back online after a reconnect

- **WHEN** the process loses its connection, and the broker publishes the offline last-will
- **AND** the broker accepts a new connection
- **THEN** the process publishes its online availability to the availability topic with the retain flag set

#### Scenario: A broker that lost its retained messages gets them back

- **WHEN** the broker restarts without keeping its retained messages
- **AND** the process reconnects
- **THEN** before the next interval, the process publishes every discovery config and state topic it had published for each pier
- **AND** each of those publishes has the payload it last had and the retain flag set

### Requirement: After a reconnect, the online availability follows the republished state

After a reconnect, to publish a message means to hand it to the MQTT client for
sending. A published message is not proof that the broker received it.

After a reconnect, the process SHALL publish the online availability only after
it has published each pier's last state again. A pier the process has not yet
published has nothing to publish again. This order covers the messages the
process publishes after the reconnect.

#### Scenario: The last state is published again before online

- **WHEN** the process has published a verdict for each pier
- **AND** it loses its connection, and the broker accepts a new connection
- **THEN** for each pier, the process publishes the same discovery configs, verdict state, attributes, narrative and provider health it last published, each retained
- **AND** it publishes its online availability only after all of them

### Requirement: The MQTT client may send a message again after a reconnect

The MQTT client MAY first send again a message it was still sending
when the connection dropped, such as an earlier online availability. The process
SHALL NOT hold such a message back.

The process learns of a drop only after the MQTT client detects it. The MQTT
client MAY send a message it received before then again after the reconnect,
before or after the republish of each pier's last state. When it comes after,
that topic shows the older payload until the process next publishes it.

#### Scenario: A message still being sent at the drop does not change the order

- **WHEN** the process publishes its online availability, and the connection drops before the broker acknowledges it
- **AND** the broker accepts a new connection
- **THEN** after the reconnect, the process publishes the state for each pier, then its online availability
- **AND** it does not withhold or remove the message the MQTT client was still sending

### Requirement: A refused refresh subscription is logged with its topic

This requirement assumes that the broker lets the process subscribe to the same
topics after a reconnect as before. When the broker refuses a subscription, or the MQTT client
cannot send it, the process SHALL log a warning that names the topic. This
applies at startup and after each reconnect.

#### Scenario: A refused subscription is logged

- **WHEN** the broker accepts a new connection
- **AND** it refuses the subscription to a pier's refresh command topic
- **THEN** the log has a warning that names that topic
- **AND** the process keeps running

### Requirement: A reconnect triggers no new verdict

A reconnect SHALL NOT trigger a new verdict. The process SHALL NOT compute a
verdict or fetch conditions because of a reconnect. The configured interval and
the refresh command keep the verdict fresh, as before.

#### Scenario: A reconnect computes no new verdict

- **WHEN** the process reconnects
- **THEN** it fetches no conditions and computes no verdict because of the reconnect
- **AND** each republished verdict carries the same generation timestamp as before the outage

### Requirement: A reconnect does not change the startup order

A reconnect is any accepted connection after the first one. The first accepted
connection is not a reconnect. A reconnect SHALL NOT change
the startup order: the startup health reset, then the online availability, then
a verdict for each pier.

#### Scenario: The first connection is not a reconnect

- **WHEN** the broker accepts the process's first connection
- **THEN** the process publishes the startup health reset, then its online availability, then a verdict for each pier
- **AND** it publishes its online availability only once at startup

#### Scenario: A reconnect during startup keeps the startup order

- **WHEN** the broker accepts the first connection
- **AND** the connection drops and the broker accepts a new one, before the process publishes the startup health reset
- **THEN** the process publishes the startup health reset, then its online availability, then a verdict for each pier
- **AND** it then publishes that same health and those verdicts again, then its online availability again

### Requirement: The outage and each reconnect are logged without the password

The process SHALL log when it loses the connection, each failed attempt to
reconnect, and each reconnect. Each log line SHALL name the broker's host and
port, and SHALL NOT contain the broker password.

#### Scenario: The outage is logged

- **WHEN** the process loses its connection, fails two attempts to reconnect, and then reconnects
- **THEN** the log has a line for the lost connection, a line for each failed attempt, and a line for the reconnect
- **AND** each line names the broker's host and port
- **AND** the log does not contain the broker password

### Requirement: A rejected login during a reconnect is logged, and the process keeps trying

When the broker rejects the login during a reconnect, the process SHALL NOT
exit. It SHALL log an error that says the broker rejected the login, with the
same advice it gives for a rejected login at startup. It SHALL keep trying to
reconnect, with the same pauses.

#### Scenario: A login rejected during a reconnect does not stop the process

- **WHEN** the broker rejects the login during a reconnect
- **THEN** the log has an error that says the broker rejected the login, with the advice the process gives at startup
- **AND** the process does not exit
- **AND** it tries to reconnect again after a pause
- **AND** it publishes its online availability once the broker accepts a connection

### Requirement: While disconnected, the process holds its publishes for the replay

The process MAY publish during an outage: on the interval, after a refresh
command, or for the startup health reset. While the process knows it is
disconnected, it SHALL hold each such message for the republish after the
reconnect instead of handing it to the MQTT client. It SHALL also hold its online
availability, which it publishes after that republish.

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

### Requirement: An error about the mqtt block shows none of its values

When the process rejects the `mqtt` block, the error and the log SHALL NOT
contain any value from that block. This SHALL hold for every source of settings:
`config.yaml`, the add-on's Configuration form, or both combined.

This requirement covers errors about the `mqtt` block only. An error about a pier
still shows that pier's values, so a user can find a bad latitude or horizon.

#### Scenario: The add-on's combined settings do not show the password

- **WHEN** the add-on combines its Configuration form with `config.yaml`
- **AND** the form sets a password
- **AND** the combined `mqtt` block fails validation, or the form and the file
  both set a broker setting
- **THEN** the add-on stops with a configuration error
- **AND** neither the error nor the log contains the password

### Requirement: An error about the mqtt block names no key the block does not define

When the process rejects the `mqtt` block from any source of settings, the error
and the log SHALL NOT contain the name of a key that the block does not define,
because a user can type a secret where a key name belongs. For such a key, the
error SHALL say that the block holds a setting it does not know, and list the
settings the block defines.

#### Scenario: An unknown key in the mqtt block is not named

- **WHEN** the process loads `config.yaml` on its own, outside the add-on
- **AND** the `mqtt` block holds a key it does not define, such as
  `pasword: hunter2`, or a bare key `hunter2`
- **THEN** the process stops with a configuration error that says the `mqtt`
  block holds a setting it does not know
- **AND** the error lists the settings the `mqtt` block defines
- **AND** neither the error nor the log contains `pasword` or `hunter2`

#### Scenario: An unknown key with a value is not named in the add-on

- **WHEN** the add-on combines its Configuration form with `config.yaml`
- **AND** the file's `mqtt` block holds a key it does not define, with a value,
  such as `pasword: hunter2`
- **THEN** the add-on stops with a configuration error that says the `mqtt`
  block holds a setting it does not know
- **AND** neither the error nor the log contains `pasword` or `hunter2`

### Requirement: An error about the mqtt block says what is wrong

An error about the `mqtt` block SHALL still say what is wrong:

- For a defined setting, it SHALL name the setting, such as `mqtt.port`, and
  state the rule the value broke.
- For an `mqtt` value that is not a mapping, it SHALL say that `mqtt` must be a
  mapping of settings.

#### Scenario: A password that is not text is rejected without its value

- **WHEN** `config.yaml` sets `mqtt.password` to a number, such as `98765`
- **THEN** the process stops with a configuration error that names
  `mqtt.password`
- **AND** neither the error nor the log contains `98765`

#### Scenario: An mqtt block that is not a mapping does not show its value

- **WHEN** `config.yaml` sets `mqtt` to a list or text that holds a secret
- **THEN** the process stops with a configuration error that says `mqtt` must be
  a mapping of settings
- **AND** neither the error nor the log contains the secret

### Requirement: The broker password is masked once the settings are valid

Once the configuration is valid, the process SHALL show the broker password as a
mask whenever it prints or logs its settings. It SHALL use the password's value
only to log in to the broker.

#### Scenario: A valid password is masked when the settings are printed

- **WHEN** the configuration is valid and sets a broker password
- **AND** the process prints or logs its settings, at any stage of loading them
- **THEN** the output does not contain the password

## REMOVED Requirements

### Requirement: Persistent operation with periodic republish

**Reason**: It bundled two behaviors. It is split into "The process publishes a
verdict at startup and on an interval" and "Discovery, state, attributes and
availability are published retained". Its 3 scenarios move word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Availability reflects process liveness via last-will

**Reason**: It bundled five behaviors. It is split into "The process registers a
retained offline last-will", "The process publishes a retained online
availability while running", "A planned stop publishes a retained offline
availability", "A planned stop waits at most two seconds for the offline
message" and "A planned stop while disconnected publishes no offline message".
Its 6 scenarios move word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Delivery failures are reported, not swallowed

**Reason**: It bundled five behaviors. It is split into "A delivery failure is
logged, not reported as success", "A failed publish does not stop the process",
"A publish held while disconnected is not logged", "A refused publish is logged
once as a warning" and "A refused online availability is sent again with the
next verdict". Its 4 scenarios move word for word, and "A publish held during an
outage logs no warning" is added, so that each new requirement has a scenario.
Its pointer to "the reconnect requirement" now names "While disconnected, the
process holds its publishes for the replay".

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The process waits for the broker at startup

**Reason**: It bundled seven behaviors. It is split into "The process keeps
trying to connect to the broker at startup", "After a temporary failure at
startup, the process pauses and tries again", "The pauses between connection
attempts grow from 1 to 120 seconds", "The process may try once more at once
with one detail changed", "Each failed connection attempt is logged without the
password", "The process publishes only once the broker accepts the connection"
and "A rejected login at startup stops the process". Its 9 scenarios move word
for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The process restores delivery after a reconnect

**Reason**: It bundled ten behaviors. It is split into "The process keeps trying
to reconnect while it runs", "After a reconnect, the process subscribes again
and republishes its last state", "After a reconnect, the online availability
follows the republished state", "The MQTT client may send a message again after
a reconnect", "A refused refresh subscription is logged with its topic", "A
reconnect triggers no new verdict", "A reconnect does not change the startup
order", "The outage and each reconnect are logged without the password", "A
rejected login during a reconnect is logged, and the process keeps trying" and
"While disconnected, the process holds its publishes for the replay". Its 14
scenarios move word for word. Its pointer to "the startup requirement" now names
"The process may try once more at once with one detail changed".

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: An error about the broker settings shows none of their text

**Reason**: It bundled four behaviors. It is split into "An error about the mqtt
block shows none of its values", "An error about the mqtt block names no key the
block does not define", "An error about the mqtt block says what is wrong" and
"The broker password is masked once the settings are valid". Its 6 scenarios
move word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.
