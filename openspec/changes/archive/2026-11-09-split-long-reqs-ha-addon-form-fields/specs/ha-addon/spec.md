## ADDED Requirements

### Requirement: A form pier's min_altitude sets a flat horizon floor

Inside an add-on, when a pier on the Configuration form sets `min_altitude`, the
service SHALL make that pier's horizon a flat floor at that altitude.

#### Scenario: A flat floor from the form

- **WHEN** the form lists a pier with `min_altitude` set to 15
- **THEN** the pier's horizon altitude is 15 degrees at every azimuth

### Requirement: A form pier's horizon_points become its horizon points

Inside an add-on, when a pier on the Configuration form sets `horizon_points`,
the service SHALL pass its value unchanged as the pier's `horizon.points`. The
core SHALL then read and check it exactly as it reads and checks
`horizon.points` in `config.yaml`. The service SHALL treat empty or blank
`horizon_points` text as unset.

#### Scenario: Horizon points from the form

- **WHEN** the form lists a pier with `horizon_points` set to
  `[[0, 10], [90, 25], [180, 5]]`
- **THEN** the pier's horizon equals the horizon of a `config.yaml` pier whose
  `horizon.points` holds the same three pairs

#### Scenario: Blank horizon points are ignored

- **WHEN** the form lists a pier with `min_altitude` set to 15 and
  `horizon_points` set to blank text
- **THEN** the pier's horizon altitude is 15 degrees at every azimuth

### Requirement: A form pier with no horizon field takes its horizon from config.yaml

Inside an add-on, when a pier on the Configuration form sets neither horizon
field, the pier's horizon SHALL come from `config.yaml`, as the requirement "A
pier in config.yaml adds its settings to the form pier with its id" describes.
When the file gives the pier no horizon either, the pier's horizon SHALL be flat
at 0 degrees.

#### Scenario: No horizon fields means open sky

- **WHEN** the form lists a pier with neither horizon field set
- **AND** `config.yaml` gives that pier no horizon
- **THEN** the pier's horizon altitude is 0 degrees at every azimuth

### Requirement: Horizon points the core cannot read skip the form pier

Inside an add-on, a pier on the Configuration form SHALL be skipped with a
logged error that names the pier and `horizon.points` in each of these cases.
The other piers SHALL still be published.

- `horizon_points` text that the core cannot read as a list of points.
- a saved `horizon_points` value that is neither text nor a list of points.

#### Scenario: Unreadable horizon points skip only that pier

- **WHEN** the form lists two piers
- **AND** one pier's `horizon_points` is `[[0, 10], [90`
- **THEN** the service logs an error that names that pier and `horizon.points`
- **AND** it publishes a verdict for the other pier

#### Scenario: Malformed saved values skip only their pier

- **WHEN** the saved form values list three piers
- **AND** one pier's `horizon_points` is the number 5, not text
- **AND** another entry in `piers` is not a mapping
- **THEN** the service logs an error for each of those two entries, naming
  `horizon.points` for the first
- **AND** it publishes a verdict for the third pier

### Requirement: A form pier's horizon that breaks the horizon rules skips the pier

Inside an add-on, a pier on the Configuration form SHALL be skipped with a
logged error that names the pier in each of these cases. The other piers SHALL
still be published.

- its horizon points fail the checks for inline points.
- it sets both `min_altitude` and `horizon_points`. This breaks the rule that a
  horizon has exactly one source.

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

### Requirement: A horizon value beside a set horizon field skips the form pier

Inside an add-on, when the saved form values give a pier both a `horizon` value
and a horizon field that is set, the service SHALL leave each set horizon field
in place. The core SHALL reject each one as a field it does not know. The pier
SHALL be skipped with a logged error that names the pier and each of those
fields. The other piers SHALL still be published. The form has no `horizon`
field, so this happens only when the saved values were written some other way.

#### Scenario: A horizon mapping beside horizon fields skips the pier

- **WHEN** the saved form values list two piers
- **AND** one pier holds a `horizon` mapping and sets `horizon_points`
- **THEN** the service logs an error that names that pier and `horizon_points`
  as a field the core does not know
