## Context

Two local Renovate dry runs (44.181.8, `--platform=local --dry-run=lookup`) and one mise test shaped this design:

- **Every manager we need is on by default.** Renovate found 56 dependencies in 8 files: `pep621` (`pyproject.toml` with `uv.lock`), `github-actions` (3 workflows), `dockerfile` (the uv stage), `docker-compose` (Mosquitto), and `mise` (all six tools, `github:andrewduckett/lets-spec` included).
- **Two defaults are wrong here.** The `pyenv` manager proposes Python 3.15 through `.python-version`. uv 0.13.5 is already out, so both the Dockerfile and `mise.toml` get a uv minor PR on the first run unless a rule stops them.
- **Packages without a version are skipped.** `ruff`, `mypy`, `pytest`, `pre-commit`, `jsonschema`, `types-pyyaml` and `PyYAML` get `skipReason: unversioned`. Packages with a range move only when `rangeStrategy` is `update-lockfile`: `pydantic-ai-slim` 2.43.0 → 2.61.0 appeared only with that setting.
- **Renovate does not touch `asset_pattern`.** It changes only the Let's Spec `version`, so the literal `lets-spec-0.4.0.tar.gz` pattern would break `mise install` on the bump.
- **The mise shim installs a newly pinned version on first use.** In a clone with Let's Spec moved to 0.6.0 and `MISE_TRUSTED_CONFIG_PATHS` set to the clone, `lets sync` installed 0.6.0, then rewrote `AGENTS.md`, 10 skill and schema files, and added one new folder.
- **Renovate needs Node `^24.11.0`.** `mise.toml` pins Node 26, which Renovate rejects.
- **Let's Spec moved to `sidereal-io/lets-spec`.** GitHub redirects the old name, which is how the dry run still found it.
- **The `main` ruleset** requires the `check` and `image` checks and an up-to-date branch. The repository is public, so Actions minutes are free.

## Goals / Non-Goals

**Goals:**
- Renovate runs with the same mise toolchain a developer has, so `lets sync` and `uv lock` behave as they do locally.
- All repository rules live in one commented config file. All runner settings live in one workflow.
- One pinned Renovate version serves both the scheduled run and the CI config check.

**Non-Goals:**
- A central runner for other repositories (D1). Moving to one later changes only the workflow.
- Refreshing indirect dependencies (D13).
- Code changes under `pierpressure/`.

## Test Seams

- **Primary test seam:** a local Renovate dry run with the repository config, `--platform=local --dry-run=lookup`. Read its "packageFiles with updates" log entry: it shows which dependencies are found and which updates each rule lets through. This is the before-merge evidence (D5).
- **Existing seams reused:** `renovate-config-validator --strict` for the config, the CI step "Check the Let's Spec files" for the Let's Spec bump, and pytest for one new guard: `tests/test_dependency_bounds.py` fails if a package in `pyproject.toml`'s dependencies or dependency groups has no version. Without it, a new unversioned package would silently drop out of Renovate.

## Scrutiny Tier & Blast Radius

- **Tier:** high. The change adds a GitHub App with write access, runs a third-party tool with that access every day, and lets it execute a command from a downloaded release.
- **Blast radius:** CI, repository settings and the update pull requests. The verdict core, the image's contents and the delivery surface are untouched.

## Decisions

### DS1. Renovate runs from npm on the runner, not from its Docker image

The job installs mise with `jdx/mise-action`, then runs `npx renovate@<version>` under Node 24 through `mise exec node@<major> --`. Renovate's `binarySource` is `global`, so it uses the uv and `lets` on PATH.

- *Alternative: `renovatebot/github-action`.* It runs Renovate in its own container, which has no mise and no `lets`. `lets sync` would need a custom image to maintain.
- *Why:* the mise test showed that `lets sync` works through the shim once the clone is trusted. The same toolchain also gives `uv lock` the uv that `[tool.uv] required-version` accepts.

