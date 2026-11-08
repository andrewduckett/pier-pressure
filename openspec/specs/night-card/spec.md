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
`docs/night-card.md` SHALL say how to add the card from the dashboard's card picker and pick the pier in the visual editor's **Pier** list. It SHALL also show the card's configuration as YAML with `type: custom:pierpressure-card` and a `pier` key, as the other route. It SHALL also say how to find the pier's Verdict entity id in Home Assistant, for a pier id that the card's slug rule cannot match.

#### Scenario: The page describes the visual editor
- **WHEN** `docs/night-card.md` is read
- **THEN** it says to pick the card from the card picker and the pier from the **Pier** list

#### Scenario: The page holds a card configuration
- **WHEN** the YAML block in `docs/night-card.md` is parsed
- **THEN** it is a card with `type: custom:pierpressure-card` and a `pier` key

#### Scenario: The page says where to find the entity id
- **WHEN** `docs/night-card.md` is read
- **THEN** it names `sensor.pierpressure_<pier>_verdict` and says where Home Assistant lists entity ids

### Requirement: The card draws the four cloud rows
Below the verdict, score and confidence, the card SHALL draw a night strip. Under the strip's Moon altitude row, the card SHALL draw the four cloud rows and, after Cloud cover, the Cloud range row, unless the Cloud range row is left out because no two forecasts give cloud. From top to bottom they SHALL be Cloud cover, Cloud range, Cloud low, Cloud mid and Cloud high, each labelled with that name. Each cloud row SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, and the Cloud cover min and max sensors hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** the strip shows the rows Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid and Cloud high, in that order, at its top
- **AND** the four cloud rows read `sensor.pierpressure_back_yard_cloud_cover`, `sensor.pierpressure_back_yard_cloud_low`, `sensor.pierpressure_back_yard_cloud_mid` and `sensor.pierpressure_back_yard_cloud_high`

### Requirement: The strip shows only with the verdict
The card SHALL draw the strip only when it shows the verdict, score and confidence. When the Verdict sensor is missing or unavailable, or Home Assistant has not yet given the card its state, the card SHALL draw no strip.

#### Scenario: PierPressure is offline
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable`
- **THEN** the card shows that PierPressure is offline and draws no strip

#### Scenario: A mistyped pier
- **WHEN** Home Assistant has no `sensor.pierpressure_frontyard_verdict` and the card is configured with `pier: frontyard`
- **THEN** the card names the missing entity and draws no strip

### Requirement: The strip spans the judged night
The strip SHALL open on the opening axis. The opening axis SHALL start at the later of two times: 4 hours before the Verdict sensor's `dark_window.start`, and 4 hours before the browser's clock. This holds unless the opening axis falls back to the browser's clock. The opening axis SHALL be as long as the time from 4 hours before `dark_window.start` to 5 hours after `dark_window.end`, so before dusk it ends 5 hours after `dark_window.end`. As the card redraws, the opening axis SHALL follow the browser's clock. Until the user pans the strip, and after the user selects "Back to tonight", the strip's time axis SHALL be the opening axis.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

#### Scenario: At dusk
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T20:30:00Z
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

#### Scenario: During the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T23:00:00Z
- **THEN** the strip's axis runs from 2026-10-31T19:00:00Z to 2026-11-01T10:55:00Z

#### Scenario: Late in the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-11-01T03:00:00Z
- **THEN** the strip's axis runs from 2026-10-31T23:00:00Z to 2026-11-01T14:55:00Z

#### Scenario: A verdict left over after dawn
- **WHEN** the Verdict sensor's `dark_window` is still `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the strip's axis runs from 2026-11-01T08:00:00Z to 2026-11-01T23:55:00Z

#### Scenario: A minute passes during the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the user has not panned the strip, and the clock moves on by 60 seconds with no new state from Home Assistant
- **THEN** the strip's axis runs from 2026-10-31T19:01:00Z to 2026-11-01T10:56:00Z

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
The card SHALL shade each cell in a cloud row in one of seven blues, the YAML night strip's shades. From lightest to darkest they are `#cde2fb`, `#9ec5f4`, `#6da7ec`, `#3987e5`, `#256abf`, `#184f95` and `#0d366b`. A value `v` in percent SHALL take shade step `min(6, floor(v / 15))`, where step 0 is the lightest.

#### Scenario: Clear and overcast
- **WHEN** the Cloud cover forecast holds 0 at one hour, 44 at another and 100 at a third
- **THEN** the cells are shaded `#cde2fb`, `#6da7ec` and `#0d366b`

### Requirement: A null hour is blank
The card SHALL draw no cell for an hour whose `forecast` value is null or not a number, or for an hour the forecast has no point for. That hour SHALL be blank in its row, distinct from every shade or arrow a value can take.

#### Scenario: Cloud low missing for an hour
- **WHEN** the Cloud low forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Cloud low row has no cell for 22:00 UTC

#### Scenario: Cloud mid at zero
- **WHEN** the Cloud mid forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": 0}` inside the axis
- **THEN** the Cloud mid row has a 22:00 UTC cell shaded `#cde2fb`

#### Scenario: Seeing missing for an hour
- **WHEN** the Seeing forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Seeing row has no cell for 22:00 UTC

#### Scenario: Temperature at zero
- **WHEN** the Temperature forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": 0}` inside the axis
- **THEN** the Temperature row has a 22:00 UTC cell

#### Scenario: Wind direction missing for an hour
- **WHEN** the Wind direction forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Wind direction row has no cell and no arrow for 22:00 UTC

### Requirement: A missing cloud sensor leaves an empty row
When a cloud sensor is missing from Home Assistant or unavailable, the card SHALL draw its row with its label and no cells. The row SHALL show the message that says why. The card SHALL do the same when the sensor has no `forecast` attribute, or its `forecast` is not a list. The card SHALL skip a point in `forecast` without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Cloud high is unavailable
- **WHEN** `sensor.pierpressure_backyard_cloud_high` has the state `unavailable` and no attributes, and the other three cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Cloud high row with its label, no cells and the message `Unavailable`
- **AND** the other three cloud rows show their cells

#### Scenario: An unavailable sensor that kept its forecast
- **WHEN** `sensor.pierpressure_backyard_cloud_high` has the state `unavailable` and a `forecast` attribute with values inside the axis
- **THEN** the strip shows the Cloud high row with its label, no cells and the message `Unavailable`

#### Scenario: No cloud sensors at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has none of the four cloud sensors
- **THEN** the card renders without an error and shows the four labelled cloud rows with no cells, each with the message `Not found`

### Requirement: Hovering over a cell shows its value
Hovering over a cell in a cloud row SHALL show the row's name, the start of the cell's hour, and the value with `%`, as `<row>, the hour from <HH:MM>: <value>%`. The card SHALL show the value as the forecast holds it.

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
- the axis span, that once the night has started the axis opens 4 hours before now and keeps its length, and its fallback on a night with no astronomical darkness;
- the shades from clear to overcast;
- blank hours;
- what hovering over a cell shows;
- that times are in Home Assistant's time zone.

#### Scenario: The page covers the strip
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the rows Cloud cover, Cloud low, Cloud mid and Cloud high, and the sensor `sensor.pierpressure_<pier>_cloud_cover`
- **AND** it says the strip runs from 4 hours before dusk to 5 hours after dawn, and from 6 hours before now to 18 hours after on a night with no astronomical darkness
- **AND** it says that once the night has started, the strip opens 4 hours before now and keeps its length
- **AND** it names the words clear, overcast, blank, hover and time zone

### Requirement: The card draws a Sun altitude row
The strip's top row SHALL be labelled Sun altitude. It SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_sun_altitude`, named from the same slug as the Verdict sensor. Each point SHALL fill the hour that starts at its `datetime`, as one cell. The card SHALL draw a cell for every hour that overlaps the axis, and no cell for an hour wholly outside it. The card SHALL cut a cell off at an axis end, and that cell SHALL reach the axis end with no gap.

#### Scenario: The row and its sensor
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, and `sensor.pierpressure_back_yard_sun_altitude` has a forecast inside the axis
- **THEN** the Sun altitude row is the strip's top row and shows cells from that forecast

#### Scenario: Hours at the axis ends
- **WHEN** the axis runs from 16:30 UTC to 08:25 UTC the next day, and the Sun altitude forecast has values at 15:00, 16:00, 17:00, 08:00 and 09:00 UTC
- **THEN** the Sun altitude row has cells for 16:00, 17:00 and 08:00 UTC, and none for 15:00 or 09:00 UTC
- **AND** the 16:00 cell starts at the axis start, and the 08:00 cell ends at the axis end

### Requirement: The Sun altitude row steps through twilight
The card SHALL shade each Sun altitude cell by the sun's altitude `v` in degrees, in the strip's blues:

- above 0°: `#cde2fb`, the sun is up;
- above −6° and at most 0°: `#9ec5f4`, civil twilight;
- above −12° and at most −6°: `#6da7ec`, nautical twilight;
- above −18° and at most −12°: `#3987e5`, astronomical twilight;
- −18° or lower: `#0d366b`, astronomical night.

#### Scenario: From day to night
- **WHEN** the Sun altitude forecast holds 10, 0, −6, −12, −18 and −30 at six hours inside the axis
- **THEN** the cells are shaded `#cde2fb`, `#9ec5f4`, `#6da7ec`, `#3987e5`, `#0d366b` and `#0d366b`

### Requirement: A missing sun altitude leaves a blank hour
The card SHALL draw no Sun altitude cell for an hour whose value is null or not a number, or for an hour the forecast has no point for. When the sun altitude sensor is missing or unavailable, or has no `forecast` list, the card SHALL draw the Sun altitude row with its label and no cells. The row SHALL show the message that says why. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: A null hour
- **WHEN** the Sun altitude forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Sun altitude row has no cell for 22:00 UTC

#### Scenario: The sensor is unavailable
- **WHEN** `sensor.pierpressure_backyard_sun_altitude` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Sun altitude row with its label, no cells and the message `Unavailable`
- **AND** the cloud rows show their cells

### Requirement: Hovering over a Sun altitude cell shows its altitude
Hovering over a Sun altitude cell SHALL show `Sun altitude, the hour from <HH:MM>: <value>°`, with the value as the forecast holds it.

#### Scenario: An hour in twilight
- **WHEN** Home Assistant's time zone is `UTC` and the Sun altitude forecast holds −14.235 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Sun altitude, the hour from 21:00: -14.235°`

### Requirement: The card draws a Moon up lane
Under the strip's last row, Rain chance, the strip SHALL have a lane labelled Moon up. The lane SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_moon_altitude`, named from the same slug as the Verdict sensor. The lane SHALL keep its label on a night when the moon never rises.

#### Scenario: The lane and its sensor
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, and `sensor.pierpressure_back_yard_moon_altitude` holds values above 0 inside the axis
- **THEN** the strip's first lane, straight under Rain chance, is labelled Moon up and shows bars from that forecast

#### Scenario: The moon stays down
- **WHEN** every value in the moon altitude forecast is 0 or below
- **THEN** the strip shows the Moon up lane with its label and no bars

