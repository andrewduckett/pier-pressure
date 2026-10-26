## 1. Move the tasks to mise and remove just

The decisions are in `brainstorm.md` (D1–D10). There is no product behavior to
test, so each task is verified by running the task itself or by a grep that
fails while a stale mention remains. `P` below is the pattern for a live `just`
mention:

`` P='`just|Justfile|\bjust (install|run|lint|format|typecheck|test|check|up|broker)|uv and just|uv, just|\[just\]|-- just|through just|just \(task|^just = ' ``

- [x] 1.1 [medium] `mise run check` runs the `lint`, `typecheck` and `test` tasks from `[tasks]` in `mise.toml`, in that order, and stops at the first failure (D3, D4) (verify: `mise run check`) (✓ `mise run check` passed: 1153 tests)
- [x] 1.2 [easy] `install`, `format`, `run`, `broker-up`, `up` and `broker-down` are mise tasks with the same commands and descriptions as their Justfile recipes, and there is no `default` task (D5, D9) (verify: `for t in install lint format typecheck test run check broker-up up broker-down; do mise tasks info "$t" >/dev/null || exit 1; done; ! mise tasks info default 2>/dev/null`) (✓ verify loop passed)
- [ ] 1.3 [medium] `mise run test-integration` starts the Compose broker, runs `pytest -m integration`, always tears the stack down, and exits with pytest's status (D7) (verify: `mise run test-integration`)
- [ ] 1.4 [easy] The `Justfile` and the `just` pin in `mise.toml` are gone, and `PYTHON_VERSION` still comes from `[env]` (D6) (verify: `test ! -e Justfile && ! grep -qE '^just = ' mise.toml && mise install && test -n "$(mise exec -- printenv PYTHON_VERSION)"`)
- [ ] 1.5 [easy] The CI and release workflows run `mise run check` and `mise run test-integration`, and their comments name only the tools mise still installs (verify: `! grep -nE "$P" .github/workflows/*.yml && grep -q 'mise run check' .github/workflows/ci.yml && grep -q 'mise run check' .github/workflows/release.yml && grep -q 'mise run test-integration' .github/workflows/ci.yml`)
- [ ] 1.6 [easy] The `compose.yaml` comments and its `PYTHON_VERSION` error message point at `mise run` (verify: `! grep -nE "$P" compose.yaml && mise exec -- docker compose --profile full config -q`)
- [ ] 1.7 [medium] The README and `docs/data-updates.md` show `mise run <task>` and `mise tasks`. For people without mise, they say to install uv and run the uv command shown for each task (D8) (verify: `! grep -nE "$P" README.md docs/data-updates.md`)
- [ ] 1.8 [easy] The Development section of `AGENTS.md`, the `context` in `openspec/config.yaml`, the discovery map in `openspec/discovery.md` and the toolchain line in `openspec/prd.md` name mise as the task runner and `mise run check` as the CI gate, and the Let's Spec block in `AGENTS.md` is untouched (D1) (verify: `! grep -nE "$P" AGENTS.md openspec/config.yaml openspec/discovery.md openspec/prd.md && mise exec -- lets sync --check`)
- [ ] 1.9 [easy] The comments in `pyproject.toml`, `Dockerfile` and `.pre-commit-config.yaml`, and the docstring in `tests/test_integration.py`, say `mise run` (D1) (verify: `! grep -nE "$P" pyproject.toml Dockerfile .pre-commit-config.yaml tests/test_integration.py`)
- [ ] 1.10 [easy] No live `just` mention is left outside the history (ADRs, changes, Let's Spec files), and the full gate passes (verify: `! git grep -nE "$P" -- . ':!openspec/changes' ':!docs/decisions' ':!.agents' ':!.claude' && mise run check`)
