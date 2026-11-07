**Why:** Renovate opens security pull requests only for dependencies it finds in `pyproject.toml`, so 37 Dependabot alerts on transitive packages in `uv.lock` sat open with no fix, against the `dependency-updates` requirement that every alert gets one.

## Story

#206 lock-maintenance — Renovate refreshes transitive uv.lock pins every week, https://github.com/andrewduckett/pier-pressure/issues/206

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | How do transitive security fixes in `uv.lock` arrive? | In a weekly lock file refresh pull request, Renovate's `lockFileMaintenance`. Direct packages keep their next-day `[security]` pull request | User |
| D2 | When does the refresh run? | On Mondays, set explicitly as `on monday`. Renovate's default of `before 4am on monday` never fires, because the runner starts at 04:17 UTC | Evidence: `.github/workflows/renovate.yml`, Renovate 44.201.1 `lockFileMaintenance` docs |
| D3 | Can an urgent transitive fix arrive sooner? | Yes. The maintainer ticks the lock file refresh on the Dependency Dashboard, and it opens at the next daily run | Evidence: Renovate Dependency Dashboard docs; `dependency-updates` "The Dependency Dashboard stays open" |
| D4 | Which lock files does it refresh? | `uv.lock` only, set on the `pep621` manager. `card/package-lock.json` is out of scope | User |
| D5 | Is the refresh a second uv pull request in the week? | Yes. It is its own pull request beside the weekly uv minor and patch one, so the grouping requirement names it as the one exception | User |
| D6 | What does the spec change? | MODIFIED "Security fixes arrive at once, on their own" (direct packages only), MODIFIED "Minor and patch updates arrive weekly, grouped by ecosystem" (the exception), ADDED a weekly `uv.lock` refresh requirement | Evidence: `openspec/specs/dependency-updates/spec.md` |
| D7 | Does it need a new decision record? | No. ADR-0024's decision stands; the spec and the README's "Dependency updates" section say how transitive fixes arrive | User |
| D8 | What proves it is done? | CI's Renovate config check passes, and the Dependency Dashboard lists the lock file refresh after the next daily run | Evidence: `.github/workflows/renovate.yml` `validate` job |

## Changes from the story

Added: the spec and README changes in D6 and D7, because the story's config change alone would contradict the `dependency-updates` spec. That takes the story from XS to S.

Confirmed by user: yes
