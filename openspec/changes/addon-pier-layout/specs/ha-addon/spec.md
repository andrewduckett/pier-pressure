## MODIFIED Requirements

### Requirement: The form's setting names match the names in config.yaml

The names of the Configuration form's settings SHALL match the names of the
same settings in `config.yaml`. The horizon and equipment fields are the
exception: a pier's fields stay in one flat list, without a `horizon` or
`equipment` block. `min_altitude` SHALL hold the value of the file's
`horizon.min_altitude`, and `horizon_points` the value of `horizon.points`.
Each `equipment_<name>` field SHALL hold the value of the file's
`equipment.<name>`.

#### Scenario: Flat form fields become the file's horizon and equipment blocks

- **WHEN** the saved form values give a pier a `min_altitude` of 15 and an
  `equipment_focal_length_mm` of 400
- **THEN** the service reads that pier with a `horizon` block whose
  `min_altitude` is 15, and an `equipment` block whose `focal_length_mm` is
  400, as a pier in `config.yaml` names them

## ADDED Requirements

### Requirement: A pier's fields appear in four sections after its id

A pier's fields on the Configuration form SHALL appear in this order, after the
pier's `id`, grouped in four sections:

| Section | Fields |
|---|---|
| Location | `latitude`, `longitude`, `elevation_m` |
| Horizon | `min_altitude`, `horizon_points` |
| Equipment | `equipment_focal_length_mm`, `equipment_sensor_width_mm`, `equipment_sensor_height_mm`, `equipment_reducer` |
| Verdict | `go_threshold`, `max_gust` |

#### Scenario: The schema lists the pier fields in section order

- **WHEN** the test suite reads the add-on config file
- **THEN** each pier item in its `schema` lists `id`, then the Location,
  Horizon, Equipment and Verdict fields, in the order the table gives

### Requirement: Each pier field's label names its section

Each pier field's English label SHALL start with its section's name, a colon
and a space, followed by the field's name in lower-case words. `GO` SHALL stay
upper case, because it is the verdict's own value. The label of `id` SHALL be
`Pier ID`, with no section.

#### Scenario: Each pier label names its section

- **WHEN** the test suite reads the add-on's English translation file
- **THEN** the pier fields' labels are exactly: `Pier ID`,
  `Location: latitude`, `Location: longitude`, `Location: elevation`,
  `Horizon: floor`, `Horizon: points`, `Equipment: focal length`,
  `Equipment: sensor width`, `Equipment: sensor height`,
  `Equipment: reducer or barlow`, `Verdict: GO threshold` and
  `Verdict: wind-gust limit`, for `id` and the fields in section order

### Requirement: The first field of each pier section introduces the section

The English description of each section's first field SHALL start with the
section's name and a colon, followed by one sentence that introduces the
section. No other pier field's description SHALL start that way.

#### Scenario: Each section's first field introduces the section

- **WHEN** the test suite reads the English translation file
- **THEN** the descriptions of `latitude`, `min_altitude`,
  `equipment_focal_length_mm` and `go_threshold` start with `Location:`,
  `Horizon:`, `Equipment:` and `Verdict:`
- **AND** no other pier field's description starts with a section's name and a
  colon
