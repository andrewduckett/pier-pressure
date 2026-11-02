## 1. Cap the update bot's own Node

- [x] 1.1 [easy] A package rule in `.github/renovate.json5` limits `node` in `.github/workflows/renovate.yml` to versions below 25, with a comment saying why and when to raise it (verify: `mise exec node@24 -- npx --yes --package renovate@44.201.1 -- renovate-config-validator --strict --no-global .github/renovate.json5`) (✓ renovate-config-validator --strict passed)
- [x] 1.2 [easy] The workflow's comment on the Node pin points to the new rule (verify: `grep -n 'renovate.json5' .github/workflows/renovate.yml`) (✓ grep found the pointer at line 25)
- [x] 1.3 [medium] A local Renovate dry run offers no Node 26 update for `RENOVATE_NODE_VERSION`, and still lists the `mise.toml` Node pin as a dependency it manages (verify: `mise exec node@24 -- npx --yes --package renovate@44.201.1 -- renovate --platform=local --dry-run=lookup` with `LOG_LEVEL=debug`, then inspect the `packageFiles with updates` output) (✓ dry run before the rule offered 24 → 26; after, no update for the workflow and mise.toml Node still listed)
- [x] 1.4 [easy] The CI gate stays green (verify: `mise run check`) (✓ mise run check passed: ruff, mypy, 1647 tests)
