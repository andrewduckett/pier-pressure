## ADDED Requirements

### Requirement: The process waits for the broker at startup

When the process starts and cannot reach the MQTT broker, it SHALL keep trying
until the broker accepts the connection. It SHALL NOT exit because the broker is
unreachable. This lets the process start before its broker, for example when Home
Assistant OS starts both at once.

The broker counts as unreachable when the connection cannot be opened, or when the
broker refuses it for any reason other than a rejected login. A rejected login is a
refusal because the username or password is wrong, or because the client is not
authorized.

The process SHALL pause between attempts. The first pause SHALL be at least 1
second. Each later pause SHALL double, up to a limit of 120 seconds.

The process SHALL log each failed attempt. The log SHALL name the broker's host and
port, and SHALL NOT contain the broker password.

Until the broker accepts the connection, the process SHALL NOT publish anything.
Once the broker accepts it, the process SHALL start as it does when the broker is
ready at once: it publishes the startup health reset, then its online availability,
then a verdict for each pier.

When the broker rejects the login, the process SHALL stop with an error and SHALL
NOT try again. The error SHALL say that the broker rejected the login, and SHALL
tell the user to check the MQTT username and password. The process SHALL NOT publish
its online availability.

#### Scenario: The broker starts after the process

- **WHEN** the process starts, and the broker cannot be reached for its first three attempts
- **AND** the broker accepts the fourth attempt
- **THEN** the process publishes the startup health reset, then its online availability
- **AND** it publishes a verdict for each pier
- **AND** it does not exit

#### Scenario: Nothing is published while the broker is unreachable

- **WHEN** the process has started and the broker cannot be reached
- **THEN** the process has published no message
- **AND** it has not exited

#### Scenario: The pause between attempts grows to a limit

- **WHEN** the broker cannot be reached for many attempts in a row
- **THEN** the first pause is at least 1 second
- **AND** each later pause is double the one before, up to 120 seconds

#### Scenario: Each failed attempt is logged

- **WHEN** an attempt to reach the broker fails
- **THEN** the log has a line for that attempt that names the broker's host and port
- **AND** the log does not contain the broker password

#### Scenario: A broker that refuses for another reason is tried again

- **WHEN** the broker refuses the connection because it is not ready to serve clients
- **THEN** the process tries again after a pause
- **AND** it does not exit

#### Scenario: A rejected login stops the process

- **WHEN** the broker refuses the connection because the username or password is wrong
- **THEN** the process exits with an error
- **AND** its log says the broker rejected the login, and tells the user to check the MQTT username and password
- **AND** it has not published its online availability

#### Scenario: An unauthorized client stops the process

- **WHEN** the broker refuses the connection because the client is not authorized
- **THEN** the process exits with an error
- **AND** its log says the broker rejected the login
- **AND** it has not published its online availability
