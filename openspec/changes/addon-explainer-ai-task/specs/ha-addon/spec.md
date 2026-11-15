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
- **AND** its `schema` declares `explainer` with an optional `enabled` of the
  bool type, an optional text `ai_task_entity`, and an optional `api_key` of the
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
- **AND** it gives a name and a description for `explainer` and each of its
  three fields: `enabled`, `ai_task_entity` and `api_key`

### Requirement: Each optional form field's description says it is optional

The English description of each form field the schema marks optional SHALL
contain the word `Optional.` The description of a field the schema requires
SHALL NOT contain it.

#### Scenario: Optional and required fields read differently

- **WHEN** the test suite reads the add-on config file and its English
  translation file
- **THEN** the description of each optional pier field, each of the four
  broker fields, `host` included, and each of the explainer's three fields
  contains `Optional.`
- **AND** the descriptions of `interval_seconds`, `id`, `latitude`,
  `longitude` and `elevation_m` do not contain `Optional.`

### Requirement: An explainer key on the form does not turn the explainer on

Inside an add-on, an `explainer.api_key` on the Configuration form SHALL NOT
turn the explainer on. Without `explainer.enabled` set to true on the form or in
`config.yaml`, the explainer SHALL stay off, as it does with a key in a file.

#### Scenario: A key alone leaves the explainer off

- **WHEN** the form lists a pier and sets `explainer.api_key`
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on starts and publishes a verdict for that pier
- **AND** it publishes no narrative entity

### Requirement: The add-on docs say where each explainer setting goes

The add-on's documentation SHALL have a section on turning on the explainer. It
SHALL describe two ways. With Home Assistant's AI Task, the user sets
**Enabled** and **AI Task entity** on the Configuration tab. With an API key, the
user puts it in the tab's **API key** field, and `explainer.enabled` and
`explainer.model` in `config.yaml`.

#### Scenario: The explainer section names both places

- **WHEN** the test suite reads the "Turn on the explainer" section of
  `ha-addon/DOCS.md`
- **THEN** it contains `**API key**`, `explainer.enabled`, `explainer.model`
  and `config.yaml`

#### Scenario: The explainer section names the AI Task fields

- **WHEN** the test suite reads the "Turn on the explainer" section of
  `ha-addon/DOCS.md`
- **THEN** it contains `**Enabled**`, `**AI Task entity**` and `AI Task`

### Requirement: Requests to the Supervisor bypass any proxy

The service SHALL send its requests, and the Supervisor's token, straight to the
Supervisor. It SHALL NOT send them through a proxy, even when the container's
environment names one.

#### Scenario: Proxy settings do not reach the token

- **WHEN** the container's environment sets `HTTP_PROXY` or `ALL_PROXY`
- **AND** the service asks the Supervisor for the broker
- **THEN** the request goes straight to the Supervisor, not through the proxy

#### Scenario: Proxy settings do not reach the AI Task request

- **WHEN** the container's environment sets `HTTP_PROXY` or `ALL_PROXY`
- **AND** the explainer asks an AI Task entity for a narrative
- **THEN** the request goes straight to the Supervisor, not through the proxy

## ADDED Requirements

### Requirement: The form's explainer block has three optional fields

The `explainer` setting of the Configuration form SHALL be a block of three
optional fields, in this order: `enabled`, a switch; `ai_task_entity`, text; and
`api_key`, the API key of the explainer's LLM provider, in a field that hides
its value. Its default SHALL be an empty block, so each field starts unset.

#### Scenario: The form declares the explainer's fields

- **WHEN** the test suite reads the add-on config file
- **THEN** its `schema` declares `explainer` with exactly the fields `enabled`
  as `bool?`, `ai_task_entity` as `str?` and `api_key` as `password?`, in that
  order
- **AND** its `options` set `explainer` to an empty block

### Requirement: The form's switch and AI Task entity turn on the AI Task narrative

Inside an add-on, a Configuration form that sets `explainer.enabled` to true and
`explainer.ai_task_entity` to an entity ID SHALL turn the explainer on with that
AI Task entity, with no `config.yaml`.

#### Scenario: Form-only AI Task setup

- **WHEN** the form lists a pier, sets `explainer.enabled` to true and
  `explainer.ai_task_entity` to `ai_task.openai`
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on starts and publishes a verdict and a narrative entity for
  that pier
- **AND** the explainer asks `ai_task.openai` for the narrative

### Requirement: Each explainer setting on the form joins config.yaml on its own

Inside an add-on, each of the form's `explainer.enabled`, `explainer.ai_task_entity`
and `explainer.api_key` SHALL count as a setting of its own. A setting given on
the form and in `config.yaml` SHALL stop the add-on with a configuration error
that names it. Explainer settings given in only one place SHALL combine.

#### Scenario: The switch in both places stops the add-on

- **WHEN** the form lists a pier and sets `explainer.enabled` to true
- **AND** `config.yaml` sets `explainer.enabled` to true
- **THEN** the add-on stops
- **AND** its configuration error names `explainer.enabled`

#### Scenario: A form entity combines with the file's switch

- **WHEN** the form lists a pier and sets `explainer.ai_task_entity` to
  `ai_task.openai`
- **AND** `config.yaml` sets `explainer.enabled` to true and `explainer.model`
- **THEN** the add-on starts, and reports no conflict for the explainer
- **AND** the explainer asks `ai_task.openai` for the narrative

### Requirement: The add-on asks for Home Assistant's Core API

The add-on's config file SHALL set `homeassistant_api` to true, so the explainer
can call Home Assistant's AI Task action through the Supervisor.

#### Scenario: The add-on config asks for the Core API

- **WHEN** the test suite reads the add-on config file
- **THEN** it sets `homeassistant_api` to true

### Requirement: The explainer section names both ways to write the narrative

The English description of the form's `explainer` setting SHALL say that
`explainer.enabled` turns the explainer on, and that the narrative comes from the
AI Task entity when one is set, or else from the model in `config.yaml` with the
API key.

#### Scenario: The explainer section names the switch and both ways

- **WHEN** the test suite reads the English translation file
- **THEN** the description of `explainer` contains `explainer.enabled`,
  `AI Task`, `explainer.model` and `config.yaml`

## REMOVED Requirements

### Requirement: The form's explainer block has one optional key field

**Reason**: The block now holds three optional fields; "The form's explainer
block has three optional fields" replaces it.
**Migration**: None for users. A saved `api_key` keeps its meaning, and the two
new fields start unset.

### Requirement: The explainer section says config.yaml turns the explainer on

**Reason**: The switch can now be set on the form too; "The explainer section
names both ways to write the narrative" replaces it.
**Migration**: None. The description still names `explainer.enabled` and
`config.yaml`.
