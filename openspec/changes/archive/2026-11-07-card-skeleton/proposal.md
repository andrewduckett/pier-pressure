## Why

Epic #132 ships a PierPressure dashboard card through HACS, and every later card
story only adds drawing to it. Before any drawing, this story proves the whole
path once: card source, build, CI, release asset, HACS install and a dashboard
that shows tonight's verdict, score and confidence for one pier.

## What Changes

- A card source folder, `card/`, in Lit with TypeScript. One build turns it
  into a single file, `pierpressure-card.js`, with Lit inside it (D3, D4).
- The card, `custom:pierpressure-card`, takes `pier: <id>`, finds that pier's
  Verdict sensor (D5), and shows the verdict, score and confidence from it
  (D6). A missing key, a missing entity and an offline PierPressure each get a
  plain message rather than a broken card (D7).
- A mise task that installs, type-checks, tests and builds the card with the
  Node pinned in `mise.toml`. CI's required `check` job runs it on every pull
  request (D8).
- `hacs.json` at the repository root names the built file, so the repository
  is a HACS Dashboard repository as well as an add-on repository.
- Each release builds the card with the release version in it. It attaches
  the file to the GitHub release, so the card's version is the app's (D9).
  The release's check gate builds and tests the card too.
- Renovate groups npm minor and patch updates into one weekly pull request
  (D10).
- `mise run dashboard-check` installs the locally built card in its throwaway
  Home Assistant and shows it, so the card can be seen working before merge
  (D11).
- A decision record that supersedes ADR 0026's "no JavaScript card of its own".
  The YAML dashboard stays (D12).
- `docs/night-card.md`: install the card as a HACS custom Dashboard repository,
  or copy the file to `/config/www`, then add it to a dashboard. The README
  links to it.

Nothing in the core, the verdict document or the MQTT delivery changes.

## Capabilities

### New Capabilities

- `night-card`: the PierPressure dashboard card. How it is configured, which
  entity it reads, what it shows and how it behaves when its entity is missing
  or unavailable, how it is built and tested, and how it is installed.

### Modified Capabilities

- `release-image`: a release also builds and tests the card in its check gate,
  and attaches the built card, carrying the release version, to the GitHub
  release.
- `dependency-updates`: npm, for the card's packages in `card/`, joins the
  tracked files and the ecosystems that get one weekly minor and patch pull
  request.

## Impact

- New: `card/` (TypeScript source, tests, `package.json`,
  `package-lock.json`, build config), `hacs.json`, `docs/night-card.md`, and
  a new decision record in `docs/decisions/`.
- Changed: `mise.toml` (card tasks), `.github/workflows/ci.yml` (`check`
  job), `.github/workflows/release.yml` (build and attach the card),
  `.github/renovate.json5` (npm group), `.gitignore` (`node_modules/`),
  `scripts/dashboard_check.py` and its test, and ADR 0026's status.
- Docs brought in step: `README.md` (a link to the card docs, and its
  development, dependency update and releasing sections) and `AGENTS.md`
  (what `mise run check` runs).
- New dependencies, for the card only: Lit at runtime; TypeScript, Vite,
  Vitest, happy-dom and `@types/node` at build time. No Python dependency changes.
- Developers and CI now need `npm ci` in `card/` to build the card. Node is
  already pinned in `mise.toml`.
