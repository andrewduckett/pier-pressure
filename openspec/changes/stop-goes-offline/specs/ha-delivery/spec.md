## MODIFIED Requirements

### Requirement: Availability reflects process liveness via last-will

The system SHALL register a retained Last-Will-and-Testament on the availability topic. The last-will marks the pier's entities unavailable if the process disconnects unexpectedly.

The system SHALL publish a retained online availability while running.

Both the online message and the last-will are retained. So after the process dies unexpectedly, a subscriber that connects later SHALL read the offline state rather than a stale online state.

A clean disconnect does not trigger the last-will, so a planned stop SHALL attempt to publish the offline state itself:

- A planned stop is an interrupt, a termination signal, or an unexpected error in the service loop, at any time after the broker accepts the connection.
- When the process stops on purpose while connected, it SHALL attempt a retained offline availability publish at QoS 1 before it disconnects.
- The process SHALL wait at most two seconds for the broker to confirm the offline message.
- The process SHALL then disconnect and exit, whether or not the broker confirmed the message.
- When the process stops while its connection is down, it SHALL NOT publish the offline message. The broker sends the last-will when it notices the lost connection.

The offline publish is a best effort. If the broker never receives it, the broker keeps the last availability it holds.

#### Scenario: A retained offline last-will is registered on connect

- **WHEN** the process connects to the broker
- **THEN** it registers a last-will message on the availability topic with an offline payload and the retain flag set

#### Scenario: A retained online availability is published while running

- **WHEN** the process is running and connected
- **THEN** an online availability message has been published to the availability topic with the retain flag set

#### Scenario: A planned stop publishes a retained offline before disconnecting

- **WHEN** the process stops on purpose while connected to the broker
- **THEN** it publishes an offline availability message to the availability topic at QoS 1 with the retain flag set
- **AND** it publishes that message before it disconnects

#### Scenario: A stop while disconnected publishes nothing

- **WHEN** the process stops on purpose while its connection to the broker is down
- **THEN** it publishes no availability message
- **AND** it exits

#### Scenario: An unconfirmed offline message does not block the stop

- **WHEN** the process stops on purpose and the broker does not confirm the offline message
- **THEN** the process waits at most two seconds for the confirmation
- **AND** it disconnects and exits

#### Scenario: A termination signal stops the process cleanly

- **WHEN** the process receives a termination signal at any time after the broker accepts the connection
- **THEN** it publishes a retained offline availability at QoS 1, disconnects, and exits with status 0
