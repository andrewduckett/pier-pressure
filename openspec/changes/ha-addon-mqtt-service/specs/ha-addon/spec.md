## MODIFIED Requirements

### Requirement: The add-on reads config from its own config folder

The add-on SHALL run the service with the config file `config.yaml` in the
add-on's own config folder. In Home Assistant, the user finds that folder as
`/addon_configs/<repository-id>_pierpressure`. The file SHALL have the same format
as outside Home Assistant. Inside the add-on, the file MAY leave out the MQTT
broker's connection settings, as the requirement "The add-on uses the
Supervisor's MQTT broker when the file names none" describes. The add-on SHALL
offer no options of its own.

#### Scenario: Config file present

- **WHEN** the user has written a valid `config.yaml` in the add-on's config
  folder and starts the add-on
- **THEN** the service loads that file and publishes a verdict for each pier

#### Scenario: Config file missing

- **WHEN** the user starts the add-on before writing `config.yaml`
- **THEN** the add-on stops
- **AND** its log contains a configuration error that names the missing file

#### Scenario: Add-on config mounts the folder

- **WHEN** the test suite reads the add-on config file
- **THEN** it maps `addon_config`
- **AND** it sets the environment variable `PIERPRESSURE_CONFIG` to
  `/config/config.yaml`

## ADDED Requirements

### Requirement: The add-on uses the Supervisor's MQTT broker when the file names none

The add-on SHALL ask Home Assistant's Supervisor for the `mqtt` service, as a
service it wants but does not need. So the add-on SHALL install and start when no
other add-on provides the service.

The connection settings are the broker's host, port, username and password. The
service SHALL take all four from one source:

- When `config.yaml` sets `mqtt.host`, all four SHALL come from the file. The
  service SHALL NOT ask the Supervisor for the broker.
- When `config.yaml` does not set `mqtt.host`, all four SHALL come from the
  Supervisor's `mqtt` service.

`mqtt.discovery_prefix` and `mqtt.base_topic` SHALL always come from the file, or
from their defaults. A file that sets `mqtt.port`, `mqtt.username` or
`mqtt.password` without `mqtt.host` SHALL be rejected with a configuration error
that says to set `mqtt.host` too.

The service SHALL ask the Supervisor only when it runs inside an add-on. Outside an
add-on, `mqtt.host` SHALL stay required, and the service SHALL behave as it did
before this change.

#### Scenario: Mosquitto user leaves out the broker settings

- **WHEN** the Mosquitto add-on provides the `mqtt` service
- **AND** the user's `config.yaml` has no `mqtt:` block
- **THEN** the service connects to the broker host and port the Supervisor gave
- **AND** it logs in with the username and password the Supervisor gave
- **AND** it publishes under the default discovery prefix and base topic

#### Scenario: The file's broker wins

- **WHEN** the Supervisor provides an `mqtt` service
- **AND** the user's `config.yaml` sets `mqtt.host`
- **THEN** the service connects with the host, port, username and password from
  the file
- **AND** it does not ask the Supervisor for the broker

#### Scenario: The file sets only its topics

- **WHEN** the Supervisor provides an `mqtt` service
- **AND** the user's `config.yaml` sets `mqtt.base_topic` but not `mqtt.host`
- **THEN** the service connects with the Supervisor's connection settings
- **AND** it publishes under the file's base topic

#### Scenario: Credentials without a host are rejected

- **WHEN** the user's `config.yaml` sets `mqtt.username` but not `mqtt.host`
- **THEN** the add-on stops
- **AND** its log contains a configuration error that says to set `mqtt.host`

#### Scenario: The log names the broker's source without the password

- **WHEN** the service uses the Supervisor's broker
- **THEN** its log says the broker came from the Supervisor's `mqtt` service, and
  names the host and port
- **AND** the log does not contain the broker password

#### Scenario: Outside an add-on, nothing changes

- **WHEN** the service runs outside an add-on with a `config.yaml` that has no
  `mqtt.host`
- **THEN** it stops with the same configuration error as before this change
- **AND** it does not try to reach the Supervisor

#### Scenario: Add-on config declares the service

- **WHEN** the test suite reads the add-on config file
- **THEN** its `services` list contains `mqtt:want`

### Requirement: The add-on waits a bounded time for the Supervisor's broker

When the service needs the Supervisor's broker and the Supervisor does not provide
it yet, the service SHALL keep asking. A Mosquitto add-on that is still starting
withdraws its service details for a few seconds, so a short wait covers a reboot.
The wait SHALL end no later than 60 seconds after the first request, including
the time of any request still in progress. If the broker's details arrive within
that time, the service SHALL use them and start normally.

These count as "not provided yet": the Supervisor says the service is not enabled,
the request cannot connect or times out, the Supervisor returns a server error, or
the response has no usable host and port.

If the details do not arrive in time, the add-on SHALL stop with an error. The
error SHALL say that no MQTT broker was found. It SHALL tell the user to install
the Mosquitto broker add-on, or to set `mqtt.host` in `config.yaml`.

If the Supervisor refuses the add-on access to the service, the add-on SHALL stop
at once, without waiting. Its error SHALL say that the Supervisor refused access
to the `mqtt` service. It SHALL tell the user to set `mqtt.host` in `config.yaml`,
and to report the problem.

#### Scenario: Mosquitto is still starting

- **WHEN** the service starts while the Supervisor does not yet provide the `mqtt`
  service
- **AND** the service appears within 60 seconds
- **THEN** the service uses the broker it gives and publishes a verdict for each
  pier

#### Scenario: No broker add-on is installed

- **WHEN** the user's `config.yaml` has no `mqtt.host`
- **AND** the Supervisor provides no `mqtt` service for 60 seconds
- **THEN** the add-on stops
- **AND** its log says no MQTT broker was found, and tells the user to install the
  Mosquitto broker add-on or to set `mqtt.host`

#### Scenario: The wait ends on time

- **WHEN** the Supervisor provides no `mqtt` service
- **AND** each request to the Supervisor takes as long as it is allowed
- **THEN** the add-on stops no later than 60 seconds after the first request

#### Scenario: The Supervisor refuses access

- **WHEN** the user's `config.yaml` has no `mqtt.host`
- **AND** the Supervisor refuses the add-on access to the `mqtt` service
- **THEN** the add-on stops at once, without waiting
- **AND** its log says the Supervisor refused access to the `mqtt` service, and
  tells the user to set `mqtt.host` and to report the problem

### Requirement: The add-on refuses a Supervisor broker that requires TLS

PierPressure does not support TLS connections. If the Supervisor's `mqtt` service
says its broker requires TLS, the add-on SHALL stop with an error. The error SHALL
say that the broker requires TLS, which PierPressure does not support. It SHALL tell
the user to set `mqtt.host` and `mqtt.port` in `config.yaml` to a broker listener
that accepts connections without TLS. The service SHALL NOT connect to that broker
without TLS.

#### Scenario: The Supervisor's broker requires TLS

- **WHEN** the user's `config.yaml` has no `mqtt.host`
- **AND** the Supervisor's `mqtt` service says its broker requires TLS
- **THEN** the add-on stops without connecting to the broker
- **AND** its log says the broker requires TLS, which PierPressure does not
  support, and tells the user to set a broker listener without TLS in
  `config.yaml`
