## Story

#180 card-skeleton — the PierPressure card installs through HACS and shows
tonight's verdict, score and confidence.
https://github.com/andrewduckett/pier-pressure/issues/180

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | A new `night-card` capability, beside `night-dashboard`; deltas to `release-image` (the card is a release asset) and `dependency-updates` (npm joins the ecosystems) | Assumption |
| D3 | Which bundler and test runner? | Vite in library mode builds one ES module with Lit inlined; Vitest with happy-dom runs the tests; npm, with a committed `package-lock.json`. One toolchain builds and tests, and npm comes with the Node already pinned | Assumption |
| D4 | What are the card's names? | Source in `card/`; built file `pierpressure-card.js`; card type `custom:pierpressure-card`; listed in Home Assistant's card picker | Assumption |
| D5 | How does `pier: <id>` find the entities? | It builds `sensor.pierpressure_<slug>_verdict`, slugging the id the way Home Assistant writes entity ids; no per-entity override | Evidence: `docs/night-dashboard.md` step 5, `pierpressure/delivery/mqtt.py` `node_id` |
| D6 | Where do verdict, score and confidence come from? | All three from the Verdict sensor: its state, and its `score` and `confidence` attributes; a null score shows as a dash | Evidence: README, "The verdict document" table |
| D7 | What does the skeleton show when something is missing? | No `pier` key is a config error; a missing Verdict entity is a notice that names the entity id; an unavailable one says PierPressure is offline. The Should story for unavailable states refines this | Assumption |
| D8 | Where does CI run the card's build and tests? | As steps in the `check` job, which `main` requires, through a mise task | Evidence: the `main` ruleset requires `check` and `image` |
| D9 | How does the card get the app's version? | The release builds the card with the release version stamped in, before it pushes the image, and attaches the file to the GitHub release; a local build says `dev` | Assumption |
| D10 | How do npm updates arrive? | One weekly pull request for npm minor and patch updates, like the other ecosystems; majors alone | Evidence: `dependency-updates` spec, "grouped by ecosystem" |
| D11 | How is the card seen working before merge? | `mise run dashboard-check` also installs the locally built card and shows it on a view; the HACS install from a release is checked by hand after the first release | Assumption |
| D12 | What does the new decision record supersede? | Only ADR 0026's "no JavaScript card of its own"; the YAML dashboard stays the no-card route | Evidence: #132 Shared decisions and Won't |
| D13 | Does the card get a linter or formatter? | Not in the skeleton: strict TypeScript type checking only | Assumption |
| D14 | Does the change need a glossary term? | No: "card" is Home Assistant's word, used in its usual meaning | Assumption |

## Changes from the story

- Added: an npm group in `.github/renovate.json5`, and npm in the
  `dependency-updates` spec's ecosystems. The packet names the file but not the
  grouping, and without it each npm package would arrive on its own.
- Added: `mise run dashboard-check` loads the built card (D11), so the card is
  seen in a real Home Assistant before the pull request merges.

Confirmed by user: yes
