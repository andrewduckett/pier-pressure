## ADDED Requirements

### Requirement: The add-on combines the Configuration form with config.yaml

Inside an add-on, the service SHALL read the values the user saved on the
Configuration form at startup. The form SHALL list at least one pier. The service
SHALL also read `config.yaml` from the add-on's config folder when that file
exists. The file MAY add any setting the form leaves unset. The service SHALL
build one set of settings from the two sources. It SHALL then check those
settings exactly as it checks a `config.yaml` on its own.

A form field that is absent, saved as null, or saved as empty or blank text SHALL
count as not set. This rule SHALL hold for number fields too. A value of 0 SHALL
count as set. The form always sets `interval_seconds`.

A file pier SHALL add its settings to the form pier with the same `id`. A pier's
`id` only matches the two sources. It SHALL NOT count as a setting, and the
combined pier SHALL keep the form's `id`.

Each setting SHALL come from the form or from the file, never from both. Each of
these groups SHALL count as one setting:

- a pier's horizon: the form's `min_altitude` or `horizon_points`, or the file's
  `horizon` block.
- a pier's equipment: any of the form's four equipment fields, or the file's
  `equipment` block.
- the broker connection: any of `mqtt.host`, `mqtt.port`, `mqtt.username` and
  `mqtt.password`.
- the recompute interval: the form's `interval_seconds`, or the file's
  `recompute` block.

Every other setting, such as a pier's `go_threshold` or `mqtt.base_topic`, SHALL
count as a setting of its own.

The add-on SHALL stop with a configuration error in each of these cases:

- A setting is given in both sources. The error SHALL name the setting, and the
  pier when it is a pier's setting. It SHALL NOT contain the setting's value.
- The file lists a pier `id` that the form does not list. The error SHALL name
  the `id`. A pier the form lists SHALL count as listed, even when the service
  skips it as invalid.
- The file lists the same pier `id` more than once. The error SHALL name the
  `id`.
- A pier in the file is not a mapping, or its `id` is missing or is not text.
  The error SHALL name the entry's position in the file's `piers` list.
- The file's `piers` is not a list.
- The file is not valid YAML, or its root is not a mapping. The error SHALL name
  the file. For a YAML mistake, it SHALL also name the line and column, and
  SHALL hold no other detail from the YAML parser.

The error SHALL list every such problem it finds, not only the first. No error
SHALL quote the content of `config.yaml` or the value of any setting. An `id` or
key name in an error SHALL be shown with any line break or other control
character escaped, so the error stays on one line.

A relative horizon `file` path in `config.yaml` SHALL be read from the add-on's
config folder.

The service SHALL check each pier after the file's settings are added to it. A
pier that fails the check SHALL be skipped with a logged error, and the other
piers SHALL still be published.

When the form lists no piers, the add-on SHALL stop with a configuration error.
The error SHALL say that nothing is set up, and SHALL tell the user to add a pier
on the Configuration tab. When `config.yaml` lists piers, the error SHALL also
name them. It SHALL say that `config.yaml` cannot list piers on its own. It SHALL
tell the user to add each of those piers on the Configuration tab with the same
`id`, and to keep only the extra settings in `config.yaml`.

When the file adds at least one setting, the log SHALL say that the settings came
from the Configuration tab and `config.yaml`. Otherwise, it SHALL say that they
came from the Configuration tab.

Outside an add-on, the service SHALL NOT read the form's values. It SHALL load
`config.yaml` on its own, as it did before this change.

#### Scenario: Form setup gives a verdict without a file

- **WHEN** the user saves an interval and one pier on the Configuration tab
- **AND** the form sets no broker field
- **AND** the add-on's config folder holds no `config.yaml`
- **AND** the Supervisor provides an `mqtt` service
- **THEN** the service connects to the Supervisor's broker
- **AND** it publishes a verdict for that pier under the default discovery prefix
  and base topic
- **AND** it recomputes at the interval from the form
- **AND** its log says the settings came from the Configuration tab

#### Scenario: A form pier takes its horizon file from config.yaml

