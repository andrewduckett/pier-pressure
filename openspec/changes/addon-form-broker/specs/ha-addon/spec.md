## MODIFIED Requirements

### Requirement: The add-on offers a Configuration form for the interval and piers

The add-on SHALL declare a Configuration form in Home Assistant with three
settings:

- `interval_seconds`: the recompute interval in seconds, a whole number of at
  least 1. Its default SHALL be 900.
- `piers`: a list of piers. Each pier SHALL have an `id` (text), a `latitude`
  (from −90 to 90 degrees), a `longitude` (from −180 to 180 degrees) and an
  `elevation_m` (metres). The default SHALL be an empty list.
- `mqtt`: the broker, as a block of four optional fields. The default SHALL be
  an empty block.

The `mqtt` block SHALL have these fields:

- `host`: the broker's host name or address, as text.
- `port`: the broker's port, from 1 to 65535. It SHALL have no default on the
  form.
- `username`: the login name, as text.
- `password`: the login password, in a field that hides its value.

Each pier SHALL also have two optional horizon fields:

- `min_altitude`: a flat horizon floor, from 0 to 90 degrees.
- `horizon_points`: horizon points as text. On save, the form SHALL accept empty
  or blank text, or text that opens with two square brackets and closes with
  two, as a list of pairs does. Spaces may sit between the brackets and around
  the text. It SHALL reject any other text.

Each pier SHALL also have four optional equipment fields. On save, the form
SHALL accept a number of at least 0 in each. The service then rejects 0, as
described in "The form sets each pier's equipment":

- `equipment_focal_length_mm`: the telescope's focal length, in millimetres.
- `equipment_sensor_width_mm`: the camera sensor's width, in millimetres.
- `equipment_sensor_height_mm`: the camera sensor's height, in millimetres.
- `equipment_reducer`: a focal reducer or barlow factor, with no unit.

These names SHALL match the names of the same settings in `config.yaml`. The
horizon and equipment fields are the exception, because a form cannot nest a
`horizon` or `equipment` block inside a pier. `min_altitude` SHALL hold the
value of the file's `horizon.min_altitude`, and `horizon_points` the value of
`horizon.points`. Each `equipment_<name>` field SHALL hold the value of the
file's `equipment.<name>`. Each form field SHALL have a label and a description
in English, and each description of a number SHALL name its unit or say it has
none.

#### Scenario: Add-on config declares the form

- **WHEN** the test suite reads the add-on config file
- **THEN** its `options` set `interval_seconds` to 900, `piers` to an empty
  list, and `mqtt` to an empty block
- **AND** its `schema` declares `interval_seconds` as a whole number, and `piers`
  as a list whose items have `id`, `latitude`, `longitude` and `elevation_m`
- **AND** each pier item has an optional `min_altitude` from 0 to 90 and an
  optional `horizon_points`
- **AND** each pier item has optional `equipment_focal_length_mm`,
  `equipment_sensor_width_mm`, `equipment_sensor_height_mm` and
  `equipment_reducer`, each a number of at least 0
- **AND** its `schema` declares `mqtt` with an optional text `host`, an optional
  `port`, an optional text `username`, and an optional `password` of the
  password type

#### Scenario: The save check on horizon points

- **WHEN** the test suite applies the schema's check for `horizon_points` to
  sample text
- **THEN** it accepts `[[0, 10], [90, 25]]`, empty text and blank text
- **AND** it rejects `[0, 10], [90, 25]` and `[[0, 10]] extra`

#### Scenario: Every form field has a label

- **WHEN** the test suite reads the add-on's English translation file
- **THEN** it gives a name and a description for `interval_seconds`, `piers`, and
  each field of a pier, including `min_altitude`, `horizon_points` and the four
  equipment fields
- **AND** it gives a name and a description for `mqtt` and each of its four
  fields

### Requirement: The add-on reads the Configuration form before the config file

Inside an add-on, the service SHALL read the values the user saved on the
Configuration form at startup. The rule for which source it uses is:

