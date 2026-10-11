## MODIFIED Requirements

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

Each pier SHALL also have four optional equipment fields. Each SHALL be a number
of at least 0:

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

## ADDED Requirements

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
that names the pier. The other piers SHALL still be published. This covers two
cases:

- a missing focal length, sensor width or sensor height, while another
  equipment field is set. The error SHALL name the missing field.
- a value of 0 or less.

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

#### Scenario: Equipment from the form ranks on field-of-view fit

- **WHEN** the form lists a pier with focal length, sensor width and sensor
  height set
- **THEN** the pier's verdict ranks its targets with a field-of-view term

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

#### Scenario: A zero value skips only that pier

- **WHEN** the form lists two piers
- **AND** one pier sets all three required equipment fields, with
  `equipment_focal_length_mm` set to 0
- **THEN** the service logs an error that names that pier
- **AND** it publishes a verdict for the other pier

#### Scenario: Incomplete equipment on the only pier stops the add-on

- **WHEN** the form lists one pier, and it sets only
  `equipment_focal_length_mm`
- **THEN** the service logs an error that names the pier
- **AND** the add-on stops with a configuration error that says no valid pier
  remains
