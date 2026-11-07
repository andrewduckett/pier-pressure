## Context

- PierPressure is a Python service. The repository holds no JavaScript yet, but
  `mise.toml` already pins `node = "26"` (for the OpenSpec CLI), so Node 26 and
  npm 11 are on every developer's and CI runner's path through mise.
- `main` requires two checks: `check` and `image`. `check` runs
  `mise run check` (ruff, mypy, pytest) and `lets sync --check`. A
  path-filtered job could not be required, so the card has to build inside
  `check`.
- The release workflow has a `check` job (`mise run check`) and a `release`
  job that computes the CalVer version, pushes the image, and then runs
  `gh release create`. The `release` job does not use mise today; it sets up
  Python with `actions/setup-python`.
- `.gitignore` already ignores every `dist/` folder, so a build output in
  `card/dist/` is never committed. It does not ignore `node_modules/` yet.
- This repository already has releases. For a repository with releases, HACS
  reads `hacs.json` and the file tree at the latest release tag, not at
  `main`, and takes the card's file from that release's assets. So HACS can
  add the repository only once a release carries `hacs.json` and the card.
- Home Assistant writes the Verdict sensor's entity id as
  `sensor.pierpressure_<pier>_verdict`: the device is `PierPressure <pier>`, the
  entity is `Verdict`, and `has_entity_name` is on
  (`pierpressure/delivery/mqtt.py`). `docs/night-dashboard.md` documents the
  same slug rule for readers.
- `scripts/dashboard_check.py` starts a throwaway Home Assistant with YAML-mode
  dashboards and YAML-mode resources, and already serves files from
  `config/www/` as `/local/`.

## Goals / Non-Goals

**Goals:**

- One command, `mise run card`, installs, type-checks, tests and builds the
  card, and `mise run check` runs it, so CI and the release run exactly what a
  developer runs.
- The card's runtime surface is as small as possible: it reads `hass.states`
  and renders inside Home Assistant's `ha-card`. Nothing else in the Home
  Assistant frontend is used.
- The card's logic is unit-tested without a browser; how it looks is checked
  by eye in the throwaway Home Assistant.

**Non-Goals:**

