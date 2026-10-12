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

Each pier SHALL also have two optional gate fields, as described in "The form
sets each pier's GO threshold and wind-gust limit":

- `go_threshold`: the score a night needs for `GO`, a whole number from 0 to
  100.
- `max_gust`: the wind-gust limit, in km/h. On save, the form SHALL accept a
  number of at least 0. The service then rejects 0.

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
- **AND** each pier item has an optional `go_threshold`, a whole number from 0
  to 100, and an optional `max_gust`, a number of at least 0
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
  each field of a pier, including `min_altitude`, `horizon_points`, the four
  equipment fields, `go_threshold` and `max_gust`
- **AND** the descriptions of `go_threshold` and `max_gust` say what an empty
  field means: a threshold of 65, and no wind gate
- **AND** it gives a name and a description for `mqtt` and each of its four
  fields


## ADDED Requirements

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

A pier whose value fails these checks SHALL be skipped with a logged error that
names the pier and the field. The other piers SHALL still be published. This
covers a `go_threshold` below 0, above 100 or not a whole number, and a
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
- **THEN** the pier gets a verdict
- **AND** it uses a GO threshold of 65
- **AND** it has no wind gate

#### Scenario: config.yaml fills an empty field

- **WHEN** the saved form values list the pier `backyard` with `max_gust` saved
  as null
- **AND** `config.yaml` lists `backyard` with `max_gust` set to 40
- **THEN** the pier's wind gate uses a gust limit of 40
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

The Supervisor normally refuses to save a `go_threshold` over 100. The service
still checks it, because it does not rely on the Supervisor's check.
