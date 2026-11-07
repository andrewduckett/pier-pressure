## 1. The card's toolchain

- [x] 1.1 [medium] `mise run card` installs the card's packages only when `card/package-lock.json` changed, then type-checks, tests and builds `card/` into one self-contained `card/dist/pierpressure-card.js` stamped with `PIERPRESSURE_VERSION`, or `dev` when it is unset or blank; `mise run check` and `mise run install` run the card tasks, and `.gitignore` ignores `node_modules/` (design DD1, DD2, DD6, DD7; test: a Vitest build test asserts one file, no `import`, and the version stamp) (verify: mise run card) (✓ mise run card and mise run check passed)

## 2. The card [depends-on: 1]

- [ ] 2.1 [easy] The pier id `Back-Yard` maps to `sensor.pierpressure_back_yard_verdict`, `Côte Nord` to `sensor.pierpressure_cote_nord_verdict`, and `"---"` to an empty slug (design DD4) (verify: mise exec -- npm --prefix card test -- entity)
- [ ] 2.2 [easy] Loading the card module defines `pierpressure-card`, adds one `window.customCards` entry, logs `PIERPRESSURE-CARD <version>`, and a second load neither throws nor adds a second entry (design DD5) (verify: mise exec -- npm --prefix card test -- register)
- [ ] 2.3 [easy] `setConfig` throws "pier is required" for no `pier`, `""`, `"   "` and `"---"`, and accepts `backyard` (verify: mise exec -- npm --prefix card test -- config)
- [ ] 2.4 [medium] The card renders its frame with nothing in it before `hass` is set, then shows the Verdict sensor's verdict, score and confidence, with `—` for `unknown`, a null or missing score, and a null or missing confidence part, and `0` for a zero score or confidence value (verify: mise exec -- npm --prefix card test -- render)
- [ ] 2.5 [easy] The card shows "No PierPressure verdict found: <entity id>" when the entity is missing, and "PierPressure is offline" when its state is `unavailable`, with no verdict, score or confidence (verify: mise exec -- npm --prefix card test -- messages)

## 3. Shipping the card [depends-on: 1]

- [ ] 3.1 [parallel] [easy] `hacs.json` at the root names `pierpressure-card.js`, beside `repository.yaml` (test: `tests/test_night_card_doc.py`) (design DD9) (verify: uv run pytest tests/test_night_card_doc.py -k hacs)
- [ ] 3.2 [medium] The release job installs mise's tools, builds the card with the release version after computing it and before the image build, and passes `card/dist/pierpressure-card.js` to `gh release create`; CI's `check` job and both release jobs cache `~/.npm` keyed on `card/package-lock.json` (design DD7, DD8; test: parse `release.yml` as `tests/test_ha_addon.py` does) (verify: uv run pytest tests/test_night_card_doc.py -k release)
- [ ] 3.3 [parallel] [easy] Renovate groups npm minor and patch updates into one pull request named "npm minor and patch" (design DD10) (verify: mise exec node@24 -- npx --yes --package renovate@44.201.1 -- renovate-config-validator --strict --no-global .github/renovate.json5)
- [ ] 3.4 [medium] `dashboard-check` depends on `card`, copies the built card into `www/pierpressure-card/`, registers it with a `?v=<hash>` query, adds a `pierpressure-card` dashboard holding `type: custom:pierpressure-card` with `pier: backyard`, prints that dashboard's URL, and fails with a message naming `mise run card` when the file is missing (design DD11) (verify: uv run pytest tests/test_dashboard_check.py)

## 4. Docs and the whole path [depends-on: 2, 3]

- [ ] 4.1 [medium] `docs/night-card.md` describes the HACS custom Dashboard route (from the first release that carries the card) and the `/config/www` route with `/local/pierpressure-card.js` as a JavaScript module, shows the card YAML, and says how to find the Verdict entity id; the README links it and its development, dependency update and releasing sections and `AGENTS.md` say what the card adds (verify: uv run pytest tests/test_night_card_doc.py -k docs)
- [ ] 4.2 [complex] The whole path works: `mise run check` is green, and `mise run dashboard-check` shows the card with tonight's verdict, score and confidence in a real Home Assistant, checked by eye (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
