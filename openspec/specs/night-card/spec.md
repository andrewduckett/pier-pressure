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

### Requirement: The card draws the four cloud rows
Below the verdict, score and confidence, the card SHALL draw a night strip with four rows. From top to bottom they SHALL be Cloud cover, Cloud low, Cloud mid and Cloud high, each labelled with that name. Each row SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard` and the Verdict sensor has the state `GO`
- **THEN** the strip shows the rows Cloud cover, Cloud low, Cloud mid and Cloud high, in that order
- **AND** they read `sensor.pierpressure_back_yard_cloud_cover`, `sensor.pierpressure_back_yard_cloud_low`, `sensor.pierpressure_back_yard_cloud_mid` and `sensor.pierpressure_back_yard_cloud_high`

### Requirement: The strip shows only with the verdict
The card SHALL draw the strip only when it shows the verdict, score and confidence. When the Verdict sensor is missing or unavailable, or Home Assistant has not yet given the card its state, the card SHALL draw no strip.

#### Scenario: PierPressure is offline
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable`
- **THEN** the card shows that PierPressure is offline and draws no strip

#### Scenario: A mistyped pier
- **WHEN** Home Assistant has no `sensor.pierpressure_frontyard_verdict` and the card is configured with `pier: frontyard`
- **THEN** the card names the missing entity and draws no strip

### Requirement: The strip spans the judged night
The strip's time axis SHALL run from 4 hours before the Verdict sensor's `dark_window.start` to 5 hours after its `dark_window.end`. The card SHALL fall back to an axis from 6 hours before the browser's current time to 18 hours after it in each of these cases:

- `dark_window`, its `start` or its `end` is missing, null or not a readable time;
- `end` is not after `start`;
- `end` is more than 48 hours after `start`.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}` and the browser's clock reads 2026-06-21T12:00:00Z
- **THEN** the strip's axis runs from 2026-06-21T06:00:00Z to 2026-06-22T06:00:00Z

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor has the state `unknown`, no attributes, and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the card still draws the strip, with its axis from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

#### Scenario: A window that ends before it starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-11-01T03:25:00Z, end: 2026-10-31T20:30:00Z}` and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the strip's axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

### Requirement: A value fills its hour
Each point in a cloud sensor's `forecast` SHALL fill the hour that starts at its `datetime`, as one cell in that sensor's row. The card SHALL draw a cell for every hour that overlaps the axis, and SHALL draw no cell for an hour wholly outside the axis. The card SHALL cut a cell off at an axis end, and that cell SHALL reach the axis end with no gap.

#### Scenario: Hours at the axis ends
- **WHEN** the axis runs from 16:30 UTC to 08:25 UTC the next day, and the Cloud cover forecast has points at 15:00, 16:00, 17:00, 08:00 and 09:00 UTC with values
- **THEN** the Cloud cover row has cells for 16:00, 17:00 and 08:00 UTC, and none for 15:00 or 09:00 UTC
- **AND** the 16:00 cell starts at the axis start, and the 08:00 cell ends at the axis end

### Requirement: More cloud is darker
The card SHALL shade each cell in one of seven blues, the YAML night strip's shades. From lightest to darkest they are `#cde2fb`, `#9ec5f4`, `#6da7ec`, `#3987e5`, `#256abf`, `#184f95` and `#0d366b`. A value `v` in percent SHALL take shade step `min(6, floor(v / 15))`, where step 0 is the lightest.

#### Scenario: Clear and overcast
- **WHEN** the Cloud cover forecast holds 0 at one hour, 44 at another and 100 at a third
- **THEN** the cells are shaded `#cde2fb`, `#6da7ec` and `#0d366b`

### Requirement: A null hour is blank
The card SHALL draw no cell for an hour whose `forecast` value is null or not a number, or for an hour the forecast has no point for. That hour SHALL be blank in its row, distinct from every shade a value can take.

#### Scenario: Cloud low missing for an hour
- **WHEN** the Cloud low forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Cloud low row has no cell for 22:00 UTC

#### Scenario: Cloud mid at zero
- **WHEN** the Cloud mid forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": 0}` inside the axis
- **THEN** the Cloud mid row has a 22:00 UTC cell shaded `#cde2fb`

