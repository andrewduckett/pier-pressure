## RENAMED Requirements

- FROM: `### Requirement: The Configuration form declares the interval, the piers and the broker`
- TO: `### Requirement: The Configuration form declares the interval, the piers, the broker and the explainer`

## MODIFIED Requirements

### Requirement: The Configuration form declares the interval, the piers, the broker and the explainer

The add-on SHALL declare a Configuration form with four settings, in this
order: `interval_seconds`, `piers`, `mqtt`, the broker, and `explainer`.

- `interval_seconds`: the recompute interval in seconds, a whole number of at
  least 1. Its default SHALL be 900.
- `piers`: a list of piers. Each pier SHALL have an `id` (text), a `latitude`
  (from −90 to 90 degrees), a `longitude` (from −180 to 180 degrees) and an
  `elevation_m` (metres). The default SHALL be an empty list.

#### Scenario: Add-on config declares the form

- **WHEN** the test suite reads the add-on config file
- **THEN** its `options` set `interval_seconds` to 900, `piers` to an empty
  list, and `mqtt` and `explainer` each to an empty block
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
- **AND** its `schema` declares `explainer` with an optional `api_key` of the
  password type
- **AND** its `schema` lists `interval_seconds`, `piers`, `mqtt` and
  `explainer` in that order

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
- **AND** it gives a name and a description for `explainer` and its `api_key`

### Requirement: Each optional form field's description says it is optional

The English description of each form field the schema marks optional SHALL
contain the word `Optional.` The description of a field the schema requires
SHALL NOT contain it.

#### Scenario: Optional and required fields read differently

- **WHEN** the test suite reads the add-on config file and its English
  translation file
- **THEN** the description of each optional pier field, each of the four
  broker fields, `host` included, and the explainer's `api_key` contains
  `Optional.`
- **AND** the descriptions of `interval_seconds`, `id`, `latitude`,
  `longitude` and `elevation_m` do not contain `Optional.`

### Requirement: The add-on's setup steps follow the Configuration tab's order

The "Set up the add-on" section of the add-on's documentation SHALL walk
through the Configuration tab in the order the tab shows it. It SHALL name, in
bold, the Recompute interval, the Piers, the Pier ID, the Location, Horizon,
Equipment and Verdict fields, the MQTT broker and the Explainer, in that order.

#### Scenario: The setup steps name the tab's parts in order

- **WHEN** the test suite reads the "Set up the add-on" section of
  `ha-addon/DOCS.md`
- **THEN** it names in bold `Recompute interval`, `Piers`, `Pier ID`,
  `Location`, `Horizon`, `Equipment`, `Verdict`, `MQTT broker` and
  `Explainer`, each first named after the one before it

#### Scenario: A part out of order fails the check

- **WHEN** the section names **MQTT broker** in bold before **Piers**
- **THEN** the test suite fails, naming `MQTT broker`

## ADDED Requirements

### Requirement: The form's explainer block has one optional key field

The `explainer` setting of the Configuration form SHALL be a block with one
optional field, `api_key`: the API key of the explainer's LLM provider, in a
field that hides its value. Its default SHALL be an empty block.

#### Scenario: The form declares the explainer key

- **WHEN** the test suite reads the add-on config file
- **THEN** its `schema` declares `explainer` with exactly one field, an optional
  `api_key` of the password type
- **AND** its `options` set `explainer` to an empty block

### Requirement: An explainer key on the form sets the explainer's API key

Inside an add-on, the Configuration form's `explainer.api_key` SHALL become the
explainer's API key, as `explainer.api_key` in `config.yaml` does. The other
explainer settings SHALL still come from `config.yaml` or their defaults.

#### Scenario: The form's key reaches the explainer

- **WHEN** the form lists a pier and sets `explainer.api_key` to `sk-8c41f2`
- **AND** `config.yaml` sets `explainer.enabled` to true and `explainer.model`
  to `openai:gpt-4o`
- **THEN** the explainer runs with the model `openai:gpt-4o` and the API key
  `sk-8c41f2`
- **AND** the log says the settings came from the Configuration tab and
  config.yaml

### Requirement: An explainer key on the form does not turn the explainer on

