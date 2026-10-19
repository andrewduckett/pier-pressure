# AGENTS.md

Guidance for AI agents working in this repo. `CLAUDE.md` is a symlink to this file.

## What this is

PierPressure decides "is tonight worth setting up for, and what should I point at
from this pier?" and delivers the verdict into Home Assistant over MQTT. A pure
Python core computes one deterministic verdict document per pier; a dumb
MQTT-discovery adapter publishes it. The product intent lives in
`openspec/prd.md`; personas and journeys live in `openspec/discovery.md`; the
backlog is the GitHub Project linked to this repository.

## Durable constraints (honor in every change)

- **Pure, deterministic core.** `pierpressure/core/` is pure Python 3.14+ with
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
  interface with graceful fallback. The optional LLM layer only
  explains an already-computed verdict — it never feeds the astronomy math.

## Development

The shared working rules are in the Let's Spec block at the end of this file.
This section adds what is specific to PierPressure.

- **Dev tools:** `mise.toml` pins `uv`, `just` and the Let's Spec tools; run
  `mise install` once. uv installs the Python in `.python-version`. Without mise,
  install uv and just yourself.
- **Toolchain:** `uv` (env/deps/lockfile), `just` (tasks), `ruff` (lint AND
  format — no black), `mypy` (strict types), `pytest`. Python 3.14, pinned only in
  `.python-version`.
- **`just check`** (`ruff check`, mypy, pytest) is the CI gate — it must be green
  before a PR. Formatting is enforced by the pre-commit hooks
  (`uv run pre-commit install` once per clone), not by `just check`. Practice TDD:
  write the failing test first.
- Add dependencies with `uv add` so `pyproject.toml` and `uv.lock` stay in step.
- **Plain language:** apply the core standard (`iso-24495-1`) to all prose, and
  the science and technical sector standard (`iso-24495-3`) to architecture specs,
  design docs and software documentation.

<!-- BEGIN lets-spec rules. lets-sync rewrites this block: change lets-spec, not this text. -->
## Workflow

These rules come from lets-spec, and apply to every agent.

- **Plan product changes with OpenSpec.** Work in progress lives in
  `openspec/changes/`, specs in `openspec/specs/`, and decision records
  in `docs/decisions/`. A change starts with a brainstorm and ends with
  archive. The schema's instructions say what to do at each step in
  between. [Routing](#routing) says where each request starts.
- **One change is one branch and one pull request,** from propose to
  archive. Independent changes branch off the repository's default
  branch. A change that
  depends on another stacks: it branches off the other change's branch
  and targets its pull request.
- **One commit per unit of work,** with Conventional Commits: `feat:`,
  `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- **Run the project's checks** before you push, and fix what they
  report. The project's own instructions say how to run them.
- **When you review code, also apply the project's `REVIEW.md`,** if it
  has one.
- **The backlog is the GitHub Project linked to this repository.**
  `lets-shape` sets kind, priority, size and readiness; `lets-build`
  picks, claims and routes. Never set a Project field with `gh` outside
  those skills. Every piece of work is an issue, and its pull request
  says `Closes #<n>`. An epic is a parent issue with its stories as
  sub-issues. Dependencies are "blocked by" links on the story they
  block. Put a blocker on each story it blocks, never only on the epic:
  picking the next story cannot see a blocker on a parent issue. A
  "relates to" link never counts as a blocker.
- **The user owns the merge.** Never merge a pull request unless the
  user asks. Stacks merge bottom-up.
- **Change requests reopen an archived change.** If a ready pull request
  gets change requests, mark it as a draft again and `git revert` the
  archive commit. Make the fixes, archive again as the last commit, and
  mark it ready. A rejected pull request is closed and its branch
  deleted.
- **Never edit what lets-spec puts in the project:** this section,
  between its markers, the skills in `.agents/skills/` and the schema
  folders in `openspec/schemas/`. `lets sync` rewrites this section, and
  the skills and the schema are read-only links into the Nix store that
  git ignores. Change lets-spec instead. Never run `openspec init` or
  `openspec update`; they write skills of their own.

### Routing

| Request | Start with |
|---|---|
| A large idea, or work that needs splitting or prioritizing | The `lets-shape` skill |
| A bug, a chore or a single story with no issue yet, or an issue with no packet | The `lets-shape` skill |
| Start the next story, or move the current branch's change on | The `lets-build` skill |
| Set up or check this repository's backlog | The `lets-setup-backlog` skill |

### Writing

- **Write prose in plain language** (ISO 24495): READMEs, decision
  records, issue bodies, `docs/`, pull request descriptions and OpenSpec
  artifacts. Put the reader first, and make each document easy to find,
  understand and act on. Code and config follow their own conventions.
- **Put scratch files in `.workspace/`** at the repo root, not in `/tmp`
  or a scratch path your tool suggests. Create it if it is missing, and
  keep it out of git. Anything worth keeping belongs in the repo or an
  issue.
<!-- END lets-spec rules -->
