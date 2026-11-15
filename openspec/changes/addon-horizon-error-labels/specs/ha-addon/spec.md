## ADDED Requirements

### Requirement: The error for both horizon fields on the form names their labels

Inside an add-on, when a pier on the Configuration form sets both
`min_altitude` and `horizon_points`, the logged error that skips the pier SHALL
name the labels `Horizon: floor` and `Horizon: points`, and SHALL say to fill in
one of them at most. It SHALL NOT name `min_altitude`. The core SHALL still
decide that the pier is invalid. An error the core reports for another setting
of the same pier SHALL be logged as the core words it.

#### Scenario: Both horizon fields on the form name their labels

- **WHEN** the form lists two piers
- **AND** one pier sets `min_altitude` to 10 and `horizon_points` to
  `[[0, 5], [180, 10]]`
- **THEN** the service logs an error that names that pier, `Horizon: floor` and
  `Horizon: points`
- **AND** the error does not contain `min_altitude`
- **AND** it publishes a verdict for the other pier

#### Scenario: Another error in the same pier keeps the core's wording

- **WHEN** a form pier sets both `min_altitude` and `horizon_points`
- **AND** the same pier has a latitude of 95
- **THEN** the logged error names `Horizon: floor` and `Horizon: points`
- **AND** it names `latitude`, as the error for a `config.yaml` pier with that
  latitude does

### Requirement: A horizon from config.yaml with two sources keeps the file's names

Inside an add-on, when a form pier sets neither horizon field and its entry in
`config.yaml` gives a `horizon` block with both `points` and `min_altitude`, the
logged error that skips the pier SHALL be the one a `config.yaml` pier outside
an add-on gets. It SHALL name `points` and `min_altitude`, and SHALL NOT name a
form label.

#### Scenario: Two horizon sources in config.yaml name the file's keys

- **WHEN** the form lists a pier with no horizon field set
- **AND** `config.yaml` gives that pier a `horizon` block with `points` and
  `min_altitude`
- **THEN** the service logs an error that names that pier, `points` and
  `min_altitude`
- **AND** the error does not contain `Horizon: floor`

### Requirement: The horizon docs name both labels for the both-fields error

The "Set a pier's horizon" section of the add-on's documentation SHALL say that
the error for a pier that fills in both horizon fields names
**Horizon: floor** and **Horizon: points**.

#### Scenario: The horizon section names the error's labels

- **WHEN** the test suite reads the "Set a pier's horizon" section of
  `ha-addon/DOCS.md`
- **THEN** a sentence that contains `error` also contains
  `**Horizon: floor**` and `**Horizon: points**`