Inside an add-on, an `explainer.api_key` on the Configuration form SHALL NOT
turn the explainer on. Without `explainer.enabled` set to true in
`config.yaml`, the explainer SHALL stay off, as it does with a key in a file.

#### Scenario: A key alone leaves the explainer off

- **WHEN** the form lists a pier and sets `explainer.api_key`
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on starts and publishes a verdict for that pier
- **AND** it publishes no narrative entity

### Requirement: A blank explainer key on the form counts as not set

Inside an add-on, an `explainer.api_key` on the Configuration form that is
absent, null, empty or blank SHALL count as not set.

#### Scenario: A blank key leaves the file's key in use

- **WHEN** the form lists a pier and saves `explainer.api_key` as blank text
- **AND** `config.yaml` sets `explainer.enabled` to true and
  `explainer.api_key` to `sk-8c41f2`
- **THEN** the add-on starts, and reports no conflict for `explainer.api_key`
- **AND** the explainer runs with the API key `sk-8c41f2`

### Requirement: An explainer key on the form and in config.yaml stops the add-on

Inside an add-on, when the Configuration form and `config.yaml` both set
`explainer.api_key`, the add-on SHALL stop with a configuration error that
names `explainer.api_key`. The error SHALL NOT contain either key.

#### Scenario: A key in both stops the add-on

- **WHEN** the form lists a pier and sets `explainer.api_key` to `sk-8c41f2`
- **AND** `config.yaml` sets `explainer.api_key` to `sk-file-5d07`
- **THEN** the add-on stops
- **AND** its configuration error names `explainer.api_key`
- **AND** no log line or error message contains `sk-8c41f2` or `sk-file-5d07`

#### Scenario: Other explainer settings in the file do not conflict

- **WHEN** the form lists a pier and sets `explainer.api_key`
- **AND** `config.yaml` sets `explainer.enabled` and `explainer.model`, but not
  `explainer.api_key`
- **THEN** the add-on starts, and reports no conflict for the explainer

### Requirement: An explainer in config.yaml that is not a mapping stops the add-on

Inside an add-on, when the Configuration form sets `explainer.api_key` and
`config.yaml` gives `explainer` a value that is not a mapping, the add-on SHALL
stop with a configuration error that says `explainer` in `config.yaml` must be
a mapping of settings. The error SHALL NOT contain the file's value.

#### Scenario: An explainer list in the file stops the add-on

- **WHEN** the form lists a pier and sets `explainer.api_key`
- **AND** `config.yaml` sets `explainer` to the list `[sk-file-5d07]`
- **THEN** the add-on stops
- **AND** its configuration error says `explainer` in config.yaml must be a
  mapping
- **AND** no log line or error message contains `sk-file-5d07`

### Requirement: No log line or error reveals the form's explainer key

Inside an add-on, the service SHALL NOT insert the Configuration form's
`explainer.api_key` into a log line or an error message.

#### Scenario: A failed explainer call does not reveal the form's key

- **WHEN** the form lists a pier and sets `explainer.api_key` to `sk-8c41f2`
- **AND** `config.yaml` sets `explainer.enabled` to true
- **AND** the explainer's call to its LLM provider fails
- **THEN** the add-on still publishes the pier's verdict
- **AND** no log line contains `sk-8c41f2`

### Requirement: The explainer section says config.yaml turns the explainer on

The English description of the form's `explainer` setting SHALL say that
`explainer.enabled` in `config.yaml` turns the explainer on.

#### Scenario: The explainer section names the switch

- **WHEN** the test suite reads the English translation file
- **THEN** the description of `explainer` contains `explainer.enabled` and
  `config.yaml`

### Requirement: The add-on docs say where each explainer setting goes

The add-on's documentation SHALL have a section on turning on the explainer. It
SHALL say to put the API key in the Configuration tab's **API key** field, and
`explainer.enabled` and `explainer.model` in `config.yaml`.

#### Scenario: The explainer section names both places

- **WHEN** the test suite reads the "Turn on the explainer" section of
  `ha-addon/DOCS.md`
- **THEN** it contains `**API key**`, `explainer.enabled`, `explainer.model`
  and `config.yaml`
