# dev-checks Specification

## Purpose
Says what `mise run check` runs before a pull request, so that a spec, code or card problem fails on a developer's machine and in CI alike.

## Requirements

### Requirement: The check task fails when a main spec fails strict validation
`mise run check` SHALL run OpenSpec's strict validation of every main spec in `openspec/specs/`, with the OpenSpec version pinned in `mise.toml`. It SHALL fail when any main spec fails that validation, which includes any OpenSpec warning, such as a requirement over 500 characters.

#### Scenario: A main spec has a requirement over 500 characters
- **WHEN** a main spec holds a requirement whose text is over 500 characters
- **AND** a developer runs `mise run check`
- **THEN** the command exits with a non-zero status
- **AND** its output names that spec and the long-requirement warning

#### Scenario: Every main spec passes strict validation
- **WHEN** every main spec in `openspec/specs/` passes strict validation
- **AND** a developer runs `mise run check`
- **THEN** the spec check exits with status 0

### Requirement: The spec check validates main specs only
The spec check SHALL validate only the main specs in `openspec/specs/`. A change in progress in `openspec/changes/` SHALL NOT fail it.

#### Scenario: Only a change in progress has a long requirement
- **WHEN** every main spec passes strict validation
- **AND** a change in `openspec/changes/` adds a requirement over 500 characters
- **AND** a developer runs `mise run specs`
- **THEN** the command exits with status 0

### Requirement: The spec check runs on its own
The project SHALL provide the task `mise run specs`, which runs only the strict validation of the main specs, with the same result as that step of `mise run check`.

#### Scenario: A developer checks the specs alone
- **WHEN** a main spec holds a requirement over 500 characters
- **AND** a developer runs `mise run specs`
- **THEN** the command exits with a non-zero status, without running lint, type checks, tests or the card

### Requirement: Every pull request runs the spec check
On every pull request, the `check` job that `main` requires SHALL run the strict spec check, with OpenSpec installed from `mise.toml`. A main spec that fails strict validation SHALL fail the `check` job.

#### Scenario: A pull request adds a long requirement
- **WHEN** a pull request changes a main spec so that it holds a requirement over 500 characters
- **THEN** the `check` job on that pull request fails
