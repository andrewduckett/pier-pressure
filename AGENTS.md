# AGENTS.md

Guidance for AI agents working in this repo. `CLAUDE.md` is a symlink to this file.

## What this is

PierPressure decides "is tonight worth setting up for, and what should I point at
from this pier?" and delivers the verdict into Home Assistant over MQTT. A pure
Python core computes one deterministic verdict document per pier; a dumb
MQTT-discovery adapter publishes it. The product intent lives in
`openspec/prd.md`; personas and journeys live in `openspec/discovery.md`; the
backlog is GitHub issues.

## Durable constraints (honor in every change)

- **Pure, deterministic core.** `pierpressure/core/` is pure Python 3.12+ with
  zero Home Assistant or MQTT imports (a test enforces the boundary). Same inputs
  — including a pinned evaluation instant from the injectable clock — yield a
  byte-identical verdict document. Astronomy is computed fully offline from a
  version-pinned ephemeris; no runtime network access.
- **The verdict document is a frozen contract.** The delivery surface (topics,
  entities, entity mapping) and the meaning of existing fields never change. The
  document may grow **additively** (new fields/objects) as new science arrives;
  reserve a field stubbed only when its shape is already known — don't invent a
  shape before the change that defines it.
- **Home Assistant is never load-bearing** for freshness or correctness. Delivery
  is via MQTT discovery (REST is an acceptable fallback). The core runs as a
  persistent container that owns its own freshness: recompute on startup, on a
  configurable interval, and on demand via a "show me now" refresh command.
- **Verdict model:** hard GATES (any fail → `NO-GO` with a reason and null score),
  then a banded 0–100 SCORE only when gates pass; `reasons[]` are the itemized
  terms. Target windows are hard-clamped to astronomical night (sun below −18°).
- **No single external data source is load-bearing:** providers sit behind an
  interface with caching and graceful fallback. The optional LLM layer only
  explains an already-computed verdict — it never feeds the astronomy math.

## Workflow

- Planning uses **OpenSpec**: in-flight work lives under `openspec/changes/`;
  durable specs under `openspec/specs/`; decision records under `docs/decisions/`. Use
  the `opsx:*` skills (propose → apply → verify → archive). OpenSpec changes carry
  product behavior. Repo maintenance (tooling, docs, backlog housekeeping) goes
  through an ordinary branch and PR with Conventional Commits.
- **Dev shell:** `flake.nix` provides Python (from `.python-version`), `uv`, and
  `just`; `direnv` loads it through `.envrc`. Without Nix, install uv and just
  yourself.
- **Toolchain:** `uv` (env/deps/lockfile), `just` (tasks), `ruff` (lint AND
  format — no black), `mypy` (strict types), `pytest`. Python pinned to 3.12.
- **`just check`** (`ruff check`, mypy, pytest) is the CI gate — it must be green
  before a PR. Formatting is enforced by the pre-commit hooks
  (`uv run pre-commit install` once per clone), not by `just check`. Practice TDD:
  write the failing test first.
- Add dependencies with `uv add` so `pyproject.toml` and `uv.lock` stay in step.

### OpenSpec git workflow

One branch and one pull request carry a change through its whole lifecycle —
propose, apply, verify, archive — and merge once. There is no "cross `main`
between phases" step.

- **Branch per change.** One OpenSpec change (one backlog issue) = one branch =
  one PR. Dependent stories **stack**: branch off the parent's branch and target
  its PR; independent stories branch off `main`.
- **A commit per unit of work.** Each artifact (proposal, design, specs, tasks) is
  its own `docs:` commit; each implementation task is its own commit with its real
  type (`feat:`/`fix:`/`refactor:`/`test:`); the archive is its own `chore:` commit.
- **Draft until archived.** Open the PR as a draft at propose, and assign its issue
  (`gh issue edit <n> --add-assignee @me`). An assigned open issue is in progress, so
  propose does not pick it again. Run propose → apply →
  verify → archive all on the branch; `archive` moves the change to
  `openspec/changes/archive/` and syncs delta specs into `openspec/specs/`. Flip the
  PR to ready when the archive commit lands.
- **User owns the merge.** The agent never merges a PR unless the user explicitly
  asks and confirms. Stacks merge bottom-up: parent to `main` first, then retarget
  and merge each child.
- **If a ready PR gets change-requests,** flip it back to draft and `git revert` the
  archive commit — this restores the change under `openspec/changes/` and unwinds the
  spec sync. Make the fixes, re-archive as the last commit, and flip ready again. A
  rejected PR is just closed and its branch deleted; `main` stays clean.
- **Every story is an issue.** Its body is the story packet; propose reads it and
  names the issue in `proposal.md`. The story's PR says `Closes #<issue>`, so merging
  closes it. An epic is a parent issue, labeled `kind/epic`, with its stories as
  sub-issues; close the epic once all its sub-issues are closed. Dependencies are
  "blocked by" links.
- **Every story carries one MoSCoW priority label:** `priority/must`,
  `priority/should`, `priority/could`, or `priority/wont`. The label matches the
  `MoSCoW` line in the story packet; when you change one, change the other in the same
  edit. Epics and untriaged issues have no priority label.

## Writing document artifacts — plain language

Write every document artifact — READMEs, ADRs, OpenSpec proposals/designs/specs,
GitHub issue bodies, `docs/`, PR descriptions, and other prose deliverables — to
the **ISO 24495 Plain Language** standard: reader-first, purposeful structure,
findable, understandable, and actionable. Apply the core standard (`iso-24495-1`) to all prose, and the
science/technical sector standard (`iso-24495-3`) to architecture specs, design
docs, and software documentation. This governs prose only — code, config, and test
fixtures follow the toolchain's own conventions.

## Scratch & Working Files

Temporary files — scratch notes, intermediate output, working scripts, throwaway data — go in
**`.workspace/`** at the repo root. It is gitignored (see `.gitignore`). **Use it instead of `/tmp`
or any scratchpad path your tooling suggests** — this convention overrides a harness-provided
scratchpad location. Create the directory if it isn't there (`mkdir -p .workspace`). Nothing durable
lives here; anything worth keeping belongs in the repo tree or a GitHub issue.