### Requirement: A Moon up bar spans each run of hours the moon is up
The card SHALL draw one grey `#898781` bar for each run of consecutive hours whose moon altitude is above 0. A bar SHALL run from the start of the run's first hour to the end of its last hour. A value of 0 or below, a null value, a value that is not a number, or an hour with no point SHALL end a run. The card SHALL cut a bar off at an axis end, and draw no bar for a run wholly outside the axis.

#### Scenario: Three runs
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **AND** the moon altitude forecast for 2026-10-31 holds 4 at 16:00, 6 at 17:00, −1 at 18:00, 2 at 19:00, 8 at 20:00, null at 21:00, 12 at 22:00 and 0 at 23:00 UTC
- **THEN** the Moon up lane has three bars: from 16:30 to 18:00, from 19:00 to 21:00, and from 22:00 to 23:00 UTC

#### Scenario: A missing hour
- **WHEN** the moon altitude forecast holds 5 at 2026-11-01T01:00:00Z and 5 at 2026-11-01T03:00:00Z, and has no point for 02:00
- **THEN** the Moon up lane has two bars: from 01:00 to 02:00, and from 03:00 to 04:00 UTC

### Requirement: A missing moon altitude leaves the Moon up lane empty
When the moon altitude sensor is missing from Home Assistant or unavailable, or has no `forecast` list, the card SHALL draw the Moon up lane with its label, no bars and the Moon altitude row's message. The card SHALL NOT throw, and SHALL draw the rows as usual.

#### Scenario: The moon sensor is unavailable
- **WHEN** `sensor.pierpressure_backyard_moon_altitude` has the state `unavailable` and a `forecast` attribute with values above 0 inside the axis
- **THEN** the strip shows the Moon up lane with its label, no bars and the message `Unavailable`

#### Scenario: No moon sensor at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no `sensor.pierpressure_backyard_moon_altitude`
- **THEN** the card renders without an error and shows the Moon up lane with no bars and the message `Not found`

### Requirement: Hovering over a Moon up bar shows its hours
Hovering over a Moon up bar SHALL show `Moon up from <HH:MM> to <HH:MM>`: the start of the run's first hour and the end of its last hour. The card SHALL show the run's own hours, even where the axis cuts the bar off. This form applies when the forecast shows both the rise and the set, and the run is shorter than 24 hours.

#### Scenario: A bar cut off at the axis start
- **WHEN** Home Assistant's time zone is `UTC` and the axis starts at 2026-10-31T16:30:00Z
- **AND** the moon altitude forecast holds −2 at 15:00, 4 at 16:00, 6 at 17:00 and −1 at 18:00 UTC
- **THEN** hovering over the bar shows `Moon up from 16:00 to 18:00`

### Requirement: A Moon up bar names only a rise or set the forecast shows
The forecast shows a run's rise when it holds a value of 0 or below for the hour just before the run. It shows the set when it holds one for the hour just after. When the forecast shows only the rise, the hover SHALL read `Moon up from <HH:MM>`. When it shows only the set, the hover SHALL read `Moon up until <HH:MM>`. When it shows neither, or the run lasts 24 hours or more, the hover SHALL read `Moon up`.

#### Scenario: The forecast starts with the moon up
- **WHEN** Home Assistant's time zone is `UTC`, and the moon altitude forecast starts with 4 at 2026-11-01T00:00:00Z and 6 at 01:00, then holds −1 at 02:00
- **THEN** hovering over the bar shows `Moon up until 02:00`

#### Scenario: The forecast ends with the moon up
- **WHEN** Home Assistant's time zone is `UTC`, and the moon altitude forecast holds −1 at 2026-11-01T06:00:00Z, then ends with 3 at 07:00 and 5 at 08:00
- **THEN** hovering over the bar shows `Moon up from 07:00`

#### Scenario: The moon never sets
- **WHEN** the moon altitude forecast holds −1 at 2026-12-20T06:00:00Z, values above 0 for each of the 30 hours from 07:00, and −1 at 2026-12-21T13:00:00Z
- **THEN** hovering over the bar shows `Moon up`

### Requirement: Dusk and dawn lines mark the dark window
When the opening axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`, each only while its time lies on the axis. Each line SHALL cross every row from Sun altitude to Rain chance, the Moon up lane and every target lane. When the opening axis falls back to the browser's current time, the card SHALL draw no dusk or dawn line.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line

#### Scenario: The lines reach the last target lane
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, and Target 1 to Target 3 each have a target tonight
- **THEN** the dusk and dawn lines run from the Sun altitude row down to the bottom of the lane labelled `Target 3`

#### Scenario: Dusk panned off the axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, and the user has panned the axis to run from 2026-10-31T22:30:00Z to 2026-11-01T14:25:00Z
- **THEN** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

#### Scenario: Dusk off the opening axis late in the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-11-01T01:00:00Z, and the user has not panned the strip
- **THEN** the strip's axis runs from 2026-10-31T21:00:00Z to 2026-11-01T12:55:00Z
- **AND** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

### Requirement: A now line marks the browser's time
The card SHALL draw a solid red `#e66767` line labelled `now` at the browser's current time, crossing every row from Sun altitude to Rain chance, the Moon up lane and every target lane. It SHALL draw the line only while that time is on the axis, from its start to its end.

#### Scenario: During the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T22:00:00Z
- **THEN** the strip has a line labelled `now` at 2026-10-31T22:00:00Z

#### Scenario: Before the axis starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has no now line

#### Scenario: The now line reaches the last target lane
- **WHEN** the browser's clock reads 2026-10-31T22:00:00Z, inside the axis, and Target 1 has a target tonight
- **THEN** the now line runs from the Sun altitude row down to the bottom of the lane labelled `Target 1`

### Requirement: The now line moves on its own
While the card is on the page, it SHALL redraw the strip every minute from the browser's clock, without waiting for Home Assistant to send new state. When the card is removed from the page, it SHALL stop redrawing.

#### Scenario: A minute passes
- **WHEN** the now line is at 2026-10-31T22:00:00Z and the browser's clock moves on by 60 seconds, with no new state from Home Assistant
- **THEN** the now line is at 2026-10-31T22:01:00Z

#### Scenario: The card is removed
- **WHEN** the card is removed from the page
- **THEN** the card leaves no timer running

### Requirement: Hovering over a line shows its time
Hovering over the dusk, dawn or now line SHALL show its name and time, in Home Assistant's time zone, as `Dusk, <HH:MM>`, `Dawn, <HH:MM>` or `Now, <HH:MM>`.

#### Scenario: Dusk in UTC
- **WHEN** Home Assistant's time zone is `UTC` and the Verdict sensor's `dark_window` starts at 2026-10-31T20:30:00Z
- **THEN** hovering over the dusk line shows `Dusk, 20:30`

### Requirement: The docs describe the night axis
`docs/night-card.md` SHALL describe the Sun altitude row, the Moon up lane and the three lines:

- the Sun altitude row, its sensor, and its steps through civil, nautical and astronomical twilight;
- that each altitude is for the start of its hour;
- the Moon up lane and its sensor, and that a bar's hover names only a rise or set inside the forecast;
- the dusk and dawn lines, and that they are missing on a night with no astronomical darkness;
- the now line, and that it moves every minute.

#### Scenario: The page covers the night axis
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the Sun altitude row, the sensors `sensor.pierpressure_<pier>_sun_altitude` and `sensor.pierpressure_<pier>_moon_altitude`, and the Moon up lane
- **AND** it names the words civil, nautical, astronomical, start of the hour, dusk, dawn, now and every minute
- **AND** it no longer says that a later release adds dusk, dawn and the moon

### Requirement: The card draws every timeline row
The strip SHALL have sixteen rows, each labelled with its name, or fifteen when the Cloud range row is left out. Fifteen rows each read one timeline sensor, from Cloud cover to Precipitation probability. The Cloud range row reads the Cloud cover min and Cloud cover max sensors. From top to bottom they SHALL be Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance.

#### Scenario: The rows in order
- **WHEN** the card is configured with `pier: backyard`, the Verdict sensor has the state `GO`, and the Cloud cover min and max sensors hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance

#### Scenario: The rows without Cloud range
- **WHEN** the Verdict sensor has the state `GO`, both Cloud range sensors are available with only null values, and Target 1 has a window from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z
- **THEN** the strip has fifteen rows, in the same order with Cloud range left out
- **AND** the lines overlay and the strip's grid end at the Target 1 lane

### Requirement: Each row reads its timeline sensor
Each row but Cloud range SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_<key>`, named from the same slug as the Verdict sensor. The key SHALL be the row's name in lower case with `_` for each space, except that Rain chance reads `precipitation_probability`.

#### Scenario: Dew point
- **WHEN** the card is configured with `pier: Back-Yard` and `sensor.pierpressure_back_yard_dew_point` has a forecast inside the axis
- **THEN** the Dew point row shows cells from that forecast

#### Scenario: Rain chance reads Precipitation probability
- **WHEN** the card is configured with `pier: Back-Yard` and `sensor.pierpressure_back_yard_precipitation_probability` has a forecast inside the axis
- **THEN** the Rain chance row shows cells from that forecast

### Requirement: A Moon altitude or weather value fills its hour
In the Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed and Wind direction rows, each point in the sensor's `forecast` SHALL fill the hour that starts at its `datetime`, as one cell. The card SHALL draw a cell for every hour that overlaps the axis, and no cell for an hour wholly outside it. The card SHALL cut a cell off at an axis end, and that cell SHALL reach the axis end with no gap.

#### Scenario: Hours at the axis ends
- **WHEN** the axis runs from 16:30 UTC to 08:25 UTC the next day, and the Wind gust forecast has values at 15:00, 16:00, 17:00, 08:00 and 09:00 UTC
- **THEN** the Wind gust row has cells for 16:00, 17:00 and 08:00 UTC, and none for 15:00 or 09:00 UTC
- **AND** the 16:00 cell starts at the axis start, and the 08:00 cell ends at the axis end

### Requirement: A Rain chance value fills the hour before its time
Each point in the precipitation probability sensor's `forecast` SHALL fill the hour that ends at its `datetime`, as one cell in the Rain chance row, because the value is the chance for that hour. The card SHALL draw a cell for every such hour that overlaps the axis, and no cell for an hour wholly outside it. The card SHALL cut a cell off at an axis end, and that cell SHALL reach the axis end with no gap.

#### Scenario: The hour before
- **WHEN** the axis runs from 16:30 UTC to 08:25 UTC the next day, and the precipitation probability forecast holds 40 at 2026-10-31T22:00:00Z
- **THEN** the Rain chance row has a cell from 21:00 to 22:00 UTC, and none from 22:00 to 23:00 UTC

#### Scenario: Hours at the axis ends
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the precipitation probability forecast has values at 16:00, 17:00, 09:00 and 10:00 UTC
- **THEN** the Rain chance row has cells for the hours from 16:00 and from 08:00 UTC, and none for the hours from 15:00 or 09:00 UTC
- **AND** the cell for the hour from 16:00 starts at the axis start, and the cell for the hour from 08:00 ends at the axis end

### Requirement: A missing sensor leaves its row empty
This requirement covers the Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance rows. When a row's sensor is missing from Home Assistant or unavailable, the card SHALL draw that row with its label and no cells. The row SHALL show the message that says why. The card SHALL do the same when the sensor has no `forecast` list. The card SHALL skip a point without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Humidity is unavailable
- **WHEN** `sensor.pierpressure_backyard_humidity` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Humidity row with its label, no cells and the message `Unavailable`
- **AND** the cloud rows show their cells

#### Scenario: Only the sun and cloud sensors
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no timeline sensor but Sun altitude and the four cloud sensors
- **THEN** the card renders without an error
- **AND** every row but Sun altitude and the four cloud rows shows its label, no cells and the message `Not found`

### Requirement: The Moon altitude row darkens as the moon climbs
The card SHALL shade each Moon altitude cell in the strip's seven blues, `#cde2fb`, `#9ec5f4`, `#6da7ec`, `#3987e5`, `#256abf`, `#184f95` and `#0d366b`, step 0 the lightest. An altitude `v` of 0° or below SHALL take step 0. An altitude above 0° SHALL take step `min(6, 1 + floor(v / 6))`.