- When the form lists at least one pier, the service SHALL take the interval,
  the piers and the broker from the form only. It SHALL NOT read settings from
  `config.yaml`.
- When the form lists no piers, the service SHALL read `config.yaml` as the
  requirement "The add-on reads config from its own config folder" describes. It
  SHALL ignore the form's interval and broker.

When the service uses the form, it SHALL choose the broker as the requirement
"The form sets the broker" describes. The discovery prefix and base topic SHALL
take their defaults.

When the service uses the form and stops with an error about the Supervisor's
broker, the error SHALL say that `config.yaml` is not read while the form lists
piers. It SHALL tell the user to set the broker on the Configuration tab. It
SHALL NOT name `config.yaml` as the place to set the broker. This covers the "no
MQTT broker was found", "access refused", TLS, MQTT version and rejected-login
errors.

The service SHALL check each pier from the form exactly as it checks a pier from
`config.yaml`. A pier that fails the check SHALL be skipped with a logged error,
and the other piers SHALL still be published.

When the service uses the form and `config.yaml` also exists, the service SHALL
log a warning that names the ignored file. It SHALL then start as usual.

When the form lists no piers and `config.yaml` is missing, the add-on SHALL stop.
Its configuration error SHALL name the missing file, and SHALL tell the user to
add a pier on the Configuration tab.

Outside an add-on, the service SHALL NOT read the form's values, and SHALL behave
as it did before this change.

#### Scenario: Form setup gives a verdict without a file

- **WHEN** the user saves an interval and one pier on the Configuration tab
- **AND** the form sets no broker host
- **AND** the add-on's config folder holds no `config.yaml`
- **AND** the Supervisor provides an `mqtt` service
- **THEN** the service connects to the Supervisor's broker
- **AND** it publishes a verdict for that pier under the default discovery prefix
  and base topic
- **AND** it recomputes at the interval from the form

#### Scenario: An empty form falls back to the file

- **WHEN** the form lists no piers
- **AND** the add-on's config folder holds a valid `config.yaml`
- **THEN** the service loads that file and publishes a verdict for each of its
  piers

#### Scenario: An empty form's broker is not used

- **WHEN** the form lists no piers and sets `mqtt.host` to `broker.lan`
- **AND** the add-on's config folder holds a valid `config.yaml` with no
  `mqtt.host`
- **AND** the Supervisor provides an `mqtt` service
- **THEN** the service connects to the Supervisor's broker, not to `broker.lan`

#### Scenario: The form wins over an existing file

- **WHEN** the form lists the pier `backyard`
- **AND** the add-on's config folder holds a `config.yaml` that lists the pier
  `roof`
- **THEN** the service publishes a verdict for `backyard` only
- **AND** its log contains a warning that names `/config/config.yaml` as ignored

#### Scenario: A bad pier in the saved form values is skipped

- **WHEN** the saved form values list two piers, and one has a latitude of 95
- **THEN** the service logs an error that names the skipped pier
- **AND** it publishes a verdict for the other pier

The Supervisor normally refuses to save such a value. The service still checks
each pier, because it does not rely on the Supervisor's check.

#### Scenario: A form user's broker error does not point only to the file

- **WHEN** the form lists a pier and sets no broker host
- **AND** the Supervisor provides no `mqtt` service within the wait
- **THEN** the add-on stops
- **AND** its log says no MQTT broker was found
- **AND** it says `config.yaml` is not read while the form lists piers
- **AND** it tells the user to set `mqtt.host` on the Configuration tab
- **AND** it does not name `config.yaml` as the place to set `mqtt.host`

#### Scenario: Nothing is set up

- **WHEN** the form lists no piers
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on stops
- **AND** its log contains a configuration error that names
  `/config/config.yaml` and tells the user to add a pier on the Configuration
  tab

#### Scenario: Outside an add-on, the form is not read

- **WHEN** the service runs outside an add-on
- **THEN** it does not read the form's values
- **AND** it loads `config.yaml` exactly as before this change

### Requirement: The add-on uses the Supervisor's MQTT broker when the file names none

