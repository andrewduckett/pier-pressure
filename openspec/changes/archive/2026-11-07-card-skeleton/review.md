## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through `lets delegate review run`, resolver t3)
- **Independent**: yes. The author is Claude; the reviewer is Gemini.
- **Tool restrictions**: read-only: the reviewer ran in plan mode and changed no file
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0034, the edit to ADR-0026, and the source files the prompt listed, at commit `ddcddf8`
- **Raw output**: the reviewer ran in plan mode, so `lets delegate` reported "the session stopped to ask" and wrote no raw file. The findings below come from the reviewer thread's final message, recovered with `t3_thread_read` into `.workspace/card-skeleton-review-raw.md`.

## Findings

Each finding was checked against the repository. CONFIRMED means the defect is real.

### 🔴 Critical (blocking)

1. **`node_modules/` is not ignored** (check: scope, contradictions). CONFIRMED for git: `.gitignore` has `dist/` but no `node_modules/`, and the plan never touched it. REFUTED for Docker: the `Dockerfile` copies named paths only (lines 24 and 31), and BuildKit sends only the files those `COPY` lines name, so `card/node_modules/` never enters the image build.
2. **The slug rule differs between the spec and DD4, and empty slugs pass** (check: contradictions, scenario testability). CONFIRMED. The spec said "letters and digits"; DD4 said NFKD and `a-z0-9`. DD4's claim to match Home Assistant for every id was false: `PierConfig.id` is any string, and Home Assistant transliterates letters such as `ß` and `ø`. `pier: "---"` passed `setConfig`.
3. **No behaviour for the state `unknown` or a card without `hass`** (check: contradictions). CONFIRMED. `Service.run` goes online before its first publish, so a retained discovery config gives a Verdict sensor in `unknown`. Home Assistant calls `setConfig` before it sets `hass`.

### 🟡 Moderate

4. **`npm ci` in `mise run check` reinstalls on every run and needs network** (check: assumption rows, test seams). CONFIRMED that `npm ci` deletes `node_modules/` every run and that release.yml had no npm cache. The comparison with uv is half right: `uv run` syncs the environment too, but it does not delete it.
5. **HACS reads the latest release tag, not `main`** (check: assumption rows). CONFIRMED. The repository has releases up to `2026.10.2`, none with `hacs.json`. The design's Context, Risks and Rollback text were wrong about it.
6. **Zero and null values, a blank version, a duplicate picker entry, `process` types** (check: scenario testability). CONFIRMED. README.md:503-504 documents `score: 0` at the end of the night.
7. **`dashboard-check` can serve a cached card and does not print its URL; the docs requirement leaves out `/local/` and the resource type** (check: test seams, scenario testability). CONFIRMED. `_reset_home_assistant_state()` keeps `www/` between runs.

### 📌 Suggestions

8. **README and AGENTS.md sections go stale; `release.yml` has a pytest seam** (check: scope). CONFIRMED. `tests/test_ha_addon.py` already parses `release.yml`. Adding CodeQL for JavaScript is declined below.
9. **Sentences over 30 words and passives without an actor** (check: plain language). CONFIRMED for the sentences listed.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Add `node_modules/` to `.gitignore` in the plan (proposal Impact, design DD7 and Blast radius). No `.dockerignore`.
2. State one slug rule in the spec, in steps, with an accented scenario. Make `setConfig` throw when the slug is empty, with a punctuation-only scenario. Drop DD4's claim, and record the transliteration limit and the docs guidance for it.
3. Add a requirement and scenario for a card with no `hass` yet, and a scenario for the state `unknown`. Make `hass` optional in DD3 and cover both in DD5.
4. Split `card-install` from `card` in DD7, with mise `sources` and `outputs` so it runs only when the lockfile changes. Run it from `install` too. Cache `~/.npm` in both release jobs.
5. Correct the HACS text in the design's Context, Risks and Migration & Rollback. Require the docs to say the HACS route works from the first release that carries the card.
6. Add scenarios for `score: 0`, `{band: LOW, value: 0}` and a null `confidence`, and one for loading the file twice. In the design: `?.trim() || "dev"`, de-duplicate `customCards` by type, and add `@types/node`.
7. In DD11, add a content-hash query to the card's resource URL and print the card dashboard's URL. Require the docs to name `/local/pierpressure-card.js` and the type JavaScript module.
8. Widen the README and AGENTS.md edits in the proposal. Add the `release.yml` assertion to the test seams.
9. Split the long sentences in the spec, design, proposal, adr.md and ADR-0034, and name the actor in the spec's error requirement and in DD7.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed in part: `.gitignore` is in proposal Impact, DD7 and Blast radius. Rebutted in part: no `.dockerignore`, because `Dockerfile` lines 24 and 31 copy named paths and BuildKit transfers only those (DD7 says so).
2. Fixed: spec "The card finds the pier's Verdict sensor" lists the four steps and adds the `Côte Nord` scenario; "The card needs a pier" requires a letter or digit and adds the `"---"` scenario; DD4 records the transliteration limit; the new requirement "The docs show how to configure the card" covers finding the real entity id.
3. Fixed: new requirement "The card waits for Home Assistant's state"; scenario "Before the first verdict" under "The card shows the verdict"; DD3 makes `hass` optional; DD5 covers both.
4. Fixed: DD7 now has `card-install` with `sources` and `outputs`, run by `install` and by `card`; npm cache in CI and both release jobs; the Risks entry is rewritten.
5. Fixed: design Context, Risks and Migration & Rollback; spec "The docs say how to install the card".
6. Fixed: scenarios "A score of zero", "A confidence of zero", "A null confidence" and "The file loads twice"; DD5 and DD6 updated; `@types/node` in DD6 and the proposal.
7. Fixed: DD11 adds the `?v=<hash>` query and the ready message; spec "The docs say how to install the card" names the URL and type.
8. Fixed: proposal Impact names the README sections and AGENTS.md; Test Seams adds the `release.yml` check. Declined: CodeQL for JavaScript. It changes the repository's code scanning, which the `main` ruleset gates on, and belongs in its own chore.
9. Fixed: the listed sentences are split; the spec says "the card throws an error"; DD7 names the implementer.