- Any drawing: the strip, the darkness bar, target windows (later #132 stories).
- Reading any entity but the Verdict sensor.
- A visual config editor, a stub config for the card picker, theming beyond
  Home Assistant's own CSS variables.
- A linter or formatter for TypeScript (brainstorm D13).
- Testing the release workflow itself. It is checked by reading it, and by
  the first release after merge.

## Test Seams

- **Primary test seam:** Vitest in `card/`, under happy-dom. Tests import the
  card module, create the element, call `setConfig` and set a fake `hass`
  object (`{ states: { ... } }`), then read the rendered shadow DOM's text.
  The same suite runs Vite's build into a temporary folder and inspects the
  output, which covers "one self-contained file" and the version stamp.
- **Existing seams reused:** pytest for repository files. A new
  `tests/test_night_card_doc.py` reads `hacs.json`, `docs/night-card.md` and
  `README.md`, in the style of `tests/test_night_dashboard_doc.py`. It also
  parses `release.yml`, as `tests/test_ha_addon.py` does, to check that the
  card build comes before the image build and that `gh release create`
  attaches the file. `tests/test_dashboard_check.py` gains tests for the
  card's resource, dashboard, file copy and ready message.

## Scrutiny Tier & Blast Radius

- **Tier:** high. The change adds a new toolchain and package ecosystem (npm),
  a new public contract (the card type, its `pier` key and the release asset
  HACS installs), and edits both required CI and the release workflow.
- **Blast radius:** new `card/` folder; `mise.toml` tasks; `.github/workflows/ci.yml`
  and `release.yml`; `.github/renovate.json5`; `hacs.json`; `.gitignore`;
  `scripts/dashboard_check.py`; `README.md`, `AGENTS.md`, docs and decision
  records. The Python package
  `pierpressure/`, the verdict document and the MQTT delivery do not change.

## Decisions

### DD1: Vite in library mode builds the file; Vitest tests it

Vite's library mode builds `src/pierpressure-card.ts` into one ES module,
`dist/pierpressure-card.js`, with no `external` entries, so Lit is bundled in.
Vitest shares Vite's config file, so one config and one toolchain do both
jobs (brainstorm D3).

- *Rollup with plugins* is what many Home Assistant cards use, but needs a
  TypeScript plugin, a resolve plugin and a separate test runner.
- *esbuild* builds fast with one dependency, but still needs a test runner and
  its config beside it.
- *@web/test-runner* tests in a real browser, but needs Playwright browsers in
  CI. happy-dom is enough for text and structure; the eye check covers the
  rest.

### DD2: Lit without decorators

The element uses Lit's `static properties` and `declare` fields instead of
`@customElement` and `@property`. That avoids choosing between TypeScript's
legacy and standard decorator modes, and keeps `tsconfig.json` to strict
defaults.

### DD3: A minimal local type for `hass`

The card declares only what it reads:
`{ states: Record<string, { state: string; attributes: Record<string, unknown> }> }`.
Its `hass` property is optional (`hass?: HomeAssistant`), because Home
Assistant calls `setConfig` and attaches the card before it sets `hass`.
It does not depend on `custom-card-helpers` or Home Assistant's frontend
types: the first is unmaintained, and the second is not published as a
package. A smaller surface also means fewer ways a frontend release can break
the card.

### DD4: The pier slug follows Home Assistant's rule

`pierSlug(pier)` lower-cases the id and removes accents: Unicode NFKD, then
it drops combining marks. It replaces each run of characters outside `a-z`
and `0-9` with one `_`, and trims `_` from both ends. `verdictEntityId(pier)`
wraps the slug. Both are pure functions, tested on their own.

The rule matches Home Assistant for ASCII and accented Latin ids, which the
night dashboard docs already assume. Home Assistant transliterates other
letters (`ß` becomes `ss`, `ø` becomes `o`, Cyrillic is romanised). The card
does not, so for such an id it shows the missing-entity message. The docs say
how to read the real entity id from Home Assistant. A transliteration table
would bring a dependency for a rare case; a later story can add an `entity`
override if anyone needs it.

### DD5: What the card renders

- `setConfig` throws `Error("pier is required")` when `pier` is not a string
  or its slug is empty (`""`, `"   "`, `"---"`). Home Assistant shows a
  thrown error as an error card.
- Before `hass` is set, the card renders the `ha-card` frame and nothing in
  it.
- The card renders an `ha-card` with the header `PierPressure <pier>` and
  three labelled values: Verdict, Score, Confidence. The state `unknown`
  shows `—` as the verdict. A `score` that is not a number shows `—`; the
  check is on type, so `0` shows `0`. Confidence shows `<band> · <value>`,
  with `—` for each missing or null part, and for a null `confidence`.
- No entity: one line, `No PierPressure verdict found: <entity id>`.
- State `unavailable`: one line, `PierPressure is offline`.
- `getCardSize()` returns 2.
- Loading the module defines `pierpressure-card` only if it is not defined
  yet. It adds `{type: "pierpressure-card", name: "PierPressure",
  description: ...}` to `window.customCards` only if no entry has that type.
  Then it calls `console.info("PIERPRESSURE-CARD <version>")`.

### DD6: The version is stamped at build time

`vite.config.ts` defines `__CARD_VERSION__` as
`process.env.PIERPRESSURE_VERSION?.trim() || "dev"`, so an unset or blank
variable gives `dev`. `@types/node` is a dev dependency, so `tsc` can check
`vite.config.ts` alongside `src/` and `test/`. The name matches the image's build argument. The
release job sets it to the computed version when it builds the card. The
`package.json` version stays `0.0.0` and `private: true`: the card is never
published to npm, and its version comes from the release (brainstorm D9).

### DD7: `mise run card`, run by `mise run check`

Two new tasks run in `card/`:

- `card-install` runs `npm ci --ignore-scripts --no-audit --no-fund`. Its mise
  `sources` is `package-lock.json` and its `outputs` is
  `node_modules/.package-lock.json`, so mise skips it while the installed
  packages match the lockfile. `npm ci` deletes `node_modules/` first, so
  this keeps `mise run check` from reinstalling on every run, and lets it
  run offline once the packages are installed.
- `card` depends on `card-install`, then runs `npm run typecheck`
  (`tsc --noEmit`), `npm test` (`vitest run`) and `npm run build`
  (`vite build`).

`install` also runs `card-install`, beside `uv sync`. `check` becomes lint,
typecheck, test, card. So the CI `check`
job and the release's `check` job run the card with no new step, and the
statement in `AGENTS.md` that `mise run check` is the CI gate stays true.
`--ignore-scripts` refuses package install scripts; Vite's and Rollup's
native binaries arrive as optional dependencies and need none. If a needed
package turns out to rely on an install script, the implementer drops the
flag and says why in a comment on the task.

- *A separate `card` step in CI only* keeps `mise run check` Python-only and
  faster, but makes "the CI gate" two commands and lets a developer push a
  broken card after a green `mise run check`.

CI's `check` job and both jobs of the release workflow cache `~/.npm`, keyed
on `card/package-lock.json`, beside the uv cache. `.gitignore` gains
`node_modules/`. The image build needs no `.dockerignore`: the `Dockerfile`
copies named paths only, and BuildKit sends only the files those `COPY`
lines name.

### DD8: The release builds and attaches the card before the image

The `release` job installs mise's tools with `jdx/mise-action` (which also
gives it the pinned Node), and runs `PIERPRESSURE_VERSION=<version> mise run card`
right after "Compute the next version" and before QEMU and the image build.
A failed card build stops the release before anything is published.
`gh release create` then names `card/dist/pierpressure-card.js` as an asset,
so the release and its card appear together. The `actions/setup-python` step
stays: the helper scripts run on it.