#### Scenario: From set to high
- **WHEN** the Moon altitude forecast holds −10, 0, 3, 6, 12, 18, 24, 30 and 60 at nine hours inside the axis
- **THEN** the cells are shaded `#cde2fb`, `#cde2fb`, `#9ec5f4`, `#6da7ec`, `#3987e5`, `#256abf`, `#184f95`, `#0d366b` and `#0d366b`

### Requirement: More wind is darker
The card SHALL shade each Wind gust and Wind speed cell in the strip's seven blues. A speed `v` in km/h SHALL take step `min(6, max(0, floor(v / 7)))`, so 42 km/h or more is the darkest.

#### Scenario: Calm to gale
- **WHEN** the Wind gust forecast holds 0, 6.9, 7, 41 and 42 at five hours inside the axis
- **THEN** the cells are shaded `#cde2fb`, `#cde2fb`, `#9ec5f4`, `#184f95` and `#0d366b`

#### Scenario: Wind speed on the same scale
- **WHEN** the Wind speed forecast holds 21 at an hour inside the axis
- **THEN** the cell is shaded `#3987e5`

### Requirement: Worse seeing and transparency are darker
The card SHALL shade each Seeing and Transparency cell in the strip's seven blues. A quality `q` from 0 to 1, where 1 is best, SHALL take step `min(6, max(0, round((1 − q) × 7)))`, where a half rounds up. So darker means worse.

#### Scenario: Excellent to poor
- **WHEN** the Seeing forecast holds 1, 0.8, 0.5 and 0 at four hours inside the axis
- **THEN** the cells are shaded `#cde2fb`, `#9ec5f4`, `#256abf` and `#0d366b`

#### Scenario: A quality above 1
- **WHEN** the Transparency forecast holds 1.2 at an hour inside the axis
- **THEN** the cell is shaded `#cde2fb`

### Requirement: Warmer is darker in Temperature and Dew point
The card SHALL shade each Temperature and Dew point cell in the strip's seven blues, on one shared scale. A temperature `v` in °C SHALL take step `min(6, max(0, floor((v + 10) / 5)))`, so below −5 °C is the lightest and 20 °C or more the darkest.

#### Scenario: A cold night to a warm one
- **WHEN** the Temperature forecast holds −8, −5, 0, 7, 12, 17 and 25 at seven hours inside the axis
- **THEN** the cells are shaded `#cde2fb`, `#9ec5f4`, `#6da7ec`, `#3987e5`, `#256abf`, `#184f95` and `#0d366b`

#### Scenario: Dew point on the same scale
- **WHEN** the Temperature forecast holds 7 and the Dew point forecast holds 6 at the same hour inside the axis
- **THEN** both cells are shaded `#3987e5`

### Requirement: More humidity and rain chance is darker
The card SHALL shade each Humidity and Rain chance cell in the strip's seven blues. A value `v` in percent SHALL take step `min(6, max(0, floor(v / 15)))`, as cloud does.

#### Scenario: Dry to saturated
- **WHEN** the Humidity forecast holds 0, 44 and 100 at three hours inside the axis
- **THEN** the cells are shaded `#cde2fb`, `#6da7ec` and `#0d366b`

#### Scenario: Rain chance on the same scale
- **WHEN** the precipitation probability forecast holds 90 inside the axis
- **THEN** its Rain chance cell is shaded `#0d366b`

### Requirement: A Wind direction arrow points downwind
Each Wind direction cell SHALL hold an arrow and no shade. The value is the direction the wind blows from, in degrees clockwise from north. The arrow SHALL point the way the wind blows to: rotated `(v + 180) mod 360` degrees clockwise from pointing up, at least 0 and below 360.

#### Scenario: A south-westerly
- **WHEN** the Wind direction forecast holds 225 at an hour inside the axis
- **THEN** that cell's arrow is rotated 45 degrees clockwise from pointing up, toward the north-east

#### Scenario: A northerly
- **WHEN** the Wind direction forecast holds 0 at an hour inside the axis
- **THEN** that cell's arrow is rotated 180 degrees, pointing down

### Requirement: Hovering over a cell shows its unit
Hovering over a cell in the Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed or Rain chance row SHALL show `<row>, the hour from <HH:MM>: <value><unit>`. The hour SHALL be the start of the hour the cell fills, and the value SHALL be as the forecast holds it. The unit SHALL be `°` for Moon altitude, ` km/h` for Wind gust and Wind speed, ` °C` for Temperature and Dew point, and `%` for Humidity and Rain chance. Seeing and Transparency SHALL show no unit.

#### Scenario: A gusty hour
- **WHEN** Home Assistant's time zone is `UTC` and the Wind gust forecast holds 12.5 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Wind gust, the hour from 21:00: 12.5 km/h`

#### Scenario: A cold hour
- **WHEN** Home Assistant's time zone is `UTC` and the Temperature forecast holds 4.2 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Temperature, the hour from 21:00: 4.2 °C`

#### Scenario: Seeing has no unit
- **WHEN** Home Assistant's time zone is `UTC` and the Seeing forecast holds 0.62 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Seeing, the hour from 21:00: 0.62`

#### Scenario: Rain chance names the hour it fills
- **WHEN** Home Assistant's time zone is `UTC` and the precipitation probability forecast holds 40 at 2026-10-31T22:00:00Z
- **THEN** hovering over that cell shows `Rain chance, the hour from 21:00: 40%`

### Requirement: Hovering over a Wind direction cell names the compass point
Hovering over a Wind direction cell SHALL show `Wind direction, the hour from <HH:MM>: <value>° from <point>`, with the value as the forecast holds it. The point SHALL be the nearest of N, NE, E, SE, S, SW, W and NW to the value, taken modulo 360; a value halfway between two points SHALL take the next point clockwise.

#### Scenario: A south-westerly
- **WHEN** Home Assistant's time zone is `UTC` and the Wind direction forecast holds 225 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Wind direction, the hour from 21:00: 225° from SW`

#### Scenario: Halfway between north and north-east
- **WHEN** Home Assistant's time zone is `UTC` and the Wind direction forecast holds 22.5 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Wind direction, the hour from 21:00: 22.5° from NE`

#### Scenario: Just short of north
- **WHEN** Home Assistant's time zone is `UTC` and the Wind direction forecast holds 350 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Wind direction, the hour from 21:00: 350° from N`

### Requirement: The docs describe every row
`docs/night-card.md` SHALL describe each of the sixteen rows:

- its name and the sensor or sensors it reads;
- for each shaded row, what its lightest and darkest shades mean, and that darker means worse for Seeing and Transparency;
- that Temperature and Dew point share one scale;
- that a Rain chance cell fills the hour before its time;
- that a Wind direction arrow points the way the wind blows to;
- what hovering over a cell shows, with its unit.

#### Scenario: The page covers every row
- **WHEN** `docs/night-card.md` is read
- **THEN** it names each of the sixteen rows and the sensors `sensor.pierpressure_<pier>_wind_gust` and `sensor.pierpressure_<pier>_precipitation_probability`
- **AND** it names the words darker means worse, same scale, hour before and blows to
- **AND** it no longer says that a later release adds the other conditions

### Requirement: The card draws a lane per ranked target
Under the Moon up lane, the strip SHALL have one lane for each rank from Target 1 to Target 10 that has a target tonight, in rank order. The lane for rank `<n>` SHALL be labelled `Target <n>` and SHALL read `sensor.pierpressure_<slug>_target_<n>`, named from the same slug as the Verdict sensor. A rank with no lane SHALL leave no gap: the next lane follows straight on.

#### Scenario: Two targets tonight
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, `sensor.pierpressure_back_yard_target_1` and `sensor.pierpressure_back_yard_target_2` each have a target tonight, and Target 3 to Target 10 are unavailable
- **THEN** under the Moon up lane the strip has two target lanes, labelled `Target 1` then `Target 2`, and no other target lane

#### Scenario: A gap in the ranks
- **WHEN** Target 1 and Target 3 have a target tonight and Target 2 is unavailable
- **THEN** the lane labelled `Target 3` comes straight after the lane labelled `Target 1`

### Requirement: A rank with no target tonight leaves no lane
A rank SHALL have a target tonight only when all of these hold:

- its sensor is in Home Assistant;
- its state is not `unavailable`, `unknown` or empty;
- its `window` attribute holds a `start` and an `end` that are readable times, with `end` after `start`.

Any other rank SHALL leave no lane. The card SHALL NOT throw, and SHALL draw the rows and the Moon up lane as usual.

#### Scenario: Every rank is empty
- **WHEN** Target 1 to Target 10 all have the state `unavailable`
- **THEN** the strip has no target lane

#### Scenario: No Target sensors at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has none of `sensor.pierpressure_backyard_target_1` to `sensor.pierpressure_backyard_target_10`
- **THEN** the card renders without an error and the strip has no target lane

#### Scenario: An unavailable rank with stale attributes
- **WHEN** `sensor.pierpressure_backyard_target_1` has the state `unavailable` and a `window` of `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** the strip has no lane labelled `Target 1`

#### Scenario: A rank whose name has not arrived
- **WHEN** Target 1 has the state `unknown` and Target 2 has an empty state, and each has a `window` of `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** the strip has no lane labelled `Target 1` or `Target 2`

#### Scenario: A broken window
- **WHEN** Target 1 has the state `Andromeda Galaxy` and a `window` of `{start: 2026-11-01T02:00:00Z, end: 2026-10-31T21:00:00Z}`, Target 2 has a `window` with no `end`, and Target 3 has a `window` whose `start` is `soon`
- **THEN** the strip has no lane labelled `Target 1`, `Target 2` or `Target 3`