- **WHEN** the form lists the pier `backyard` with no horizon field set
- **AND** `config.yaml` lists the pier `backyard` with a `horizon` block whose
  `file` is `backyard.hrz` and whose `format` is `nina`
- **AND** `backyard.hrz` is a valid NINA horizon file in the add-on's config
  folder
- **THEN** the pier's horizon equals the horizon read from `backyard.hrz`
- **AND** the service publishes a verdict for `backyard`
- **AND** its log says the settings came from the Configuration tab and
  `config.yaml`

#### Scenario: The file adds pier settings the form does not show

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists the pier `backyard` with `go_threshold` set to 75
  and `max_gust` set to 40
- **THEN** the pier's GO threshold is 75
- **AND** the pier's wind gate uses a gust limit of 40

#### Scenario: The file adds the topic names

- **WHEN** the form lists a pier
- **AND** `config.yaml` sets `mqtt.base_topic` to `observatory` and sets no other
  `mqtt` field
- **THEN** the service publishes under the base topic `observatory`

#### Scenario: A file pier with only an id adds nothing

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists the pier `backyard` with no other key
- **THEN** the add-on starts, and reports no conflict for `id`
- **AND** the service publishes a verdict for `backyard`
- **AND** its log says the settings came from the Configuration tab

#### Scenario: Blank number fields count as not set

- **WHEN** the saved form values list the pier `backyard` with `min_altitude`
  saved as empty text, and each equipment field saved as blank text
- **AND** `config.yaml` gives `backyard` no horizon and no equipment
- **THEN** the pier's horizon altitude is 0 degrees at every azimuth
- **AND** the pier has no equipment
- **AND** the service publishes a verdict for `backyard`

#### Scenario: A horizon floor of 0 counts as set

- **WHEN** the form lists the pier `backyard` with `min_altitude` set to 0
- **AND** `config.yaml` gives `backyard` a `horizon` block
- **THEN** the add-on stops
- **AND** its configuration error names `horizon` and `backyard`

#### Scenario: A file pier id that is not text stops the add-on

- **WHEN** the form lists the pier `backyard`
- **AND** the first pier in `config.yaml` has an `id` that is null, a number, a
  list or a mapping
- **THEN** the add-on stops
- **AND** its configuration error names the first entry of the file's `piers`
  list

This holds for each of the four kinds of value.

#### Scenario: A YAML error does not quote the file

- **WHEN** the form lists a pier
- **AND** line 3 of `config.yaml` is `  password: [pw-8c41f2` or
  `  password: *pw-8c41f2`, either of which is not valid YAML
- **THEN** the add-on stops
- **AND** its configuration error names `/config/config.yaml` and line 3
- **AND** no log line or error message contains `pw-8c41f2`

This holds for both lines.

#### Scenario: A control character in an id stays escaped

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists a pier whose `id` holds a line break
- **THEN** the add-on stops with one configuration error
- **AND** that error is a single line, with the line break shown escaped

#### Scenario: Horizon points from the file are used

- **WHEN** the form lists the pier `backyard` with no horizon field set
- **AND** `config.yaml` lists the pier `backyard` with `horizon.points` set to
  `[[0, 10], [180, 20]]`
- **THEN** the pier's horizon equals the horizon of those two points

#### Scenario: A horizon in both stops the add-on

- **WHEN** the form lists the pier `backyard` with `min_altitude` set to 10
- **AND** `config.yaml` gives the pier `backyard` a `horizon` block
- **THEN** the add-on stops
- **AND** its configuration error names `horizon` and `backyard`

#### Scenario: Equipment in both stops the add-on

- **WHEN** the form lists the pier `backyard` with `equipment_focal_length_mm`
  set
- **AND** `config.yaml` gives the pier `backyard` an `equipment` block
- **THEN** the add-on stops
- **AND** its configuration error names `equipment` and `backyard`