- **AND** the add-on reports no error of its own for that pier
- **AND** it publishes a verdict for the other pier

#### Scenario: A horizon mapping beside unset horizon fields is used

- **WHEN** the saved form values list a pier that holds a `horizon` mapping
  with `min_altitude` 15
- **AND** the pier's `horizon_points` is blank text and its `min_altitude` is
  null
- **THEN** the pier passes the service's checks
- **AND** its horizon altitude is 15 degrees at every azimuth

### Requirement: A form pier's equipment fields set its equipment

Inside an add-on, when a pier on the Configuration form sets at least one
equipment field, the service SHALL build the pier's equipment from the fields
that are set. It SHALL then check the equipment exactly as it checks a file's
`equipment` block.

#### Scenario: Equipment from the form

- **WHEN** the form lists a pier with `equipment_focal_length_mm` set to 400,
  `equipment_sensor_width_mm` to 23.5, `equipment_sensor_height_mm` to 15.7 and
  `equipment_reducer` to 0.8
- **THEN** the pier's equipment equals the equipment of a `config.yaml` pier
  whose `equipment` block holds the same four values

#### Scenario: Equipment from the form ranks like file equipment

- **WHEN** an add-on's form lists a pier with all four equipment fields set
- **AND** a separate `config.yaml`, used outside an add-on, lists a pier with the
  same id, location, elevation and horizon, and the same four values in its
  `equipment` block
- **AND** the top pick at the chosen evaluation instant has a known catalog size
- **THEN** at that instant and with the same conditions, both piers get the same
  verdict document
- **AND** its `reasons[]` say how the top pick fits the field of view

### Requirement: A form pier's reducer defaults to 1.0

Inside an add-on, when a pier on the Configuration form does not set
`equipment_reducer`, its reducer SHALL be 1.0, as in the file.

#### Scenario: The reducer defaults to 1.0

- **WHEN** the form lists a pier with focal length, sensor width and sensor
  height set, and no `equipment_reducer`
- **THEN** the pier's equipment has a reducer of 1.0

### Requirement: A form pier with no equipment field takes its equipment from config.yaml

Inside an add-on, when a pier on the Configuration form sets no equipment field,
the pier's equipment SHALL come from `config.yaml`, as the requirement "A pier
in config.yaml adds its settings to the form pier with its id" describes. When
the file gives the pier no equipment either, the pier SHALL have no equipment.
It SHALL rank targets without a field-of-view term.

#### Scenario: No equipment fields means no equipment

- **WHEN** the form lists a pier with no equipment field set
- **AND** `config.yaml` gives that pier no equipment
- **THEN** the pier has no equipment
- **AND** no field-of-view term contributes to any of its targets' scores

#### Scenario: Saved null values count as unset

- **WHEN** the saved form values list two piers
- **AND** one pier has all four equipment fields saved as `null`
- **AND** the other pier sets focal length and sensor width, with
  `equipment_sensor_height_mm` saved as `null`
- **THEN** the first pier has no equipment and gets a verdict
- **AND** the service logs an error that names the second pier and
  `sensor_height_mm`

### Requirement: Incomplete equipment skips the form pier

Inside an add-on, when a pier on the Configuration form sets an equipment field
but leaves out the focal length, sensor width or sensor height, the pier SHALL
be skipped with a logged error that names the pier. The error SHALL name the
missing field. The other piers SHALL still be published.

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

### Requirement: An equipment value of 0 or less skips the form pier

Inside an add-on, when a pier on the Configuration form sets an equipment field
to 0 or less, the pier SHALL be skipped with a logged error that names the pier.
The other piers SHALL still be published.

#### Scenario: A value of 0 or less skips only its pier

- **WHEN** the form lists two piers, each with all three required equipment
  fields set
- **AND** one pier sets one of the four equipment fields to 0 or to −1
- **THEN** the service logs an error that names that pier and the field's
  `equipment` key, such as `focal_length_mm`
- **AND** it publishes a verdict for the other pier

This holds for each of the four fields and both values.

### Requirement: An equipment value beside an equipment field skips the form pier