### Requirement: A target bar spans its window
Each target lane SHALL hold one violet `#6250d6` bar from the target's `window.start` to its `window.end`. The card SHALL cut the bar off at an axis end. A window wholly outside the axis SHALL keep its lane, with no bar. A window that ends at the axis start, or starts at the axis end, counts as wholly outside.

#### Scenario: A window inside the night
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z and Target 1's `window` is `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** the lane labelled `Target 1` has one bar from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z

#### Scenario: A window past the axis end
- **WHEN** the axis ends at 2026-11-01T08:25:00Z and Target 1's `window` is `{start: 2026-11-01T06:00:00Z, end: 2026-11-01T10:00:00Z}`
- **THEN** the lane's bar runs from 2026-11-01T06:00:00Z to 2026-11-01T08:25:00Z

#### Scenario: A window off the axis
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z and Target 1's `window` is `{start: 2026-11-02T21:00:00Z, end: 2026-11-03T02:00:00Z}`
- **THEN** the strip has a lane labelled `Target 1` with no bar

### Requirement: A target bar holds the target's name
Each target bar SHALL show the Target sensor's state, the target's name, as its text.

#### Scenario: A named target
- **WHEN** `sensor.pierpressure_backyard_target_1` has the state `Andromeda Galaxy` and a window on the axis
- **THEN** the lane labelled `Target 1` has a bar whose text is `Andromeda Galaxy`

### Requirement: Hovering over a target bar shows its window
Hovering over a target bar SHALL show `<name> from <HH:MM> to <HH:MM>`. The name SHALL be the Target sensor's state. The two times SHALL be the window's own start and end in Home Assistant's time zone, even where the axis cuts the bar off. When the window lasts 24 hours or more, or its start and end read the same `HH:MM`, the hover SHALL show `<name>` alone.

#### Scenario: A window in UTC
- **WHEN** Home Assistant's time zone is `UTC`, Target 1 has the state `Andromeda Galaxy` and its `window` is `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** hovering over its bar shows `Andromeda Galaxy from 21:00 to 02:00`

#### Scenario: A window cut off at the axis end
- **WHEN** Home Assistant's time zone is `UTC`, the axis ends at 2026-11-01T08:25:00Z, Target 1 has the state `Orion Nebula` and its `window` is `{start: 2026-11-01T06:00:00Z, end: 2026-11-01T10:00:00Z}`
- **THEN** hovering over its bar shows `Orion Nebula from 06:00 to 10:00`

#### Scenario: A target up all through a polar night
- **WHEN** Home Assistant's time zone is `UTC`, Target 1 has the state `IC2184` and its `window` is `{start: 2026-12-21T10:58:02Z, end: 2026-12-22T10:58:32Z}`
- **THEN** hovering over its bar shows `IC2184`

### Requirement: The card's size grows with its target lanes
The card SHALL report a size of 10 to Home Assistant, plus 1 for every three target lanes it shows, rounding up, plus 1 for every two reasons it shows, rounding up.

#### Scenario: No targets
- **WHEN** the strip has no target lane and the card shows no reason
- **THEN** the card reports a size of 10

#### Scenario: Four targets
- **WHEN** the strip has four target lanes and the card shows no reason
- **THEN** the card reports a size of 12

#### Scenario: Ten targets
- **WHEN** the strip has ten target lanes and the card shows no reason
- **THEN** the card reports a size of 14

#### Scenario: Three reasons
- **WHEN** the strip has no target lane and the card shows three reasons
- **THEN** the card reports a size of 12

#### Scenario: Targets and reasons
- **WHEN** the strip has four target lanes and the card shows one reason
- **THEN** the card reports a size of 13

#### Scenario: Offline with reasons left over
- **WHEN** the Verdict sensor has the state `unavailable` and a `reasons` attribute that holds four strings
- **THEN** the card reports a size of 10

### Requirement: The docs describe the target lanes
`docs/night-card.md` SHALL describe the target lanes:

- that each lane reads one of `sensor.pierpressure_<pier>_target_1` to `sensor.pierpressure_<pier>_target_10`, and is labelled `Target <n>`;
- that its bar runs from the start to the end of the target's observable window and holds the target's name;
- what hovering over a bar shows;
- that a rank with no target tonight leaves no lane;
- that the dusk, dawn and now lines cross the target lanes.

#### Scenario: The page covers the target lanes
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the sensors `sensor.pierpressure_<pier>_target_1` and `sensor.pierpressure_<pier>_target_10` and the lane label `Target 1`
- **AND** it names the words observable window, no target tonight and leaves no lane

### Requirement: The docs' opening names the targets
The opening paragraph of `docs/night-card.md` SHALL say that the card shows the ranked targets' windows as well as the conditions.

#### Scenario: The opening names the targets
- **WHEN** the first paragraph of `docs/night-card.md` is read
- **THEN** it names the ranked targets

### Requirement: A row with no cell says why
When one of the strip's rows but Cloud range would draw no cell at all, the card SHALL show a message in that row's track that names the cause. The message SHALL be the first of these that applies to the row's sensor:

1. `Not found`, when Home Assistant has no entity with the sensor's id.
2. `Unavailable`, when the sensor's state is `unavailable`.
3. `No forecast`, otherwise: no `forecast` list, an empty one, or no value for any hour on the axis.

#### Scenario: Seeing is unavailable
- **WHEN** `sensor.pierpressure_backyard_seeing` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the Seeing row shows the message `Unavailable` and no cells
- **AND** the cloud rows show their cells and no message

#### Scenario: Humidity is not in Home Assistant
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no `sensor.pierpressure_backyard_humidity`
- **THEN** the Humidity row shows the message `Not found` and no cells

#### Scenario: Wind gust has an empty forecast
- **WHEN** `sensor.pierpressure_backyard_wind_gust` has the state `unknown` and a `forecast` attribute of `[]`
- **THEN** the Wind gust row shows the message `No forecast` and no cells

#### Scenario: Temperature has no forecast attribute
- **WHEN** `sensor.pierpressure_backyard_temperature` has the state `unknown` and no attributes
- **THEN** the Temperature row shows the message `No forecast`

#### Scenario: Every hour on the axis is null
- **WHEN** every point of the Cloud low forecast inside the axis has the value `null`
- **THEN** the Cloud low row shows the message `No forecast` and no cells

#### Scenario: A forecast wholly off the axis
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z and the Dew point forecast holds values only on 2026-11-02
- **THEN** the Dew point row shows the message `No forecast`

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor and all seventeen timeline sensors have the state `unknown` and no attributes
- **THEN** each of the fifteen rows but Cloud range shows the message `No forecast`
- **AND** the strip has no Cloud range row

### Requirement: A row with a cell shows no message
A row that draws at least one cell SHALL show no message. Its hours without a value SHALL stay blank.

#### Scenario: A row with one value
- **WHEN** the Cloud mid forecast inside the axis holds one value, 40 at 2026-10-31T22:00:00Z, and null for every other hour
- **THEN** the Cloud mid row has one cell and shows no message

### Requirement: Hovering over a row's message names its sensor
Hovering over the message of a row but Cloud range SHALL name the row's sensor by its entity id and say the cause:

- `<entity id> is not in Home Assistant` for `Not found`;
- `<entity id> is unavailable` for `Unavailable`;
- `<entity id> has no forecast for these hours` for `No forecast`.

#### Scenario: An unavailable sensor
- **WHEN** `sensor.pierpressure_backyard_seeing` has the state `unavailable`
- **THEN** hovering over the Seeing row's message shows `sensor.pierpressure_backyard_seeing is unavailable`

#### Scenario: A sensor that is not there
- **WHEN** the card is configured with `pier: Back-Yard` and Home Assistant has no `sensor.pierpressure_back_yard_humidity`
- **THEN** hovering over the Humidity row's message shows `sensor.pierpressure_back_yard_humidity is not in Home Assistant`

#### Scenario: A sensor with no forecast
- **WHEN** `sensor.pierpressure_backyard_wind_gust` has a `forecast` attribute of `[]`
- **THEN** hovering over the Wind gust row's message shows `sensor.pierpressure_backyard_wind_gust has no forecast for these hours`

### Requirement: The Moon up lane says why with the Moon altitude row
When the Moon altitude row shows a message, the Moon up lane SHALL show the same message, with the same hover text, and no bars. When the Moon altitude row draws at least one cell, the Moon up lane SHALL show no message, even if it has no bars.

#### Scenario: The moon sensor is not there
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no `sensor.pierpressure_backyard_moon_altitude`
- **THEN** the Moon altitude row and the Moon up lane each show the message `Not found`
- **AND** hovering over the Moon up lane's message shows `sensor.pierpressure_backyard_moon_altitude is not in Home Assistant`

#### Scenario: The moon stays down
- **WHEN** the moon altitude forecast holds at least one value inside the axis, and every value inside the axis is 0 or below
- **THEN** the Moon up lane shows no bars and no message

### Requirement: The card notes a night with no astronomical darkness
The card SHALL show the note `No astronomical darkness tonight` when the Verdict sensor's `dark_window` has a `start` of null and an `end` of null. The note SHALL sit between the confidence and the strip. The card SHALL still draw the strip on its fallback axis.

The card SHALL show no such note in any other case: a missing `dark_window`, only one null end, or an end that is not a readable time.

#### Scenario: A summer night far north
- **WHEN** the Verdict sensor has the state `NO-GO` and its `dark_window` is `{start: null, end: null}`
- **THEN** the card shows `No astronomical darkness tonight` after the confidence and before the strip
- **AND** it still draws the strip, with no dusk or dawn line

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the card shows no note about darkness

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor has the state `unknown` and no attributes
- **THEN** the card shows no note about darkness

#### Scenario: An unreadable window
- **WHEN** the Verdict sensor's `dark_window` is `{start: "soon", end: null}`
- **THEN** the card shows no note about darkness and draws the strip on its fallback axis

### Requirement: The docs describe the row messages and the darkness note
Where `docs/night-card.md` describes the strip, it SHALL describe:

- the row messages `Not found`, `Unavailable` and `No forecast`, and what each means;
- that hovering over `Not found`, `Unavailable` or `No forecast` names the sensor, except that hovering over the Cloud range row's `No forecast` says what the row needs;
- that the Moon up lane repeats the Moon altitude row's message;
- the note `No astronomical darkness tonight`.

It SHALL NOT name `Needs two forecasts`.

#### Scenario: The strip section covers the messages
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** it names `Not found`, `Unavailable`, `No forecast` and `No astronomical darkness tonight`
- **AND** it names the words hover and Moon up in the same paragraph as `No forecast`

#### Scenario: The retired message is gone
- **WHEN** `docs/night-card.md` is read
- **THEN** it does not contain `Needs two forecasts`

### Requirement: The docs say what to do when something is missing
The "If something looks wrong" section of `docs/night-card.md` SHALL say what to do when the card shows each of these:

- `PierPressure is offline`;
- `No PierPressure verdict found`;
- a row that says `Not found`, `Unavailable` or `No forecast`;
- a strip with no Cloud range row;
- `No astronomical darkness tonight`.

