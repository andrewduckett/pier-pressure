# night-dashboard Specification

## Purpose
The night-dashboard capability documents a Home Assistant dashboard that a user pastes in to see tonight's verdict and the night strip for one pier, built only from the entities PierPressure already publishes. Scenarios about the YAML's content are asserted by a test that reads the docs page; scenarios about how Home Assistant draws it are confirmed by the documented check against a real Home Assistant.

## Requirements

### Requirement: The docs publish one complete dashboard
The project SHALL publish a docs page, `docs/night-dashboard.md`, that holds one complete Home Assistant dashboard as a single YAML block. The dashboard SHALL use only Home Assistant core cards and plotly-graph-card, whose card type is `custom:plotly-graph`. It SHALL add no JavaScript of its own beyond the expressions that plotly-graph-card evaluates.

#### Scenario: The YAML parses as a dashboard
- **WHEN** the dashboard YAML block is read from `docs/night-dashboard.md` and parsed
- **THEN** it parses without error into a dashboard with at least one view

#### Scenario: Only core cards and plotly-graph-card
- **WHEN** every card `type` in the parsed dashboard is listed, including cards nested in stacks and grids
- **THEN** each type is either a Home Assistant core card type or `custom:plotly-graph`

### Requirement: The dashboard reads only what PierPressure publishes
Every PierPressure entity id the dashboard YAML names SHALL be one the MQTT adapter announces for the example pier `backyard`. Every attribute of a PierPressure entity that the YAML reads SHALL be a key the adapter publishes in that entity's attributes payload.

#### Scenario: Every entity id exists
- **WHEN** every `sensor.pierpressure_backyard_*` entity id in the dashboard YAML is collected
- **THEN** each one matches an entity that the adapter's discovery configs announce for pier `backyard`

#### Scenario: Every attribute exists
- **WHEN** the YAML reads an attribute of a PierPressure entity, such as `forecast` on `sensor.pierpressure_backyard_seeing` or `window` on `sensor.pierpressure_backyard_target_1`
- **THEN** that key is present in the attributes payload the adapter publishes for that entity

#### Scenario: A renamed attribute fails the check
- **WHEN** the YAML reads an attribute key that the adapter does not publish for that entity
- **THEN** the docs test fails and names the entity id and the missing key

### Requirement: The strip has one row per timeline sensor
The night strip SHALL draw one row per timeline sensor, from that sensor's `forecast` attribute, in this order from top to bottom: Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency. Each row SHALL be labelled with that name.

#### Scenario: Rows in order
- **WHEN** the strip's rows are listed from the dashboard YAML
- **THEN** there are nine rows, labelled Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing and Transparency, in that order
- **AND** each row reads the `forecast` attribute of the timeline sensor with that name

### Requirement: A null hour is a gap
An hour whose `forecast` value is null SHALL be drawn as a gap in its row: no colour, distinct from every shade a value can take.

#### Scenario: Seeing missing for an hour
- **WHEN** the Seeing forecast holds `{"datetime": "2026-10-31T16:00:00Z", "value": null}`
- **THEN** the Seeing row's 16:00 UTC cell is empty, not drawn in the lightest or darkest shade

### Requirement: Darker means more, or poorer
Within each row, a darker shade SHALL mean more of what the row names. For Seeing and Transparency, darker SHALL mean poorer, that is a lower value. The Sun altitude row SHALL darken as the sun sinks, so astronomical night is darkest. The Moon altitude row SHALL be lightest while the moon is below the horizon and darken as it climbs.

#### Scenario: More cloud is darker
- **WHEN** the Cloud cover forecast holds 10 at one hour and 90 at another
- **THEN** the 90 cell is darker than the 10 cell

#### Scenario: Poorer seeing is darker
- **WHEN** the Seeing forecast holds 0.71 at one hour and 0.43 at another
- **THEN** the 0.43 cell is darker than the 0.71 cell

#### Scenario: Night sun is darkest
- **WHEN** the Sun altitude forecast holds 9 at one hour and -25 at another
- **THEN** the -25 cell is darker than the 9 cell

### Requirement: The strip spans tonight
The strip's time axis SHALL run from 4 hours before `dark_window.start` to 5 hours after `dark_window.end`, read from the Verdict entity's attributes. When `dark_window.start` or `dark_window.end` is null, the axis SHALL run from 6 hours before the browser's current time to 18 hours after it. The axis SHALL show times in Home Assistant's configured time zone.

#### Scenario: A normal night
- **WHEN** the Verdict's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the axis runs from 16:30 UTC on 31 October to 08:25 UTC on 1 November, shown in Home Assistant's time zone

#### Scenario: No astronomical night
- **WHEN** the Verdict's `dark_window` is `{start: null, end: null}`
- **THEN** the axis runs from 6 hours before the current time to 18 hours after it
- **AND** no dusk or dawn line is drawn

### Requirement: Dusk and dawn lines
The strip SHALL draw a labelled vertical line at `dark_window.start` (dusk) and another at `dark_window.end` (dawn), across every row and lane.

#### Scenario: Dusk and dawn marked
- **WHEN** the Verdict's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** a line labelled dusk crosses the strip at 20:30 UTC and a line labelled dawn at 03:25 UTC

### Requirement: A Moon up lane
Below the condition rows, the strip SHALL draw a lane labelled "Moon up" with a bar over each run of hours whose Moon altitude forecast value is above 0°. It SHALL read the Moon altitude forecast, not `moon.rise` or `moon.set`, which cover only the dark window.

