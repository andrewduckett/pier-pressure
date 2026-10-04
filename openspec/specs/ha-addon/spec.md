# ha-addon Specification

## Purpose

The ha-addon capability lets a Home Assistant OS user install and run PierPressure
as a Home Assistant add-on (also called an app). The add-on is packaging only: it
runs the released image with the user's own config file and adds no behaviour.

## Requirements

### Requirement: The repository is an add-on repository

The PierPressure GitHub repository SHALL be a valid Home Assistant add-on
repository. It SHALL hold one add-on with the slug `pierpressure`. A user SHALL be
able to add the repository URL in Home Assistant and see PierPressure in the add-on
store.

#### Scenario: Add the repository by URL

- **WHEN** a Home Assistant OS user adds
  `https://github.com/andrewduckett/pier-pressure` as an add-on repository
- **THEN** the add-on store lists a PierPressure add-on from that repository

#### Scenario: Add-on files are valid

- **WHEN** the test suite reads the repository file and the add-on config file
- **THEN** both parse as YAML
- **AND** the add-on config sets `name`, `version`, `slug`, `description`, `arch`
  and `image`, with `slug` equal to `pierpressure`

### Requirement: The add-on runs the released image

The add-on SHALL run the published release image
`ghcr.io/andrewduckett/pier-pressure`. Its `version` SHALL be a release version,
so Home Assistant pulls the image tag with that version. Home Assistant SHALL NOT
build the image on the user's machine.

#### Scenario: Install pulls the pinned release

- **WHEN** a user installs the add-on while its version is `2026.10.0`
- **THEN** Home Assistant pulls `ghcr.io/andrewduckett/pier-pressure:2026.10.0`
- **AND** the add-on log's first line contains `2026.10.0`

#### Scenario: Add-on version is a release version

- **WHEN** the test suite reads the add-on config file
- **THEN** its `version` matches the release format `YYYY.M.N`
- **AND** its `image` is `ghcr.io/andrewduckett/pier-pressure`, with no tag and no
  architecture placeholder

### Requirement: The add-on supports the image's platforms

The add-on SHALL declare exactly the architectures that the release image is built
for: `amd64` for `linux/amd64` and `aarch64` for `linux/arm64`.

#### Scenario: Architectures match the release build

- **WHEN** the test suite compares the add-on's `arch` list with the platforms the
  release workflow builds
- **THEN** each release platform has its add-on architecture, and the add-on lists
  no other architecture

### Requirement: The add-on reads config from its own config folder

The add-on SHALL run the service with the config file `config.yaml` in the
add-on's own config folder. In Home Assistant, the user finds that folder as
`/addon_configs/<repository-id>_pierpressure`. The file SHALL have the same format
as outside Home Assistant, including the MQTT broker settings. The add-on SHALL
offer no options of its own.

#### Scenario: Config file present

- **WHEN** the user has written a valid `config.yaml` in the add-on's config
  folder and starts the add-on
- **THEN** the service loads that file and publishes a verdict for each pier

#### Scenario: Config file missing

- **WHEN** the user starts the add-on before writing `config.yaml`
- **THEN** the add-on stops
- **AND** its log contains a configuration error that names the missing file

#### Scenario: Add-on config mounts the folder

- **WHEN** the test suite reads the add-on config file
- **THEN** it maps `addon_config`
- **AND** it sets the environment variable `PIERPRESSURE_CONFIG` to
  `/config/config.yaml`

### Requirement: The add-on behaves like the container

The add-on SHALL publish the same entities, topics and verdict documents as the
same image run with Docker and the same config file. It SHALL NOT add, remove or
rename any entity or topic.

#### Scenario: Same entities as a Docker install

- **WHEN** a user runs the add-on with a config file that works under Docker
- **THEN** Home Assistant shows the same PierPressure device and entities as it
  does for the Docker install
