## ADDED Requirements

### Requirement: A pier id repeated on the Configuration form stops the add-on

When the Configuration form lists the same pier `id` more than once, the add-on
SHALL stop with a configuration error that names the `id`. This SHALL hold
whether or not `config.yaml` exists.

#### Scenario: A pier listed twice on the form stops the add-on

- **WHEN** the form lists the pier `backyard` twice
- **AND** there is no `config.yaml`
- **THEN** the add-on stops
- **AND** its configuration error names `backyard`

#### Scenario: A form repeat stops the add-on when config.yaml adds to the pier

- **WHEN** the form lists the pier `backyard` twice
- **AND** `config.yaml` lists the pier `backyard` once, with its `metar_station`
- **THEN** the add-on stops
- **AND** its configuration error names `backyard`

### Requirement: Form horizon points read numbers as config.yaml does

Inside an add-on, a form pier's `horizon_points` text SHALL follow the number
rules of the configuration file. A zero-padded azimuth SHALL be read as a
decimal number, and a base-60 value SHALL skip the pier with a logged error that
names the pier and `horizon.points`.

#### Scenario: A padded azimuth on the form is decimal

- **WHEN** a form pier's `horizon_points` is `[[045, 10], [180, 5]]`
- **THEN** the pier's horizon samples are `(45, 10)` and `(180, 5)`

#### Scenario: A base-60 azimuth on the form skips only that pier

- **WHEN** the form lists two piers
- **AND** one pier's `horizon_points` is `[[1:30, 20], [180, 5]]`
- **THEN** the service logs an error that names that pier and `horizon.points`
- **AND** it publishes a verdict for the other pier