#### Scenario: A pier key in both stops the add-on

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` sets `latitude` for the pier `backyard`
- **THEN** the add-on stops
- **AND** its configuration error names `latitude` and `backyard`

#### Scenario: A broker connection split across both stops the add-on

- **WHEN** the form lists a pier and sets `mqtt.host` to `broker.lan`
- **AND** `config.yaml` sets `mqtt.password` to `pw-8c41f2`
- **THEN** the add-on stops without connecting to a broker
- **AND** its configuration error names the broker connection
- **AND** no log line or error message contains `pw-8c41f2`

#### Scenario: An interval in the file stops the add-on

- **WHEN** the form lists a pier
- **AND** `config.yaml` sets `recompute.interval_seconds` to 600
- **THEN** the add-on stops
- **AND** its configuration error names the recompute interval

#### Scenario: A file pier the form does not list stops the add-on

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists the pier `roof`
- **THEN** the add-on stops
- **AND** its configuration error names `roof`

#### Scenario: A skipped form pier still counts as listed

- **WHEN** the form lists the piers `backyard` and `roof`
- **AND** the `horizon_points` of `backyard` cannot be read
- **AND** `config.yaml` lists the pier `backyard` with `go_threshold` set
- **THEN** the service logs an error that names `backyard` and `horizon_points`
- **AND** no error says that `backyard` is not on the Configuration tab
- **AND** the service publishes a verdict for `roof`

#### Scenario: A pier listed twice in the file stops the add-on

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists the pier `backyard` twice
- **THEN** the add-on stops
- **AND** its configuration error names `backyard`

#### Scenario: One error lists every problem

- **WHEN** the form lists the pier `backyard` with `min_altitude` set
- **AND** `config.yaml` gives `backyard` a `horizon` block, and lists the pier
  `roof`
- **THEN** the add-on stops with one configuration error
- **AND** that error names the `horizon` of `backyard`, and names `roof`

#### Scenario: An unreadable horizon file skips only its pier

- **WHEN** the form lists the piers `backyard` and `roof`
- **AND** `config.yaml` gives `backyard` a horizon `file` that does not exist in
  the add-on's config folder
- **THEN** the service logs an error that names `backyard`
- **AND** it publishes a verdict for `roof`

#### Scenario: A config.yaml that is not valid YAML stops the add-on

- **WHEN** the form lists a pier
- **AND** `config.yaml` is not valid YAML
- **THEN** the add-on stops
- **AND** its configuration error names `/config/config.yaml`

#### Scenario: Nothing is set up

- **WHEN** the form lists no piers
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on stops
- **AND** its configuration error says that nothing is set up, and tells the user
  to add a pier on the Configuration tab

#### Scenario: An empty form names the file's piers

- **WHEN** the form lists no piers
- **AND** `config.yaml` lists the piers `roof` and `shed`
- **THEN** the add-on stops without publishing a verdict
- **AND** its configuration error says that nothing is set up, and names `roof`
  and `shed`
- **AND** it says that `config.yaml` cannot list piers on its own
- **AND** it tells the user to add each pier on the Configuration tab with the
  same `id`, and to keep only the extra settings in `config.yaml`

#### Scenario: A bad pier in the saved form values is skipped

- **WHEN** the saved form values list two piers, and one has a latitude of 95
- **THEN** the service logs an error that names the skipped pier
- **AND** it publishes a verdict for the other pier

The Supervisor normally refuses to save such a value. The service still checks
each pier, because it does not rely on the Supervisor's check.

#### Scenario: Outside an add-on, the form is not read

- **WHEN** the service runs outside an add-on
- **THEN** it does not read the form's values
- **AND** it loads `config.yaml` on its own, exactly as before this change

## MODIFIED Requirements

### Requirement: The add-on reads config from its own config folder

Inside an add-on, the service SHALL read `config.yaml` from the add-on's own
config folder when that file exists. The file adds settings to the Configuration
form, as the requirement "The add-on combines the Configuration form with
config.yaml" describes. In Home Assistant, the user finds that folder as
`/addon_configs/<repository-id>_pierpressure`.

The file SHALL use the same keys and values as outside Home Assistant. Inside the
add-on, it holds only the settings the form leaves unset. So each of its piers
needs only an `id` and the settings it adds. The file MAY leave out the MQTT
broker's connection settings, as the requirement "The add-on uses the
Supervisor's MQTT broker when the settings name none" describes.

The file is optional. When the form lists a pier and the file does not exist, the
add-on SHALL start with the form's settings only.

#### Scenario: Config file present

- **WHEN** the form lists the pier `backyard`
- **AND** the user has written a `config.yaml` in the add-on's config folder that
  sets `go_threshold` to 75 for `backyard`
- **AND** the user starts the add-on
- **THEN** the service publishes a verdict for `backyard` with a GO threshold of
  75

#### Scenario: Config file missing

- **WHEN** the form lists a pier
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on starts
- **AND** it publishes a verdict for that pier

#### Scenario: Add-on config mounts the folder

- **WHEN** the test suite reads the add-on config file
- **THEN** it maps `addon_config`
- **AND** it sets the environment variable `PIERPRESSURE_CONFIG` to
  `/config/config.yaml`

### Requirement: The form sets each pier's horizon

The service SHALL turn a form pier's horizon fields into that pier's horizon:

- When `min_altitude` is set, the pier's horizon SHALL be a flat floor at that
  altitude.
- When `horizon_points` is set, the service SHALL read the text with the same
  parser it uses for `config.yaml`. The result SHALL be the pier's inline
  horizon points. The service SHALL then check them exactly as it checks a
  file's `horizon.points`.
- When neither is set, the pier's horizon SHALL come from `config.yaml`, as the
  requirement "The add-on combines the Configuration form with config.yaml"
  describes. When the file gives the pier no horizon either, the pier's horizon
  SHALL be flat at 0 degrees.

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
- **AND** `config.yaml` gives that pier no horizon
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
- When no equipment field is set, the pier's equipment SHALL come from
  `config.yaml`, as the requirement "The add-on combines the Configuration form
  with config.yaml" describes. When the file gives the pier no equipment either,
  the pier SHALL have no equipment. It SHALL rank targets without a
  field-of-view term.

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
- **AND** `config.yaml` gives that pier no equipment
- **THEN** the pier has no equipment
- **AND** no field-of-view term contributes to any of its targets' scores

#### Scenario: Equipment from the form ranks like file equipment

- **WHEN** an add-on's form lists a pier with all four equipment fields set
- **AND** a separate `config.yaml`, used outside an add-on, lists a pier with the
  same id, location, elevation and horizon, and the same four values in its
  `equipment` block
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
same image run with Docker and the same settings. It SHALL NOT add, remove or
rename any entity or topic.

#### Scenario: Same entities as a Docker install

- **WHEN** a user sets up the add-on with the settings of a working Docker
  install, split between the Configuration tab and `config.yaml`
- **THEN** Home Assistant shows the same PierPressure device and entities as it
  does for the Docker install

### Requirement: The add-on uses the Supervisor's MQTT broker when the settings name none

The add-on SHALL ask Home Assistant's Supervisor for the `mqtt` service, as a
service it wants but does not need. So the add-on SHALL install and start when no
other add-on provides the service.

The connection settings are the broker's host, port, username and password.
Inside the add-on, the service SHALL take all four from one source:

- When the form sets `mqtt.host`, all four SHALL come from the form, as the
  requirement "The form sets the broker" describes.
- When `config.yaml` sets `mqtt.host`, all four SHALL come from the file. The
  service SHALL NOT ask the Supervisor for the broker.
- When neither the form nor `config.yaml` sets `mqtt.host`, all four SHALL come
  from the Supervisor's `mqtt` service.

The form and the file cannot both set connection settings, as the requirement
"The add-on combines the Configuration form with config.yaml" describes.

`mqtt.discovery_prefix` and `mqtt.base_topic` SHALL always come from
`config.yaml`, or from their defaults. A file that sets `mqtt.port`,
`mqtt.username` or `mqtt.password` without `mqtt.host` SHALL be rejected with a
configuration error that says to set `mqtt.host` too.

The service SHALL ask the Supervisor only when it runs inside an add-on. Outside an
add-on, `mqtt.host` SHALL stay required, and the service SHALL behave as it did
before this change.

The service SHALL send its requests, and the Supervisor's token, straight to the
Supervisor. It SHALL NOT send them through a proxy, even when the container's
environment names one.

#### Scenario: Mosquitto user leaves out the broker settings

- **WHEN** the Mosquitto add-on provides the `mqtt` service
- **AND** the form lists a pier and sets no broker field
- **AND** the add-on's config folder holds no `config.yaml`, or one with no
  `mqtt:` block
- **THEN** the service connects to the broker host and port the Supervisor gave
- **AND** it logs in with the username and password the Supervisor gave
- **AND** it publishes under the default discovery prefix and base topic

#### Scenario: The file's broker wins

- **WHEN** the Supervisor provides an `mqtt` service
- **AND** the form lists a pier and sets no broker field
- **AND** the user's `config.yaml` sets `mqtt.host`
- **THEN** the service connects with the host, port, username and password from
  the file
- **AND** it does not ask the Supervisor for the broker

#### Scenario: The file sets only its topics

- **WHEN** the Supervisor provides an `mqtt` service
- **AND** the form lists a pier and sets no broker field
- **AND** the user's `config.yaml` sets `mqtt.base_topic` but not `mqtt.host`
- **THEN** the service connects with the Supervisor's connection settings
- **AND** it publishes under the file's base topic

#### Scenario: Credentials without a host are rejected

- **WHEN** the form lists a pier and sets no broker field
- **AND** the user's `config.yaml` sets `mqtt.username` but not `mqtt.host`
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
SHALL stop with an error. The error SHALL say that no MQTT broker was found. It
SHALL tell the user to install the Mosquitto broker add-on, or to set `mqtt.host`
on the Configuration tab or in `config.yaml`.

If the Supervisor refuses the add-on access to the service, the add-on SHALL stop
at once, without waiting. Its error SHALL say that the Supervisor refused access
to the `mqtt` service. It SHALL tell the user to set `mqtt.host` on the
Configuration tab or in `config.yaml`, and to report the problem.

Neither error SHALL say that `config.yaml` is not read.

#### Scenario: Mosquitto is still starting

- **WHEN** the service starts while the Supervisor does not yet provide the `mqtt`
  service
- **AND** a request started within 60 seconds of the first returns usable broker
  details
- **THEN** the service uses the broker it gives and publishes a verdict for each
  pier

#### Scenario: No broker add-on is installed

- **WHEN** neither the form nor `config.yaml` sets `mqtt.host`
- **AND** no request started within 60 seconds of the first returns usable broker
  details
- **THEN** the add-on stops
- **AND** its log says no MQTT broker was found
- **AND** it tells the user to install the Mosquitto broker add-on, or to set
  `mqtt.host` on the Configuration tab or in `config.yaml`
- **AND** it does not say that `config.yaml` is not read

#### Scenario: The wait ends on time

- **WHEN** the Supervisor provides no `mqtt` service
- **AND** each request to the Supervisor times out
- **THEN** the service starts no request later than 60 seconds after the first
- **AND** the add-on stops no later than 65 seconds after the first request

#### Scenario: The Supervisor refuses access

- **WHEN** neither the form nor `config.yaml` sets `mqtt.host`
- **AND** the Supervisor refuses the add-on access to the `mqtt` service
- **THEN** the add-on stops at once, without waiting
- **AND** its log says the Supervisor refused access to the `mqtt` service
- **AND** it tells the user to set `mqtt.host` on the Configuration tab or in
  `config.yaml`, and to report the problem

### Requirement: The add-on refuses a Supervisor broker that requires TLS

PierPressure does not support TLS connections. If the Supervisor's `mqtt` service
says its broker requires TLS, the add-on SHALL stop with an error. The error SHALL
say that the broker requires TLS, which PierPressure does not support. It SHALL
tell the user to set `mqtt.host` and `mqtt.port` to a broker listener that accepts
connections without TLS, on the Configuration tab or in `config.yaml`. The service
SHALL NOT connect to that broker without TLS.

#### Scenario: The Supervisor's broker requires TLS

- **WHEN** neither the form nor `config.yaml` sets `mqtt.host`
- **AND** the Supervisor's `mqtt` service says its broker requires TLS
- **THEN** the add-on stops without connecting to the broker
- **AND** its log says the broker requires TLS, which PierPressure does not
  support
- **AND** it tells the user to set a broker listener without TLS on the
  Configuration tab or in `config.yaml`

#### Scenario: A form user's TLS error names the Configuration tab

- **WHEN** the form lists a pier and sets no `mqtt.host`
- **AND** `config.yaml` sets no `mqtt.host`
- **AND** the Supervisor's `mqtt` service says its broker requires TLS
- **THEN** the add-on stops without connecting to the broker
- **AND** its log names the Configuration tab as a place to set the broker
  listener
- **AND** it does not say that `config.yaml` is not read

### Requirement: The add-on refuses a Supervisor broker that needs another MQTT version

PierPressure speaks MQTT version 3.1.1. If the Supervisor's `mqtt` service names
any other protocol version, the add-on SHALL stop with an error. The error SHALL
name the version the broker asked for, and say that PierPressure supports only
3.1.1. It SHALL tell the user to set `mqtt.host` and `mqtt.port` to a broker that
accepts 3.1.1, on the Configuration tab or in `config.yaml`. A response that names
no protocol SHALL count as 3.1.1, which is the Supervisor's default.

#### Scenario: The Supervisor's broker asks for MQTT 3.1

- **WHEN** neither the form nor `config.yaml` sets `mqtt.host`
- **AND** the Supervisor's `mqtt` service names protocol `3.1`
- **THEN** the add-on stops without connecting to the broker
- **AND** its log names protocol `3.1`, and says PierPressure supports only 3.1.1
- **AND** it tells the user to set `mqtt.host` on the Configuration tab or in
  `config.yaml`

### Requirement: The form sets the broker

Inside an add-on, the form's broker fields SHALL work as follows:

- When the form sets `mqtt.host`, the host, port, username and password SHALL
  all come from the form. The service SHALL NOT ask the Supervisor for the
  broker. A port the form does not set SHALL be 1883.
- When the form does not set `mqtt.host`, the requirement "The add-on uses the
  Supervisor's MQTT broker when the settings name none" decides where all four
  come from.

A form field that is empty or blank SHALL count as not set. A form that sets
`mqtt.port`, `mqtt.username` or `mqtt.password` without `mqtt.host` SHALL be
rejected with the same configuration error that `config.yaml` gets. The error
SHALL say to set `mqtt.host` too.

When the broker rejects a login from the form, the error SHALL tell the user to
check the username and password. It SHALL NOT tell the user to restart the
Mosquitto add-on.

The log SHALL say that the broker came from the Configuration tab, and SHALL
name its host and port. The service SHALL NOT read or insert `mqtt.password`
when it builds a log line or an error message. The log may still show the host,
even when the user enters the same text as the host and the password.

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

- **WHEN** the form lists a pier, sets `mqtt.host` to `broker.lan`, and sets
  `mqtt.password` to `pw-8c41f2`
- **AND** the broker rejects the login
- **THEN** no log line or error message contains `pw-8c41f2`

## REMOVED Requirements

### Requirement: The add-on reads the Configuration form before the config file

**Reason**: The service no longer uses the form or the file alone. The form and
`config.yaml` now combine, and an empty form no longer falls back to the file.

**Migration**: The requirement "The add-on combines the Configuration form with
config.yaml" replaces this one. Its still-valid scenarios move there. A user with
a `config.yaml` that lists piers adds each pier on the Configuration tab with the
same `id`, and keeps only the extra settings in the file.

## RENAMED Requirements

- FROM: `### Requirement: The add-on uses the Supervisor's MQTT broker when the file names none`
- TO: `### Requirement: The add-on uses the Supervisor's MQTT broker when the settings name none`