#### Scenario: The troubleshooting section covers the missing cases
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** it names `PierPressure is offline`, `No PierPressure verdict found`, `Not found`, `Unavailable`, `No forecast`, Cloud range and `No astronomical darkness tonight`

### Requirement: The docs name the causes of No forecast
For a row that says `No forecast`, the "If something looks wrong" section of `docs/night-card.md` SHALL name three causes. Either no weather source in the pier's `providers` gave that condition a value for these hours, or the strip is panned past the last hour that condition's weather source forecasts, or every weather source failed. It SHALL point to the pier's weather source health sensors.

#### Scenario: The causes and where to look
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** it names the word health and the `providers` setting

#### Scenario: A later night
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** its `No forecast` help names a later night, past a weather source's last hour, as a cause

### Requirement: The Cloud range row reads the cloud cover min and max sensors
The Cloud range row SHALL read the `forecast` attributes of `sensor.pierpressure_<slug>_cloud_cover_min` and `sensor.pierpressure_<slug>_cloud_cover_max`, named from the same slug as the Verdict sensor. It SHALL pair the two forecasts' points by their `datetime`.

#### Scenario: A pier id with a capital and a dash
- **WHEN** the card is configured with `pier: Back-Yard`, and `sensor.pierpressure_back_yard_cloud_cover_min` and `sensor.pierpressure_back_yard_cloud_cover_max` hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** the Cloud range row has one column, for the hour from 2026-10-31T21:00:00Z

### Requirement: A Cloud range column fills its hour
For each hour where both forecasts hold a number, the card SHALL draw one column in the Cloud range row. The column SHALL fill the hour that starts at the points' `datetime`. The card SHALL cut a column off at an axis end, as it cuts a cell. It SHALL draw no column for an hour wholly outside the axis.

#### Scenario: Hours at the axis ends
- **WHEN** the axis runs from 16:30 UTC to 08:25 UTC the next day, and both forecasts have values at 15:00, 16:00 and 09:00 UTC
- **THEN** the Cloud range row has a column for 16:00 UTC, which starts at the axis start, and none for 15:00 or 09:00 UTC

### Requirement: A Cloud range bar runs from the lowest to the highest cloud
A column's height SHALL stand for 0 to 100% cloud, with 0 at the bottom. Inside it, the card SHALL draw a range bar from the min value to the max value. The card SHALL draw a value below 0 at 0, and a value above 100 at 100.

#### Scenario: Forecasts that disagree
- **WHEN** the min forecast holds 40 and the max forecast holds 70 at 2026-10-31T21:00:00Z
- **THEN** the range bar for that hour starts 40% of the way up the column and ends 70% of the way up

#### Scenario: Values outside 0 to 100
- **WHEN** the min forecast holds -5 and the max forecast holds 120 at 2026-10-31T21:00:00Z
- **THEN** the range bar for that hour runs from the bottom of the column to its top

### Requirement: The Cloud range row has its own shades and height
The Cloud range row SHALL be twice as tall as a shaded row. Each hour column SHALL be the lightest blue, `#cde2fb`, and each range bar the blue `#256abf`. A range bar SHALL stay inside its column.

#### Scenario: The shades
- **WHEN** the min and max forecasts hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** that hour's column is shaded `#cde2fb` and its range bar `#256abf`

### Requirement: Forecasts that agree still draw a bar
When an hour's two values are equal, the card SHALL still draw its range bar, as a line at least 2 px tall at that level. At 100% the line SHALL stay inside the top of the column.

#### Scenario: Two forecasts give 40%
- **WHEN** the min and max forecasts both hold 40 at 2026-10-31T21:00:00Z
- **THEN** that hour's range bar sits 40% of the way up the column and is at least 2 px tall

#### Scenario: Two forecasts give 100%
- **WHEN** the min and max forecasts both hold 100 at 2026-10-31T21:00:00Z
- **THEN** that hour's range bar is at least 2 px tall and its top is at the top of the column

### Requirement: An hour without a readable pair has no Cloud range column
The card SHALL draw no Cloud range column for an hour where either forecast has no point, a null value or a value that is not a number. It SHALL draw none where the min value is above the max value.

#### Scenario: One forecast for the hour
- **WHEN** the min and max forecasts both hold null at 2026-10-31T22:00:00Z and numbers at 2026-10-31T21:00:00Z
- **THEN** the Cloud range row has a column for 21:00 UTC and none for 22:00 UTC

#### Scenario: A min with no max
- **WHEN** the min forecast holds 40 at 2026-10-31T21:00:00Z and the max forecast has no point at that time, and both forecasts hold numbers at 2026-10-31T23:00:00Z
- **THEN** the Cloud range row has no column for 21:00 UTC

#### Scenario: A min above the max
- **WHEN** the min forecast holds 70 and the max forecast holds 20 at 2026-10-31T21:00:00Z
- **THEN** the strip has a Cloud range row with no column for that hour

### Requirement: Hovering over a Cloud range column shows both values
Hovering over a Cloud range column SHALL show `Cloud range, the hour from <HH:MM>: <min>% to <max>%`, with the values as the forecasts hold them.

#### Scenario: Forecasts that disagree
- **WHEN** Home Assistant's time zone is `UTC` and the min and max forecasts hold 40 and 70.5 at 2026-10-31T21:00:00Z
- **THEN** hovering over that column shows `Cloud range, the hour from 21:00: 40% to 70.5%`

### Requirement: A Cloud range row with no column says why
When the Cloud range row is in the strip but would draw no column at all, the card SHALL show a message in its track. The message SHALL be the first of these that applies:

1. `Not found`, when Home Assistant has no entity with the min sensor's id, or else none with the max sensor's id.
2. `Unavailable`, when the min sensor's state is `unavailable`, or else the max sensor's.
3. `No forecast`, otherwise: the forecasts have a paired hour, but no readable pair on the hours of the axis.

A Cloud range row that draws at least one column SHALL show no message. The card SHALL NOT show the message `Needs two forecasts`.

#### Scenario: One cloud provider
- **WHEN** both sensors are in Home Assistant and available, and every point of both forecasts is null
- **THEN** the strip shows no Cloud range row, and so no Cloud range message
- **AND** the Cloud cover row shows its cells and no message

#### Scenario: Forecasts that end before the axis
- **WHEN** both sensors are in Home Assistant and available, the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the only readable pair is 40 and 70 at 2026-10-31T12:00:00Z
- **THEN** the Cloud range row shows the message `No forecast` and no columns
- **AND** the message is marked `no-forecast`, as the other rows' `No forecast` is

#### Scenario: The max sensor is not there
- **WHEN** the min sensor has values inside the axis and Home Assistant has no `sensor.pierpressure_backyard_cloud_cover_max`
- **THEN** the Cloud range row shows the message `Not found`

#### Scenario: The min sensor is unavailable
- **WHEN** `sensor.pierpressure_backyard_cloud_cover_min` has the state `unavailable` and a `forecast` attribute with values inside the axis, and `sensor.pierpressure_backyard_cloud_cover_max` is available with values at the same hours
- **THEN** the Cloud range row shows the message `Unavailable`

#### Scenario: A missing sensor comes before an unavailable one
- **WHEN** `sensor.pierpressure_backyard_cloud_cover_min` has the state `unavailable` and Home Assistant has no `sensor.pierpressure_backyard_cloud_cover_max`
- **THEN** the Cloud range row shows the message `Not found`

#### Scenario: Before the first verdict
- **WHEN** both sensors have the state `unknown` and no attributes
- **THEN** the strip shows no Cloud range row, and so no Cloud range message

### Requirement: Hovering over the Cloud range message says what it needs
Hovering over the Cloud range row's message SHALL show:

- `<entity id> is not in Home Assistant` for `Not found`, naming the sensor that is missing;
- `<entity id> is unavailable` for `Unavailable`, naming the sensor that is unavailable;
- `No hour on the strip has cloud cover from two or more forecasts` for `No forecast`.

#### Scenario: The max sensor is not there
- **WHEN** the min sensor is in Home Assistant and there is no `sensor.pierpressure_backyard_cloud_cover_max`
- **THEN** hovering over the Cloud range row's message shows `sensor.pierpressure_backyard_cloud_cover_max is not in Home Assistant`

#### Scenario: One cloud provider
- **WHEN** both sensors are available and every point of both forecasts is null
- **THEN** the strip has no Cloud range message to hover over, because it has no Cloud range row

#### Scenario: Panned past the forecasts
- **WHEN** the min and max forecasts hold 40 and 70 at 2026-10-31T12:00:00Z and null at every hour on the axis, so the Cloud range row shows `No forecast`
- **THEN** hovering over the message shows `No hour on the strip has cloud cover from two or more forecasts`

### Requirement: The docs describe the Cloud range row
Where `docs/night-card.md` describes the strip, it SHALL describe the Cloud range row:

- the two sensors it reads;
- that each range bar runs from the lowest to the highest cloud cover any forecast gives for the hour;
- that the row's height runs from 0% at the bottom to 100% at the top;
- that a tall range bar means the forecasts disagree;
- that an hour with fewer than two forecasts is blank;
- what hovering over an hour shows;
- that the strip leaves the row out when no hour of the forecast has cloud cover from two or more forecasts, as with the default providers, but keeps it to say `Not found` or `Unavailable`;
- that the row says `No forecast` when it is in the strip but no hour on the strip has two forecasts.

#### Scenario: The strip section covers the Cloud range row
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** it names Cloud range, `sensor.pierpressure_<pier>_cloud_cover_min` and `sensor.pierpressure_<pier>_cloud_cover_max`
- **AND** it names the words lowest, highest and disagree
- **AND** it says the row is left out with one cloud forecast, in the same paragraph as `No hour on the strip has cloud cover from two or more forecasts`

### Requirement: The card shows a Moon section beside the verdict
The card SHALL show a Moon section beside its Verdict, Score and Confidence lines, above the strip. The section SHALL read only the Verdict sensor's `moon` attribute, and its `illumination`, `phase`, `rise` and `set` fields.

#### Scenario: A night with a waxing gibbous moon
- **WHEN** the Verdict sensor's `moon` attribute is `{illumination: 0.78, phase: "waxing gibbous", rise: "2026-10-31T21:14:00Z", set: null}` and Home Assistant's time zone is `UTC`
- **THEN** the card shows a moon drawing, the phase `Waxing gibbous`, the illumination `78%`, the moonrise `21:14` and the moonset `—`

### Requirement: The Moon section shows only with the verdict
The card SHALL show no Moon section when it shows no verdict: before Home Assistant gives it a state, and when it shows a message in place of the verdict.

#### Scenario: Before Home Assistant gives the card its state
- **WHEN** the card is configured and Home Assistant has not yet given it a state
- **THEN** the card shows no moon drawing and no moon text