Inside an add-on, when the saved form values give a pier both an `equipment`
value and any equipment field, the service SHALL leave each set `equipment_*`
field in place. The core SHALL reject each one as a field it does not know. The
pier SHALL be skipped with a logged error that names the pier and each of those
fields. The other piers SHALL still be published. The form has no `equipment`
field, so this happens only when the saved values were written some other way.

#### Scenario: An equipment mapping beside equipment fields skips the pier

- **WHEN** the saved form values list two piers
- **AND** one pier holds an `equipment` mapping and sets
  `equipment_focal_length_mm`
- **THEN** the service logs an error that names that pier and
  `equipment_focal_length_mm` as a field the core does not know
- **AND** the add-on reports no error of its own for that pier
- **AND** it publishes a verdict for the other pier

#### Scenario: An equipment mapping beside unset equipment fields is used

- **WHEN** the saved form values list a pier that holds a complete `equipment`
  mapping
- **AND** the pier's `equipment_focal_length_mm` is null
- **THEN** the pier passes the service's checks
- **AND** its equipment equals the `equipment` mapping

### Requirement: A form pier's go_threshold and max_gust pass to the pier

Inside an add-on, the service SHALL pass a Configuration form pier's
`go_threshold` and `max_gust` to that pier when they are set. It SHALL then
check them exactly as it checks the same settings in `config.yaml`.

#### Scenario: Both values from the form

- **WHEN** an add-on's form lists a pier with `go_threshold` set to 75 and
  `max_gust` set to 40
- **AND** a separate `config.yaml`, used outside an add-on, lists a pier with the
  same id, location and elevation, and the same two values
- **THEN** at the same evaluation instant and with the same conditions, both
  piers get the same verdict document

#### Scenario: A gust over the form's limit is a NO-GO

- **WHEN** the form lists a pier with `max_gust` set to 30
- **AND** the forecast gives a gust of 45 km/h during the pier's dark window
- **AND** no other gate fails
- **THEN** the pier's verdict is `NO-GO`
- **AND** its score is null
- **AND** its `reasons[]` name the 30 km/h limit

### Requirement: An unset go_threshold or max_gust on the form comes from config.yaml

Inside an add-on, when a Configuration form pier does not set `go_threshold` or
`max_gust`, the value SHALL come from `config.yaml`, as the requirement "A pier
in config.yaml adds its settings to the form pier with its id" describes. A
field that is absent, saved as null, or saved as empty or blank text SHALL count
as not set. A `go_threshold` of 0 SHALL count as set.

#### Scenario: config.yaml fills an empty field

- **WHEN** the saved form values list the pier `backyard` with `max_gust` saved
  as null
- **AND** `config.yaml` lists `backyard` with `max_gust` set to 40
- **THEN** the pier's checked settings hold a `max_gust` of 40
- **AND** the add-on does not report a setting given in both places

#### Scenario: A value set in both places stops the add-on

- **WHEN** the form lists the pier `backyard` with `go_threshold` set to 70
- **AND** `config.yaml` lists `backyard` with `go_threshold` set to 75
- **THEN** the add-on stops with a configuration error that names
  `go_threshold` and `backyard`

### Requirement: A form pier with no go_threshold or max_gust uses the file defaults

Inside an add-on, when neither the Configuration form nor `config.yaml` sets a
pier's `go_threshold` or `max_gust`, the pier SHALL behave as a file pier
without that setting:

- Without `go_threshold`, the pier SHALL use the default threshold of 65.
- Without `max_gust`, the pier SHALL have no wind gate. No forecast gust SHALL
  cause a `NO-GO`.

#### Scenario: Empty fields use the defaults

- **WHEN** the saved form values list a pier with `go_threshold` and `max_gust`
  each absent, saved as null, or saved as blank text
- **AND** `config.yaml` does not set them for that pier
- **THEN** the pier passes the service's checks
- **AND** its checked settings hold a `go_threshold` of 65 and no `max_gust`

### Requirement: A bad go_threshold or max_gust skips the form pier

Inside an add-on, when a Configuration form pier's `go_threshold` or `max_gust`
fails the checks, the service SHALL skip that pier and log an error that names
the pier and the field. It SHALL still publish the other piers. This covers a
`go_threshold` below 0, above 100 or not a whole number, and a `max_gust` of 0
or less.

