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

These names SHALL match the names of the same settings in `config.yaml`. The two
horizon fields are the exception, because a form cannot nest a `horizon` block
inside a pier. `min_altitude` SHALL hold the value of the file's
`horizon.min_altitude`, and `horizon_points` the value of `horizon.points`. Each
form field SHALL have a label and a description in English, and each description
of a number SHALL name its unit.

#### Scenario: Add-on config declares the form

- **WHEN** the test suite reads the add-on config file
- **THEN** its `options` set `interval_seconds` to 900 and `piers` to an empty
  list
- **AND** its `schema` declares `interval_seconds` as a whole number, and `piers`
  as a list whose items have `id`, `latitude`, `longitude` and `elevation_m`
- **AND** each pier item has an optional `min_altitude` from 0 to 90 and an
  optional `horizon_points`

#### Scenario: The save check on horizon points

- **WHEN** the test suite applies the schema's check for `horizon_points` to
  sample text
- **THEN** it accepts `[[0, 10], [90, 25]]`, empty text and blank text
- **AND** it rejects `[0, 10], [90, 25]` and `[[0, 10]] extra`

#### Scenario: Every form field has a label

- **WHEN** the test suite reads the add-on's English translation file
- **THEN** it gives a name and a description for `interval_seconds`, `piers`, and
  each field of a pier, including `min_altitude` and `horizon_points`

## ADDED Requirements

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