#### Scenario: PierPressure is offline
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable` and a `moon` attribute
- **THEN** the card shows no moon drawing and no moon text

#### Scenario: A mistyped pier
- **WHEN** Home Assistant has no `sensor.pierpressure_frontyard_verdict` and the card is configured with `pier: frontyard`
- **THEN** the card shows no moon drawing and no moon text

### Requirement: The card shows the moon's phase
The card SHALL show the `moon.phase` field with its first letter in capitals. The valid phases are `new`, `waxing crescent`, `first quarter`, `waxing gibbous`, `full`, `waning gibbous`, `last quarter` and `waning crescent`. When the field is missing or holds any other value, the card SHALL show a dash, `—`, as the phase.

#### Scenario: Last quarter
- **WHEN** `moon.phase` is `last quarter`
- **THEN** the card shows the phase `Last quarter`

#### Scenario: An unknown phase name
- **WHEN** `moon.phase` is `blue`
- **THEN** the card shows `—` as the phase

### Requirement: The card shows the moon's illumination as a percent
The card SHALL show the `moon.illumination` field as a whole percent, rounded to the nearest whole number. When the field is missing, or is not a number from 0 to 1, the card SHALL show a dash, `—`, as the illumination.

#### Scenario: A new moon
- **WHEN** `moon.illumination` is `0`
- **THEN** the card shows the illumination `0%`

#### Scenario: Rounding
- **WHEN** `moon.illumination` is `0.996`
- **THEN** the card shows the illumination `100%`

#### Scenario: An illumination outside 0 to 1
- **WHEN** `moon.illumination` is `1.5`
- **THEN** the card shows `—` as the illumination

### Requirement: The card shows moonrise and moonset
The card SHALL show `moon.rise` as the moonrise and `moon.set` as the moonset. It SHALL show each as a time in Home Assistant's time zone on a 24-hour clock, as the strip shows times. When a field is null, missing or not a readable time, the card SHALL show a dash, `—`, for it.

#### Scenario: Moonrise in Tokyo
- **WHEN** Home Assistant's time zone is `Asia/Tokyo` and `moon.rise` is `2026-10-31T12:14:00Z`
- **THEN** the card shows the moonrise `21:14`

#### Scenario: The moon sets after dawn
- **WHEN** `moon.set` is null
- **THEN** the card shows `—` as the moonset

### Requirement: Before the first verdict the Moon section shows dashes
When the Verdict sensor has no `moon` attribute, or the attribute is not an object, the card SHALL show a dash, `—`, for each of the four moon texts.

#### Scenario: Before the first verdict
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unknown` and no attributes
- **THEN** the card shows `—` as the phase, the illumination, the moonrise and the moonset
- **AND** it shows no moon drawing

### Requirement: The moon drawing needs a phase and an illumination
The card SHALL draw the moon only when both the phase and the illumination are valid, as the requirements on showing them say. Otherwise it SHALL show no drawing, and the texts SHALL still show.

#### Scenario: A phase with no illumination
- **WHEN** `moon.phase` is `full` and the `moon` attribute has no `illumination`
- **THEN** the card shows no moon drawing
- **AND** it shows the phase `Full` and `—` as the illumination

### Requirement: The moon drawing lights the illumination's share of the disc
For a phase other than `new` and `full`, the drawing SHALL be a disc whose lit part lies between one edge of the disc and a terminator. Across the disc's middle, from edge to edge, the lit part SHALL span the illumination's share of the disc's width. The terminator SHALL be a straight line at an illumination of 0.5, and curved otherwise. An illumination of 0 SHALL draw no lit part, and 1 the whole disc lit. The drawing SHALL show no position angle, libration or earthshine.

#### Scenario: A first quarter
- **WHEN** `moon.phase` is `first quarter` and `moon.illumination` is `0.5`
- **THEN** half the disc is lit, and the terminator is a straight line through its middle

#### Scenario: Illumination at the ends of its range
- **WHEN** `moon.phase` is `waxing crescent` and `moon.illumination` is `0`, or `moon.phase` is `waxing gibbous` and `moon.illumination` is `1`
- **THEN** the first draws the disc's outline and no lit part, and the second the whole disc lit

#### Scenario: A waxing crescent
- **WHEN** `moon.phase` is `waxing crescent` and `moon.illumination` is `0.25`
- **THEN** across the disc's middle, the lit part spans a quarter of the disc's width

#### Scenario: A waning gibbous
- **WHEN** `moon.phase` is `waning gibbous` and `moon.illumination` is `0.75`
- **THEN** across the disc's middle, the lit part spans three quarters of the disc's width

### Requirement: Waxing is lit on the right in the northern hemisphere
For `waxing crescent`, `first quarter` and `waxing gibbous`, the lit part SHALL touch the disc's right edge. For `waning gibbous`, `last quarter` and `waning crescent`, it SHALL touch the left edge. When Home Assistant's latitude is below 0, the card SHALL mirror both: waxing touches the left edge and waning the right. When Home Assistant gives no latitude, the card SHALL draw as for the northern hemisphere.

#### Scenario: First quarter in the north
- **WHEN** Home Assistant's latitude is `52.1`, `moon.phase` is `first quarter` and `moon.illumination` is `0.5`
- **THEN** the right half of the disc is lit

#### Scenario: First quarter in the south
- **WHEN** Home Assistant's latitude is `-33.9`, `moon.phase` is `first quarter` and `moon.illumination` is `0.5`
- **THEN** the left half of the disc is lit

#### Scenario: No latitude
- **WHEN** Home Assistant gives no latitude, `moon.phase` is `waning crescent` and `moon.illumination` is `0.2`
- **THEN** the lit part touches the disc's left edge

### Requirement: A new moon is unlit and a full moon fully lit
For `new`, the card SHALL draw the disc with no lit part. For `full`, it SHALL draw the whole disc lit. Both SHALL hold whatever the illumination, since the phase does not say which side a sliver is on. An unlit disc SHALL still show its outline.

#### Scenario: A new moon with a sliver
- **WHEN** `moon.phase` is `new` and `moon.illumination` is `0.03`
- **THEN** the drawing shows the disc's outline and no lit part

#### Scenario: A full moon just past full
- **WHEN** `moon.phase` is `full` and `moon.illumination` is `0.96`
- **THEN** the whole disc is lit

### Requirement: The moon drawing has a text alternative
The drawing SHALL carry the text `Moon: <phase>, <illumination>% lit`, with the phase as the document gives it and the illumination as the card shows it. Hovering over the drawing SHALL show the same text, and a screen reader SHALL read it.

#### Scenario: A waxing gibbous moon
- **WHEN** `moon.phase` is `waxing gibbous` and `moon.illumination` is `0.78`
- **THEN** the drawing's text alternative and hover text are `Moon: waxing gibbous, 78% lit`

### Requirement: The docs describe the Moon section's texts
Where `docs/night-card.md` says what the card shows, it SHALL say that the Moon section reads the Verdict sensor's `moon` attribute, and describe the phase, the illumination, the moonrise and the moonset. It SHALL say that the moonrise and moonset are only those inside the dark window, and that a dash means the moon does not rise or set then.

#### Scenario: The page covers the Moon section's texts
- **WHEN** the part of `docs/night-card.md` before its "The night strip" section is read
- **THEN** it names Moon, Phase, Illumination, Moonrise, Moonset and dark window

### Requirement: The docs say how to read the moon drawing
Where `docs/night-card.md` describes the Moon section, it SHALL say:

- the drawing's lit part is the illumination's share of the disc;
- a waxing moon is lit on the right and a waning moon on the left;
- the card mirrors both when Home Assistant's location is south of the equator;
- the card takes the hemisphere from Home Assistant's location, not the pier's, so a pier in the other hemisphere shows the moon mirrored;
- the card draws a new moon unlit and a full moon fully lit.

#### Scenario: The page says how to read the drawing
- **WHEN** the part of `docs/night-card.md` before its "The night strip" section is read
- **THEN** it names waxing, waning, right, left, south, Home Assistant, new and full

### Requirement: The card picker shows a preview
The card's entry in Home Assistant's list of custom cards SHALL ask for a preview, so the dashboard's card picker draws the card before it is added.

#### Scenario: The picker entry asks for a preview
- **WHEN** the file is loaded in a page
- **THEN** the entry in `window.customCards` whose `type` is `pierpressure-card` has `preview` equal to `true`

### Requirement: The card offers a starting configuration
When Home Assistant asks the card for a starting configuration, the card SHALL give `type: custom:pierpressure-card` with the `pier` value of the first pier the editor lists. When the editor lists no pier, the starting configuration SHALL have no `pier` key.

#### Scenario: Two piers are known
- **WHEN** Home Assistant has `sensor.pierpressure_frontyard_verdict` with the `pier` attribute `frontyard` and `sensor.pierpressure_backyard_verdict` with the `pier` attribute `backyard`, and asks for a starting configuration
- **THEN** the card gives `type: custom:pierpressure-card` and `pier: backyard`

#### Scenario: No pier is known
- **WHEN** Home Assistant has no entity whose id has the form `sensor.pierpressure_<slug>_verdict`, and asks for a starting configuration
- **THEN** the card gives `type: custom:pierpressure-card` and no `pier` key

### Requirement: The card has a visual editor
The card SHALL give Home Assistant a configuration editor when Home Assistant asks for one, so the card can be set up without YAML. The editor SHALL have one field, labelled **Pier**, that sets the card's `pier` key. The editor SHALL report each change to Home Assistant as the card's whole new configuration.

#### Scenario: Home Assistant asks for the editor
- **WHEN** Home Assistant asks the card for its configuration editor
- **THEN** it gets an element that takes the card's configuration and Home Assistant's state
- **AND** the element shows one field labelled **Pier**

### Requirement: The editor lists the known piers
The editor's **Pier** field SHALL list one pier for each entity in Home Assistant's states whose id has the form `sensor.pierpressure_<slug>_verdict`, where `<slug>` holds at least one character. Each pier SHALL be shown by the entity's `pier` attribute when it is a non-empty string, and otherwise by `<slug>`. The list SHALL be in alphabetical order of what it shows. No other entity SHALL add a pier.

#### Scenario: Two piers in alphabetical order
- **WHEN** Home Assistant has `sensor.pierpressure_frontyard_verdict` with the `pier` attribute `frontyard` and `sensor.pierpressure_back_yard_verdict` with the `pier` attribute `Back-Yard`
- **THEN** the **Pier** field lists `Back-Yard`, then `frontyard`

#### Scenario: A pier before its first verdict
- **WHEN** Home Assistant has `sensor.pierpressure_backyard_verdict` with the state `unknown` and no attributes
- **THEN** the **Pier** field lists `backyard`

#### Scenario: Other PierPressure sensors are not piers
- **WHEN** Home Assistant has `sensor.pierpressure_backyard_verdict`, `sensor.pierpressure_backyard_score` and `sensor.weather_verdict`
- **THEN** the **Pier** field lists only `backyard`

### Requirement: Picking a pier sets a value that finds its Verdict sensor
When the user picks a listed pier, the editor SHALL set `pier` to the entity's `pier` attribute if the card's slug rule turns that attribute into the entity's `<slug>`. Otherwise the editor SHALL set `pier` to `<slug>`, so the card always reads the Verdict sensor the user picked.

