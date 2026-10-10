## MODIFIED Requirements

### Requirement: Availability reflects process liveness via last-will

The system SHALL register a retained Last-Will-and-Testament that marks the pier's entities unavailable if the process disconnects unexpectedly, and SHALL publish a retained online availability while running. Because both the online message and the last-will are retained, a subscriber connecting after the process has died SHALL read the offline state rather than a stale online state.

A clean disconnect does not trigger the last-will. So when the process stops on purpose while connected, it SHALL publish a retained offline availability before it disconnects. A planned stop includes an interrupt, a termination signal, and an unexpected error in the service loop. The process SHALL wait a bounded time for the broker to confirm the offline message, then SHALL disconnect and exit even if the broker has not confirmed it. When the process stops while disconnected, it SHALL NOT publish the offline message, because the broker has already sent the last-will.

#### Scenario: A retained offline last-will is registered on connect

- **WHEN** the process connects to the broker
- **THEN** it registers a last-will message on the availability topic with an offline payload and the retain flag set

#### Scenario: A retained online availability is published while running

- **WHEN** the process is running and connected
- **THEN** an online availability message has been published to the availability topic with the retain flag set

#### Scenario: A planned stop publishes a retained offline before disconnecting

- **WHEN** the process stops on purpose while connected to the broker
- **THEN** it publishes an offline availability message to the availability topic with the retain flag set
- **AND** it publishes that message before it disconnects

#### Scenario: A stop while disconnected publishes nothing

- **WHEN** the process stops on purpose while its connection to the broker is down
- **THEN** it publishes no availability message
- **AND** it exits

#### Scenario: An unconfirmed offline message does not block the stop

- **WHEN** the process stops on purpose and the broker does not confirm the offline message within the wait
- **THEN** the process disconnects and exits

#### Scenario: A termination signal stops the process cleanly

- **WHEN** the process receives a termination signal while running
- **THEN** it publishes a retained offline availability, disconnects, and exits with status 0
