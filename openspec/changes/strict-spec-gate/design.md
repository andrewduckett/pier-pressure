## Context

- `[tasks.check]` in `mise.toml` is a list of task references (`lint`, `typecheck`, `test`, `card`) that run in order and stop at the first failure. A mise task runs from the folder that holds `mise.toml`, the repository root, unless it sets `dir`.
- `mise.toml` pins `npm:@fission-ai/openspec` at 1.16.0. In CI, `jdx/mise-action` installs every pinned tool and puts it on PATH in both `check` jobs (`ci.yml` and `release.yml`). So `openspec` is there for `mise run check` with no new step.
- With `--strict`, `openspec validate --specs` exits 1 when any main spec has a warning, and 0 when none has one. Without `--strict`, a warning never changes the exit status.
- OpenSpec 1.16.0 turns off its usage telemetry and its update check when `CI` is set, or when `OPENSPEC_TELEMETRY=0` and `OPENSPEC_NO_UPDATE_CHECK` are set. It reads its global configuration, which can name stores, from `$XDG_CONFIG_HOME/openspec/` when that variable is set.
- `tests/test_dashboard_check.py` already reads `mise.toml` with `tomllib`, and `tests/test_paho_contract.py` already pins the behavior of a third-party library with a contract test.

## Goals / Non-Goals

**Goals:**

- `mise run check` fails on a main spec that fails strict validation, on a developer's machine and in CI.
- A test fails if `check` stops running the spec check, or if the pinned OpenSpec stops failing a requirement over 500 characters.

**Non-Goals:**

- Validating changes in progress or archived changes.
- Adding the spec check to the pre-commit hooks.
- Changing any CI workflow step.

## Test Seams

- **Primary test seam:** a new pytest module, `tests/test_dev_checks.py`. It reads `mise.toml` to check what the tasks run, and it runs the `specs` task's command against throwaway OpenSpec roots in `tmp_path`.
- **Existing seams reused:** the `tomllib` reading of `mise.toml` from `tests/test_dashboard_check.py`, and the YAML reading of the workflows from `tests/test_night_card_doc.py`.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the developer and CI toolchain only: `mise.toml` (a new task, and the `check` task's references and description), one new test module, two documents (AGENTS.md and the README) and one workflow comment. No product code, verdict document or delivery surface changes.

## Decisions

1. **A task named `specs`, referenced first in `check`.** The task runs `openspec validate --specs --strict --no-interactive`, and `check` becomes `specs`, `lint`, `typecheck`, `test`, `card`. The name matches `card`: a noun for the thing it checks. The spec check takes about a second, so it goes first and fails fast. The alternative, last place, keeps the old order but makes a spec failure wait about two and a half minutes for the tests. Calling `openspec` inline in `check` was rejected, because then the spec check cannot run alone (`dev-checks` "The spec check runs on its own").
2. **`--no-interactive`.** It stops OpenSpec from ever waiting for an answer, on a terminal or not. It changes nothing in CI today, and it costs nothing.
3. **The contract test runs the task's own command.** It reads `tasks.specs.run` from `mise.toml` and splits it with `shlex`, rather than repeating the command. So the test checks what `mise run specs` runs, and an edit to the task cannot leave the test checking a different command. It builds each OpenSpec root in `tmp_path`: an `openspec/config.yaml` and one main spec. The cases are a requirement over 500 characters (fails, and the output names the spec and the warning), one under it (passes), and a long requirement only in `openspec/changes/` (passes). OpenSpec prints the spec name and the warning on standard error, so the test reads standard output and standard error together. Each throwaway main spec has a `## Purpose` of at least 50 characters, and SHALL in every requirement, so that only the length can fail strict validation.
4. **The contract test keeps OpenSpec offline and away from the user's settings.** Its subprocess gets a copy of the test's environment, so `PATH` still finds `openspec` and Node, with `OPENSPEC_TELEMETRY=0`, `OPENSPEC_NO_UPDATE_CHECK=1` and `XDG_CONFIG_HOME` set to a folder in `tmp_path`. So the suite sends nothing, as the project's tests do elsewhere, and a store or a setting in the user's global configuration cannot change the result.
5. **A missing `openspec` skips the contract test, except in CI.** `mise run test` and `mise run check` put the pinned `openspec` on PATH. A developer who runs `uv run pytest` without mise may not have it, and the rest of the suite should still run. When `CI` is set, a missing `openspec` fails the test, so CI can never pass by skipping it.
6. **The `check` job is tested through its workflow file.** A test asserts that the `check` job in `ci.yml` installs the mise tools before it runs `mise run check`. Together with the `mise.toml` test, that proves every pull request runs the spec check (`dev-checks` "Every pull request runs the spec check"). `release.yml` runs the same `mise run check`, so it needs no test of its own.
7. **The README's no-mise route names the pinned version, not a number.** It says to install the OpenSpec CLI at the version `mise.toml` pins. A number in the README would fall behind when Renovate moves the pin.

No decision here is costly to reverse: removing one task reference undoes the change.

## Risks / Trade-offs

- [An OpenSpec update stops failing strict mode on a long requirement, or renames `--specs`] → The contract test fails on the Renovate pull request that moves the pin, such as PR #266.
- [A new OpenSpec rule adds a warning that today's specs break] → The same Renovate pull request fails `check`. Fix the spec, or hold the pin, in that pull request.
- [CI skips the contract test because `openspec` is missing from PATH] → The test fails instead of skipping when `CI` is set (decision 5).
- [A change archives a long requirement into a main spec] → That is what the check is for. `lets-build` already runs `openspec validate <change> --strict` before archive, so it should rarely get that far.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, remove `{ task = "specs" }` from `[tasks.check]`.
