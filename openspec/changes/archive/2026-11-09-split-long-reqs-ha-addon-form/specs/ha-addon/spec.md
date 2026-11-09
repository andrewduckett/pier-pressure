## ADDED Requirements

### Requirement: The Configuration form declares the interval, the piers and the broker

The add-on SHALL declare a Configuration form in Home Assistant with three
settings: `interval_seconds`, `piers` and `mqtt`, the broker.

- `interval_seconds`: the recompute interval in seconds, a whole number of at
  least 1. Its default SHALL be 900.
- `piers`: a list of piers. Each pier SHALL have an `id` (text), a `latitude`
  (from −90 to 90 degrees), a `longitude` (from −180 to 180 degrees) and an
  `elevation_m` (metres). The default SHALL be an empty list.

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
- **AND** each pier item has an optional `go_threshold`, a whole number from 0
  to 100, and an optional `max_gust`, a number of at least 0
- **AND** its `schema` declares `mqtt` with an optional text `host`, an optional
  `port`, an optional text `username`, and an optional `password` of the
  password type

### Requirement: The form's broker block has four optional fields

The `mqtt` setting of the Configuration form SHALL be a block of four optional
fields. Its default SHALL be an empty block. It SHALL have these fields:

- `host`: the broker's host name or address, as text.
- `port`: the broker's port, from 1 to 65535. It SHALL have no default on the
  form.
- `username`: the login name, as text.
- `password`: the login password, in a field that hides its value.

#### Scenario: The form declares the broker's four fields

- **WHEN** the test suite reads the add-on config file
- **THEN** its `schema` declares `mqtt` with an optional text `host`, an optional
  `port`, an optional text `username`, and an optional `password` of the
  password type
- **AND** its `options` set `mqtt` to an empty block, so `port` has no default

### Requirement: Each pier on the form has two optional horizon fields

Each pier on the Configuration form SHALL have two optional horizon fields:

- `min_altitude`: a flat horizon floor, from 0 to 90 degrees.
- `horizon_points`: horizon points as text. On save, the form SHALL accept empty
  or blank text, or text that opens with two square brackets and closes with
  two, as a list of pairs does. Spaces may sit between the brackets and around
  the text. It SHALL reject any other text.

#### Scenario: The save check on horizon points

- **WHEN** the test suite applies the schema's check for `horizon_points` to
  sample text
- **THEN** it accepts `[[0, 10], [90, 25]]`, empty text and blank text
- **AND** it rejects `[0, 10], [90, 25]` and `[[0, 10]] extra`

### Requirement: Each pier on the form has four optional equipment fields

Each pier on the Configuration form SHALL have four optional equipment fields.
On save, the form SHALL accept a number of at least 0 in each. The service then
rejects 0.

- `equipment_focal_length_mm`: the telescope's focal length, in millimetres.
- `equipment_sensor_width_mm`: the camera sensor's width, in millimetres.
- `equipment_sensor_height_mm`: the camera sensor's height, in millimetres.
- `equipment_reducer`: a focal reducer or barlow factor, with no unit.

#### Scenario: The form declares the four equipment fields

- **WHEN** the test suite reads the add-on config file
- **THEN** each pier item in its `schema` has an optional
  `equipment_focal_length_mm`, `equipment_sensor_width_mm`,
  `equipment_sensor_height_mm` and `equipment_reducer`, each a number of at
  least 0

### Requirement: Each pier on the form has two optional gate fields

Each pier on the Configuration form SHALL have two optional gate fields:

- `go_threshold`: the score a night needs for `GO`, a whole number from 0 to
  100.
- `max_gust`: the wind-gust limit, in km/h. On save, the form SHALL accept a
  number of at least 0. The service then rejects 0.

#### Scenario: The form declares the two gate fields

- **WHEN** the test suite reads the add-on config file
- **THEN** each pier item in its `schema` has an optional `go_threshold`, a
  whole number from 0 to 100, and an optional `max_gust`, a number of at least 0

### Requirement: The form's setting names match the names in config.yaml

The names of the Configuration form's settings SHALL match the names of the
same settings in `config.yaml`. The horizon and equipment fields are the
exception, because a form cannot nest a `horizon` or `equipment` block inside a
pier. `min_altitude` SHALL hold the value of the file's `horizon.min_altitude`,
and `horizon_points` the value of `horizon.points`. Each `equipment_<name>`
field SHALL hold the value of the file's `equipment.<name>`.

