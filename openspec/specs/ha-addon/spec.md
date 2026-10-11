# ha-addon Specification

## Purpose

The ha-addon capability lets a Home Assistant OS user install and run PierPressure
as a Home Assistant add-on (also called an app). The add-on runs the released
image. The user sets it up on the add-on's Configuration form, or with their own
config file. Its behaviour of its own is to read that form before the file, and
to use the broker from the Home Assistant Supervisor's `mqtt` service when the
settings name none.

## Requirements

### Requirement: The repository is an add-on repository

The PierPressure GitHub repository SHALL be a valid Home Assistant add-on
repository. It SHALL hold one add-on with the slug `pierpressure`. A user SHALL be
able to add the repository URL in Home Assistant and see PierPressure in the add-on
store.

#### Scenario: Add the repository by URL

- **WHEN** a Home Assistant OS user adds
  `https://github.com/andrewduckett/pier-pressure` as an add-on repository
- **THEN** the add-on store lists a PierPressure add-on from that repository

#### Scenario: Add-on files are valid

- **WHEN** the test suite reads the repository file and the add-on config file
- **THEN** both parse as YAML
- **AND** the add-on config sets `name`, `version`, `slug`, `description`, `arch`
  and `image`, with `slug` equal to `pierpressure`

### Requirement: The add-on runs the released image

The add-on SHALL run the published release image
`ghcr.io/andrewduckett/pier-pressure`. Its `version` SHALL be a release version,
so Home Assistant pulls the image tag with that version. Home Assistant SHALL NOT
build the image on the user's machine.

#### Scenario: Install pulls the pinned release

- **WHEN** a user installs the add-on while its version is `2026.10.0`
- **THEN** Home Assistant pulls `ghcr.io/andrewduckett/pier-pressure:2026.10.0`
- **AND** the add-on log's first line contains `2026.10.0`

#### Scenario: Add-on version is a release version

- **WHEN** the test suite reads the add-on config file
- **THEN** its `version` matches the release format `YYYY.M.N`
- **AND** its `image` is `ghcr.io/andrewduckett/pier-pressure`, with no tag and no
  architecture placeholder

### Requirement: The add-on supports the image's platforms

The add-on SHALL declare exactly the architectures that the release image is built
for: `amd64` for `linux/amd64` and `aarch64` for `linux/arm64`.

#### Scenario: Architectures match the release build

- **WHEN** the test suite compares the add-on's `arch` list with the platforms the
  release workflow builds
- **THEN** each release platform has its add-on architecture, and the add-on lists
  no other architecture

### Requirement: The add-on reads config from its own config folder

When the Configuration form lists no piers, the add-on SHALL run the service with
the config file `config.yaml` in the add-on's own config folder. The requirement
"The add-on reads the Configuration form before the config file" describes when
the form is used instead. In Home Assistant, the user finds that folder as
`/addon_configs/<repository-id>_pierpressure`. The file SHALL have the same format
as outside Home Assistant. Inside the add-on, the file MAY leave out the MQTT
broker's connection settings, as the requirement "The add-on uses the
Supervisor's MQTT broker when the file names none" describes.

#### Scenario: Config file present

- **WHEN** the form lists no piers
- **AND** the user has written a valid `config.yaml` in the add-on's config
  folder and starts the add-on
- **THEN** the service loads that file and publishes a verdict for each pier

#### Scenario: Config file missing

- **WHEN** the form lists no piers
- **AND** the user starts the add-on before writing `config.yaml`
- **THEN** the add-on stops
- **AND** its log contains a configuration error that names the missing file

#### Scenario: Add-on config mounts the folder

- **WHEN** the test suite reads the add-on config file
- **THEN** it maps `addon_config`
- **AND** it sets the environment variable `PIERPRESSURE_CONFIG` to
  `/config/config.yaml`

### Requirement: The add-on offers a Configuration form for the interval and piers

The add-on SHALL declare a Configuration form in Home Assistant with two
settings:

- `interval_seconds`: the recompute interval in seconds, a whole number of at
  least 1. Its default SHALL be 900.
- `piers`: a list of piers. Each pier SHALL have an `id` (text), a `latitude`
  (from −90 to 90 degrees), a `longitude` (from −180 to 180 degrees) and an
  `elevation_m` (metres). The default SHALL be an empty list.

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
- **THEN** its `options` set `interval_seconds` to 900 and `piers` to an empty
  list
- **AND** its `schema` declares `interval_seconds` as a whole number, and `piers`
  as a list whose items have `id`, `latitude`, `longitude` and `elevation_m`
- **AND** each pier item has an optional `min_altitude` from 0 to 90 and an
  optional `horizon_points`
- **AND** each pier item has optional `equipment_focal_length_mm`,
  `equipment_sensor_width_mm`, `equipment_sensor_height_mm` and
  `equipment_reducer`, each a number of at least 0

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

### Requirement: The add-on reads the Configuration form before the config file

Inside an add-on, the service SHALL read the values the user saved on the
Configuration form at startup. The rule for which source it uses is:

- When the form lists at least one pier, the service SHALL take the interval and
  the piers from the form only. It SHALL NOT read settings from `config.yaml`.
- When the form lists no piers, the service SHALL read `config.yaml` as the
  requirement "The add-on reads config from its own config folder" describes. It
  SHALL ignore the form's interval.

When the service uses the form, it SHALL take the broker from the Supervisor's
`mqtt` service. The broker's host, port, username and password all come from
there. The discovery prefix and base topic SHALL take their defaults.

When the service uses the form and stops with a broker error, the error SHALL
say that `config.yaml` is not read while the form lists piers. It SHALL NOT tell
the user only to set `mqtt.host` in `config.yaml`. This covers the "no MQTT
broker was found", "access refused", TLS, MQTT version and rejected-login
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

- **WHEN** the form lists a pier
- **AND** the Supervisor provides no `mqtt` service within the wait
- **THEN** the add-on stops
- **AND** its log says no MQTT broker was found
- **AND** it says `config.yaml` is not read while the form lists piers

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

### Requirement: The form sets each pier's horizon

The service SHALL turn a form pier's horizon fields into that pier's horizon:

- When `min_altitude` is set, the pier's horizon SHALL be a flat floor at that
  altitude.
- When `horizon_points` is set, the service SHALL read the text with the same
  parser it uses for `config.yaml`. The result SHALL be the pier's inline
  horizon points. The service SHALL then check them exactly as it checks a
  file's `horizon.points`.
- When neither is set, the pier's horizon SHALL be flat at 0 degrees.

The service SHALL treat empty or blank `horizon_points` text as unset.

A pier whose horizon fails these rules SHALL be skipped with a logged error that
names the pier. The other piers SHALL still be published. This covers four
cases:

- `horizon_points` text that the parser cannot read. The error SHALL name
  `horizon_points`.
- a saved `horizon_points` value that is not text. The error SHALL name
  `horizon_points`.
- points that fail the checks for inline points.
- both `min_altitude` and `horizon_points` set. This breaks the rule that a
  horizon has exactly one source.

When every pier is skipped, the add-on SHALL stop with a configuration error, as
it does for any setup with no valid pier.

#### Scenario: A flat floor from the form

- **WHEN** the form lists a pier with `min_altitude` set to 15
- **THEN** the pier's horizon altitude is 15 degrees at every azimuth

#### Scenario: Horizon points from the form

- **WHEN** the form lists a pier with `horizon_points` set to
  `[[0, 10], [90, 25], [180, 5]]`
- **THEN** the pier's horizon equals the horizon of a `config.yaml` pier whose
  `horizon.points` holds the same three pairs

#### Scenario: No horizon fields means open sky

- **WHEN** the form lists a pier with neither horizon field set
- **THEN** the pier's horizon altitude is 0 degrees at every azimuth