#### Scenario: A pier id the slug rule matches
- **WHEN** the user picks the pier listed for `sensor.pierpressure_back_yard_verdict`, whose `pier` attribute is `Back-Yard`
- **THEN** the editor reports a configuration with `pier: Back-Yard`

#### Scenario: A pier id the slug rule cannot match
- **WHEN** the user picks the pier listed for `sensor.pierpressure_dong_jing_verdict`, whose `pier` attribute is `東京`
- **THEN** the editor reports a configuration with `pier: dong_jing`

#### Scenario: A pier with no attributes yet
- **WHEN** the user picks the pier listed for `sensor.pierpressure_backyard_verdict`, which has no attributes
- **THEN** the editor reports a configuration with `pier: backyard`

### Requirement: The editor keeps the rest of the configuration
When the editor reports a new configuration, it SHALL change only the `pier` key and keep every other key and value as it was.

#### Scenario: A key the editor does not edit
- **WHEN** the card is configured with `type: custom:pierpressure-card`, `pier: backyard` and `title: Garden`, and the user picks `frontyard`
- **THEN** the editor reports `type: custom:pierpressure-card`, `pier: frontyard` and `title: Garden`

### Requirement: The editor keeps a pier it does not list
When the configured `pier` is not among the listed piers, the editor SHALL show it as the **Pier** field's current value. The editor SHALL NOT report a new configuration until the user changes the field.

#### Scenario: A pier Home Assistant has lost
- **WHEN** the card is configured with `pier: oldpier` and Home Assistant has no `sensor.pierpressure_oldpier_verdict`
- **THEN** the **Pier** field shows `oldpier` as its current value
- **AND** the editor reports no new configuration

### Requirement: The editor accepts a typed pier
The **Pier** field SHALL accept a pier the user types, as well as one picked from the list, and SHALL set `pier` to the typed text unchanged.

#### Scenario: A pier that has not published yet
- **WHEN** the user types `garden` in the **Pier** field
- **THEN** the editor reports a configuration with `pier: garden`

### Requirement: The editor says when it finds no pier
When the editor lists no pier, it SHALL say "No PierPressure piers found" and SHALL still accept a typed pier.

#### Scenario: PierPressure has never published
- **WHEN** Home Assistant has no entity whose id has the form `sensor.pierpressure_<slug>_verdict`
- **THEN** the editor shows "No PierPressure piers found"
- **AND** the **Pier** field still accepts a typed pier

### Requirement: The opening axis falls back to the browser's clock
The card SHALL fall back to an opening axis from 6 hours before the browser's current time to 18 hours after it in each of these cases:

- `dark_window`, its `start` or its `end` is missing, null or not a readable time;
- `end` is not after `start`;
- `end` is more than 48 hours after `start`.

#### Scenario: A window over 48 hours long
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2006-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the strip's axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

### Requirement: The strip pans as far as the forecast reaches
The user SHALL be able to pan the strip's axis earlier or later, inside the reach. The axis SHALL always be as long as the opening axis. The reach SHALL run from the start of the earliest timeline hour to the end of the latest, and SHALL always cover the opening axis.

#### Scenario: Panning past the last forecast hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only row sensor with a forecast, and its points run hourly from 2026-10-31T12:00:00Z to 2026-11-03T11:00:00Z
- **AND** the user pans later by more than three days
- **THEN** the strip's axis runs from 2026-11-02T20:05:00Z to 2026-11-03T12:00:00Z

#### Scenario: Panning past the first forecast hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only row sensor with a forecast, and its points run hourly from 2026-10-31T12:00:00Z to 2026-11-03T11:00:00Z
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis runs from 2026-10-31T12:00:00Z to 2026-11-01T03:55:00Z

#### Scenario: A forecast shorter than the opening axis
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and every row sensor's points lie between 2026-10-31T18:00:00Z and 2026-11-01T06:00:00Z
- **AND** the user pans later by an hour
- **THEN** the strip's axis still runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

### Requirement: The reach counts every row's forecast
A timeline hour SHALL be the hour that starts at the `datetime` of a point in the `forecast` of a row's sensor, the Cloud range row's two sensors included. Every such point with a readable `datetime` SHALL count, whatever its value. A Rain chance point SHALL count only when it holds a number, and then for the hour before its time, the hour its cell fills. The reach SHALL leave out the forecast of a sensor that is `unavailable`.

#### Scenario: A Rain chance cell before the first hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the earliest point of any row sensor is a Rain chance point `{"datetime": "2026-10-31T12:00:00Z", "value": 20}`
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis starts at 2026-10-31T11:00:00Z

#### Scenario: A null Rain chance at the first hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, every row sensor's earliest point is at 2026-10-31T12:00:00Z, and the Rain chance point there is `{"datetime": "2026-10-31T12:00:00Z", "value": null}`
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis starts at 2026-10-31T12:00:00Z

#### Scenario: A null value still counts
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only row sensor with a forecast, and its last point is `{"datetime": "2026-11-02T11:00:00Z", "value": null}`
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-02T12:00:00Z

#### Scenario: An unavailable sensor's stale forecast
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover's points end at 2026-11-01T11:00:00Z, and the Seeing sensor is `unavailable` with points to 2026-11-03T11:00:00Z
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-01T12:00:00Z

### Requirement: Dragging the strip pans it
A mouse drag or a touch swipe across the strip's rows and lanes SHALL pan the axis as if the user moved the strip itself. Dragging to the left SHALL move the axis later, and dragging to the right SHALL move it earlier. The axis SHALL move by the same share of its length as the sideways distance is of the width the hours are drawn across. Dragging SHALL NOT select the strip's text.

#### Scenario: A drag to the left
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user drags the strip to the left by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A touch swipe to the right
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user swipes the strip to the right by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T00:00:00Z to 2026-11-02T00:00:00Z

### Requirement: A small or cancelled gesture pans nothing
A drag SHALL start to pan only once the pointer has moved more than 8 px sideways, and further sideways than up or down. When the browser cancels a gesture, such as to scroll the page, the axis SHALL return to where it was when the gesture began. The strip SHALL leave touch swipes up and down to the browser, so the page scrolls.

#### Scenario: A tap that slips
- **WHEN** the axis is the opening axis, and the user presses on the strip, moves 5 px to the left and releases
- **THEN** the strip's axis is unchanged, and the card shows no `Back to tonight` button

#### Scenario: Scrolling past the card on a phone
- **WHEN** the axis is the opening axis, and a finger on the strip moves 12 px to the left and 4 px up, and the browser then cancels the gesture to scroll the page
- **THEN** the strip's axis is the opening axis, and the card shows no `Back to tonight` button

#### Scenario: A mostly vertical drag
- **WHEN** the axis is the opening axis, and the user presses on the strip and moves 10 px to the left and 30 px down
- **THEN** the strip's axis is unchanged

### Requirement: One pointer drags the strip at a time
While one pointer drags the strip, the card SHALL ignore every other pointer, such as a second finger.

#### Scenario: A second finger
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs further either way, one finger drags the strip to the left by a quarter of the width its hours are drawn across, and a second finger then touches the strip and moves
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

### Requirement: A sideways wheel or trackpad swipe pans the strip
A sideways wheel movement over the strip, such as a two-finger swipe on a trackpad, SHALL pan the axis. A movement to the right SHALL move the axis later by the same share of its length as the distance is of the width the hours are drawn across. A wheel movement that is mostly up or down SHALL scroll the page and SHALL NOT pan the axis.

#### Scenario: A trackpad swipe
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and a wheel movement over the strip moves right by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A mouse wheel scrolls the page
- **WHEN** a wheel movement over the strip moves only down
- **THEN** the strip's axis is unchanged

### Requirement: The arrow keys pan the strip
The strip SHALL take keyboard focus from the Tab key. Its accessible name SHALL say that the Left and Right arrow keys move through the forecast. While the strip has focus, the Right arrow key SHALL pan the axis one hour later, and the Left arrow key one hour earlier, inside the reach.

#### Scenario: One hour later
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs further either way, and the user presses the Right arrow key with the strip focused
- **THEN** the strip's axis runs from 2026-11-01T07:00:00Z to 2026-11-02T07:00:00Z

#### Scenario: At the end of the reach
- **WHEN** the axis ends where the reach ends, and the user presses the Right arrow key with the strip focused
- **THEN** the strip's axis is unchanged

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw every row's cells, the Cloud range row's columns, the Moon up bars, the target bars, the lines with their labels, and the time labels for the new axis. It SHALL draw them by the same rules as for the opening axis. The row and lane labels SHALL stay where they are. Dusk and dawn lines and target bars come only from the dark window and target windows Home Assistant holds, so a night other than the judged one has none.

#### Scenario: The next night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, the Cloud cover forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later
- **THEN** the strip's axis runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **AND** the Cloud cover row has a cell for each hour that overlaps that axis
- **AND** the strip has no dusk line and no dawn line, and the lane labelled `Target 1` has no bar
- **AND** the row labels read from `Sun altitude` to `Rain chance`, as before

### Requirement: The strip stays where the user panned it
After the user pans, the axis SHALL keep its start when Home Assistant sends new state and when the card redraws each minute. When the reach no longer holds the axis, the card SHALL move the axis only as far as it needs to stay inside the reach. A pan that the reach stops entirely SHALL count as no pan. A pan that brings the axis back to the opening axis SHALL count as selecting `Back to tonight`. A later pan is one that leaves the axis starting after the opening axis. When the opening axis moves on to or past the start of a later pan, the strip SHALL follow the opening axis again. An earlier pan SHALL keep its start as the opening axis moves away from it.

#### Scenario: New state after a pan
- **WHEN** the user has panned the axis to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z, and Home Assistant sends new state with the same `dark_window` and forecasts
- **THEN** the strip's axis still runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z

#### Scenario: A minute passes after a pan
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the user has panned the axis to run from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z, and the browser's clock moves on by 60 seconds
- **THEN** the strip's axis still runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A minute passes after a pan during the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the reach runs further either way, the user presses the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-10-31T18:00:00Z to 2026-11-01T09:55:00Z, and the card shows a `Back to tonight` button

#### Scenario: The opening axis catches up with a pan
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the reach runs further either way, the user presses the Right arrow key with the strip focused, and the clock then moves on to 2026-11-01T00:01:00Z
- **THEN** the strip's axis runs from 2026-10-31T20:01:00Z to 2026-11-01T11:56:00Z, and the card shows no `Back to tonight` button

#### Scenario: The forecast moves on past the axis
- **WHEN** the user has panned the axis to start at 2026-10-31T12:00:00Z, and new state from Home Assistant makes the reach start at 2026-10-31T14:00:00Z
- **THEN** the strip's axis starts at 2026-10-31T14:00:00Z and is as long as the opening axis

#### Scenario: A new night of another length
- **WHEN** the user has panned the axis to start at 2026-11-01T16:30:00Z, and a new `dark_window` makes the opening axis 17 hours long, starting before 2026-11-01T16:30:00Z
- **THEN** the strip's axis starts at 2026-11-01T16:30:00Z and is 17 hours long