#### Scenario: Flat form fields become the file's horizon and equipment blocks

- **WHEN** the saved form values give a pier a `min_altitude` of 15 and an
  `equipment_focal_length_mm` of 400
- **THEN** the service reads that pier with a `horizon` block whose
  `min_altitude` is 15, and an `equipment` block whose `focal_length_mm` is
  400, as a pier in `config.yaml` names them

### Requirement: Every form field has an English label and description

Each field of the Configuration form SHALL have a label and a description in
English, and each description of a number SHALL name its unit or say it has
none.

#### Scenario: Every form field has a label

- **WHEN** the test suite reads the add-on's English translation file
- **THEN** it gives a name and a description for `interval_seconds`, `piers`, and
  each field of a pier, including `min_altitude`, `horizon_points`, the four
  equipment fields, `go_threshold` and `max_gust`
- **AND** the descriptions of `go_threshold` and `max_gust` say what an empty
  field means: a threshold of 65, and no wind gate
- **AND** it gives a name and a description for `mqtt` and each of its four
  fields

### Requirement: The add-on builds one set of settings from the form and config.yaml

Inside an add-on, the service SHALL read the values the user saved on the
Configuration form at startup. The service SHALL also read `config.yaml` from
the add-on's config folder when that file exists. The file MAY add any setting
the form leaves unset. The service SHALL build one set of settings from the two
sources. It SHALL then check those settings exactly as it checks a
`config.yaml` on its own.

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

#### Scenario: The file adds the topic names

- **WHEN** the form lists a pier
- **AND** `config.yaml` sets `mqtt.base_topic` to `observatory` and sets no other
  `mqtt` field
- **THEN** the service publishes under the base topic `observatory`

### Requirement: An empty or blank form field counts as not set

Inside an add-on, a Configuration form field that is absent, saved as null, or
saved as empty or blank text SHALL count as not set. This rule SHALL hold for
number fields too. A value of 0 SHALL count as set. The form always sets
`interval_seconds`.

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

### Requirement: A pier in config.yaml adds its settings to the form pier with its id

A pier in `config.yaml` SHALL add its settings to the pier on the Configuration
form with the same `id`. A pier's `id` only matches the two sources. It
SHALL NOT count as a setting, and the combined pier SHALL keep the form's `id`.

#### Scenario: The file adds pier settings the form does not show

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists the pier `backyard` with `go_threshold` set to 75
  and `max_gust` set to 40
- **THEN** the pier's GO threshold is 75
- **AND** the pier's wind gate uses a gust limit of 40

#### Scenario: A file pier with only an id adds nothing

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists the pier `backyard` with no other key
- **THEN** the add-on starts, and reports no conflict for `id`
- **AND** the service publishes a verdict for `backyard`
- **AND** its log says the settings came from the Configuration tab

#### Scenario: Horizon points from the file are used

- **WHEN** the form lists the pier `backyard` with no horizon field set
- **AND** `config.yaml` lists the pier `backyard` with `horizon.points` set to
  `[[0, 10], [180, 20]]`
- **THEN** the pier's horizon equals the horizon of those two points

### Requirement: A setting given on the form and in config.yaml stops the add-on

Each setting SHALL come from the Configuration form or from `config.yaml`, never
from both. When a setting is given in both, the add-on SHALL stop with a
configuration error. The error SHALL name the setting, and the pier when it is a
pier's setting. It SHALL NOT contain the setting's value. Every setting outside
the groups that count as one setting, such as a pier's `go_threshold` or
`mqtt.base_topic`, SHALL count as a setting of its own.

