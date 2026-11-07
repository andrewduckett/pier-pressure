## MODIFIED Requirements

### Requirement: Minor and patch updates arrive weekly, grouped by ecosystem
The update bot SHALL open at most one pull request a week for each ecosystem, holding all of that ecosystem's minor and patch updates. The ecosystems are uv, GitHub Actions, Docker, `mise.toml` and npm. The weekly `uv.lock` refresh is a separate pull request, and is the only other scheduled uv pull request in a week.

#### Scenario: Two Python packages get patch releases
- **WHEN** two packages in `uv.lock` get patch releases in the same week
- **THEN** one pull request updates both

#### Scenario: Two card packages get minor releases
- **WHEN** two packages in `card/package-lock.json` get minor releases in the same week
- **THEN** one npm pull request updates both

#### Scenario: Updates in two ecosystems
- **WHEN** an action and a Python package both get minor releases in the same week
- **THEN** they arrive in two pull requests, one per ecosystem

#### Scenario: A uv week with a lock refresh
- **WHEN** ruff gets a patch release and a transitive package in `uv.lock` gets a minor release in the same week
- **THEN** ruff arrives in the weekly uv pull request, and the transitive package arrives in the weekly `uv.lock` refresh pull request

### Requirement: Security fixes arrive at once, on their own
When a Dependabot alert reports a vulnerable dependency that the update bot tracks by name, the update bot SHALL open a separate pull request that moves it to a fixed version. The pull request's title SHALL end with `[security]`, and it SHALL ignore the weekly schedule. A vulnerable transitive package in `uv.lock`, one that `pyproject.toml` does not list, SHALL move to a fixed version through the weekly `uv.lock` refresh instead.

#### Scenario: An alert on a Python package
- **WHEN** a Dependabot alert opens on Tuesday for a package that `pyproject.toml` lists, and a fixed version exists
- **THEN** by the end of the next daily run, a pull request whose title ends with `[security]` moves that package to the fixed version, and it is labelled `security`

#### Scenario: An alert on a transitive Python package
- **WHEN** a Dependabot alert opens on Tuesday for certifi, which `uv.lock` holds and `pyproject.toml` does not list, and a fixed version exists
- **THEN** no `[security]` pull request opens for certifi, and the next Monday's `uv.lock` refresh pull request moves certifi to the fixed version

## ADDED Requirements

### Requirement: uv.lock is refreshed every week
The update bot SHALL open one pull request each Monday that moves every package in `uv.lock`, transitive packages included, to the latest version the ranges in `pyproject.toml` allow. The refresh SHALL leave `pyproject.toml` and every other lock file unchanged.

#### Scenario: A transitive package falls behind
- **WHEN** `uv.lock` holds pyasn1 0.6.4, which no range in `pyproject.toml` lists, and pyasn1 0.6.5 is released on a Wednesday
- **THEN** the next Monday's daily run opens a pull request that moves pyasn1 to 0.6.5 in `uv.lock`, labelled `dependencies`, with a commit message that starts with `build(deps):`

#### Scenario: Only uv.lock is refreshed
- **WHEN** the update bot opens the weekly `uv.lock` refresh pull request
- **THEN** the pull request changes `uv.lock` and no other file, `card/package-lock.json` included

### Requirement: The maintainer can ask for the uv.lock refresh early
The Dependency Dashboard SHALL list the weekly `uv.lock` refresh while it waits for Monday. Ticking it there SHALL open the refresh pull request at the next daily run.

#### Scenario: An urgent transitive fix
- **WHEN** a transitive package in `uv.lock` gets a security fix on a Tuesday, and the maintainer ticks the `uv.lock` refresh on the Dependency Dashboard
- **THEN** the refresh pull request opens at the next daily run, without waiting for Monday
