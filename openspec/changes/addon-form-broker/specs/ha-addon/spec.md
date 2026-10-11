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

When the service uses the form and stops with a broker error, the error SHALL
say that `config.yaml` is not read while the form lists piers. It SHALL tell the
user to set the broker on the Configuration tab, not in `config.yaml`. This
covers the "no MQTT broker was found", "access refused", TLS, MQTT version and
rejected-login errors for a broker from the Supervisor.

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
- **AND** it tells the user to set the broker on the Configuration tab

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
name its host and port. No log line or error message SHALL contain the
password.

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

- **WHEN** the form lists a pier and sets `mqtt.host` and `mqtt.password`
- **THEN** the log says the broker came from the Configuration tab, and names
  the host and port
- **AND** no log line contains the password
