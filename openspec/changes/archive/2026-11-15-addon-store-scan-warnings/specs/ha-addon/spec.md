## ADDED Requirements

### Requirement: The add-on store reads only two config files from the repository

The Home Assistant Supervisor reads as an add-on config each file named
`config.*` with a `.yaml`, `.yml` or `.json` suffix, unless a part of its path
starts with `.` or is named `rootfs`. Of the repository's tracked files, only
`ha-addon/config.yaml` and `openspec/config.yaml` SHALL match that rule.
OpenSpec reads its config only at `openspec/config.yaml`, so that file is the
one allowed exception.

#### Scenario: Only the add-on config and the OpenSpec config match

- **WHEN** the test suite applies the Supervisor's rule to the repository's
  tracked files
- **THEN** the files that match are exactly `ha-addon/config.yaml` and
  `openspec/config.yaml`

#### Scenario: A new tracked file that matches fails the check

- **WHEN** a tracked file such as `docs/examples/config.sample.yaml` is added
- **THEN** the check fails and names `docs/examples/config.sample.yaml`

### Requirement: The add-on docs explain the Supervisor's warning for the OpenSpec config

The add-on documentation SHALL name the warning that the Supervisor logs for
`openspec/config.yaml` on each store reload, `Can't read …/openspec/config.yaml:
Invalid app config!`. It SHALL say that the file is not an add-on, and that the
warning is harmless and needs no action. The README's add-on install steps SHALL
link to that explanation.

#### Scenario: The add-on docs name the warning

- **WHEN** a user reads `ha-addon/DOCS.md`
- **THEN** one section quotes `openspec/config.yaml: Invalid app config!` and
  says the warning needs no action

#### Scenario: The README links to the explanation

- **WHEN** a user reads the README's steps to install the add-on
- **THEN** the step that adds the repository links to that section of
  `ha-addon/DOCS.md`
