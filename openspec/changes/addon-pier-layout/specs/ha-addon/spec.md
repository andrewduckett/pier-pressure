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
horizon and equipment fields are the exception: a pier's fields stay in one
flat list, without a `horizon` or `equipment` block. `min_altitude` SHALL hold
the value of the file's `horizon.min_altitude`, and `horizon_points` the value
of `horizon.points`. Each `equipment_<name>` field SHALL hold the value of the
file's `equipment.<name>`. Each form field SHALL have a label and a description
in English, and each description of a number SHALL name its unit or say it has
none.

A pier's fields SHALL appear in this order, in four sections after the pier's
`id`. Each field's English label SHALL start with its section's name, a colon
and a space, such as `Horizon: floor`. The `id` label SHALL have no section.

| Section | Fields |
|---|---|
| Location | `latitude`, `longitude`, `elevation_m` |
| Horizon | `min_altitude`, `horizon_points` |
| Equipment | `equipment_focal_length_mm`, `equipment_sensor_width_mm`, `equipment_sensor_height_mm`, `equipment_reducer` |
| Verdict | `go_threshold`, `max_gust` |

The description of each section's first field SHALL start with the section's
name and a colon, followed by one sentence that introduces the section. No
other field's description SHALL start that way.

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

#### Scenario: Each pier label names its section

- **WHEN** the test suite reads the add-on config file and its English
  translation file
- **THEN** the pier fields in the schema follow the order `id`, then the
  Location, Horizon, Equipment and Verdict fields as the table lists them
- **AND** the label of each of those fields starts with its section's name and
  `: `, such as `Location: latitude` and `Verdict: wind-gust limit`
- **AND** the label of `id` is `Pier ID`

#### Scenario: Each section's first field introduces the section

- **WHEN** the test suite reads the English translation file
- **THEN** the descriptions of `latitude`, `min_altitude`,
  `equipment_focal_length_mm` and `go_threshold` start with `Location:`,
  `Horizon:`, `Equipment:` and `Verdict:`
- **AND** no other pier field's description starts with a section's name and a
  colon
