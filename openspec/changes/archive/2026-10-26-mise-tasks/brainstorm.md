**Why:** mise already installs every development tool and sets the environment, so a separate `just` runner adds a tool to pin and a second config to keep in step; moving the tasks into `mise.toml` leaves one file and one command.

## Story

#127 mise-tasks — mise runs the dev tasks, and just is gone
https://github.com/andrewduckett/pier-pressure/issues/127

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | How far does the removal reach beyond the issue's file list? | Every live mention: also the comments in `pyproject.toml`, `Dockerfile`, `.pre-commit-config.yaml`, `tests/test_integration.py`, `release.yml` and the `context` in `openspec/config.yaml`. ADRs and archived changes stay as written. | User |
| D2 | Does any spec need a change? | No: no spec in `openspec/specs/` names `just` or a task runner. | Evidence: `grep -rnw just openspec/specs` |
| D3 | How does `mise run check` run its parts? | In order, stopping at the first failure: `run = [{ task = "lint" }, { task = "typecheck" }, { task = "test" }]`. | User |
| D4 | Does this mise version run task references in order and fail fast? | Yes. mise 2026.10.3 stops at the first failing task reference and exits non-zero. | Evidence: scratch `mise.toml` in `.workspace/` |
| D5 | What replaces the `default` recipe (`just --list`)? | Nothing. A bare `mise run` lists the tasks, and the docs name `mise tasks`. | User |
| D6 | Where does `PYTHON_VERSION` come from once the Justfile goes? | The `[env]` entry already in `mise.toml`. Nothing to add. | Evidence: `mise.toml` `[env]` |
| D7 | Can `test-integration` keep its always-tear-down bash script? | Yes. A multi-line `run` with a `#!/usr/bin/env bash` shebang runs as bash and passes its exit status through. | Evidence: scratch `mise.toml` in `.workspace/` |
| D8 | What do the docs tell people without mise? | Install uv and run the uv command shown next to each task. | User |
| D9 | Do the task names change? | No. `install`, `lint`, `format`, `typecheck`, `test`, `run`, `check`, `broker-up`, `up`, `broker-down` and `test-integration` keep their names and commands. | Evidence: #127, `Justfile` |
| D10 | Does Renovate need a change? | No. It reads `mise.toml` through its `mise` manager, and nothing in it names `just`. | Evidence: `.github/renovate.json5` |

## Changes from the story

- Added: the extra live mentions in D1, so that `just` is gone everywhere except the history.

Confirmed by user: yes
