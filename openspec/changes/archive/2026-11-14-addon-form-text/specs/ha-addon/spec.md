## ADDED Requirements

### Requirement: Each optional form field's description says it is optional

The English description of each form field the schema marks optional SHALL
contain the word `Optional.` The description of a field the schema requires
SHALL NOT contain it.

#### Scenario: Optional and required fields read differently

- **WHEN** the test suite reads the add-on config file and its English
  translation file
- **THEN** the description of each optional pier field and each of the four
  broker fields, `host` included, contains `Optional.`
- **AND** the descriptions of `interval_seconds`, `id`, `latitude`,
  `longitude` and `elevation_m` do not contain `Optional.`

### Requirement: The recompute interval's description names its default and the Refresh button

The English description of `interval_seconds` SHALL name its unit, seconds,
and its default, 900. It SHALL also say that a pier's Refresh button
recomputes the verdict at once, between intervals.

#### Scenario: The interval explains its default and the Refresh button

- **WHEN** the test suite reads the English translation file
- **THEN** the description of `interval_seconds` contains `seconds`, `900` and
  `Refresh`

### Requirement: The Piers introduction names a pier's four sections in order

The English description of `piers` SHALL name the four sections of a pier's
fields, Location, Horizon, Equipment and Verdict, in that order, and say that
each field's label starts with its section's name.

#### Scenario: The Piers introduction lists the sections

- **WHEN** the test suite reads the English translation file
- **THEN** the description of `piers` contains `Location`, `Horizon`,
  `Equipment` and `Verdict`, each first named after the one before it
- **AND** it contains the word `label`

### Requirement: The broker section says where the broker comes from when it is empty

The English description of `mqtt` SHALL say that with no host set, the add-on
uses the broker in `config.yaml`, or else the Mosquitto broker add-on.

#### Scenario: The broker section names both fallbacks

- **WHEN** the test suite reads the English translation file
- **THEN** the description of `mqtt` contains `config.yaml` and `Mosquitto`

### Requirement: Each broker login field's description says it needs a host

The English descriptions of the broker's `port`, `username` and `password`
SHALL each say that the field is set only with a host.

#### Scenario: Port, username and password name the host

- **WHEN** the test suite reads the English translation file
- **THEN** the descriptions of `port`, `username` and `password` each contain
  `only with a host`

### Requirement: The add-on's setup steps follow the Configuration tab's order

The "Set up the add-on" section of the add-on's documentation SHALL walk
through the Configuration tab in the order the tab shows it. It SHALL name, in
bold, the Recompute interval, the Piers, the Pier ID, the Location, Horizon,
Equipment and Verdict fields, and the MQTT broker, in that order.

#### Scenario: The setup steps name the tab's parts in order

- **WHEN** the test suite reads the "Set up the add-on" section of
  `ha-addon/DOCS.md`
- **THEN** it names in bold `Recompute interval`, `Piers`, `Pier ID`,
  `Location`, `Horizon`, `Equipment`, `Verdict` and `MQTT broker`, each first
  named after the one before it

#### Scenario: A part out of order fails the check

- **WHEN** the section names **MQTT broker** in bold before **Piers**
- **THEN** the test suite fails, naming `MQTT broker`