#### Scenario: A bad value skips only its pier

- **WHEN** the saved form values list two piers
- **AND** one pier sets `max_gust` to 0, or `go_threshold` to 101
- **THEN** the service logs an error that names that pier and the field
- **AND** it publishes a verdict for the other pier

### Requirement: Skipping every pier on the Configuration form stops the add-on

Inside an add-on, when the service skips every pier on the Configuration form,
the add-on SHALL stop with a configuration error, as it does for any setup with
no valid pier.

#### Scenario: A bad horizon on the only pier stops the add-on

- **WHEN** the form lists one pier, and its `horizon_points` cannot be read
- **THEN** the service logs an error that names the pier and `horizon.points`
- **AND** the add-on stops with a configuration error that says no valid pier
  remains

#### Scenario: Incomplete equipment on the only pier stops the add-on

- **WHEN** the form lists one pier, and it sets only
  `equipment_focal_length_mm`
- **THEN** the service logs an error that names the pier
- **AND** the add-on stops with a configuration error that says no valid pier
  remains

### Requirement: A broker host on the form sets all four connection settings

Inside an add-on, when the Configuration form sets `mqtt.host`, the host, port,
username and password SHALL all come from the form. The service SHALL NOT ask
the Supervisor for the broker. A port the form does not set SHALL be 1883. When
the form does not set `mqtt.host`, the requirement "The add-on uses the
Supervisor's MQTT broker when the settings name none" decides where all four
come from.

#### Scenario: The form's broker is used

- **WHEN** the form lists a pier and sets `mqtt.host` to `broker.lan`,
  `mqtt.port` to 1884, `mqtt.username` to `pier`, and `mqtt.password`
- **THEN** the service connects to `broker.lan` on port 1884
- **AND** it logs in with the username `pier` and the form's password
- **AND** it does not ask the Supervisor for the broker

#### Scenario: The form's broker uses port 1883 by default

- **WHEN** the form lists a pier and sets `mqtt.host` but not `mqtt.port`
- **THEN** the service connects to that host on port 1883

### Requirement: A blank broker field on the form counts as not set

Inside an add-on, a broker field on the Configuration form that is empty or
blank SHALL count as not set.

#### Scenario: Blank broker fields count as not set

- **WHEN** the form lists a pier and sets `mqtt.host`
- **AND** its `mqtt.username` and `mqtt.password` are empty text
- **THEN** the service connects to that host without a username or password

### Requirement: Broker login fields on the form without a host stop the add-on

Inside an add-on, a Configuration form that sets `mqtt.port`, `mqtt.username`
or `mqtt.password` without `mqtt.host` SHALL be rejected with the same
configuration error that `config.yaml` gets. The error SHALL say to set
`mqtt.host` too.

#### Scenario: Credentials on the form without a host are rejected

- **WHEN** the form lists a pier and sets `mqtt.username` but not `mqtt.host`
- **THEN** the add-on stops without asking the Supervisor for the broker
- **AND** its log contains a configuration error that says to set `mqtt.host`

### Requirement: A rejected login from the form points to the form's login

Inside an add-on, when the broker rejects a login from the Configuration form,
the error SHALL tell the user to check the username and password. It SHALL NOT
tell the user to restart the Mosquitto add-on.

#### Scenario: A rejected login from the form points to the form's login

- **WHEN** the form lists a pier and sets `mqtt.host`
- **AND** the broker rejects the login
- **THEN** the add-on stops
- **AND** its log tells the user to check the username and password
- **AND** it does not tell the user to restart the Mosquitto add-on

### Requirement: The log names the Configuration tab as the broker's source

Inside an add-on, when the broker comes from the Configuration form, the log
SHALL say that the broker came from the Configuration tab, and SHALL name its
host and port.

#### Scenario: The log names the form as the broker's source

- **WHEN** the form lists a pier, sets `mqtt.host` to `broker.lan`, and sets
  `mqtt.password` to `pw-8c41f2`
- **THEN** the log says the broker came from the Configuration tab, and names
  `broker.lan` and port 1883
