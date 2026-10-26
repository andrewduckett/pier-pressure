## Why

Dependabot can't read `mise.toml`, so the development tools pinned there are bumped by hand and fall behind: Let's Spec is at 0.4.0 against 0.6.0, OpenSpec at 1.13.2 against 1.15.0, and gh at 2.102 against 2.103.2. Dependabot alerts are also off (D9), so nothing reports a vulnerable dependency. Renovate reads `mise.toml`. Running it beside Dependabot for version updates would open duplicate pull requests, so Renovate takes over every update, and Dependabot only raises alerts.

## What Changes

- **New:** a self-hosted Renovate run, from a daily scheduled workflow in this repository, signed in as a GitHub App (D1, D3, D7).
- **New:** Renovate updates uv (`pyproject.toml` and `uv.lock`), GitHub Actions, the Dockerfile's uv stage, the Mosquitto image in `compose.yaml` (D2) and every tool in `mise.toml`.
- **New:** a security alert becomes its own `[SECURITY]` pull request. It ignores the weekly schedule and arrives at the next daily run (D3).
- **New:** a Let's Spec bump gets its own pull request (D6). Renovate runs `lets sync` on it and commits what that writes, so `lets sync --check` passes. `lets sync` is the only command Renovate may run.
- **New:** the Dependency Dashboard issue lists what Renovate found and what it is holding back (D4).
- **New:** CI checks the Renovate config on every pull request that changes it (D5).
- **Kept:** one weekly pull request per ecosystem for minor and patch updates, and each major update in its own pull request. Commit prefixes and labels stay as they are today (D12, D15).
- **Changed:** each Python package that `pyproject.toml` lists without a version gets a lower bound at its locked version, so it is updated by name, as under Dependabot (D13). Updates within a range move only `uv.lock`.
- **Kept:** uv moves only by patch releases. A uv minor stays a deliberate change to `mise.toml`, `[tool.uv] required-version` and the Dockerfile together (D10).
- **Kept:** Python is never updated. It changes only through `.python-version` (D8). The add-on's `version` stays with the release workflow (D11).
- **Changed:** the OpenSpec CLI is an ordinary pin, no longer moved together with Let's Spec. The Let's Spec `asset_pattern` becomes a glob, so a version bump doesn't break `mise install`.
- **Removed:** `.github/dependabot.yml`. Dependabot version updates and security updates are off; the dependency graph and Dependabot alerts are on.
- **Changed:** the README, `docs/data-updates.md`, `openspec/discovery.md` and code comments name Renovate instead of Dependabot.
- **Not included:** auto-merge. The maintainer merges every update.

## Capabilities

### New Capabilities

- `dependency-updates`: how pinned dependencies are kept current. It covers which files are watched, how updates are grouped and scheduled, how security fixes arrive, how a Let's Spec bump stays in sync, and what is never updated.

### Modified Capabilities

None. `release-image` relies on CI building the image on update pull requests, and that does not change.

## Impact

- **Added:** a Renovate config file; `.github/workflows/renovate.yml`; a CI job that validates the Renovate config.
- **Removed:** `.github/dependabot.yml`.
- **Changed:** `pyproject.toml` (lower bounds for unversioned packages); `mise.toml` (the Let's Spec `asset_pattern` and comment); comments in `Dockerfile` and `.github/workflows/ci.yml`; `README.md`; `docs/data-updates.md`; `openspec/discovery.md`.
- **Repository settings:** the dependency graph and Dependabot alerts are turned on.
- **Maintainer setup, outside the repository:** a GitHub App installed on pier-pressure, and its ID and private key stored as the secrets `RENOVATE_APP_ID` and `RENOVATE_APP_PRIVATE_KEY`. The workflow cannot run until these exist.
- **The verdict core:** unaffected. No code under `pierpressure/` changes.
