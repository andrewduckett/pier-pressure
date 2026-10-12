## ADDED Requirements

### Requirement: The core checks every saved setting

The core SHALL check every setting the add-on reads, as it checks the same
setting in `config.yaml`. The add-on SHALL only read the saved form values,
rename form fields to their `config.yaml` names, and combine them with
`config.yaml`. It SHALL NOT decide whether a setting's value is valid. It SHALL
pass on any value it does not expect, so the core can reject it.

The Supervisor checks the form's values when the user saves them. That check is
a convenience, not a guarantee. A pier SHALL get the same result, and an error
that names the same setting, whether or not the Supervisor checked its values.

The add-on SHALL still stop with a configuration error when the saved values do
not have the shape it needs to run:

- The saved values are not valid JSON, or their root is not a mapping.
- Their `piers` is not a list.

The rules for combining the form with `config.yaml` stay with the add-on, as the
requirement "The add-on combines the Configuration form with config.yaml"
describes, because only the add-on has two sources.

#### Scenario: Values the Supervisor would refuse get the core's errors

- **WHEN** the saved form values list four piers
- **AND** one pier has a latitude of 95
- **AND** one pier has a `go_threshold` of 101
- **AND** one pier has `horizon_points` saved as the number 5
- **THEN** the service logs an error for each of those three piers
- **AND** each error names the same setting as the error for a `config.yaml`
  pier with the same value: `latitude`, `go_threshold` and `horizon.points`
- **AND** it publishes a verdict for the fourth pier

#### Scenario: Saved values that are not a mapping stop the add-on

- **WHEN** the saved form values are a list, not a mapping
- **THEN** the add-on stops with a configuration error that names the file of
  saved values

## MODIFIED Requirements

### Requirement: The form sets each pier's horizon

The service SHALL turn a form pier's horizon fields into that pier's horizon:

- When `min_altitude` is set, the pier's horizon SHALL be a flat floor at that
  altitude.
- When `horizon_points` is set, the service SHALL pass its value unchanged as
  the pier's `horizon.points`. The core SHALL then read and check it exactly as
  it reads and checks `horizon.points` in `config.yaml`.
- When neither is set, the pier's horizon SHALL come from `config.yaml`, as the
  requirement "The add-on combines the Configuration form with config.yaml"
  describes. When the file gives the pier no horizon either, the pier's horizon
  SHALL be flat at 0 degrees.

The service SHALL treat empty or blank `horizon_points` text as unset.

A pier whose horizon fails these rules SHALL be skipped with a logged error that
names the pier. The other piers SHALL still be published. This covers four
cases:

- `horizon_points` text that the core cannot read as a list of points. The
  error SHALL name `horizon.points`.
- a saved `horizon_points` value that is neither text nor a list of points. The
  error SHALL name `horizon.points`.
- points that fail the checks for inline points.
- both `min_altitude` and `horizon_points` set. This breaks the rule that a
  horizon has exactly one source.
- saved values that hold both a `horizon` value and a horizon field that is
  set. The service SHALL leave that pier's horizon fields as they were saved,
  and the core SHALL reject each set horizon field as a field it does not know.
  The error SHALL name each of those fields. The form has no `horizon` field, so
  this happens only when the saved values were written some other way.

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
- **THEN** the service logs an error that names that pier and `horizon.points`
- **AND** it publishes a verdict for the other pier

#### Scenario: Malformed saved values skip only their pier

- **WHEN** the saved form values list three piers
- **AND** one pier's `horizon_points` is the number 5, not text
- **AND** another entry in `piers` is not a mapping
- **THEN** the service logs an error for each of those two entries, naming
  `horizon.points` for the first
- **AND** it publishes a verdict for the third pier

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

#### Scenario: A horizon mapping beside horizon fields skips the pier

- **WHEN** the saved form values list two piers
- **AND** one pier holds a `horizon` mapping and sets `horizon_points`
- **THEN** the service logs an error that names that pier and `horizon_points`
  as a field the core does not know
- **AND** the add-on reports no error of its own for that pier
- **AND** it publishes a verdict for the other pier

#### Scenario: A bad horizon on the only pier stops the add-on

- **WHEN** the form lists one pier, and its `horizon_points` cannot be read
- **THEN** the service logs an error that names the pier and `horizon.points`
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
- saved values that hold both an `equipment` value and any equipment field.
  The service SHALL leave that pier's fields as they were saved, and the core
  SHALL reject each set `equipment_*` field as a field it does not know. The
  error SHALL name each of those fields. The form has no `equipment` field, so
  this happens only when the saved values were written some other way.

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

This holds for each of the four fields and both values.

#### Scenario: An equipment mapping beside equipment fields skips the pier

- **WHEN** the saved form values list two piers
- **AND** one pier holds an `equipment` mapping and sets
  `equipment_focal_length_mm`
- **THEN** the service logs an error that names that pier and
  `equipment_focal_length_mm` as a field the core does not know
- **AND** the add-on reports no error of its own for that pier
- **AND** it publishes a verdict for the other pier

#### Scenario: Incomplete equipment on the only pier stops the add-on

- **WHEN** the form lists one pier, and it sets only
  `equipment_focal_length_mm`
- **THEN** the service logs an error that names the pier
- **AND** the add-on stops with a configuration error that says no valid pier
  remains

### Requirement: The form sets each pier's GO threshold and wind-gust limit

The service SHALL pass a form pier's `go_threshold` and `max_gust` to that pier
when they are set. It SHALL then check them exactly as it checks the same
settings in `config.yaml`.

When a field is not set, the value SHALL come from `config.yaml`, as the
requirement "The add-on combines the Configuration form with config.yaml"
describes. When the file does not set it either, the pier SHALL behave as a file
pier without that setting:

- Without `go_threshold`, the pier SHALL use the default threshold of 65.
- Without `max_gust`, the pier SHALL have no wind gate. No forecast gust SHALL
  cause a `NO-GO`.

A field that is absent, saved as null, or saved as empty or blank text SHALL
count as not set. A `go_threshold` of 0 SHALL count as set.

When a pier's value fails these checks, the service SHALL skip that pier and
log an error that names the pier and the field. It SHALL still publish the other
piers. This covers a `go_threshold` below 0, above 100 or not a whole number, and a
`max_gust` of 0 or less. When every pier is skipped, the add-on SHALL stop with
a configuration error, as it does for any setup with no valid pier.

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

#### Scenario: Empty fields use the defaults

- **WHEN** the saved form values list a pier with `go_threshold` and `max_gust`
  each absent, saved as null, or saved as blank text
- **AND** `config.yaml` does not set them for that pier
- **THEN** the pier passes the service's checks
- **AND** its checked settings hold a `go_threshold` of 65 and no `max_gust`

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

#### Scenario: A bad value skips only its pier

- **WHEN** the saved form values list two piers
- **AND** one pier sets `max_gust` to 0, or `go_threshold` to 101
- **THEN** the service logs an error that names that pier and the field
- **AND** it publishes a verdict for the other pier


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
- **THEN** the service logs an error that names `backyard` and `horizon.points`
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

#### Scenario: Outside an add-on, the form is not read

- **WHEN** the service runs outside an add-on
- **THEN** it does not read the form's values
- **AND** it loads `config.yaml` on its own, exactly as before this change
