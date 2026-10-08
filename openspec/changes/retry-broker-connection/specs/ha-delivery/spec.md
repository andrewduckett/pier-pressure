## ADDED Requirements

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
