---
id: adrs-adr0024
date: 2026-10-25
status: accepted
title: 'ADR-0024: Self-hosted Renovate owns every dependency update, and Dependabot only raises alerts'
description: Architecture decision record for replacing Dependabot version updates with a self-hosted Renovate run, while Dependabot alerts stay on as the source of security fixes.
---

# ADR-0024: Self-hosted Renovate owns every dependency update, and Dependabot only raises alerts

## Context

PierPressure pins its dependencies in four places: `pyproject.toml` with `uv.lock`, the actions in `.github/workflows/`, the images in the `Dockerfile` and `compose.yaml`, and the development tools in `mise.toml`. The tools in `mise.toml` include uv, just, Node, gh, the OpenSpec CLI and Let's Spec.

Dependabot covered the first three, but it can't read `mise.toml`. Those tools were bumped by hand and fell behind. A Let's Spec bump also has to run `lets sync` and commit what it writes, or CI's Let's Spec check fails.

Two bots that both open version updates for the same file open duplicate pull requests. So one tool has to own every version update.

## Decision

Renovate owns every version update. It runs self-hosted, from a scheduled GitHub Actions workflow in this repository, with the repository's own mise toolchain on PATH. It signs in as a GitHub App. Dependabot keeps only its alerts: version updates and Dependabot security updates are off. Renovate reads the alerts and opens a separate pull request for each fix.

## Consequences

- **Easier:** every pin, `mise.toml` included, gets update pull requests, with one set of grouping and schedule rules.
- **Easier:** a Let's Spec bump arrives complete. Renovate runs `lets sync` on it, so the pull request already passes the Let's Spec check.
- **Easier:** security fixes and version updates come from one bot, so they never race each other on the same dependency.
- **Harder:** the project now runs a bot of its own. The workflow, the GitHub App, its private key and the Renovate version all need looking after.
- **Harder:** the update rules are Renovate's, not Dependabot's, and some defaults differ. For example, Renovate skips a Python package listed without a version, so every direct package needs a lower bound.
- **Harder:** adding a Dependabot version update back, even for one ecosystem, reintroduces duplicate pull requests.

## Alternatives Considered

### Alternative 1: Keep Dependabot, and bump `mise.toml` by hand
- **Pros**: nothing new to run. Dependabot is built into GitHub.
- **Cons**: the hand-bumped tools keep drifting. Let's Spec, OpenSpec and gh were all behind when this was decided.
- **Why not**: it leaves the original problem in place.

### Alternative 2: Dependabot for its ecosystems, Renovate for `mise.toml` only
- **Pros**: the update rules for uv, Actions and Docker stay as they were.
- **Cons**: two bots with two configs, two dashboards and two sets of rules. Renovate's default managers would also need turning off, one by one, to avoid duplicates.
- **Why not**: two configs to keep in step cost more than moving the existing rules to Renovate once.

### Alternative 3: Mend's hosted Renovate app
- **Pros**: nothing to run or keep up to date. The hosted service schedules the runs.
- **Cons**: it doesn't run post-upgrade commands from a repository's config.
- **Why not**: a Let's Spec bump would then fail the Let's Spec check until someone ran `lets sync` by hand.