The add-on SHALL ask Home Assistant's Supervisor for the `mqtt` service, as a
service it wants but does not need. So the add-on SHALL install and start when no
other add-on provides the service.

This requirement applies when the service uses settings from `config.yaml`. When
the service uses the Configuration form, the requirement "The form sets the
broker" applies instead.

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

The service SHALL send its requests, and the Supervisor's token, straight to the
Supervisor. It SHALL NOT send them through a proxy, even when the container's
environment names one.

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

#### Scenario: Proxy settings do not reach the token

- **WHEN** the container's environment sets `HTTP_PROXY` or `ALL_PROXY`
- **AND** the service asks the Supervisor for the broker
- **THEN** the request goes straight to the Supervisor, not through the proxy

#### Scenario: Add-on config declares the service

- **WHEN** the test suite reads the add-on config file
- **THEN** its `services` list contains `mqtt:want`

### Requirement: The add-on waits a bounded time for the Supervisor's broker

When the service needs the Supervisor's broker and the Supervisor does not provide
it yet, the service SHALL keep asking. A Mosquitto add-on that is still starting
withdraws its service details for a few seconds, so a short wait covers a reboot.
The service SHALL start no new request later than 60 seconds after the first one.
Each request SHALL have a timeout of no more than 5 seconds. If a request started
within those 60 seconds returns usable broker details, the service SHALL
use them and start normally.

These cases count as "not provided yet":

- The Supervisor says the service is not enabled.
- The request cannot connect, or it times out.
- The Supervisor returns a server error.
- The response has no usable host and port.

If no request started within those 60 seconds returns usable details, the add-on
SHALL stop with an error. The
error SHALL say that no MQTT broker was found. It SHALL tell the user to install
the Mosquitto broker add-on, or to set `mqtt.host` where the settings come from.

If the Supervisor refuses the add-on access to the service, the add-on SHALL stop
at once, without waiting. Its error SHALL say that the Supervisor refused access
to the `mqtt` service. It SHALL tell the user to set `mqtt.host` where the
settings come from, and to report the problem.

"Where the settings come from" is `config.yaml` when the service uses the file,
and the Configuration tab when it uses the form.

#### Scenario: Mosquitto is still starting

- **WHEN** the service starts while the Supervisor does not yet provide the `mqtt`
  service
- **AND** a request started within 60 seconds of the first returns usable broker
  details
- **THEN** the service uses the broker it gives and publishes a verdict for each
  pier

#### Scenario: No broker add-on is installed

- **WHEN** the user's `config.yaml` has no `mqtt.host`
- **AND** no request started within 60 seconds of the first returns usable broker
  details
- **THEN** the add-on stops
- **AND** its log says no MQTT broker was found, and tells the user to install the
  Mosquitto broker add-on or to set `mqtt.host`

#### Scenario: The wait ends on time

- **WHEN** the Supervisor provides no `mqtt` service
- **AND** each request to the Supervisor times out
- **THEN** the service starts no request later than 60 seconds after the first
- **AND** the add-on stops no later than 65 seconds after the first request

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
the user to set `mqtt.host` and `mqtt.port` to a broker listener that accepts
connections without TLS. It SHALL name `config.yaml` when the service uses the
file, and the Configuration tab when it uses the form. The service SHALL NOT connect to that broker
without TLS.

#### Scenario: The Supervisor's broker requires TLS

- **WHEN** the user's `config.yaml` has no `mqtt.host`
- **AND** the Supervisor's `mqtt` service says its broker requires TLS
- **THEN** the add-on stops without connecting to the broker
- **AND** its log says the broker requires TLS, which PierPressure does not
  support, and tells the user to set a broker listener without TLS in
  `config.yaml`

#### Scenario: A form user's TLS error names the Configuration tab

- **WHEN** the form lists a pier and sets no `mqtt.host`
- **AND** the Supervisor's `mqtt` service says its broker requires TLS
- **THEN** the add-on stops without connecting to the broker
- **AND** its log tells the user to set a broker listener without TLS on the
  Configuration tab, and does not name `config.yaml` as the place to set it