### Requirement: A missing cloud sensor leaves an empty row
The card SHALL draw a cloud sensor's row with its label and no cells when that sensor is missing from Home Assistant or unavailable. It SHALL do the same when the sensor has no `forecast` attribute, or its `forecast` is not a list. The card SHALL skip a point in `forecast` without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Cloud high is unavailable
- **WHEN** `sensor.pierpressure_backyard_cloud_high` has the state `unavailable` and no attributes, and the other three cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Cloud high row with its label and no cells
- **AND** the other three rows show their cells

#### Scenario: An unavailable sensor that kept its forecast
- **WHEN** `sensor.pierpressure_backyard_cloud_high` has the state `unavailable` and a `forecast` attribute with values inside the axis
- **THEN** the strip shows the Cloud high row with its label and no cells

#### Scenario: No cloud sensors at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has none of the four cloud sensors
- **THEN** the card renders without an error and shows the four labelled rows with no cells

### Requirement: Hovering over a cell shows its value
Hovering over a cell SHALL show the row's name, the start of the cell's hour, and the value with `%`, as `<row>, the hour from <HH:MM>: <value>%`. The card SHALL show the value as the forecast holds it.

#### Scenario: A cloudy hour
- **WHEN** Home Assistant's time zone is `UTC` and the Cloud cover forecast holds 40 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Cloud cover, the hour from 21:00: 40%`

### Requirement: The strip shows times in Home Assistant's time zone
The strip SHALL show every time in Home Assistant's configured time zone, whatever time zone the browser or the user profile uses. It SHALL write each time on a 24-hour clock as `HH:MM`, in the digits `0` to `9`, whatever the browser's language.

#### Scenario: Hover in Tokyo
- **WHEN** Home Assistant's time zone is `Asia/Tokyo` and the Cloud cover forecast holds 40 at 2026-10-31T12:00:00Z
- **THEN** hovering over that cell shows `Cloud cover, the hour from 21:00: 40%`

#### Scenario: A browser in Arabic
- **WHEN** the browser's language is `ar-EG`, Home Assistant's time zone is `UTC`, and the Cloud cover forecast holds 40 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Cloud cover, the hour from 21:00: 40%`

### Requirement: The axis carries time labels
The axis SHALL carry a time label at each whole hour strictly between its start and its end, in Home Assistant's time zone, whose hour is a multiple of 3. When the axis spans more than 24 hours, the card SHALL label only the hours that are a multiple of 6. When a clock change makes two such instants show the same time, the card SHALL label only the first.

#### Scenario: Axis labels in UTC
- **WHEN** Home Assistant's time zone is `UTC` and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the axis labels read `18:00`, `21:00`, `00:00`, `03:00` and `06:00`, in that order

#### Scenario: Axis labels in a half-hour time zone
- **WHEN** Home Assistant's time zone is `Asia/Kolkata` and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the axis labels read `00:00`, `03:00`, `06:00`, `09:00` and `12:00`, in that order, the first at 2026-10-31T18:30:00Z

#### Scenario: Polar night
- **WHEN** Home Assistant's time zone is `UTC` and the axis runs from 2026-12-20T07:00:00Z to 2026-12-21T16:00:00Z
- **THEN** the axis labels read `12:00`, `18:00`, `00:00`, `06:00` and `12:00`, in that order

#### Scenario: Clocks go back
- **WHEN** Home Assistant's time zone is `Europe/Athens` and the axis runs from 2026-10-24T18:00:00Z to 2026-10-25T09:00:00Z
- **THEN** the axis shows exactly one label that reads `03:00`, at 2026-10-25T00:00:00Z

### Requirement: The docs describe the cloud rows
`docs/night-card.md` SHALL describe the strip's cloud rows:

- the four rows and the sensors they read;
- the axis span, and its fallback on a night with no astronomical darkness;
- the shades from clear to overcast;
- blank hours;
- what hovering over a cell shows;
- that times are in Home Assistant's time zone.

#### Scenario: The page covers the strip
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the rows Cloud cover, Cloud low, Cloud mid and Cloud high, and the sensor `sensor.pierpressure_<pier>_cloud_cover`
- **AND** it says the strip runs from 4 hours before dusk to 5 hours after dawn, and from 6 hours before now to 18 hours after on a night with no astronomical darkness
- **AND** it names the words clear, overcast, blank, hover and time zone