### DS2. Renovate and its Node version are pinned in the workflow, and Renovate updates them

`RENOVATE_VERSION` and `RENOVATE_NODE_VERSION` sit in the workflow's `env`, each with a `# renovate: datasource=… depName=…` comment. The `customManagers:githubActionsVersions` preset reads those comments, so both move in the weekly Actions PR. Node is pinned by major and stays inside the range Renovate's `engines` allows.

- *Alternative: pin Renovate in `mise.toml`.* Every developer would install Renovate with `mise install`.

### DS3. One workflow runs Renovate and checks its config

`.github/workflows/renovate.yml` has three triggers:
- a daily `schedule` (D3)
- `workflow_dispatch`, for the first run and for retries
- `pull_request`, filtered to the config file and the workflow

Its `validate` job runs only on `pull_request`, and runs `renovate-config-validator --strict` with the same pinned version. Its `renovate` job runs on the other two triggers. A `concurrency` group keeps one Renovate run at a time. The workflow sets `permissions: {}`, and each job asks only for what it needs.

- *Alternative: a validator job in `ci.yml`.* It would need a second Renovate pin and a path filter inside a workflow that runs on every pull request.

### DS4. The GitHub App token comes from `actions/create-github-app-token`

The job mints a one-hour token from the `RENOVATE_APP_ID` and `RENOVATE_APP_PRIVATE_KEY` secrets, scoped to this repository, and passes it as `RENOVATE_TOKEN`. With an app token, Renovate's default `platformCommit: auto` makes commits through the GitHub API. They show the app as author and are verified, so no `gitAuthor` lookup is needed.

### DS5. Runner-only settings are environment variables; rules live in `.github/renovate.json5`

**Settings only the runner may set** go in the workflow's `env`:
- `RENOVATE_REPOSITORIES`: this repository
- `RENOVATE_ONBOARDING=false` and `RENOVATE_REQUIRE_CONFIG=required`
- `RENOVATE_ALLOWED_COMMANDS='["^lets sync$"]'`
- `RENOVATE_BINARY_SOURCE=global`
- `MISE_TRUSTED_CONFIG_PATHS`, set to Renovate's clone folder, and passed into child processes through `customEnvVariables`

A repository config can't widen any of these. That is what keeps `lets sync` the only command (spec: the update bot runs no other commands).

**The repository rules** go in `.github/renovate.json5`, because JSON5 allows comments that give each rule's reason, as `dependabot.yml` did. It extends `config:recommended` and `customManagers:githubActionsVersions`, then sets:

| Setting | Value | Covers |
|---|---|---|
| `schedule` | `["on monday"]`, `timezone: "UTC"` | Weekly window. The whole day, so a manual rerun on Monday still counts. |
| `prHourlyLimit` | `0` | D14 |
| `rebaseWhen` | `behind-base-branch` | The ruleset's up-to-date rule. Renovate can't read rulesets with these permissions. |
| `labels` | `["dependencies"]` | D15 |
| `semanticCommits` | `enabled`, type `build`, scope `deps` | D12 |
| `vulnerabilityAlerts` | `addLabels: ["security"]` | Renovate's defaults already give a separate, unscheduled PR with a `[SECURITY]` suffix |
| `pyenv` | `enabled: false` | D8 |
| `pep621` | `rangeStrategy: "update-lockfile"` | Range-satisfying releases move `uv.lock` only |

`packageRules`, in order (a later rule wins):
1. **Group minor and patch updates by ecosystem:** `pep621`; `github-actions` plus the custom manager; `dockerfile` plus `docker-compose`; `mise`.
2. **Actions commits:** `matchManagers: ["github-actions"]` gets `semanticCommitType: "ci"`.
3. **Let's Spec on its own:** `matchPackageNames: ["sidereal-io/lets-spec"]` gets its own `groupName`, plus `postUpgradeTasks` with `commands: ["lets sync"]`, `fileFilters: ["**/*"]` and `executionMode: "branch"`.
4. **uv by patch only:** `matchPackageNames: ["astral-sh/uv", "ghcr.io/astral-sh/uv"]` with `matchUpdateTypes: ["minor", "major"]` gets `enabled: false`. The dry run classed 0.12 → 0.13 as `minor`.

