## MODIFIED Requirements

### Requirement: A form pier's horizon that breaks the horizon rules skips the pier

Inside an add-on, a pier on the Configuration form SHALL be skipped with a
logged error that names the pier in each of these cases. The other piers SHALL
still be published.

- its horizon points fail the checks for inline points.
- it sets both `min_altitude` and `horizon_points`, and a horizon has exactly
  one source. The error SHALL name the labels
  `Horizon: floor` and `Horizon: points`, SHALL say to fill in one of them at
  most, and SHALL NOT contain `min_altitude`.

#### Scenario: An out-of-range point skips only that pier

- **WHEN** the form lists two piers
- **AND** one pier's `horizon_points` holds the pair `[0, 95]`
- **THEN** the service logs an error that names that pier
- **AND** it publishes a verdict for the other pier

#### Scenario: Both horizon fields skip the pier

- **WHEN** the form lists two piers
- **AND** one pier sets `min_altitude` to 10 and `horizon_points` to
  `[[0, 5], [180, 10]]`
- **THEN** the service logs an error that names that pier, `Horizon: floor` and
  `Horizon: points`
- **AND** the error does not contain `min_altitude`
- **AND** it publishes a verdict for the other pier

#### Scenario: A field error comes before the horizon error

- **WHEN** a form pier sets both `min_altitude` and `horizon_points`
- **AND** the same pier has a latitude of 95
- **THEN** the logged error names `latitude`, as the error for a `config.yaml`
  pier with that latitude does
- **AND** it does not contain `Horizon: floor`

## ADDED Requirements

### Requirement: A horizon from config.yaml with two sources keeps the file's names

Inside an add-on, a form pier can set neither horizon field while its entry in
`config.yaml` gives a `horizon` block with both `points` and `min_altitude`.
The logged error that skips that pier SHALL be the error a `config.yaml` pier
outside an add-on gets. It SHALL name `points` and `min_altitude`. It SHALL NOT
name a form label.

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