#### Scenario: The moon rises before dusk
- **WHEN** the Moon altitude forecast is at or below 0 up to 20:00 UTC and above 0 from 21:00 UTC to 06:00 UTC
- **THEN** the Moon up lane shows one bar covering the hours from 21:00 UTC through 06:00 UTC

#### Scenario: The moon stays down
- **WHEN** every Moon altitude forecast value on the axis is at or below 0
- **THEN** the Moon up lane is drawn with no bar

### Requirement: One lane per ranked target
The strip SHALL draw one lane for each of Target 1 to Target 10 that is available, in rank order. Each lane SHALL hold one bar from that target's `window.start` to `window.end`, labelled with the Target sensor's state. A rank that is unavailable SHALL leave no lane.

#### Scenario: Two targets tonight
- **WHEN** Target 1 is M31 Andromeda with window 21:00 to 02:00 UTC, Target 2 is M42 Orion with window 01:00 to 03:00 UTC, and Target 3 to Target 10 are unavailable
- **THEN** the strip shows two target lanes: M31 Andromeda from 21:00 to 02:00 UTC, then M42 Orion from 01:00 to 03:00 UTC

#### Scenario: No targets tonight
- **WHEN** Target 1 to Target 10 are all unavailable
- **THEN** the strip shows no target lane

### Requirement: A now line at the current time
The strip SHALL draw a labelled vertical "now" line at the browser's current time, not at the verdict's `generated_at`, and SHALL move it as the card refreshes.

#### Scenario: Now differs from the last recompute
- **WHEN** the verdict's `generated_at` is 21:00 UTC and the browser's clock reads 23:30 UTC
- **THEN** the now line crosses the strip at 23:30 UTC

### Requirement: The cards around the strip
Beside the strip, the dashboard SHALL show:
- a tonight card with the verdict, score, confidence band and value, the dark window and the reasons, read from the Verdict entity;
- a moon card with the moon's illumination, phase, rise and set, read from the Verdict entity's `moon` attribute;
- a target table listing Target 1 to Target 10;
- one health chip for each weather source, Open-Meteo health and 7Timer! health.

#### Scenario: Every card is present
- **WHEN** the parsed dashboard's cards are listed
- **THEN** it holds a card that reads `verdict`, `score`, `confidence`, `dark_window` and `reasons` from `sensor.pierpressure_backyard_verdict`
- **AND** a card that reads `moon` from `sensor.pierpressure_backyard_verdict`
- **AND** a card that lists `sensor.pierpressure_backyard_target_1` through `sensor.pierpressure_backyard_target_10`
- **AND** chips for `sensor.pierpressure_backyard_open_meteo_health` and `sensor.pierpressure_backyard_7timer_health`

### Requirement: The dashboard survives PierPressure going offline
When PierPressure is offline, Home Assistant drops the attributes of its entities. The dashboard SHALL then still render, with an empty strip and its cards showing the entities as unavailable, and SHALL show no card error.

#### Scenario: PierPressure stopped
- **WHEN** PierPressure publishes `offline` on its availability topic and the dashboard is open
- **THEN** every card renders without a card error, and the strip shows no cells, lanes or dusk and dawn lines

### Requirement: The docs say how to install and adapt it
The docs page SHALL give the steps to install plotly-graph-card through HACS, and SHALL say to replace the example pier id `backyard` with the reader's own pier id.

#### Scenario: A reader follows the page
- **WHEN** a reader with Home Assistant and HACS but without plotly-graph-card follows the page from the top
- **THEN** the page tells them to install plotly-graph-card through HACS before pasting the YAML
- **AND** it tells them to replace `backyard` with their pier id

### Requirement: The dashboard is checked against a real Home Assistant
The dashboard YAML SHALL be checked in a real Home Assistant fed by a running PierPressure over MQTT, and the docs page SHALL show a screenshot from that check, stored in `docs/images/`.

#### Scenario: The check passes
- **WHEN** the dashboard YAML is pasted unchanged, apart from the pier id, into a Home Assistant whose MQTT broker receives a running PierPressure's publishes
- **THEN** every card renders without a card error and the strip shows its nine rows, its lanes, and its dusk, dawn and now lines

#### Scenario: The page shows the result
- **WHEN** `docs/night-dashboard.md` is rendered
- **THEN** it shows an image stored under `docs/images/` of the dashboard from that check

### Requirement: Cells and lane bars have rounded corners
Each hour cell in the strip's condition rows and each bar in the Moon up and target lanes SHALL be drawn with rounded corners: a radius of 2 px for a cell and 4 px for a lane bar. Rounding SHALL not change what the cells show: a null hour stays a gap, and hovering over a cell still shows the hour and the value.

#### Scenario: The YAML rounds cells and lane bars
- **WHEN** the strip's traces are read from the dashboard YAML
- **THEN** the trace that draws the condition rows sets a corner radius of 2 px
- **AND** the trace that draws the lanes sets a corner radius of 4 px

#### Scenario: A null hour stays a gap after rounding
- **WHEN** the Seeing forecast holds `{"datetime": "2026-10-31T16:00:00Z", "value": null}`
- **THEN** the Seeing row draws no cell for 16:00 UTC, and hovering there shows nothing

#### Scenario: The check shows rounded corners
- **WHEN** the documented check renders the dashboard in a real Home Assistant
- **THEN** every cell and every lane bar has visibly rounded corners, and the screenshot on the page shows them