### Requirement: The add-on refuses a Supervisor broker that needs another MQTT version

PierPressure speaks MQTT version 3.1.1. If the Supervisor's `mqtt` service names
any other protocol version, the add-on SHALL stop with an error. The error SHALL
name the version the broker asked for, and say that PierPressure supports only
3.1.1. It SHALL tell the user to set `mqtt.host` and `mqtt.port` to a broker that
accepts 3.1.1. It SHALL name `config.yaml` when the service uses the file, and
the Configuration tab when it uses the form. A response that names no protocol SHALL count as
3.1.1, which is the Supervisor's default.

#### Scenario: The Supervisor's broker asks for MQTT 3.1

- **WHEN** the user's `config.yaml` has no `mqtt.host`
- **AND** the Supervisor's `mqtt` service names protocol `3.1`
- **THEN** the add-on stops without connecting to the broker
- **AND** its log names protocol `3.1`, and says PierPressure supports only 3.1.1

## ADDED Requirements

### Requirement: The form sets the broker

When the service uses the form, it SHALL take the broker's four connection
settings from one source, as it does for `config.yaml`:

- When the form sets `mqtt.host`, the host, port, username and password SHALL
  all come from the form. The service SHALL NOT ask the Supervisor for the
  broker. A port the form does not set SHALL be 1883.
- When the form does not set `mqtt.host`, all four SHALL come from the
  Supervisor's `mqtt` service.

A form field that is empty or blank SHALL count as not set. A form that sets
`mqtt.port`, `mqtt.username` or `mqtt.password` without `mqtt.host` SHALL be
rejected with the same configuration error that `config.yaml` gets. The error
SHALL say to set `mqtt.host` too.

When the broker rejects a login from the form, the error SHALL tell the user to
check the username and password. It SHALL NOT tell the user to restart the
Mosquitto add-on.

The log SHALL say that the broker came from the Configuration tab, and SHALL
name its host and port. No log line or error message SHALL contain the value of
the password field.

#### Scenario: The form's broker is used

- **WHEN** the form lists a pier and sets `mqtt.host` to `broker.lan`,
  `mqtt.port` to 1884, `mqtt.username` to `pier`, and `mqtt.password`
- **THEN** the service connects to `broker.lan` on port 1884
- **AND** it logs in with the username `pier` and the form's password
- **AND** it does not ask the Supervisor for the broker

#### Scenario: The form's broker uses port 1883 by default

- **WHEN** the form lists a pier and sets `mqtt.host` but not `mqtt.port`
- **THEN** the service connects to that host on port 1883

#### Scenario: Blank broker fields count as not set

- **WHEN** the form lists a pier and sets `mqtt.host`
- **AND** its `mqtt.username` and `mqtt.password` are empty text
- **THEN** the service connects to that host without a username or password

#### Scenario: Credentials on the form without a host are rejected

- **WHEN** the form lists a pier and sets `mqtt.username` but not `mqtt.host`
- **THEN** the add-on stops without asking the Supervisor for the broker
- **AND** its log contains a configuration error that says to set `mqtt.host`

#### Scenario: A rejected login from the form points to the form's login

- **WHEN** the form lists a pier and sets `mqtt.host`
- **AND** the broker rejects the login
- **THEN** the add-on stops
- **AND** its log tells the user to check the username and password
- **AND** it does not tell the user to restart the Mosquitto add-on

#### Scenario: The log names the form as the broker's source

- **WHEN** the form lists a pier, sets `mqtt.host` to `broker.lan`, and sets
  `mqtt.password` to `pw-8c41f2`
- **THEN** the log says the broker came from the Configuration tab, and names
  `broker.lan` and port 1883
- **AND** no log line contains `pw-8c41f2`

#### Scenario: A rejected login does not reveal the form's password

- **WHEN** the form lists a pier, sets `mqtt.host`, and sets `mqtt.password` to
  `pw-8c41f2`
- **AND** the broker rejects the login
- **THEN** no log line or error message contains `pw-8c41f2`
