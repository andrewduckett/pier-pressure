# night-card Specification

## Purpose
The night-card capability is PierPressure's own Home Assistant dashboard card. It covers how the card is installed, configured for one pier, what it reads and shows, and how it behaves when its entity is missing or not ready. The card only displays published entities; it never computes a verdict or fetches data.

## Requirements

### Requirement: The repository is a HACS Dashboard repository
The repository root SHALL hold a `hacs.json` file whose `filename` is `pierpressure-card.js`. HACS reads it when a user adds this repository as a custom Dashboard repository. The add-on repository file, `repository.yaml`, SHALL stay at the root beside it.

#### Scenario: HACS finds the card's file
- **WHEN** `hacs.json` is read from the repository root
- **THEN** it parses as JSON with a `name` and with `filename` equal to `pierpressure-card.js`
- **AND** `repository.yaml` is still present at the root

### Requirement: The card is one self-contained file
The card's build SHALL produce exactly one JavaScript file, `pierpressure-card.js`, that a browser can load as a module with no other file. Every library the card uses SHALL be inside that file.

#### Scenario: The built file imports nothing
- **WHEN** the card is built
- **THEN** the build output holds `pierpressure-card.js` and no other JavaScript file
- **AND** the file contains no `import` of another module

### Requirement: The card registers as a custom card
Loading the file SHALL define the card type `custom:pierpressure-card`. It SHALL also add one entry for the card to Home Assistant's list of custom cards, so the card appears in the dashboard's card picker. Loading the file a second time SHALL neither throw nor add a second entry.

#### Scenario: The card is in the picker
- **WHEN** the file is loaded in a page
- **THEN** the element `pierpressure-card` is defined
- **AND** `window.customCards` holds an entry whose `type` is `pierpressure-card` and whose `name` is `PierPressure`

#### Scenario: The file loads twice
- **WHEN** the file is loaded a second time in the same page
- **THEN** no error is thrown
- **AND** `window.customCards` still holds exactly one entry whose `type` is `pierpressure-card`

### Requirement: The card reports its version
Loading the file SHALL write one line to the browser console that names the card and its version. A card built by a release SHALL carry that release's version. A card built any other way SHALL carry the version `dev`.

#### Scenario: A release build
- **WHEN** release `2026.11.0` builds the card and a browser loads the file
- **THEN** the browser console shows a line with `PIERPRESSURE-CARD` and `2026.11.0`

#### Scenario: A local build
- **WHEN** a developer builds the card outside a release and a browser loads the file
- **THEN** the browser console shows a line with `PIERPRESSURE-CARD` and `dev`

### Requirement: The card needs a pier
The card's configuration SHALL hold a `pier` key with at least one letter or digit in it. Given any other configuration, the card SHALL throw an error that says `pier` is required. Home Assistant shows that error in place of the card.

#### Scenario: No pier given
- **WHEN** the card is configured as `type: custom:pierpressure-card` with no `pier` key
- **THEN** the card throws an error whose message says `pier` is required

#### Scenario: An empty pier
- **WHEN** the card is configured with `pier: ""`
- **THEN** the card throws an error whose message says `pier` is required

#### Scenario: A pier of punctuation only
- **WHEN** the card is configured with `pier: "---"`
- **THEN** the card throws an error whose message says `pier` is required

### Requirement: The card finds the pier's Verdict sensor
From the `pier` key, the card SHALL read the entity `sensor.pierpressure_<slug>_verdict`. The card SHALL make `<slug>` from the pier id in four steps:

1. Write it in lower case.
2. Remove accents: split each accented letter into its base letter and its accent marks, and drop the marks.
3. Replace each run of characters outside `a` to `z` and `0` to `9` with one `_`.
4. Drop any `_` at either end.

#### Scenario: A plain pier id
- **WHEN** the card is configured with `pier: backyard`
- **THEN** it reads `sensor.pierpressure_backyard_verdict`

#### Scenario: A pier id with capitals and punctuation
- **WHEN** the card is configured with `pier: Back-Yard`
- **THEN** it reads `sensor.pierpressure_back_yard_verdict`

#### Scenario: A pier id with an accent
- **WHEN** the card is configured with `pier: Côte Nord`
- **THEN** it reads `sensor.pierpressure_cote_nord_verdict`

### Requirement: The card waits for Home Assistant's state
Until Home Assistant has given the card its state, the card SHALL render its frame with no verdict, score, confidence or message, and SHALL NOT throw.

#### Scenario: Configured before the state arrives
- **WHEN** the card is configured with `pier: backyard` and Home Assistant has not yet given it any state
- **THEN** the card renders without an error
- **AND** it shows no verdict and no message that the verdict is missing

### Requirement: The card shows the verdict
The card SHALL show the Verdict sensor's state, `GO`, `MAYBE` or `NO-GO`, as tonight's verdict. While the state is `unknown`, the card SHALL show a dash, `—`, as the verdict.

