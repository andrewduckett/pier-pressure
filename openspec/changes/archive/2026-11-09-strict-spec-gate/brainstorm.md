## Story

#245 strict-spec-gate — `mise run check` fails when a main spec breaks an OpenSpec rule, so long requirements cannot return.
https://github.com/andrewduckett/pier-pressure/issues/245

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Is the main-spec count really zero on this base? | Yes. `openspec validate --specs --strict` passes all 11 main specs and exits 0 on the base, `split-long-reqs-night-verdict-confidence` at 8a0587b. | Evidence: `openspec validate --specs --strict` |
| D2 | Does strict mode turn a warning into a failure? | Yes. On a throwaway spec with one 511-character requirement, OpenSpec 1.16.0 exits 1 with `--strict` and 0 without it. The warning is the same in both runs. | Evidence: probe in `.workspace/strict-probe` |
| D3 | Which command does the `check` task run? | `openspec validate --specs --strict --no-interactive`. It checks the main specs only. Changes in progress (`--changes`), archived changes and the 500-character limit stay out of scope. | Evidence: #245 Scope; `openspec validate --help` |
| D4 | Does `check` call the command directly, or through a task of its own? | Through a new task of its own, which `check` references like `lint`, `typecheck`, `test` and `card`. A developer can then run the spec check alone. The design names the task and places it in the order. | Assumption (the user delegated the brainstorm). Evidence: `mise.toml` `[tasks.check]` holds only task references |
| D5 | Where does the requirement live? | In a new capability, `dev-checks`, about what the `check` task runs. No existing spec fits: `dependency-updates` is about the update bot, and `night-card` covers only the card's own build. Its text says "the `check` task", not "gate", because "gate" means a verdict's hard gate in the specs. | Assumption. Evidence: `openspec list --specs`; `openspec/specs/night-card/spec.md` "Every pull request builds and tests the card" |
| D6 | How is the change proven, test first? | Two tests, written before `mise.toml` changes. A configuration test reads `mise.toml` and asserts that `check` runs the new task, and that the task runs the strict command. A contract test runs the pinned OpenSpec on a throwaway spec: a requirement over 500 characters fails, and one under it passes. | Assumption. Evidence: `tests/test_dashboard_check.py` reads `mise.toml`; `tests/test_paho_contract.py` is a contract test |
| D7 | Why a contract test, when OpenSpec is not our code? | PR #266 (Renovate) already moves the OpenSpec pin to 1.16.1. If a later release stops failing strict mode on a long requirement, the gate would pass unseen. The contract test fails instead. | Evidence: PR #266 |
| D8 | Does CI get `openspec` from `mise.toml`? | Yes. In both `ci.yml` and `release.yml`, the `check` job installs every `mise.toml` tool with `jdx/mise-action`. The CI log for run 42621588987 shows `npm:@fission-ai/openspec@1.16.0` installed and on PATH. No workflow step changes. | Evidence: `.github/workflows/ci.yml`; `.github/workflows/release.yml`; CI run 42621588987 |
| D9 | Which documents change? | The `mise run check` line in AGENTS.md's Development section (not the lets-spec block). In the README, the task list and the line that says how to run `check` without mise. The header comment of `ci.yml`. | Evidence: `AGENTS.md:53`; `README.md:747`, `README.md:752`; `.github/workflows/ci.yml:3` |
| D10 | Does `docs/data-updates.md` change? | No. It only says to wait for `mise run check` to pass, and does not list what the task runs. Those steps stay true. | Evidence: `docs/data-updates.md:74`, `:80`, `:108` |
| D11 | Does another change in flight clash? | No. PR #266 changes the OpenSpec pin line in `mise.toml`, not `[tasks.check]`. No other open pull request touches `mise.toml`, the workflows, AGENTS.md, the README or `docs/data-updates.md`. | Evidence: `gh pr list` with each pull request's files |
| D12 | Does the epic's scenario check (#230 Shared decision 6) apply? | No. This change adds a new spec and changes no existing main spec, so no scenario can be lost. | Evidence: #230 Shared decision 6 |
| D13 | What does "done" mean for this story? | `openspec validate strict-spec-gate --strict` passes before archive. After archive, `mise run check` runs the strict spec check and is green, including on the new `dev-checks` spec. The contract test shows a long requirement fails the check. | Evidence: #230 Shared decision 7; #245 |

## Changes from the story

- Cut: `docs/data-updates.md` needs no edit, because it never lists what `mise run check` runs (D10).
- Cut: no CI workflow step changes, only the header comment of `ci.yml`, because CI already installs OpenSpec from `mise.toml` (D8).
- Added: a contract test on the pinned OpenSpec, because PR #266 shows the pin moves (D6, D7).

The user delegated the brainstorm and asked for the recommended answers to be taken, so that stands as confirmation.

Confirmed by user: yes