### DD9: `hacs.json` at the root

```json
{ "name": "PierPressure", "filename": "pierpressure-card.js" }
```

No `content_in_root` (HACS reads the release asset), and no minimum Home
Assistant version until the card uses something that needs one.

### DD10: Renovate groups npm minor and patch updates

A package rule `{ matchManagers: ["npm"], matchUpdateTypes: ["minor", "patch"],
groupName: "npm minor and patch" }`, beside the other ecosystem groups. Majors
fall through and arrive alone, as for every ecosystem. Renovate's npm manager
is on by default and finds `card/package.json` without further config.

### DD11: `dashboard-check` shows the locally built card

`mise run dashboard-check` gains `depends = ["card"]`. The script copies
`card/dist/pierpressure-card.js` into `config/www/pierpressure-card/`, adds
`/local/pierpressure-card/pierpressure-card.js?v=<hash>` to the YAML-mode
resources, where `<hash>` is the first 12 hex digits of the file's SHA-256.
The query makes the browser fetch a rebuilt card instead of a cached one.
It adds a second YAML-mode dashboard, `pierpressure-card`, whose one view holds
`type: custom:pierpressure-card` with `pier: backyard`. `ready_message()`
prints that dashboard's URL beside the night dashboard's. A missing
built file is a `RuntimeError` naming `mise run card`. The night dashboard
YAML stays exactly the docs page's block.

### DD12: The decision record supersedes ADR 0026 in part

A new ADR records that PierPressure ships its own card, from this repository,
through HACS, with the card versioned with the app. ADR 0026 is marked
superseded by it for its "no JavaScript card of its own" decision; its YAML
dashboard decision stands. The ADR step writes it.

## Risks / Trade-offs

- [npm brings a large dependency tree into a Python project] → Only build-time
  tools and Lit; `npm ci` from a committed lockfile; install scripts refused
  (DD7); Renovate and Dependabot alerts cover it like the other ecosystems.
- [TypeScript 7 is the new native compiler, released recently] → The card uses
  plain strict TypeScript with no decorators or emit; `tsc` only type-checks.
  If it misbehaves, pin TypeScript 5.9, which needs no code change.
- [Until a release carries the card, HACS cannot add this repository: it
  validates the latest release tag, which has no `hacs.json`] → The docs say
  the HACS route works from the first release that carries the card. The
  maintainer cuts a release after merge and checks the HACS install then.
- [happy-dom is not a browser, and Home Assistant's `ha-card` is not defined in
  tests] → Tests read text and structure only. `dashboard-check` shows the
  card in a real Home Assistant, by eye, before the pull request is ready.
- [The release workflow cannot run before merge] → A pytest test parses
  `release.yml` and checks the order of the card build and the image build,
  and the asset on `gh release create`. The maintainer checks the first
  release by hand: the asset exists, and its console line shows the version.
- [`mise run check` needs network the first time, to install the card's
  packages] → `card-install` runs only when the lockfile changes (DD7). After
  that, `mise run check` works offline.

## Migration & Rollback

N/A: no data or document shape changes. Rollback is a revert. HACS reads the
latest release tag, so a revert on `main` changes nothing for HACS users
until the next release, which then carries no `hacs.json` and no card. Cards
already installed keep working until the user removes them.