Majors stay ungrouped because the group rules match only `minor` and `patch`. `automerge` stays at its default, off.

### DS6. `mise.toml` points Let's Spec at its new home, with a glob pattern

The entry becomes `"github:sidereal-io/lets-spec" = { version = "0.4.0", asset_pattern = "lets-spec-*.tar.gz" }`. We're editing this line anyway. The new name removes the dependency on GitHub's redirect, and rule 3 matches it. The comment that tied OpenSpec to Let's Spec is replaced: OpenSpec is an ordinary pin.

### DS7. Lower bounds come from today's `uv.lock`

Each package in `[project] dependencies` and `[dependency-groups]` without a version gets `>=` its locked version. For example, `ruff>=0.17.1` and `PyYAML>=6.0.3`. `uv lock` must leave `uv.lock`'s package versions unchanged. `[build-system] requires` stays unversioned: it isn't locked, and Dependabot never updated it either.

### DS8. Repository settings change through the API, during apply

Two calls, run as their own task:
- `gh api -X PUT repos/{owner}/{repo}/vulnerability-alerts` turns on Dependabot alerts.
- `gh api -X PATCH repos/{owner}/{repo}` with `security_and_analysis` turns on the dependency graph, if it is off.

`dependabot_security_updates` stays `disabled`, as it is now. Then `.github/dependabot.yml` is deleted in the same pull request.

## Risks / Trade-offs

- [The App's private key leaks, and someone writes to the repository as the app.] → The app is installed on pier-pressure only, with the permissions in the setup steps. The key lives only in the two secrets and the maintainer's password manager. Rotate it from the app's page.
- [`MISE_TRUSTED_CONFIG_PATHS` doesn't reach `lets sync`, because Renovate gives child processes a reduced environment.] → It goes through `customEnvVariables`. The first live run's checklist (D5) checks the Let's Spec PR. If it fails, Renovate posts an artifact error on the PR, and a bug issue follows.
- [The Monday run fails, and weekly updates wait a week.] → The window is all of Monday, so a manual `workflow_dispatch` that day catches up. The dashboard can also request any held-back update.
- [A uv minor never gets a PR, and the dashboard doesn't list disabled updates, so the project can fall behind on uv.] → The README says uv minors are moved by hand, and how.
- [GitHub's dependency graph doesn't index `uv.lock`, so Python packages raise no alerts.] → See Open Questions. Actions and Docker alerts are unaffected.
- [Renovate's npm package runs with a write token.] → It's pinned to an exact version, and updates arrive as reviewed PRs. The token expires within an hour.

## Migration & Rollback

**Before merge:** the maintainer creates the app and the two secrets (proposal, Impact). Until then, the `renovate` job fails loudly at the token step. The `validate` job needs no secrets.

**After merge:** Dependabot opens nothing more, and Renovate starts at the next daily run. The maintainer can start it at once with `workflow_dispatch`. The first run opens the dashboard and the PRs already due: Let's Spec 0.6.0, OpenSpec and gh, and `pydantic-ai-slim` and `ruff`. The PR checklist (D5) is ticked against that run.

**Rollback:** revert the pull request, which restores `dependabot.yml` and removes the workflow. Then uninstall the app, close Renovate's PRs and the dashboard issue, and delete its `renovate/*` branches. Alerts can stay on.

## Open Questions

- Does GitHub's dependency graph index `uv.lock`? Check it once the graph is on (DS8): `gh api repos/{owner}/{repo}/dependency-graph/sbom` should list the PyPI packages. If it doesn't, Python security PRs need another source, such as Renovate's OSV alerts. That goes in a follow-up issue, not this change.
