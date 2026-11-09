## Why

Epic #230 brought every main spec to zero OpenSpec warnings, and strict validation now passes (D1). But `mise run check` does not run it, so the next requirement over 500 characters, or any other warning, would pass CI unseen. Strict mode turns that warning into a failure (D2), so adding it to the check keeps the epic's work from regressing.

## What Changes

- `mise run check` runs `openspec validate --specs --strict --no-interactive`, through a task of its own that a developer can also run alone (D3, D4). A main spec that breaks an OpenSpec rule fails the check, and so fails CI.
- Changes in progress, archived changes and the 500-character limit stay as they are (D3).
- Two tests, written first: one reads `mise.toml` and checks that `check` runs the strict spec check; a contract test runs the pinned OpenSpec on a throwaway spec and checks that a long requirement fails (D6). The contract test catches an OpenSpec update that stops failing on one, as Renovate already moves the pin (D7).
- The docs that list what `mise run check` runs say so: AGENTS.md's Development section, the README and the header comment of `ci.yml` (D9). `docs/data-updates.md` needs no edit (D10).
- CI needs no new step, because its `check` jobs already install OpenSpec from `mise.toml` (D8).
- Nothing is **BREAKING**. A change that adds a long requirement to a main spec now fails the check, which is the point.

## Capabilities

### New Capabilities

- `dev-checks`: what the `check` task runs before a pull request, starting with strict validation of the main specs (D5).

### Modified Capabilities

None.

## Impact

- `mise.toml`: a new task, and one more task reference in `[tasks.check]`.
- `tests/`: a configuration test for `mise.toml`, and a contract test that runs the `openspec` CLI.
- `AGENTS.md` (Development section only, not the lets-spec block), `README.md` and the header comment of `.github/workflows/ci.yml`.
- CI time grows by the second or so that OpenSpec takes to validate 11 specs.
- PR #266 (Renovate) changes the OpenSpec pin line in `mise.toml`, not `[tasks.check]`, so the two do not clash (D11).
- No product code, verdict document or delivery surface changes. No existing main spec changes, so the epic's scenario check does not apply (D12).
