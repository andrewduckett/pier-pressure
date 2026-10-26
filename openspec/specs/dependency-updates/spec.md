# dependency-updates Specification

## Purpose
Keeps every pinned dependency current through update pull requests that the maintainer reviews and merges, and turns each security alert into its own pull request.

## Requirements

### Requirement: Updates cover every pinned dependency file
The update bot SHALL track the dependencies pinned in these places:

- `pyproject.toml` and `uv.lock`
- the actions in `.github/workflows/`
- the uv stage in the `Dockerfile`
- the images in `compose.yaml`
- the tools in `mise.toml`

#### Scenario: A mise tool falls behind
- **WHEN** `mise.toml` pins gh at `2.102` and gh 2.103.2 is released
- **THEN** the update bot opens a pull request that changes the gh pin in `mise.toml`

#### Scenario: The broker image gets a new major
- **WHEN** `compose.yaml` uses `eclipse-mosquitto:2` and Mosquitto 3 is released
- **THEN** the update bot opens a pull request that changes the image tag to `3`

#### Scenario: The dashboard lists what was found
- **WHEN** the update bot has run on `main`
- **THEN** the Dependency Dashboard issue lists dependencies from each of `pyproject.toml`, `uv.lock`, `.github/workflows/`, `Dockerfile`, `compose.yaml` and `mise.toml`

### Requirement: Every direct Python package is updated by name
The update bot SHALL track each package listed in `pyproject.toml`'s dependencies and dependency groups by name. When a newer release still satisfies the listed range, the update SHALL change `uv.lock` and leave the range in `pyproject.toml` as it is.

#### Scenario: A development tool gets a patch release
- **WHEN** `uv.lock` holds ruff 0.17.1 and ruff 0.17.2 is released
- **THEN** the weekly uv pull request moves ruff to 0.17.2 in `uv.lock`

#### Scenario: A release inside the listed range
- **WHEN** `pyproject.toml` lists `pydantic-ai-slim>=2.43.0`, `uv.lock` holds 2.43.0, and 2.61.0 is released
- **THEN** the weekly uv pull request moves `uv.lock` to 2.61.0, and `pyproject.toml` still says `>=2.43.0`

### Requirement: Python is never updated
The update bot SHALL NOT propose a change to `.python-version` or to the Python base image. Python changes only by a hand edit to `.python-version`.

#### Scenario: A new Python release
- **WHEN** `.python-version` holds `3.14` and Python 3.15 is released
- **THEN** no update pull request changes `.python-version` or the `Dockerfile`'s Python base image

### Requirement: Minor and patch updates arrive weekly, grouped by ecosystem
The update bot SHALL open at most one pull request a week for each ecosystem, holding all of that ecosystem's minor and patch updates. The ecosystems are uv, GitHub Actions, Docker and `mise.toml`.

#### Scenario: Two Python packages get patch releases
- **WHEN** two packages in `uv.lock` get patch releases in the same week
- **THEN** one pull request updates both

#### Scenario: Updates in two ecosystems
- **WHEN** an action and a Python package both get minor releases in the same week
- **THEN** they arrive in two pull requests, one per ecosystem

### Requirement: Each major update arrives on its own
The update bot SHALL open a separate pull request for each major update, never grouped with other updates.

#### Scenario: A major and a minor in one week
- **WHEN** one action gets a major release and another gets a minor release in the same week
- **THEN** the major arrives in its own pull request, and the minor arrives in the weekly Actions pull request

### Requirement: Let's Spec updates arrive on their own
The update bot SHALL open a separate pull request for each Let's Spec update, of any size, never grouped with other `mise.toml` tools.

#### Scenario: Let's Spec and gh move in the same week
- **WHEN** Let's Spec and gh both get minor releases in the same week
- **THEN** Let's Spec arrives in its own pull request, and gh arrives in the weekly `mise.toml` pull request

### Requirement: A Let's Spec update carries what `lets sync` writes
A Let's Spec update pull request SHALL include the files `lets sync` writes for the new version. `mise install` and `lets sync --check` SHALL then pass on it without a hand edit.

#### Scenario: Let's Spec moves from 0.4.0 to 0.6.0
- **WHEN** the update bot opens the pull request that moves Let's Spec from 0.4.0 to 0.6.0
- **THEN** the pull request holds the `mise.toml` change and the files `lets sync` wrote, and the CI step "Check the Let's Spec files" passes

