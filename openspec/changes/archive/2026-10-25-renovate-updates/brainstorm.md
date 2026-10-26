## Story

#119 renovate-updates — Renovate keeps every pin current, mise.toml included, and opens security PRs.
https://github.com/andrewduckett/pier-pressure/issues/119

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What does Renovate sign in with, and where does it run? | A GitHub App the maintainer can reuse on other repositories. The scheduled workflow and the app's two secrets live in pier-pressure; a central runner can replace them later without changing the Renovate config. | User |
| D2 | Does Renovate track the Mosquitto image in `compose.yaml`, which Dependabot never read? | Yes. A new major arrives as its own PR, and the integration tests run on it. | User |
| D3 | How often does the Renovate workflow run? | Once a day. A security PR arrives within a day of its alert; regular updates keep their weekly window. | User |
| D4 | Is the Dependency Dashboard issue on? | Yes. A ticked box takes effect at the next daily run; there is no extra trigger. | User |
| D5 | What proves the work is done? | Before merge: the config validator passes, and runs in CI on any PR that changes the Renovate config; a local dry run lists every dependency found and shows `.python-version` untouched. After merge: a checklist in the PR for the first live run. A failure there becomes a bug issue. | User |
| D6 | Does Let's Spec share the weekly `mise.toml` PR? | No. A Let's Spec bump gets its own PR; the other `mise.toml` tools stay grouped. | User |
| D7 | Can the workflow's built-in `GITHUB_TOKEN` open the PRs? | No. PRs it opens do not trigger CI, and the `main` ruleset requires the `check` and `image` checks. | Evidence: `main` ruleset |
| D8 | Does Renovate update Python? | No. Its `pyenv` manager, which reads `.python-version`, is turned off. | Evidence: #119 scope (out) |
| D9 | Are Dependabot alerts on today? | No. The vulnerability-alerts API returns 404, so this change turns on the dependency graph and alerts. | Evidence: GitHub API |
| D10 | Where does the uv patch-only rule apply? | To every uv pin Renovate reads: the Dockerfile's uv stage and `mise.toml`. `mise.toml`'s `uv = "0.12"` already floats over patches, so in practice only the Dockerfile gets uv PRs. | Evidence: `mise.toml`, `Dockerfile`, `pyproject.toml` |
| D11 | Does the HA add-on's `version` in `ha-addon/config.yaml` get Renovate PRs? | No. The release workflow owns it, and Renovate has no manager for that file. | Evidence: `.github/workflows/release.yml` |
| D12 | Which commit prefixes do update PRs use? | Today's: `build(deps)` for uv, Docker and `mise.toml`; `ci(deps)` for Actions. | Evidence: `.github/dependabot.yml` (`prefix`, `include: scope`) |
| D13 | How do the Python packages that `pyproject.toml` lists without a version get updated? | Each gets a lower bound at its `uv.lock` version, so the weekly uv PR moves it by name, as Dependabot did. No weekly lock refresh: indirect dependencies move only through direct updates and security PRs, as today. A local Renovate dry run showed it skips unversioned packages. | User |
| D14 | Does Renovate's default limit of two new PRs an hour apply? | No. With one run a day it would hold PRs back for days, so the hourly limit is lifted. The limit on open PRs stays at the default. | Assumption |
| D15 | How are update PRs labelled? | `dependencies`, as Dependabot did; security PRs also get `security`. | Evidence: Dependabot's default label |

## Changes from the story

- Added: Mosquitto in `compose.yaml` is tracked (D2). The story's Docker scope covered only the Dockerfile.
- Changed: Let's Spec gets its own PR instead of sharing the weekly `mise.toml` group (D6), so its rule changes can be reviewed and reverted alone.
- Added: each Python package listed without a version in `pyproject.toml` gets a lower bound (D13), so Renovate can track it.
- Added: CI runs the Renovate config validator on PRs that change the config (D5).
- Settled: the story's "its own token or GitHub App" is a GitHub App (D1).

Confirmed by user: yes
