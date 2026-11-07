## Purpose

The night-card capability is PierPressure's own Home Assistant dashboard card. It covers how the card is installed from this repository, how it is configured for one pier, what it reads and shows, and how it behaves when its entity is missing or unavailable. The card only displays published entities; it never computes a verdict or fetches data.

## ADDED Requirements

### Requirement: The repository is a HACS Dashboard repository
The repository root SHALL hold a `hacs.json` file whose `filename` is `pierpressure-card.js`, so that HACS can install the card when a user adds this repository as a custom Dashboard repository. The add-on repository file, `repository.yaml`, SHALL stay at the root beside it.

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
Loading the file SHALL define the card type `custom:pierpressure-card` and SHALL add an entry for it to Home Assistant's list of custom cards, so it appears in the dashboard's card picker.

#### Scenario: The card is in the picker
- **WHEN** the file is loaded in a page
- **THEN** the element `pierpressure-card` is defined
- **AND** `window.customCards` holds an entry whose `type` is `pierpressure-card` and whose `name` is `PierPressure`

### Requirement: The card reports its version
Loading the file SHALL write one line to the browser console that names the card and its version. A card built by a release SHALL carry that release's version. A card built any other way SHALL carry the version `dev`.

#### Scenario: A release build
- **WHEN** release `2026.11.0` builds the card and a browser loads the file
- **THEN** the browser console shows a line with `PIERPRESSURE-CARD` and `2026.11.0`

#### Scenario: A local build
- **WHEN** a developer builds the card outside a release and a browser loads the file
- **THEN** the browser console shows a line with `PIERPRESSURE-CARD` and `dev`

### Requirement: The card needs a pier
The card's configuration SHALL require a `pier` key holding a non-empty pier id. A configuration without one SHALL be refused with an error that says `pier` is required, which Home Assistant shows in place of the card.

#### Scenario: No pier given
- **WHEN** the card is configured as `type: custom:pierpressure-card` with no `pier` key
- **THEN** the configuration is refused with an error whose message says `pier` is required

#### Scenario: An empty pier
- **WHEN** the card is configured with `pier: ""`
- **THEN** the configuration is refused with an error whose message says `pier` is required

### Requirement: The card finds the pier's Verdict sensor
From the `pier` key, the card SHALL read the entity `sensor.pierpressure_<pier>_verdict`, where `<pier>` is the pier id written the way Home Assistant writes it in an entity id: in lower case, with each run of characters other than letters and digits as one `_`, and with no `_` at either end.

#### Scenario: A plain pier id
- **WHEN** the card is configured with `pier: backyard`
- **THEN** it reads `sensor.pierpressure_backyard_verdict`

#### Scenario: A pier id with capitals and punctuation
- **WHEN** the card is configured with `pier: Back-Yard`
- **THEN** it reads `sensor.pierpressure_back_yard_verdict`

### Requirement: The card shows the verdict
The card SHALL show the Verdict sensor's state, `GO`, `MAYBE` or `NO-GO`, as tonight's verdict.

#### Scenario: A GO night
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `GO`
- **THEN** the card configured with `pier: backyard` shows the verdict `GO`

### Requirement: The card shows the score
The card SHALL show the Verdict sensor's `score` attribute. When the score is null or the attribute is missing, the card SHALL show a dash, `—`, instead of a number.

#### Scenario: A scored night
- **WHEN** the Verdict sensor's `score` attribute is `72`
- **THEN** the card shows the score `72`

#### Scenario: A gated NO-GO
- **WHEN** the Verdict sensor's state is `NO-GO` and its `score` attribute is null
- **THEN** the card shows `—` as the score and shows no `0`

### Requirement: The card shows the confidence
The card SHALL show the Verdict sensor's `confidence` attribute as its band and its value. When the attribute or either of its keys is missing or null, the card SHALL show a dash, `—`, in place of each missing part.

#### Scenario: A confident forecast
- **WHEN** the Verdict sensor's `confidence` attribute is `{band: HIGH, value: 82}`
- **THEN** the card shows the confidence band `HIGH` and the value `82`

#### Scenario: No confidence attribute
- **WHEN** the Verdict sensor has no `confidence` attribute
- **THEN** the card shows `—` for the confidence band and value
- **AND** the card still shows the verdict

### Requirement: A missing Verdict sensor is named
When Home Assistant has no entity with the Verdict sensor's id, the card SHALL show a message that says no PierPressure verdict was found and names that entity id, instead of the verdict, score and confidence.

#### Scenario: A mistyped pier
- **WHEN** the card is configured with `pier: frontyard` and Home Assistant has no `sensor.pierpressure_frontyard_verdict`
- **THEN** the card shows a message that names `sensor.pierpressure_frontyard_verdict`
- **AND** it shows no verdict, score or confidence

### Requirement: An unavailable Verdict sensor says PierPressure is offline
When the Verdict sensor's state is `unavailable`, the card SHALL show a message that says PierPressure is offline, instead of the verdict, score and confidence.

#### Scenario: PierPressure has stopped
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable`
- **THEN** the card shows a message that says PierPressure is offline
- **AND** it shows no verdict, score or confidence

### Requirement: Every pull request builds and tests the card
The `check` job that `main` requires SHALL type-check, test and build the card on every pull request, with the Node version pinned in `mise.toml`. A type error, a failing card test or a failed build SHALL fail the `check` job.

#### Scenario: A failing card test
- **WHEN** a pull request changes the card so that one of its tests fails
- **THEN** the `check` job on that pull request fails

### Requirement: The docs say how to install and add the card
The project SHALL publish `docs/night-card.md`, linked from the README. It SHALL describe two ways to install the card: adding this repository to HACS as a custom Dashboard repository, and copying `pierpressure-card.js` to `/config/www` and adding it as a dashboard resource. It SHALL show the card's configuration as YAML with `type: custom:pierpressure-card` and a `pier` key.

#### Scenario: The page covers both routes
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the HACS custom repository route with the category Dashboard, and the `/config/www` route
- **AND** it holds a YAML block that parses to a card with `type: custom:pierpressure-card` and a `pier` key

#### Scenario: The README links the page
- **WHEN** `README.md` is read
- **THEN** it holds a link to `docs/night-card.md`