#### Scenario: A pier key in both stops the add-on

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` sets `latitude` for the pier `backyard`
- **THEN** the add-on stops
- **AND** its configuration error names `latitude` and `backyard`

### Requirement: A pier's horizon and its equipment each count as one setting

In the rule that each setting comes from the Configuration form or from
`config.yaml`, never from both, each of these groups SHALL count as one setting:

- a pier's horizon: the form's `min_altitude` or `horizon_points`, or the file's
  `horizon` block.
- a pier's equipment: any of the form's four equipment fields, or the file's
  `equipment` block.

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

### Requirement: The broker connection and the recompute interval each count as one setting

In the rule that each setting comes from the Configuration form or from
`config.yaml`, never from both, each of these groups SHALL count as one setting:

- the broker connection: any of `mqtt.host`, `mqtt.port`, `mqtt.username` and
  `mqtt.password`.
- the recompute interval: the form's `interval_seconds`, or the file's
  `recompute` block.

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

### Requirement: A pier in config.yaml that the form does not list stops the add-on

When `config.yaml` lists a pier `id` that the Configuration form does not list,
the add-on SHALL stop with a configuration error. The error SHALL name the `id`.
A pier the form lists SHALL count as listed, even when the service skips it as
invalid.

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

### Requirement: A pier id repeated in config.yaml stops the add-on

When `config.yaml` lists the same pier `id` more than once, the add-on SHALL
stop with a configuration error. The error SHALL name the `id`.

#### Scenario: A pier listed twice in the file stops the add-on

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists the pier `backyard` twice
- **THEN** the add-on stops
- **AND** its configuration error names `backyard`

### Requirement: A pier list of the wrong shape in config.yaml stops the add-on

The add-on SHALL stop with a configuration error when the `piers` of
`config.yaml` is not a list, or when a pier in that list is not a mapping, or
its `id` is missing or is not text. For such a pier, the error SHALL name the
entry's position in the file's `piers` list.

#### Scenario: A file pier id that is not text stops the add-on

- **WHEN** the form lists the pier `backyard`
- **AND** the first pier in `config.yaml` has an `id` that is null, a number, a
  list or a mapping
- **THEN** the add-on stops
- **AND** its configuration error names the first entry of the file's `piers`
  list

This holds for each of the four kinds of value.

### Requirement: A config.yaml that is not a valid YAML mapping stops the add-on

When `config.yaml` is not valid YAML, or its root is not a mapping, the add-on
SHALL stop with a configuration error. The error SHALL name the file. For a YAML
mistake, it SHALL also name the line and column, and SHALL hold no other detail
from the YAML parser.

#### Scenario: A config.yaml that is not valid YAML stops the add-on

- **WHEN** the form lists a pier
- **AND** `config.yaml` is not valid YAML
- **THEN** the add-on stops
- **AND** its configuration error names `/config/config.yaml`

### Requirement: One configuration error lists every problem the combine finds

When the add-on finds problems in combining the Configuration form with
`config.yaml`, its configuration error SHALL list every problem it finds, not
only the first.

#### Scenario: One error lists every problem

- **WHEN** the form lists the pier `backyard` with `min_altitude` set
- **AND** `config.yaml` gives `backyard` a `horizon` block, and lists the pier
  `roof`
- **THEN** the add-on stops with one configuration error
- **AND** that error names the `horizon` of `backyard`, and names `roof`

### Requirement: No combine error quotes config.yaml or a setting's value

When the add-on combines the Configuration form with `config.yaml`, no error
SHALL quote the content of `config.yaml` or the value of any setting.

#### Scenario: A YAML error does not quote the file

- **WHEN** the form lists a pier
- **AND** line 3 of `config.yaml` is `  password: [pw-8c41f2` or
  `  password: *pw-8c41f2`, either of which is not valid YAML
- **THEN** the add-on stops
- **AND** its configuration error names `/config/config.yaml` and line 3
- **AND** no log line or error message contains `pw-8c41f2`

This holds for both lines.

### Requirement: An id or key name in a combine error stays on one line

When the add-on combines the Configuration form with `config.yaml`, an `id` or
key name in an error SHALL be shown with any line break or other control
character escaped, so the error stays on one line.

#### Scenario: A control character in an id stays escaped

- **WHEN** the form lists the pier `backyard`
- **AND** `config.yaml` lists a pier whose `id` holds a line break
- **THEN** the add-on stops with one configuration error
- **AND** that error is a single line, with the line break shown escaped

### Requirement: A relative horizon file path in config.yaml is read from the add-on's config folder

Inside an add-on, a relative horizon `file` path in `config.yaml` SHALL be read
from the add-on's config folder.

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

### Requirement: Each pier is checked after the file's settings are added to it

Inside an add-on, the service SHALL check each pier after the settings from
`config.yaml` are added to it. A pier that fails the check SHALL be skipped with
a logged error, and the other piers SHALL still be published.

#### Scenario: An unreadable horizon file skips only its pier

- **WHEN** the form lists the piers `backyard` and `roof`
- **AND** `config.yaml` gives `backyard` a horizon `file` that does not exist in
  the add-on's config folder
- **THEN** the service logs an error that names `backyard`
- **AND** it publishes a verdict for `roof`

#### Scenario: A bad pier in the saved form values is skipped

- **WHEN** the saved form values list two piers, and one has a latitude of 95
- **THEN** the service logs an error that names the skipped pier
- **AND** it publishes a verdict for the other pier

### Requirement: A Configuration form with no piers stops the add-on

Inside an add-on, the Configuration form SHALL list at least one pier. When the
form lists no piers, the add-on SHALL stop with a configuration error. The error
SHALL say that nothing is set up, and SHALL tell the user to add a pier on the
Configuration tab.

#### Scenario: Nothing is set up

- **WHEN** the form lists no piers
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on stops
- **AND** its configuration error says that nothing is set up, and tells the user
  to add a pier on the Configuration tab

### Requirement: The empty-form error names the piers that config.yaml lists

When the Configuration form lists no piers and `config.yaml` lists piers, the
add-on's configuration error SHALL also name those piers. It SHALL say that
`config.yaml` cannot list piers on its own. It SHALL tell the user to add each of
those piers on the Configuration tab with the same `id`, and to keep only the
extra settings in `config.yaml`.

#### Scenario: An empty form names the file's piers

- **WHEN** the form lists no piers
- **AND** `config.yaml` lists the piers `roof` and `shed`
- **THEN** the add-on stops without publishing a verdict
- **AND** its configuration error says that nothing is set up, and names `roof`
  and `shed`
- **AND** it says that `config.yaml` cannot list piers on its own
- **AND** it tells the user to add each pier on the Configuration tab with the
  same `id`, and to keep only the extra settings in `config.yaml`

### Requirement: The log says whether config.yaml added a setting

Inside an add-on, when `config.yaml` adds at least one setting, the log SHALL
say that the settings came from the Configuration tab and `config.yaml`.
Otherwise, it SHALL say that they came from the Configuration tab.

#### Scenario: A broker from config.yaml is logged as from both sources

- **WHEN** the form lists the pier `backyard` and sets no broker field
- **AND** `config.yaml` sets `mqtt.host`, `mqtt.username` and `mqtt.password`
- **THEN** its log says the settings came from the Configuration tab and
  `config.yaml`

### Requirement: Outside an add-on, the service does not read the Configuration form

Outside an add-on, the service SHALL NOT read the Configuration form's values.
It SHALL load `config.yaml` on its own, as it did before the add-on could read
the form.

#### Scenario: Outside an add-on, the form is not read

- **WHEN** the service runs outside an add-on
- **THEN** it does not read the form's values
- **AND** it loads `config.yaml` on its own, exactly as before this change

## REMOVED Requirements

### Requirement: The add-on offers a Configuration form for the interval and piers

**Reason**: It bundled seven behaviors. It is split into "The Configuration form declares the interval, the piers and the broker", "The form's broker block has four optional fields", "Each pier on the form has two optional horizon fields", "Each pier on the form has four optional equipment fields", "Each pier on the form has two optional gate fields", "The form's setting names match the names in config.yaml" and "Every form field has an English label and description", with the same meaning, and every scenario carried over word for word.

**Migration**: None. Nothing changes for users or code.

### Requirement: The add-on combines the Configuration form with config.yaml

**Reason**: It bundled nineteen behaviors. It is split into "The add-on builds one set of settings from the form and config.yaml", "An empty or blank form field counts as not set", "A pier in config.yaml adds its settings to the form pier with its id", "A setting given on the form and in config.yaml stops the add-on", "A pier's horizon and its equipment each count as one setting", "The broker connection and the recompute interval each count as one setting", "A pier in config.yaml that the form does not list stops the add-on", "A pier id repeated in config.yaml stops the add-on", "A pier list of the wrong shape in config.yaml stops the add-on", "A config.yaml that is not a valid YAML mapping stops the add-on", "One configuration error lists every problem the combine finds", "No combine error quotes config.yaml or a setting's value", "An id or key name in a combine error stays on one line", "A relative horizon file path in config.yaml is read from the add-on's config folder", "Each pier is checked after the file's settings are added to it", "A Configuration form with no piers stops the add-on", "The empty-form error names the piers that config.yaml lists", "The log says whether config.yaml added a setting" and "Outside an add-on, the service does not read the Configuration form", with the same meaning, and every scenario carried over word for word.

**Migration**: None. Nothing changes for users or code.
