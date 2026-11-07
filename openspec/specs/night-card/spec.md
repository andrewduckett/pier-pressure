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
Below the verdict, score and confidence, the card SHALL draw a night strip. Under the strip's Moon altitude row, the card SHALL draw four cloud rows. From top to bottom they SHALL be Cloud cover, Cloud low, Cloud mid and Cloud high, each labelled with that name. Each row SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard` and the Verdict sensor has the state `GO`
- **THEN** the strip shows the rows Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid and Cloud high, in that order, at its top
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
The card SHALL draw a cloud sensor's row with its label and no cells when that sensor is missing from Home Assistant or unavailable. It SHALL do the same when the sensor has no `forecast` attribute, or its `forecast` is not a list. The card SHALL skip a point in `forecast` without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Cloud high is unavailable
- **WHEN** `sensor.pierpressure_backyard_cloud_high` has the state `unavailable` and no attributes, and the other three cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Cloud high row with its label and no cells
- **AND** the other three cloud rows show their cells

#### Scenario: An unavailable sensor that kept its forecast
- **WHEN** `sensor.pierpressure_backyard_cloud_high` has the state `unavailable` and a `forecast` attribute with values inside the axis
- **THEN** the strip shows the Cloud high row with its label and no cells

#### Scenario: No cloud sensors at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has none of the four cloud sensors
- **THEN** the card renders without an error and shows the four labelled cloud rows with no cells

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
The card SHALL draw no Sun altitude cell for an hour whose value is null or not a number, or for an hour the forecast has no point for. When the sun altitude sensor is missing or unavailable, or has no `forecast` list, the card SHALL draw the Sun altitude row with its label and no cells. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: A null hour
- **WHEN** the Sun altitude forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Sun altitude row has no cell for 22:00 UTC

#### Scenario: The sensor is unavailable
- **WHEN** `sensor.pierpressure_backyard_sun_altitude` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Sun altitude row with its label and no cells
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
When the moon altitude sensor is missing from Home Assistant or unavailable, or has no `forecast` list, the card SHALL draw the Moon up lane with its label and no bars. The card SHALL NOT throw, and SHALL draw the rows as usual.

#### Scenario: The moon sensor is unavailable
- **WHEN** `sensor.pierpressure_backyard_moon_altitude` has the state `unavailable` and a `forecast` attribute with values above 0 inside the axis
- **THEN** the strip shows the Moon up lane with its label and no bars

#### Scenario: No moon sensor at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no `sensor.pierpressure_backyard_moon_altitude`
- **THEN** the card renders without an error and shows the Moon up lane with no bars

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
When the axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`. Each line SHALL cross every row from Sun altitude to Rain chance, the Moon up lane and every target lane. When the axis falls back to the browser's current time, the card SHALL draw no dusk or dawn line.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line

#### Scenario: The lines reach the last target lane
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and Target 1 to Target 3 each have a target tonight
- **THEN** the dusk and dawn lines run from the Sun altitude row down to the bottom of the lane labelled `Target 3`

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
The strip SHALL have fifteen rows, one per timeline sensor, each labelled with its name. From top to bottom they SHALL be Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance.

#### Scenario: The rows in order
- **WHEN** the card is configured with `pier: backyard` and the Verdict sensor has the state `GO`
- **THEN** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance

### Requirement: Each row reads its timeline sensor
Each row SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_<key>`, named from the same slug as the Verdict sensor. The key SHALL be the row's name in lower case with `_` for each space, except that Rain chance reads `precipitation_probability`.

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
When the sensor of the Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction or Rain chance row is missing from Home Assistant or unavailable, the card SHALL draw that row with its label and no cells. It SHALL do the same when the sensor has no `forecast` list. The card SHALL skip a point without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Humidity is unavailable
- **WHEN** `sensor.pierpressure_backyard_humidity` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Humidity row with its label and no cells
- **AND** the cloud rows show their cells

#### Scenario: Only the sun and cloud sensors
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no timeline sensor but Sun altitude and the four cloud sensors
- **THEN** the card renders without an error
- **AND** every row but Sun altitude and the four cloud rows shows its label and no cells

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
`docs/night-card.md` SHALL describe each of the fifteen rows:

- its name and the sensor it reads;
- for each shaded row, what its lightest and darkest shades mean, and that darker means worse for Seeing and Transparency;
- that Temperature and Dew point share one scale;
- that a Rain chance cell fills the hour before its time;
- that a Wind direction arrow points the way the wind blows to;
- what hovering over a cell shows, with its unit.

#### Scenario: The page covers every row
- **WHEN** `docs/night-card.md` is read
- **THEN** it names each of the fifteen rows and the sensors `sensor.pierpressure_<pier>_wind_gust` and `sensor.pierpressure_<pier>_precipitation_probability`
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
The card SHALL report a size of 10 to Home Assistant, plus 1 for every three target lanes it shows, rounding up.

#### Scenario: No targets
- **WHEN** the strip has no target lane
- **THEN** the card reports a size of 10

#### Scenario: Four targets
- **WHEN** the strip has four target lanes
- **THEN** the card reports a size of 12

#### Scenario: Ten targets
- **WHEN** the strip has ten target lanes
- **THEN** the card reports a size of 14

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