### Requirement: The update bot runs no other commands
The update bot SHALL run `lets sync` as its only command after an update. A repository config that asks for any other command SHALL NOT run it.

#### Scenario: A config asks for another command
- **WHEN** the repository's update config asks to run `rm -rf docs` after an update
- **THEN** the update bot does not run it, and reports the command as not allowed

### Requirement: The OpenSpec CLI updates on its own
The update bot SHALL update the OpenSpec CLI pin in `mise.toml` like any other tool, without tying it to the Let's Spec version.

#### Scenario: OpenSpec releases without Let's Spec
- **WHEN** OpenSpec 1.15.0 is released and Let's Spec does not move
- **THEN** the weekly `mise.toml` pull request moves the OpenSpec pin to 1.15.0

### Requirement: uv moves only by patch releases
The update bot SHALL offer only patch releases of uv. A uv minor release SHALL NOT produce an update pull request.

#### Scenario: A uv patch release
- **WHEN** the `Dockerfile` pins the uv image at `0.12.24` and uv 0.12.25 is released
- **THEN** the weekly Docker pull request moves the uv image to `0.12.25`

#### Scenario: A uv minor release
- **WHEN** uv 0.13.0 is released
- **THEN** no update pull request moves uv to 0.13 in the `Dockerfile` or `mise.toml`

### Requirement: Security fixes arrive at once, on their own
When a Dependabot alert reports a vulnerable dependency, the update bot SHALL open a separate pull request that moves it to a fixed version. The pull request's title SHALL end with `[security]`, and it SHALL ignore the weekly schedule.

#### Scenario: An alert on a Python package
- **WHEN** a Dependabot alert opens on Tuesday for a package in `uv.lock`, and a fixed version exists
- **THEN** by the end of the next daily run, a pull request whose title ends with `[security]` moves that package to the fixed version, and it is labelled `security`

### Requirement: The update bot runs every day
The update bot SHALL run once a day on `main`.

#### Scenario: A day passes
- **WHEN** 24 hours pass
- **THEN** the update workflow has run once on `main`

### Requirement: Update pull requests run the required checks
Update pull requests SHALL trigger the CI workflows, so the `check` and `image` checks that `main` requires run on them.

#### Scenario: A weekly uv pull request opens
- **WHEN** the update bot opens the weekly uv pull request
- **THEN** the `check`, `integration` and `image` jobs run on it

### Requirement: Nothing merges automatically
The update bot SHALL NOT merge any pull request. The maintainer merges every update.

#### Scenario: All checks pass
- **WHEN** every check passes on an update pull request
- **THEN** the pull request stays open until the maintainer merges it

### Requirement: Update pull requests follow the commit conventions
Update commits SHALL use the Conventional Commits prefix `ci(deps):` for GitHub Actions and `build(deps):` for every other ecosystem. Update pull requests SHALL carry the label `dependencies`.

#### Scenario: An Actions update
- **WHEN** the update bot opens a GitHub Actions pull request
- **THEN** its commit message starts with `ci(deps):` and it has the label `dependencies`

#### Scenario: A mise.toml update
- **WHEN** the update bot opens a `mise.toml` pull request
- **THEN** its commit message starts with `build(deps):`

### Requirement: The Dependency Dashboard stays open
The update bot SHALL keep one open Dependency Dashboard issue. It lists the dependencies found and the updates being held back. Ticking an update's box there SHALL produce that pull request at the next daily run.

#### Scenario: The maintainer asks for a held-back update
- **WHEN** the maintainer ticks a held-back update on the Dependency Dashboard
- **THEN** that update's pull request opens at the next daily run

### Requirement: A broken update config fails CI
CI SHALL validate the update config on every pull request that changes it, and fail when the config is invalid.

#### Scenario: A typo in the config
- **WHEN** a pull request changes the update config to hold an unknown option
- **THEN** CI reports a failed config check on that pull request

### Requirement: Dependabot only raises alerts
The repository SHALL have the dependency graph and Dependabot alerts on. Dependabot SHALL NOT open version update or security update pull requests.

#### Scenario: A vulnerable package is found
- **WHEN** a dependency in `uv.lock` has a published advisory
- **THEN** a Dependabot alert opens, and Dependabot opens no pull request for it

### Requirement: The add-on version is left to the release
The update bot SHALL NOT change `version` in `ha-addon/config.yaml`.

#### Scenario: A new release image exists
- **WHEN** a new PierPressure image is published to GHCR
- **THEN** no update pull request changes `ha-addon/config.yaml`