#### Scenario: Blank horizon points are ignored

- **WHEN** the form lists a pier with `min_altitude` set to 15 and
  `horizon_points` set to blank text
- **THEN** the pier's horizon altitude is 15 degrees at every azimuth

#### Scenario: Unreadable horizon points skip only that pier

- **WHEN** the form lists two piers
- **AND** one pier's `horizon_points` is `[[0, 10], [90`
- **THEN** the service logs an error that names that pier and `horizon_points`
- **AND** it publishes a verdict for the other pier

#### Scenario: Malformed saved values skip only their pier

- **WHEN** the saved form values list three piers
- **AND** one pier's `horizon_points` is the number 5, not text
- **AND** another entry in `piers` is not a mapping
- **THEN** the service logs an error for each of those two entries, naming
  `horizon_points` for the first
- **AND** it publishes a verdict for the third pier

The Supervisor normally refuses to save such values. The service still checks
them, because it does not rely on the Supervisor's check.

#### Scenario: An out-of-range point skips only that pier

- **WHEN** the form lists two piers
- **AND** one pier's `horizon_points` holds the pair `[0, 95]`
- **THEN** the service logs an error that names that pier
- **AND** it publishes a verdict for the other pier

#### Scenario: Both horizon fields skip the pier

- **WHEN** the form lists two piers
- **AND** one pier sets both `min_altitude` and `horizon_points`
- **THEN** the service logs an error that names that pier
- **AND** it publishes a verdict for the other pier

#### Scenario: A bad horizon on the only pier stops the add-on

- **WHEN** the form lists one pier, and its `horizon_points` cannot be read
- **THEN** the service logs an error that names the pier and `horizon_points`
- **AND** the add-on stops with a configuration error that says no valid pier
  remains

### Requirement: The form sets each pier's equipment

The service SHALL turn a form pier's equipment fields into that pier's
equipment:

- When at least one equipment field is set, the service SHALL build the pier's
  equipment from the fields that are set. It SHALL then check the equipment
  exactly as it checks a file's `equipment` block.
- When no equipment field is set, the pier SHALL have no equipment. It SHALL
  rank targets without a field-of-view term.

When `equipment_reducer` is not set, the reducer SHALL be 1.0, as in the file.

A pier whose equipment fails these checks SHALL be skipped with a logged error
that names the pier. The other piers SHALL still be published. This covers three
cases:

- a missing focal length, sensor width or sensor height, while another
  equipment field is set. The error SHALL name the missing field.
- a value of 0 or less.
- saved values that hold both an `equipment` mapping and any equipment field.
  The error SHALL name `equipment`. The form has no `equipment` field, so this
  happens only when the saved values were written some other way.

When every pier is skipped, the add-on SHALL stop with a configuration error, as
it does for any setup with no valid pier.

#### Scenario: Equipment from the form

- **WHEN** the form lists a pier with `equipment_focal_length_mm` set to 400,
  `equipment_sensor_width_mm` to 23.5, `equipment_sensor_height_mm` to 15.7 and
  `equipment_reducer` to 0.8
- **THEN** the pier's equipment equals the equipment of a `config.yaml` pier
  whose `equipment` block holds the same four values

#### Scenario: The reducer defaults to 1.0

- **WHEN** the form lists a pier with focal length, sensor width and sensor
  height set, and no `equipment_reducer`
- **THEN** the pier's equipment has a reducer of 1.0

#### Scenario: No equipment fields means no equipment

- **WHEN** the form lists a pier with no equipment field set
- **THEN** the pier has no equipment
- **AND** no field-of-view term contributes to any of its targets' scores

#### Scenario: Equipment from the form ranks like file equipment

- **WHEN** the form lists a pier with all four equipment fields set
- **AND** a `config.yaml` pier has the same id, location, elevation and horizon,
  and the same four values in its `equipment` block
