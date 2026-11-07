## ADDED Requirements

### Requirement: A row with no cell says why
When one of the strip's fifteen rows would draw no cell at all, the card SHALL show a message in that row's track that names the cause. The message SHALL be the first of these that applies to the row's sensor:

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
- **WHEN** the Verdict sensor and all fifteen timeline sensors have the state `unknown` and no attributes
- **THEN** each of the fifteen rows shows the message `No forecast`

### Requirement: A row with a cell shows no message
A row that draws at least one cell SHALL show no message. Its hours without a value SHALL stay blank.

#### Scenario: A row with one value
- **WHEN** the Cloud mid forecast inside the axis holds one value, 40 at 2026-10-31T22:00:00Z, and null for every other hour
- **THEN** the Cloud mid row has one cell and shows no message

### Requirement: Hovering over a row's message names its sensor
Hovering over a row's message SHALL name the row's sensor by its entity id and say the cause:

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

#### Scenario: The moon stays down
- **WHEN** every value in the moon altitude forecast inside the axis is 0 or below
- **THEN** the Moon up lane shows no bars and no message

### Requirement: A night with no astronomical darkness is noted
When the Verdict sensor's `dark_window` has a `start` of null and an `end` of null, the card SHALL show the note `No astronomical darkness tonight` between the confidence and the strip, and SHALL still draw the strip on its fallback axis. The card SHALL show no such note in any other case: when `dark_window` is missing, when only one of its ends is null, or when an end is not a readable time.

#### Scenario: A summer night far north
- **WHEN** the Verdict sensor has the state `NO-GO` and its `dark_window` is `{start: null, end: null}`
- **THEN** the card shows `No astronomical darkness tonight` above the strip
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

### Requirement: The docs say what each missing case looks like
`docs/night-card.md` SHALL describe the row messages `Not found`, `Unavailable` and `No forecast`, what each means, and that the Moon up lane repeats the Moon altitude row's message. It SHALL describe the note `No astronomical darkness tonight`. Its "If something looks wrong" section SHALL say what to do when the card shows:

- `PierPressure is offline`;
- `No PierPressure verdict found`;
- a row that says `Not found`, `Unavailable` or `No forecast`;
- `No astronomical darkness tonight`.

#### Scenario: The page covers the missing cases
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the messages `Not found`, `Unavailable`, `No forecast` and `No astronomical darkness tonight`
- **AND** its "If something looks wrong" section names `PierPressure is offline`, `No PierPressure verdict found`, `Not found`, `Unavailable`, `No forecast` and `No astronomical darkness tonight`

## MODIFIED Requirements

### Requirement: A missing cloud sensor leaves an empty row
The card SHALL draw a cloud sensor's row with its label, no cells and the message that says why, when that sensor is missing from Home Assistant or unavailable. It SHALL do the same when the sensor has no `forecast` attribute, or its `forecast` is not a list. The card SHALL skip a point in `forecast` without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

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

### Requirement: A missing sun altitude leaves a blank hour
The card SHALL draw no Sun altitude cell for an hour whose value is null or not a number, or for an hour the forecast has no point for. When the sun altitude sensor is missing or unavailable, or has no `forecast` list, the card SHALL draw the Sun altitude row with its label, no cells and the message that says why. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: A null hour
- **WHEN** the Sun altitude forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Sun altitude row has no cell for 22:00 UTC

#### Scenario: The sensor is unavailable
- **WHEN** `sensor.pierpressure_backyard_sun_altitude` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Sun altitude row with its label, no cells and the message `Unavailable`
- **AND** the cloud rows show their cells

### Requirement: A missing moon altitude leaves the Moon up lane empty
When the moon altitude sensor is missing from Home Assistant or unavailable, or has no `forecast` list, the card SHALL draw the Moon up lane with its label, no bars and the Moon altitude row's message. The card SHALL NOT throw, and SHALL draw the rows as usual.

#### Scenario: The moon sensor is unavailable
- **WHEN** `sensor.pierpressure_backyard_moon_altitude` has the state `unavailable` and a `forecast` attribute with values above 0 inside the axis
- **THEN** the strip shows the Moon up lane with its label, no bars and the message `Unavailable`

#### Scenario: No moon sensor at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no `sensor.pierpressure_backyard_moon_altitude`
- **THEN** the card renders without an error and shows the Moon up lane with no bars and the message `Not found`

### Requirement: A missing sensor leaves its row empty
When the sensor of the Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction or Rain chance row is missing from Home Assistant or unavailable, the card SHALL draw that row with its label, no cells and the message that says why. It SHALL do the same when the sensor has no `forecast` list. The card SHALL skip a point without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Humidity is unavailable
- **WHEN** `sensor.pierpressure_backyard_humidity` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Humidity row with its label, no cells and the message `Unavailable`
- **AND** the cloud rows show their cells

#### Scenario: Only the sun and cloud sensors
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no timeline sensor but Sun altitude and the four cloud sensors
- **THEN** the card renders without an error
- **AND** every row but Sun altitude and the four cloud rows shows its label, no cells and the message `Not found`
