## 1. Pins Renovate can read

- [x] 1.1 [easy] Every package in `pyproject.toml`'s `[project] dependencies` and `[dependency-groups]` has a lower bound at its `uv.lock` version (design DS7). `tests/test_dependency_bounds.py` fails on any package with no version. `[build-system] requires` stays unversioned, and `uv.lock`'s package versions don't change. (verify: uv run pytest tests/test_dependency_bounds.py && uv lock --check) (✓ `uv run pytest tests/test_dependency_bounds.py && uv lock --check` passed; uv.lock package versions unchanged)
- [x] 1.2 [easy] `mise.toml` installs Let's Spec as `github:sidereal-io/lets-spec`, with `asset_pattern = "lets-spec-*.tar.gz"` (design DS6). The comment that tied OpenSpec to Let's Spec now says OpenSpec is an ordinary pin. (verify: mise install && mise exec -- lets sync --check) (✓ `mise install && mise exec -- lets sync --check` passed)

## 2. Renovate [depends-on: 1]

- [x] 2.1 [medium] `.github/renovate.json5` holds the repository rules in design DS5: the settings table and packageRules 1 to 5, with a comment giving each rule's reason. The config passes the validator. (verify: mise exec node@24 -- npx --yes --package renovate@44.181.8 -- renovate-config-validator --strict .github/renovate.json5) (✓ validator passed, as global and with `--no-global`; a typo copy fails it)
- [x] 2.2 [complex] `.github/workflows/renovate.yml` runs Renovate as design DS1 to DS5 say: (✓ local dry run finds `renovate` and `node` in the workflow through the custom manager; file staged, since the local platform reads tracked files)
  - **Triggers:** a daily schedule, `workflow_dispatch`, and `pull_request` filtered to the config and the workflow.
  - **`validate` job:** runs on pull requests only.
  - **`renovate` job:** checkout, `jdx/mise-action`, mise's shims on PATH, an app token from `actions/create-github-app-token`, and the runner settings as environment variables.
  - **Pins:** `RENOVATE_VERSION` and `RENOVATE_NODE_VERSION`, each with a `# renovate:` comment.
  - **Permissions:** `permissions: {}`, with each job asking for what it needs.

  A local dry run finds both pins through the custom manager. (verify: LOG_LEVEL=debug LOG_FORMAT=json mise exec node@24 -- npx --yes renovate@44.181.8 --platform=local --dry-run=lookup > .workspace/renovate-dry-run.ndjson && jq -e -s '[.[] | select(.msg=="packageFiles with updates") | .config[][] | select(.packageFile==".github/workflows/renovate.yml") | .deps[] | .depName] | (index("renovate") != null and index("node") != null)' .workspace/renovate-dry-run.ndjson)

## 3. Dependabot stands down [depends-on: 2]

- [x] 3.1 [easy] `.github/dependabot.yml` is gone, so Dependabot opens no version update pull requests. (verify: test ! -e .github/dependabot.yml) (✓ `test ! -e .github/dependabot.yml` passed)
- [x] 3.2 [easy] The repository has the dependency graph and Dependabot alerts on, and Dependabot security updates off (design DS8). Then check the Open Question: list the ecosystems the SBOM holds, and file a follow-up issue if PyPI is missing. (verify: gh api repos/andrewduckett/pier-pressure/vulnerability-alerts --silent && test "$(gh api repos/andrewduckett/pier-pressure --jq .security_and_analysis.dependabot_security_updates.status)" = disabled) (✓ alerts on, security updates `disabled`; the graph is always on for a public repository. SBOM: 75 `pypi`, 11 `githubactions`, 1 `github`, so PyPI is indexed and no follow-up issue is needed)

## 4. Docs name Renovate [depends-on: 2]

- [x] 4.1 [medium] The README's "Dependency updates" section covers: (✓ verify grep passed)
  - **What Renovate does:** what it updates and how it groups updates, the Let's Spec pull request, `[SECURITY]` pull requests and the Dependency Dashboard.
  - **Setup:** the GitHub App setup, with design DS4's permissions table, and the two secrets.
  - **By hand:** uv minors and Python are moved by hand.

  (verify: grep -q RENOVATE_APP_PRIVATE_KEY README.md && ! grep -q -E 'dependabot\.yml|Dependabot opens' README.md)
- [x] 4.2 [parallel] [easy] These name Renovate instead of Dependabot: (✓ verify grep passed)
  - `docs/data-updates.md`
  - stage 6 of `openspec/discovery.md`
  - the comment on line 11 of the `Dockerfile`
  - the comment on line 79 of `.github/workflows/ci.yml`

  (verify: ! grep -n -i dependabot docs/data-updates.md openspec/discovery.md Dockerfile .github/workflows/ci.yml)

## 5. Proof before merge [depends-on: 3, 4]

- [x] 5.1 [complex] A full local dry run with the repository config shows the spec's behavior: (✓ dry run shows every file, no Python or uv minor branch, ruff and pydantic-ai-slim in the uv group, Let's Spec alone; post-filter check passed; summary in PR #120)
  - Dependencies are found in `pyproject.toml`, `uv.lock`, the workflows, the `Dockerfile`, `compose.yaml` and `mise.toml`.
  - No update for `python` or `.python-version`, and no uv minor.
  - `ruff` and `pydantic-ai-slim` updates in the uv group.
  - Let's Spec in its own group.

  Paste a summary into the PR description. (verify: LOG_LEVEL=debug LOG_FORMAT=json mise exec node@24 -- npx --yes renovate@44.181.8 --platform=local --dry-run=lookup > .workspace/renovate-dry-run.ndjson && jq -e -s '[.[] | select(.msg=="packageFiles with updates") | .config[][] | .deps[] | select(.depName=="python" or .depName=="uv" or .depName=="ghcr.io/astral-sh/uv") | .updates[]? | select(.updateType != "patch")] | length == 0' .workspace/renovate-dry-run.ndjson)
- [x] 5.2 [easy] The PR description carries the post-merge checklist from D5. Every check passes on the branch. (verify: just check && mise exec -- lets sync --check) (✓ `just check` passed, 1153 tests; `lets sync --check` passed; checklist in PR #120)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-10-26, task 2.1: rule 3 also sets `groupSlug: "lets-spec"`. The group name alone gave the branch `renovate/let's-spec`.
- 2026-10-26, task 2.2: the `validate` job passes `--no-global`, so the file is checked as a repository config. Without it the validator treats any named file as global config, and a runner-only option there would pass.
- 2026-10-26, task 2.2: `actions/create-github-app-token@v3` deprecates `app-id` for `client-id`. The input takes either, so the existing `RENOVATE_APP_ID` secret goes into `client-id` and keeps its name.
- 2026-10-26, task 2.2: the workflow's read-only token reaches Renovate as `MISE_READ_TOKEN`, not `GITHUB_TOKEN`, so Renovate never mistakes it for its own token.
- 2026-10-26, task 5.1: the planned `jq` check reads the `packageFiles with updates` log, which lists updates before package rules disable them, so it fails on the uv minors that rule 4 holds back. The check used reads the post-filter `flattened updates found` entry instead: `jq -e -s '[.[] | select(.msg|test("flattened updates found"))] | length == 1 and (.[0].msg | test("(^|[ ,:])(uv|python|ghcr\\.io/astral-sh/uv)(,|$)") | not)'`. Turning rule 4 off makes a Docker uv branch appear, which confirms the rule works.
- 2026-10-26, task 5.1: the dry run showed `chore(deps):` commits, because `config:recommended` sets the type through a package rule. The config now has `ignorePresets: [":semanticPrefixFixDepsChoreOthers"]`.
