**Why:** pre-commit's virtualenv and filelock carry 31 open advisories (19 virtualenv, 12 filelock), and Renovate opened no fix because both are transitive.

## Story

#205 dev-lock-security — pre-commit runs on patched virtualenv and filelock, https://github.com/andrewduckett/pier-pressure/issues/205

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which packages move? | virtualenv to 21.15.6, python-discovery to 1.9.5 (which that virtualenv needs) and filelock to 4.2.9, through `uv lock --upgrade-package`; no other package in `uv.lock` moves | Evidence: trial `uv lock --upgrade-package` run on 2026-11-07 |
| D2 | Is the filelock 3 to 4 major safe to take? | Yes. Only virtualenv and python-discovery use it, and every pre-commit hook passed on it in the trial | Evidence: `uv tree --invert --package filelock`, trial `pre-commit run --all-files` |
| D3 | Does `pyproject.toml` or the image change? | No. All three are transitive through pre-commit in the `dev` group, and the image installs with `--no-dev` | Evidence: `uv tree --invert`, `Dockerfile` |
| D4 | Does any behavior change? | No. This is a lockfile-only bump, so the change sets `skip_specs: true` | Evidence: `uv.lock`, `openspec/specs/` |
| D5 | What proves it is done? | `mise run check` and `pre-commit run --all-files` pass, and Dependabot alerts 1–4, 11–17, 19–29 and 31–39 close once it merges to `main` | Evidence: `.github/workflows/ci.yml` |
| D6 | Which commit prefix does the bump use? | `build(deps):`, the prefix update commits use | Evidence: `openspec/specs/dependency-updates/spec.md` |

## Changes from the story

None. The runtime bumps are #204, and the Renovate gap is #206.

Confirmed by user: yes
