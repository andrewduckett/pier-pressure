## ADDED Requirements

### Requirement: The add-on offers a Configuration form for the interval and piers

The add-on SHALL declare a Configuration form in Home Assistant with two
settings:

- `interval_seconds`: the recompute interval in seconds, a whole number of at
  least 1. Its default SHALL be 900.
- `piers`: a list of piers. Each pier SHALL have an `id` (text), a `latitude`
  (from −90 to 90 degrees), a `longitude` (from −180 to 180 degrees) and an
  `elevation_m` (metres). The default SHALL be an empty list.

These names SHALL match the names of the same settings in `config.yaml`. Each
form field SHALL have a label and a description in English, and each description
of a number SHALL name its unit.

#### Scenario: Add-on config declares the form

- **WHEN** the test suite reads the add-on config file
- **THEN** its `options` set `interval_seconds` to 900 and `piers` to an empty
  list
- **AND** its `schema` declares `interval_seconds` as a whole number, and `piers`
  as a list whose items have `id`, `latitude`, `longitude` and `elevation_m`

#### Scenario: Every form field has a label

- **WHEN** the test suite reads the add-on's English translation file
- **THEN** it gives a name and a description for `interval_seconds`, `piers`, and
  each field of a pier

### Requirement: The add-on reads the Configuration form before the config file

Inside an add-on, the service SHALL read the values the user saved on the
Configuration form at startup. The rule for which source it uses is:

- When the form lists at least one pier, the service SHALL take the interval and
  the piers from the form only. It SHALL NOT read settings from `config.yaml`.
- When the form lists no piers, the service SHALL read `config.yaml` as the
  requirement "The add-on reads config from its own config folder" describes. It
  SHALL ignore the form's interval.

When the service uses the form, it SHALL take the broker from the Supervisor's
`mqtt` service. The broker's host, port, username and password all come from
there. The discovery prefix and base topic SHALL take their defaults.

When the service uses the form and stops with a broker error, the error SHALL
say that `config.yaml` is not read while the form lists piers. It SHALL NOT tell
the user only to set `mqtt.host` in `config.yaml`. This covers the "no MQTT
broker was found", "access refused", TLS, MQTT version and rejected-login
errors.

The service SHALL check each pier from the form exactly as it checks a pier from
`config.yaml`. A pier that fails the check SHALL be skipped with a logged error,
and the other piers SHALL still be published.

When the service uses the form and `config.yaml` also exists, the service SHALL
log a warning that names the ignored file. It SHALL then start as usual.

When the form lists no piers and `config.yaml` is missing, the add-on SHALL stop.
Its configuration error SHALL name the missing file, and SHALL tell the user to
add a pier on the Configuration tab.

Outside an add-on, the service SHALL NOT read the form's values, and SHALL behave
as it did before this change.

#### Scenario: Form setup gives a verdict without a file

- **WHEN** the user saves an interval and one pier on the Configuration tab
- **AND** the add-on's config folder holds no `config.yaml`
- **AND** the Supervisor provides an `mqtt` service
- **THEN** the service connects to the Supervisor's broker
- **AND** it publishes a verdict for that pier under the default discovery prefix
  and base topic
- **AND** it recomputes at the interval from the form

#### Scenario: An empty form falls back to the file

- **WHEN** the form lists no piers
- **AND** the add-on's config folder holds a valid `config.yaml`
- **THEN** the service loads that file and publishes a verdict for each of its
  piers

#### Scenario: The form wins over an existing file

- **WHEN** the form lists the pier `backyard`
- **AND** the add-on's config folder holds a `config.yaml` that lists the pier
  `roof`
- **THEN** the service publishes a verdict for `backyard` only
- **AND** its log contains a warning that names `/config/config.yaml` as ignored

#### Scenario: A bad pier in the saved form values is skipped

- **WHEN** the saved form values list two piers, and one has a latitude of 95
- **THEN** the service logs an error that names the skipped pier
- **AND** it publishes a verdict for the other pier

The Supervisor normally refuses to save such a value. The service still checks
each pier, because it does not rely on the Supervisor's check.

#### Scenario: A form user's broker error does not point only to the file

- **WHEN** the form lists a pier
- **AND** the Supervisor provides no `mqtt` service within the wait
- **THEN** the add-on stops
- **AND** its log says no MQTT broker was found
- **AND** it says `config.yaml` is not read while the form lists piers

#### Scenario: Nothing is set up

- **WHEN** the form lists no piers
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on stops
- **AND** its log contains a configuration error that names
  `/config/config.yaml` and tells the user to add a pier on the Configuration
  tab

#### Scenario: Outside an add-on, the form is not read

- **WHEN** the service runs outside an add-on
- **THEN** it does not read the form's values
- **AND** it loads `config.yaml` exactly as before this change

## MODIFIED Requirements

### Requirement: The add-on reads config from its own config folder

When the Configuration form lists no piers, the add-on SHALL run the service with
the config file `config.yaml` in the add-on's own config folder. The requirement
"The add-on reads the Configuration form before the config file" describes when
the form is used instead. In Home Assistant, the user finds that folder as
`/addon_configs/<repository-id>_pierpressure`. The file SHALL have the same format
as outside Home Assistant. Inside the add-on, the file MAY leave out the MQTT
broker's connection settings, as the requirement "The add-on uses the
Supervisor's MQTT broker when the file names none" describes.

#### Scenario: Config file present

- **WHEN** the form lists no piers
- **AND** the user has written a valid `config.yaml` in the add-on's config
  folder and starts the add-on
- **THEN** the service loads that file and publishes a verdict for each pier

#### Scenario: Config file missing

- **WHEN** the form lists no piers
- **AND** the user starts the add-on before writing `config.yaml`
- **THEN** the add-on stops
- **AND** its log contains a configuration error that names the missing file

#### Scenario: Add-on config mounts the folder

- **WHEN** the test suite reads the add-on config file
- **THEN** it maps `addon_config`
- **AND** it sets the environment variable `PIERPRESSURE_CONFIG` to
  `/config/config.yaml`
