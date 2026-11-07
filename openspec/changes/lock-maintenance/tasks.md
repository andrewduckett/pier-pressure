## 1. Refresh uv.lock weekly

- [x] 1.1 [easy] Renovate's pep621 manager runs lock file maintenance, so a weekly pull request refreshes uv.lock and no other lock file (verify: mise exec node@24 -- npx --yes --package renovate@44.201.1 -- renovate-config-validator --strict --no-global .github/renovate.json5) (✓ renovate-config-validator passed; a local --platform=local dry run plans renovate/lock-file-maintenance, which it did not before)
- [x] 1.2 [easy] The lock file refresh is scheduled `on monday`, so it fires within the 04:17 UTC daily run rather than Renovate's default `before 4am on monday` (verify: mise exec node@24 -- npx --yes --package renovate@44.201.1 -- renovate-config-validator --strict --no-global .github/renovate.json5) (✓ renovate-config-validator passed)
- [ ] 1.3 [easy] The README's "What Renovate updates" list describes the weekly uv.lock refresh, and how to get it early from the Dependency Dashboard (verify: grep -q 'uv.lock` refresh' README.md)
- [ ] 1.4 [easy] The README's security bullet says a transitive package's fix arrives in the uv.lock refresh, not in a `[security]` pull request (verify: grep -q 'transitive' README.md)
- [ ] 1.5 [easy] The project's checks pass with the change (verify: mise run check)