- **AND** the top pick at the chosen evaluation instant has a known catalog size
- **THEN** at that instant and with the same conditions, both piers get the same
  verdict document
- **AND** its `reasons[]` say how the top pick fits the field of view

#### Scenario: Saved null values count as unset

- **WHEN** the saved form values list two piers
- **AND** one pier has all four equipment fields saved as `null`
- **AND** the other pier sets focal length and sensor width, with
  `equipment_sensor_height_mm` saved as `null`
- **THEN** the first pier has no equipment and gets a verdict
- **AND** the service logs an error that names the second pier and
  `sensor_height_mm`

#### Scenario: Incomplete equipment skips only that pier

- **WHEN** the form lists two piers
- **AND** one pier sets `equipment_focal_length_mm` and
  `equipment_sensor_width_mm`, but not `equipment_sensor_height_mm`
- **THEN** the service logs an error that names that pier and
  `sensor_height_mm`
- **AND** it publishes a verdict for the other pier

#### Scenario: A reducer alone skips the pier

- **WHEN** the form lists two piers
- **AND** one pier sets only `equipment_reducer`
- **THEN** the service logs an error that names that pier and
  `focal_length_mm`
- **AND** it publishes a verdict for the other pier

#### Scenario: A value of 0 or less skips only its pier

- **WHEN** the form lists two piers, each with all three required equipment
  fields set
- **AND** one pier sets one of the four equipment fields to 0 or to −1
- **THEN** the service logs an error that names that pier and the field's
  `equipment` key, such as `focal_length_mm`
- **AND** it publishes a verdict for the other pier

This holds for each of the four fields and both values. The Supervisor normally
refuses to save a negative value. The service still checks it, because it does
not rely on the Supervisor's check.

#### Scenario: An equipment mapping beside equipment fields skips the pier

- **WHEN** the saved form values list two piers
- **AND** one pier holds an `equipment` mapping and sets
  `equipment_focal_length_mm`
- **THEN** the service logs an error that names that pier and `equipment`
- **AND** it publishes a verdict for the other pier

#### Scenario: Incomplete equipment on the only pier stops the add-on

- **WHEN** the form lists one pier, and it sets only
  `equipment_focal_length_mm`
- **THEN** the service logs an error that names the pier
- **AND** the add-on stops with a configuration error that says no valid pier
  remains

### Requirement: The add-on behaves like the container

The add-on SHALL publish the same entities, topics and verdict documents as the
same image run with Docker and the same config file. It SHALL NOT add, remove or
rename any entity or topic.

#### Scenario: Same entities as a Docker install

- **WHEN** a user runs the add-on with a config file that works under Docker
- **THEN** Home Assistant shows the same PierPressure device and entities as it
  does for the Docker install

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
the Mosquitto broker add-on, or to set `mqtt.host` in `config.yaml`.

If the Supervisor refuses the add-on access to the service, the add-on SHALL stop
at once, without waiting. Its error SHALL say that the Supervisor refused access
to the `mqtt` service. It SHALL tell the user to set `mqtt.host` in `config.yaml`,
and to report the problem.

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

### Requirement: The add-on refuses a Supervisor broker that needs another MQTT version

PierPressure speaks MQTT version 3.1.1. If the Supervisor's `mqtt` service names
any other protocol version, the add-on SHALL stop with an error. The error SHALL
name the version the broker asked for, and say that PierPressure supports only
3.1.1. It SHALL tell the user to set `mqtt.host` and `mqtt.port` in `config.yaml`
to a broker that accepts 3.1.1. A response that names no protocol SHALL count as
3.1.1, which is the Supervisor's default.

#### Scenario: The Supervisor's broker asks for MQTT 3.1

- **WHEN** the user's `config.yaml` has no `mqtt.host`
- **AND** the Supervisor's `mqtt` service names protocol `3.1`
- **THEN** the add-on stops without connecting to the broker
- **AND** its log names protocol `3.1`, and says PierPressure supports only 3.1.1