#### Scenario: A GO night
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `GO`
- **THEN** the card configured with `pier: backyard` shows the verdict `GO`

#### Scenario: Before the first verdict
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unknown` and no attributes
- **THEN** the card shows `—` as the verdict, the score and the confidence
- **AND** it does not show the word `unknown`

### Requirement: The card shows the score
The card SHALL show the Verdict sensor's `score` attribute. When the score is null or the attribute is missing, the card SHALL show a dash, `—`, instead of a number.

#### Scenario: A scored night
- **WHEN** the Verdict sensor's `score` attribute is `72`
- **THEN** the card shows the score `72`

#### Scenario: A score of zero
- **WHEN** the Verdict sensor's state is `MAYBE` and its `score` attribute is `0`
- **THEN** the card shows the score `0`

#### Scenario: A gated NO-GO
- **WHEN** the Verdict sensor's state is `NO-GO` and its `score` attribute is null
- **THEN** the card shows `—` as the score and shows no `0`

### Requirement: The card shows the confidence
The card SHALL show the Verdict sensor's `confidence` attribute as its band and its value. The card SHALL show a dash, `—`, for each part that is missing or null, including when the whole attribute is.

#### Scenario: A confident forecast
- **WHEN** the Verdict sensor's `confidence` attribute is `{band: HIGH, value: 82}`
- **THEN** the card shows the confidence band `HIGH` and the value `82`

#### Scenario: A confidence of zero
- **WHEN** the Verdict sensor's `confidence` attribute is `{band: LOW, value: 0}`
- **THEN** the card shows the confidence band `LOW` and the value `0`

#### Scenario: No confidence attribute
- **WHEN** the Verdict sensor has no `confidence` attribute
- **THEN** the card shows `—` for the confidence band and value
- **AND** the card still shows the verdict

#### Scenario: A null confidence
- **WHEN** the Verdict sensor's `confidence` attribute is null
- **THEN** the card shows `—` for the confidence band and value

### Requirement: A missing Verdict sensor is named
When Home Assistant has no entity with the Verdict sensor's id, the card SHALL show a message that names that entity id and says no PierPressure verdict was found. It SHALL show no verdict, score or confidence.

#### Scenario: A mistyped pier
- **WHEN** the card is configured with `pier: frontyard` and Home Assistant has no `sensor.pierpressure_frontyard_verdict`
- **THEN** the card shows a message that names `sensor.pierpressure_frontyard_verdict`
- **AND** it shows no verdict, score or confidence

### Requirement: An unavailable Verdict sensor says PierPressure is offline
When the Verdict sensor's state is `unavailable`, the card SHALL show a message that says PierPressure is offline. It SHALL show no verdict, score or confidence.

#### Scenario: PierPressure has stopped
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable`
- **THEN** the card shows a message that says PierPressure is offline
- **AND** it shows no verdict, score or confidence

### Requirement: Every pull request builds and tests the card
On every pull request, the `check` job that `main` requires SHALL type-check, test and build the card with the Node version pinned in `mise.toml`. A type error, a failing card test or a failed build SHALL fail the `check` job.

#### Scenario: A failing card test
- **WHEN** a pull request changes the card so that one of its tests fails
- **THEN** the `check` job on that pull request fails

### Requirement: The docs say how to install the card
The project SHALL publish `docs/night-card.md`, and the README SHALL link to it. The page SHALL describe two ways to install the card:

- Add this repository to HACS as a custom repository of the category Dashboard. This works from the first release that carries `pierpressure-card.js`, and the page SHALL say so.
- Copy `pierpressure-card.js` to `/config/www`, then add `/local/pierpressure-card.js` as a dashboard resource of the type JavaScript module.

#### Scenario: The page covers both routes
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the HACS custom repository route with the category Dashboard, and the `/config/www` route
- **AND** it names the resource URL `/local/pierpressure-card.js` and the type JavaScript module

#### Scenario: The README links the page
- **WHEN** `README.md` is read
- **THEN** it holds a link to `docs/night-card.md`

### Requirement: The docs show how to configure the card
`docs/night-card.md` SHALL show the card's configuration as YAML with `type: custom:pierpressure-card` and a `pier` key. It SHALL also say how to find the pier's Verdict entity id in Home Assistant, for a pier id that the card's slug rule cannot match.

#### Scenario: The page holds a card configuration
- **WHEN** the YAML block in `docs/night-card.md` is parsed
- **THEN** it is a card with `type: custom:pierpressure-card` and a `pier` key

#### Scenario: The page says where to find the entity id
- **WHEN** `docs/night-card.md` is read
- **THEN** it names `sensor.pierpressure_<pier>_verdict` and says where Home Assistant lists entity ids
