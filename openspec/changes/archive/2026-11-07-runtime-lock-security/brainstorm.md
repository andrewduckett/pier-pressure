**Why:** The container image installs certifi, pyasn1 and opentelemetry-api at versions with open advisories (one critical, four high, one medium), and Renovate opened no fix because all three are transitive.

## Story

#204 runtime-lock-security — the image ships patched certifi, pyasn1 and opentelemetry-api, https://github.com/andrewduckett/pier-pressure/issues/204

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which packages move? | certifi to 2026.10.23, pyasn1 to 0.6.5 and opentelemetry-api to 1.45.2, through `uv lock --upgrade-package` for each; no other package in `uv.lock` moves | Evidence: trial `uv lock --upgrade-package` run on 2026-11-07 |
| D2 | Does `pyproject.toml` change? | No. All three are transitive (httpx/requests/skyfield, google-auth, anthropic/pydantic-ai-slim), so no range lists them | Evidence: `uv tree --invert` |
| D3 | Does any behavior change? | No. This is a lockfile-only bump, so the change sets `skip_specs: true` | Evidence: `uv.lock`, `openspec/specs/` |
| D4 | What proves it is done? | `mise run check` passes, CI's `image` job builds, and Dependabot alerts 18, 30 and 40–43 close once it merges to `main` | Evidence: `.github/workflows/ci.yml` |
| D5 | Which commit prefix does the bump use? | `build(deps):`, the prefix update commits use | Evidence: `openspec/specs/dependency-updates/spec.md` |

## Changes from the story

None. The dev-group bumps are #205, and the Renovate gap that let these alerts build up is #206.

Confirmed by user: yes