#### Scenario: Panning back by hand
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the browser's clock reads 2026-11-01T12:00:00Z, the reach runs further either way, the user presses the Right arrow key and then the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-11-01T06:01:00Z to 2026-11-02T06:01:00Z, and the card shows no `Back to tonight` button

#### Scenario: A new pier
- **WHEN** the user has panned the axis 24 hours later, and the card's configuration changes to another pier
- **THEN** the strip's axis is the new pier's opening axis, and the card shows no `Back to tonight` button

#### Scenario: A pan against the reach's start
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the browser's clock reads 2026-11-01T12:00:00Z, the reach starts at 2026-11-01T06:00:00Z, the user presses the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-11-01T06:01:00Z to 2026-11-02T06:01:00Z, and the card shows no `Back to tonight` button

### Requirement: A Back to tonight button returns the strip to the opening axis
While the strip's axis is not the opening axis, the card SHALL show a button labelled `Back to tonight` above the strip. Selecting it SHALL return the axis to the opening axis at that time, and move keyboard focus to the strip. While the axis is the opening axis, the card SHALL hide the button but keep its place, so showing it moves nothing on the card.

#### Scenario: On opening
- **WHEN** the card first draws the strip
- **THEN** the card shows no `Back to tonight` button

#### Scenario: After a pan
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the user has panned the axis 24 hours later
- **THEN** the card shows a `Back to tonight` button

#### Scenario: Going back
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, the user has panned the axis 24 hours later, and the user selects `Back to tonight`
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **AND** the card shows no `Back to tonight` button, and the strip has keyboard focus

#### Scenario: Going back after the night has moved on
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the user pans the axis 24 hours later, the clock moves on to 2026-11-01T00:00:00Z, and the user selects `Back to tonight`
- **THEN** the strip's axis runs from 2026-10-31T20:00:00Z to 2026-11-01T11:55:00Z

#### Scenario: Pressing the button does not pan
- **WHEN** the user has panned the axis 24 hours later, and presses `Back to tonight` with the mouse, moving 12 px to the left before releasing, so the browser clicks the button
- **THEN** the strip's axis is the opening axis

### Requirement: The docs describe panning the strip
`docs/night-card.md` SHALL describe panning the strip:

- that the strip opens on the judged night;
- the inputs that pan it, and that an up or down swipe scrolls the page;
- that it stops at the first and last forecast hour;
- that other nights have no dusk line, dawn line or target bar;
- that a row says "No forecast" past its weather source's last hour;
- the `Back to tonight` button.

#### Scenario: The page covers panning
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words drag, swipe, trackpad, arrow keys and `Back to tonight`
- **AND** it says the strip opens on the judged night, and stops at the first and last forecast hour
- **AND** its "No forecast" help names a later night past a weather source's last hour as a cause

### Requirement: The Cloud range row shows only when two forecasts give cloud
The card SHALL leave the Cloud range row out of the strip, with no label, no track and no message, when all of these hold:

- Home Assistant has both `sensor.pierpressure_<slug>_cloud_cover_min` and `sensor.pierpressure_<slug>_cloud_cover_max`;
- neither sensor's state is `unavailable`;
- their forecasts have no paired hour.

A paired hour SHALL be a min point and a max point with the same `datetime` whose values are both numbers, in either order.

#### Scenario: One cloud provider
- **WHEN** both sensors are in Home Assistant and available, the Cloud cover forecast holds values inside the axis, and every point of both the min and the max forecast is null
- **THEN** the strip has no row labelled Cloud range
- **AND** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance
- **AND** the Cloud cover row shows its cells and no message

#### Scenario: Every paired hour has its min above its max
- **WHEN** both sensors are available, and the min and max forecasts hold 70 and 20 at 2026-10-31T21:00:00Z and null at every other hour
- **THEN** the strip has a Cloud range row
- **AND** the row shows the message `No forecast` and no columns

#### Scenario: A sensor that is not there keeps the row
- **WHEN** the min sensor is in Home Assistant with null values, and Home Assistant has no `sensor.pierpressure_backyard_cloud_cover_max`
- **THEN** the strip has a Cloud range row, which shows the message `Not found`

#### Scenario: An unavailable sensor keeps the row
- **WHEN** `sensor.pierpressure_backyard_cloud_cover_min` has the state `unavailable` and no attributes, and the max sensor is available with null values
- **THEN** the strip has a Cloud range row, which shows the message `Unavailable`

#### Scenario: Before the first verdict
- **WHEN** both sensors have the state `unknown` and no attributes
- **THEN** the strip has no row labelled Cloud range

### Requirement: The Cloud range row is judged on the whole forecast
The card SHALL look for a paired hour in every point of both forecasts, not only the hours on the axis. Panning the strip SHALL never add or remove the Cloud range row.

#### Scenario: A pair only off the axis
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the min and max forecasts hold 40 and 70 at 2026-11-02T21:00:00Z and null at every hour on the axis
- **THEN** the strip has a Cloud range row
- **AND** the row shows the message `No forecast` and no columns

#### Scenario: Panning past the shorter forecast
- **WHEN** the min and max forecasts hold 40 and 70 at every hour from 2026-10-31T12:00:00Z to 2026-11-01T11:00:00Z and null after it, the Cloud cover forecast runs hourly to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later
- **THEN** the strip still has a Cloud range row, under Cloud cover
- **AND** the row shows the message `No forecast` and no columns

### Requirement: The docs say how to bring back the Cloud range row
For a strip with no Cloud range row, the "If something looks wrong" section of `docs/night-card.md` SHALL name two causes. Either fewer than two providers in the `providers` list under `conditions` give cloud cover, or a listed cloud provider failed for a whole fetch. For the first, it SHALL say that adding a provider that gives cloud cover, such as an Open-Meteo model, brings the row back. For the second, it SHALL point to the provider's health sensor.

#### Scenario: The troubleshooting section covers a missing Cloud range row
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** one list item starts with the strip having no Cloud range row
- **AND** that item names `conditions`, `providers`, Open-Meteo and the word health

### Requirement: The card lists the verdict's reasons
The card SHALL read the Verdict sensor's `reasons` attribute and show each reason as one item of a list named `Reasons`, in the attribute's order. The list SHALL sit under the Verdict, Score and Confidence lines and the Moon section, and before the note `No astronomical darkness tonight`, the `Back to tonight` button and the strip.

#### Scenario: A gated NO-GO
- **WHEN** the Verdict sensor has the state `NO-GO`, its `score` attribute is null, and its `reasons` attribute is `["Wind gust over the 40 km/h limit during the dark window."]`
- **THEN** the card shows a list named `Reasons` with one item, `Wind gust over the 40 km/h limit during the dark window.`
- **AND** the list comes after the Moon section and before the strip

#### Scenario: A scored night keeps the order
- **WHEN** the Verdict sensor has the state `GO` and its `reasons` attribute is `["Cloud: 90% of the dark window usable.", "Atmosphere factor 95%.", "Score 86/100."]`
- **THEN** the list shows three items, in that order

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor has the state `NO-GO`, its `dark_window` is `{start: null, end: null}`, and its `reasons` attribute is `["No astronomical night tonight: the sun never drops below -18°."]`
- **THEN** the card shows the list with that reason, then the note `No astronomical darkness tonight`, then the strip

### Requirement: The card shows every reason in full
The card SHALL show every item of the list at every card width. It SHALL offer no control that hides or shortens the list.

#### Scenario: Ten reasons
- **WHEN** the Verdict sensor's `reasons` attribute holds ten strings
- **THEN** the list shows ten items, each with its whole text
- **AND** the list holds no button and no `details` element

### Requirement: Reasons that are not a list of strings show no list
The card SHALL show no list when the `reasons` attribute is missing, null, an empty list, not a list, or a list with an item that is not a string. The card SHALL render the rest as usual and SHALL NOT throw.

#### Scenario: No reasons attribute
- **WHEN** the Verdict sensor has the state `GO` and no `reasons` attribute
- **THEN** the card shows no `Reasons` list and still shows the verdict and the strip

#### Scenario: An empty list
- **WHEN** the Verdict sensor's `reasons` attribute is `[]`
- **THEN** the card shows no `Reasons` list

#### Scenario: A string, not a list
- **WHEN** the Verdict sensor's `reasons` attribute is `"Score 72/100."`
- **THEN** the card shows no `Reasons` list

#### Scenario: A list with a number in it
- **WHEN** the Verdict sensor's `reasons` attribute is `["Score 72/100.", 3]`
- **THEN** the card shows no `Reasons` list

### Requirement: The reasons list shows only with the verdict
The card SHALL show no `Reasons` list when it shows no verdict: before Home Assistant gives it a state, and when it shows a message in place of the verdict.

#### Scenario: PierPressure is offline
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable` and a `reasons` attribute of `["Score 72/100."]`
- **THEN** the card shows that PierPressure is offline and shows no `Reasons` list

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor has the state `unknown` and no attributes
- **THEN** the card shows no `Reasons` list

#### Scenario: Reasons left over while the verdict is unknown
- **WHEN** the Verdict sensor has the state `unknown` and a `reasons` attribute of `["Score 72/100."]`
- **THEN** the card shows `—` as the verdict and shows no `Reasons` list

### Requirement: A reason's UTC times show in Home Assistant's time zone
In each reason, the card SHALL show every UTC time written as `YYYY-MM-DDTHH:MM:SSZ` as a 24-hour `HH:MM` in Home Assistant's time zone, as the strip shows times. The card SHALL leave the rest of the reason's text as it is, and SHALL leave a time it cannot read as it is.

#### Scenario: The span line
- **WHEN** Home Assistant's time zone is `UTC` and a reason is `Scored from 2026-10-31T21:00:00Z to 2026-11-01T03:25:00Z (the rest of tonight).`
- **THEN** the list shows `Scored from 21:00 to 03:25 (the rest of tonight).`

#### Scenario: Another time zone
- **WHEN** Home Assistant's time zone is `Europe/Paris` and a reason is `Scored from 2026-10-31T21:00:00Z to 2026-11-01T03:25:00Z (the rest of tonight).`
- **THEN** the list shows `Scored from 22:00 to 04:25 (the rest of tonight).`

#### Scenario: A reason with no time
- **WHEN** a reason is `Atmosphere factor 95%.`
- **THEN** the list shows `Atmosphere factor 95%.`

#### Scenario: A time that is not a real time
- **WHEN** a reason is `Scored from 2026-13-45T21:00:00Z onwards.`
- **THEN** the list shows `Scored from 2026-13-45T21:00:00Z onwards.`

### Requirement: The docs describe the reasons
Where `docs/night-card.md` says what the card shows, it SHALL have a **Reasons** line. The line SHALL say:

- that the card lists the Verdict sensor's reasons in order;
- that a gated `NO-GO` names its failed gate there;
- that times in a reason show in the Home Assistant time zone;
- that equipment notes come after the scoring reasons.

#### Scenario: The table covers the reasons
- **WHEN** the "What the card shows" section of `docs/night-card.md` is read
- **THEN** it has a line that starts with **Reasons**
- **AND** that line names `NO-GO`, gate, time zone and equipment
