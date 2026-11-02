## ADDED Requirements

### Requirement: The update bot's own Node stays inside Renovate's supported range
The update bot SHALL offer only Node versions for its own runner, `RENOVATE_NODE_VERSION` in `.github/workflows/renovate.yml`, that fall inside the `engines.node` range of the pinned Renovate release. The cap SHALL NOT hold back the Node pin in `mise.toml`.

#### Scenario: A Node major Renovate does not support
- **WHEN** the runner is on Node 24, Renovate's `engines.node` is `^24.11.0`, and Node 26 is released
- **THEN** no update pull request moves `RENOVATE_NODE_VERSION` to 26

#### Scenario: The mise.toml Node pin falls behind
- **WHEN** `mise.toml` pins Node 26 and Node 28 is released
- **THEN** an update pull request moves the `mise.toml` Node pin to 28
