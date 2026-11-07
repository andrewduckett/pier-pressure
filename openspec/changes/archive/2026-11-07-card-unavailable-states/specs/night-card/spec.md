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
- that hovering over a message names the sensor;
- that the Moon up lane repeats the Moon altitude row's message;
- the note `No astronomical darkness tonight`.

#### Scenario: The strip section covers the messages
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** it names `Not found`, `Unavailable`, `No forecast` and `No astronomical darkness tonight`
- **AND** it names the words hover and Moon up in the same paragraph as `No forecast`

### Requirement: The docs say what to do when something is missing
The "If something looks wrong" section of `docs/night-card.md` SHALL say what to do when the card shows each of these:

- `PierPressure is offline`;
- `No PierPressure verdict found`;
- a row that says `Not found`, `Unavailable` or `No forecast`;
- `No astronomical darkness tonight`.

#### Scenario: The troubleshooting section covers the missing cases
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** it names `PierPressure is offline`, `No PierPressure verdict found`, `Not found`, `Unavailable`, `No forecast` and `No astronomical darkness tonight`

### Requirement: The docs name the causes of No forecast
For a row that says `No forecast`, the "If something looks wrong" section of `docs/night-card.md` SHALL name two causes. Either no weather source in the pier's `providers` gave that condition a value for these hours, or every weather source failed. It SHALL point to the pier's weather source health sensors.

#### Scenario: The causes and where to look
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** it names the word health and the `providers` setting

## MODIFIED Requirements

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

### Requirement: A missing sun altitude leaves a blank hour
The card SHALL draw no Sun altitude cell for an hour whose value is null or not a number, or for an hour the forecast has no point for. When the sun altitude sensor is missing or unavailable, or has no `forecast` list, the card SHALL draw the Sun altitude row with its label and no cells. The row SHALL show the message that says why. The card SHALL NOT throw, and SHALL draw the other rows as usual.

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
This requirement covers the Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance rows. When a row's sensor is missing from Home Assistant or unavailable, the card SHALL draw that row with its label and no cells. The row SHALL show the message that says why. The card SHALL do the same when the sensor has no `forecast` list. The card SHALL skip a point without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Humidity is unavailable
- **WHEN** `sensor.pierpressure_backyard_humidity` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Humidity row with its label, no cells and the message `Unavailable`
- **AND** the cloud rows show their cells

#### Scenario: Only the sun and cloud sensors
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no timeline sensor but Sun altitude and the four cloud sensors
- **THEN** the card renders without an error
- **AND** every row but Sun altitude and the four cloud rows shows its label, no cells and the message `Not found`