- **AND** no log line contains `pw-8c41f2`

### Requirement: No log line or error reveals the form's broker password

Inside an add-on, the service SHALL NOT read or insert the Configuration form's
`mqtt.password` when it builds a log line or an error message. The log may
still show the host, even when the user enters the same text as the host and
the password.

#### Scenario: A rejected login does not reveal the form's password

- **WHEN** the form lists a pier, sets `mqtt.host` to `broker.lan`, and sets
  `mqtt.password` to `pw-8c41f2`
- **AND** the broker rejects the login
- **THEN** no log line or error message contains `pw-8c41f2`

## MODIFIED Requirements

### Requirement: The add-on uses the Supervisor's MQTT broker when the settings name none

The add-on SHALL ask Home Assistant's Supervisor for the `mqtt` service, as a
service it wants but does not need. So the add-on SHALL install and start when no
other add-on provides the service.

The connection settings are the broker's host, port, username and password.
Inside the add-on, the service SHALL take all four from one source:

- When the form sets `mqtt.host`, all four SHALL come from the form, as the
  requirement "A broker host on the form sets all four connection settings"
  describes.
- When `config.yaml` sets `mqtt.host`, all four SHALL come from the file. The
  service SHALL NOT ask the Supervisor for the broker.
- When neither the form nor `config.yaml` sets `mqtt.host`, all four SHALL come
  from the Supervisor's `mqtt` service.

The form and the file cannot both set connection settings, as the requirement
"The broker connection and the recompute interval each count as one setting"
describes.

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

## REMOVED Requirements

### Requirement: The form sets each pier's horizon

**Reason**: Split into requirements that each state one behavior: "A form pier's min_altitude sets a flat horizon floor", "A form pier's horizon_points become its horizon points", "A form pier with no horizon field takes its horizon from config.yaml", "Horizon points the core cannot read skip the form pier", "A form pier's horizon that breaks the horizon rules skips the pier", "A horizon value beside a set horizon field skips the form pier" and, with the other form field requirements, "Skipping every pier on the Configuration form stops the add-on". Its pointer to the removed requirement "The add-on combines the Configuration form with config.yaml" now names "A pier in config.yaml adds its settings to the form pier with its id".

**Migration**: None. Nothing changes for users or code.

### Requirement: The form sets each pier's equipment

**Reason**: Split into requirements that each state one behavior: "A form pier's equipment fields set its equipment", "A form pier's reducer defaults to 1.0", "A form pier with no equipment field takes its equipment from config.yaml", "Incomplete equipment skips the form pier", "An equipment value of 0 or less skips the form pier", "An equipment value beside an equipment field skips the form pier" and, with the other form field requirements, "Skipping every pier on the Configuration form stops the add-on". Its pointer to the removed requirement "The add-on combines the Configuration form with config.yaml" now names "A pier in config.yaml adds its settings to the form pier with its id".

**Migration**: None. Nothing changes for users or code.

### Requirement: The form sets each pier's GO threshold and wind-gust limit

**Reason**: Split into requirements that each state one behavior: "A form pier's go_threshold and max_gust pass to the pier", "An unset go_threshold or max_gust on the form comes from config.yaml", "A form pier with no go_threshold or max_gust uses the file defaults", "A bad go_threshold or max_gust skips the form pier" and, with the other form field requirements, "Skipping every pier on the Configuration form stops the add-on". Its pointer to the removed requirement "The add-on combines the Configuration form with config.yaml" now names "A pier in config.yaml adds its settings to the form pier with its id".

**Migration**: None. Nothing changes for users or code.

### Requirement: The form sets the broker

**Reason**: Split into requirements that each state one behavior: "A broker host on the form sets all four connection settings", "A blank broker field on the form counts as not set", "Broker login fields on the form without a host stop the add-on", "A rejected login from the form points to the form's login", "The log names the Configuration tab as the broker's source" and "No log line or error reveals the form's broker password". The requirement "The add-on uses the Supervisor's MQTT broker when the settings name none" pointed here, so this change MODIFIES it to name "A broker host on the form sets all four connection settings" instead.

**Migration**: None. Nothing changes for users or code.