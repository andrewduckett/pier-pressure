## MODIFIED Requirements

### Requirement: Updates cover every pinned dependency file
The update bot SHALL track the dependencies pinned in these places:

- `pyproject.toml` and `uv.lock`
- the actions in `.github/workflows/`
- the uv stage in the `Dockerfile`
- the images in `compose.yaml`
- the tools in `mise.toml`
- the dashboard card's packages in `card/package.json` and `card/package-lock.json`

#### Scenario: A mise tool falls behind
- **WHEN** `mise.toml` pins gh at `2.102` and gh 2.103.2 is released
- **THEN** the update bot opens a pull request that changes the gh pin in `mise.toml`

#### Scenario: The broker image gets a new major
- **WHEN** `compose.yaml` uses `eclipse-mosquitto:2` and Mosquitto 3 is released
- **THEN** the update bot opens a pull request that changes the image tag to `3`

#### Scenario: A card package gets a patch release
- **WHEN** `card/package-lock.json` holds lit 3.3.1 and lit 3.3.2 is released
- **THEN** the weekly npm pull request moves lit to 3.3.2 in `card/package-lock.json`

#### Scenario: The dashboard lists what was found
- **WHEN** the update bot has run on `main`
- **THEN** the Dependency Dashboard issue lists dependencies from each of `pyproject.toml`, `uv.lock`, `.github/workflows/`, `Dockerfile`, `compose.yaml`, `mise.toml` and `card/package.json`

### Requirement: Minor and patch updates arrive weekly, grouped by ecosystem
The update bot SHALL open at most one pull request a week for each ecosystem, holding all of that ecosystem's minor and patch updates. The ecosystems are uv, GitHub Actions, Docker, `mise.toml` and npm.

#### Scenario: Two Python packages get patch releases
- **WHEN** two packages in `uv.lock` get patch releases in the same week
- **THEN** one pull request updates both

#### Scenario: Two card packages get minor releases
- **WHEN** two packages in `card/package-lock.json` get minor releases in the same week
- **THEN** one npm pull request updates both

#### Scenario: Updates in two ecosystems
- **WHEN** an action and a Python package both get minor releases in the same week
- **THEN** they arrive in two pull requests, one per ecosystem
