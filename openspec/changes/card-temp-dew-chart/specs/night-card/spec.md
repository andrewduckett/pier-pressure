<!-- Plain language: Name the actor, condition and observable result. Explain necessary domain terms using the agreed glossary. Keep requirement and scenario headings and WHEN/THEN syntax exactly as required. -->

## ADDED Requirements

### Requirement: The card draws a Temperature chart under the target lanes
The strip SHALL draw the Temperature chart under the last target lane, or under the Moon up lane when there is no target lane, and above the time labels. The chart SHALL draw a Temperature line from the `forecast` of `sensor.pierpressure_<slug>_temperature` and a Dew point line from the `forecast` of `sensor.pierpressure_<slug>_dew_point`, named from the same slug as the Verdict sensor. Its label column SHALL hold a key that names Temperature, then Dew point.

#### Scenario: Under two target lanes
- **WHEN** the Verdict sensor has the state `GO`, and Target 1 and Target 2 each have a target tonight
- **THEN** the Temperature chart comes after the lane labelled `Target 2` and before the time labels
- **AND** its key reads `Temperature`, then `Dew point`

#### Scenario: No target tonight
- **WHEN** the Verdict sensor has the state `GO` and no rank has a target tonight
- **THEN** the Temperature chart comes straight after the Moon up lane

#### Scenario: The sensors named from the pier
- **WHEN** the card is configured with `pier: Back-Yard`, and `sensor.pierpressure_back_yard_temperature` and `sensor.pierpressure_back_yard_dew_point` each hold values inside the axis
- **THEN** the Temperature chart draws a Temperature line and a Dew point line from those forecasts

### Requirement: A Temperature chart point sits at the middle of its hour
The chart SHALL place each point that holds a number at the middle of the hour that starts at its `datetime`, at the height of its value on the °C scale. The chart SHALL draw the points of every hour that overlaps the axis, and of the hour just before and just after those hours, and SHALL cut its lines off at the axis ends.

#### Scenario: A point at mid-hour
- **WHEN** the Temperature forecast holds 4 at 2026-10-31T21:00:00Z, inside the axis
- **THEN** the Temperature line's point for that hour is at 2026-10-31T21:30:00Z

#### Scenario: Lines reach the axis ends
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the Temperature forecast holds a value at every hour from 2026-10-31T15:00:00Z to 2026-11-01T09:00:00Z
- **THEN** the Temperature line runs without a break from the axis start to the axis end

### Requirement: A Temperature chart line breaks where an hour has no value
A line SHALL join the points of two neighbouring hours only when both hold a number. An hour whose value is null or not a number, or that has no point, SHALL leave a break in the line. A point whose hour before and hour after both hold no number SHALL be drawn as a dot.

#### Scenario: A null hour
- **WHEN** the Temperature forecast holds 4 at 2026-10-31T21:00:00Z, null at 22:00, 3 at 23:00 and 2 at 2026-11-01T00:00:00Z, and no other point near them
- **THEN** the Temperature line has a dot at 2026-10-31T21:30:00Z
- **AND** it joins 23:30 to 00:30, and has no line from 21:30 to 23:30

#### Scenario: A missing point
- **WHEN** the Dew point forecast holds 1 at 2026-10-31T21:00:00Z and 2 at 23:00, and no point at 22:00
- **THEN** the Dew point line has a dot at 21:30 and a dot at 23:30, and no line between them

### Requirement: The Temperature chart's scale fits the whole reach
The °C scale SHALL run from the lowest number in either line's forecast, rounded down to a multiple of 5, to the highest, rounded up to a multiple of 5. When that spans less than 10 °C, its top SHALL be raised to 10 °C above its bottom. Every point with a readable `datetime` SHALL count, on the axis or not, except that the forecast of an unavailable sensor SHALL NOT count. Each 5 °C step SHALL be 16 px tall.

#### Scenario: Both lines set the scale
- **WHEN** the Temperature forecast's numbers run from 3.2 to 14.8 and the Dew point forecast's from −1.5 to 9
- **THEN** the scale runs from −5 °C to 15 °C, and the chart is 64 px tall

#### Scenario: A narrow range
- **WHEN** both forecasts' numbers lie between 6 and 8
- **THEN** the scale runs from 5 °C to 15 °C

#### Scenario: Values on a step
- **WHEN** both forecasts' numbers run from exactly 0 to exactly 10
- **THEN** the scale runs from 0 °C to 10 °C

#### Scenario: A later night counts
- **WHEN** the Temperature forecast holds numbers from 5 to 10 inside the axis, and −3 on a later night outside it
- **THEN** the scale runs from −5 °C to 10 °C

#### Scenario: An unavailable sensor's stale forecast
- **WHEN** the Temperature forecast's numbers run from 5 to 10, and the Dew point sensor is `unavailable` with a `forecast` that holds −12
- **THEN** the scale runs from 5 °C to 15 °C

### Requirement: The Temperature chart labels each 5 °C step
The chart SHALL draw a gridline at each multiple of 5 °C on its scale, and a label level with it in the label column that reads `<value> °C`. The gridlines and labels SHALL stay where they are while the strip pans. When neither forecast counts a number toward the scale, the chart SHALL be 32 px tall, with no gridline and no label.

#### Scenario: The labels from top to bottom
- **WHEN** the scale runs from −5 °C to 15 °C
- **THEN** the chart's labels read, top to bottom, `15 °C`, `10 °C`, `5 °C`, `0 °C` and `-5 °C`, each level with a gridline

#### Scenario: A pan keeps the scale
- **WHEN** the scale runs from −5 °C to 15 °C and the user pans the axis 24 hours later
- **THEN** the chart's labels still read `15 °C`, `10 °C`, `5 °C`, `0 °C` and `-5 °C`

#### Scenario: No value at all
- **WHEN** both sensors have the state `unknown` and no attributes
- **THEN** the chart is 32 px tall, with no gridline and no label

### Requirement: The Temperature chart's lines are orange and green
The Temperature line SHALL be orange `#d97706`, and the Dew point line green `#15803d`, each with its dots. The key SHALL show each line's name beside a sample of its colour. Each colour SHALL have a contrast ratio of at least 3:1 against Home Assistant's default card background in the light theme, `#ffffff`, and in the dark theme, `#1c1c1c`. Contrast ratios are as WCAG 2.2 defines them.

#### Scenario: The two colours
- **WHEN** the Temperature and Dew point forecasts hold values inside the axis
- **THEN** the Temperature line and its key sample are `#d97706`, and the Dew point line and its key sample are `#15803d`

#### Scenario: Against the light and dark card
- **WHEN** the contrast ratio of each line's colour is computed against `#ffffff` and against `#1c1c1c`
- **THEN** all four are at least 3:1

### Requirement: Hovering over a Temperature chart hour shows both values
Each hour that overlaps the axis and holds a number on either line SHALL have a hover area the full height of the chart, placed as a row's cell is. Hovering SHALL show `The hour from <HH:MM>: Temperature <value> °C, Dew point <value> °C`, in Home Assistant's time zone, with each value as the forecast holds it. A line with no number for the hour SHALL be left out of the text. An hour with no number on either line SHALL have no hover area.

#### Scenario: Both values
- **WHEN** Home Assistant's time zone is `UTC`, and the Temperature and Dew point forecasts hold 4.2 and 1.5 at 2026-10-31T21:00:00Z
- **THEN** hovering over that hour shows `The hour from 21:00: Temperature 4.2 °C, Dew point 1.5 °C`

#### Scenario: Only the dew point
- **WHEN** Home Assistant's time zone is `UTC`, the Temperature forecast holds null at 2026-10-31T21:00:00Z, and the Dew point forecast holds −1.5 there
- **THEN** hovering over that hour shows `The hour from 21:00: Dew point -1.5 °C`

#### Scenario: In Tokyo
- **WHEN** Home Assistant's time zone is `Asia/Tokyo`, and the Temperature forecast holds 4.2 at 2026-10-31T12:00:00Z and the Dew point forecast has no point there
- **THEN** hovering over that hour shows `The hour from 21:00: Temperature 4.2 °C`

#### Scenario: Neither value
- **WHEN** both forecasts hold null at 2026-10-31T22:00:00Z, inside the axis
- **THEN** the chart has no hover area for the hour from 22:00

### Requirement: A Temperature chart line that cannot draw says why
When a line holds no number for any hour that overlaps the axis, the key SHALL show a message beside that line's name: `Not found`, `Unavailable` or `No forecast`, chosen as for a row with no cell. Hovering over the message SHALL name the sensor and the cause, as for a row's message. The chart SHALL keep its place, and SHALL draw the other line as usual. A line with a number for at least one such hour SHALL show no message.

#### Scenario: The dew point sensor is not there
- **WHEN** the Temperature forecast holds values inside the axis and Home Assistant has no `sensor.pierpressure_backyard_dew_point`
- **THEN** the key shows `Not found` beside `Dew point`, and no message beside `Temperature`
- **AND** the chart draws the Temperature line and no Dew point line
- **AND** hovering over the message shows `sensor.pierpressure_backyard_dew_point is not in Home Assistant`

#### Scenario: An unavailable sensor that kept its forecast
- **WHEN** `sensor.pierpressure_backyard_temperature` has the state `unavailable` and a `forecast` with values inside the axis
- **THEN** the key shows `Unavailable` beside `Temperature`, and the chart draws no Temperature line

#### Scenario: Before the first verdict
- **WHEN** both sensors have the state `unknown` and no attributes
- **THEN** the key shows `No forecast` beside `Temperature` and beside `Dew point`, and the chart draws no line

#### Scenario: Panned past the forecast
- **WHEN** the Temperature forecast's numbers end on 2026-11-01, and the user pans the axis to 2026-11-02, where the Dew point forecast still holds values
- **THEN** the key shows `No forecast` beside `Temperature`, and the chart draws the Dew point line

### Requirement: The docs describe the Temperature chart
`docs/night-card.md` SHALL describe the Temperature chart: where it sits on the strip and the two sensors it reads; that each point is at the middle of its hour; that a line breaks where an hour has no value; the °C scale and that it stays put while the strip pans; the two colours and the key; that dew is more likely the closer the two lines come; what hovering shows; and its messages.

#### Scenario: The page covers the Temperature chart
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the Temperature chart and the sensors `sensor.pierpressure_<pier>_temperature` and `sensor.pierpressure_<pier>_dew_point`
- **AND** it names the words middle of the hour, break, °C, orange, green, key, dew and hover

## MODIFIED Requirements

### Requirement: A null hour is blank
The card SHALL draw no cell for an hour whose `forecast` value is null or not a number, or for an hour the forecast has no point for. That hour SHALL be blank in its row, distinct from every shade or arrow a value can take. On the Temperature chart, such an hour SHALL have no point on that line, and a value of 0 SHALL count as a number.

#### Scenario: Cloud low missing for an hour
- **WHEN** the Cloud low forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Cloud low row has no cell for 22:00 UTC

#### Scenario: Cloud mid at zero
- **WHEN** the Cloud mid forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": 0}` inside the axis
- **THEN** the Cloud mid row has a 22:00 UTC cell shaded `#0d366b`

#### Scenario: Seeing missing for an hour
- **WHEN** the Seeing forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Seeing row has no cell for 22:00 UTC

#### Scenario: Temperature at zero
- **WHEN** the Temperature forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": 0}` inside the axis
- **THEN** the Temperature chart's Temperature line has a point at 2026-10-31T22:30:00Z, level with the `0 °C` gridline

#### Scenario: Wind direction missing for an hour
- **WHEN** the Wind direction forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Wind direction row has no cell and no arrow for 22:00 UTC

### Requirement: Dusk and dawn lines mark the dark window
When the opening axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`, each only while its time lies on the axis. Each line SHALL cross every row from Sun altitude to Rain chance, the Moon up lane, every target lane and the Temperature chart. When the opening axis falls back to the browser's current time, the card SHALL draw no dusk or dawn line.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line

#### Scenario: The lines reach the last target lane
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, and Target 1 to Target 3 each have a target tonight
- **THEN** the dusk and dawn lines run from the Sun altitude row, past the lane labelled `Target 3`, down to the bottom of the Temperature chart

#### Scenario: Dusk panned off the axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, and the user has panned the axis to run from 2026-10-31T22:30:00Z to 2026-11-01T14:25:00Z
- **THEN** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

#### Scenario: Dusk off the opening axis late in the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-11-01T01:00:00Z, and the user has not panned the strip
- **THEN** the strip's axis runs from 2026-10-31T21:00:00Z to 2026-11-01T12:55:00Z
- **AND** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

### Requirement: A now line marks the browser's time
The card SHALL draw a solid red `#e66767` line labelled `now` at the browser's current time, crossing every row from Sun altitude to Rain chance, the Moon up lane, every target lane and the Temperature chart. It SHALL draw the line only while that time is on the axis, from its start to its end.

#### Scenario: During the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T22:00:00Z
- **THEN** the strip has a line labelled `now` at 2026-10-31T22:00:00Z

#### Scenario: Before the axis starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has no now line

#### Scenario: The now line reaches the last target lane
- **WHEN** the browser's clock reads 2026-10-31T22:00:00Z, inside the axis, and Target 1 has a target tonight
- **THEN** the now line runs from the Sun altitude row, past the lane labelled `Target 1`, down to the bottom of the Temperature chart

### Requirement: Each row reads its timeline sensor
Each row but Cloud range SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_<key>`, named from the same slug as the Verdict sensor. The key SHALL be the row's name in lower case with `_` for each space, except that Rain chance reads `precipitation_probability`.

#### Scenario: Dew point
- **WHEN** the card is configured with `pier: Back-Yard` and `sensor.pierpressure_back_yard_dew_point` has a forecast inside the axis
- **THEN** the strip has no row labelled Dew point
- **AND** the Temperature chart draws its Dew point line from that forecast

#### Scenario: Rain chance reads Precipitation probability
- **WHEN** the card is configured with `pier: Back-Yard` and `sensor.pierpressure_back_yard_precipitation_probability` has a forecast inside the axis
- **THEN** the Rain chance row shows cells from that forecast

### Requirement: A Moon altitude or weather value fills its hour
In the Moon altitude, Wind gust, Seeing, Transparency, Humidity, Wind speed and Wind direction rows, each point in the sensor's `forecast` SHALL fill the hour that starts at its `datetime`, as one cell. The card SHALL draw a cell for every hour that overlaps the axis, and no cell for an hour wholly outside it. The card SHALL cut a cell off at an axis end, and that cell SHALL reach the axis end with no gap.

#### Scenario: Hours at the axis ends
- **WHEN** the axis runs from 16:30 UTC to 08:25 UTC the next day, and the Wind gust forecast has values at 15:00, 16:00, 17:00, 08:00 and 09:00 UTC
- **THEN** the Wind gust row has cells for 16:00, 17:00 and 08:00 UTC, and none for 15:00 or 09:00 UTC
- **AND** the 16:00 cell starts at the axis start, and the 08:00 cell ends at the axis end

### Requirement: Hovering over a cell shows its unit
Hovering over a cell in the Moon altitude, Wind gust, Seeing, Transparency, Humidity, Wind speed or Rain chance row SHALL show `<row>, the hour from <HH:MM>: <value><unit>`. The hour SHALL be the start of the hour the cell fills, and the value SHALL be as the forecast holds it. The unit SHALL be `°` for Moon altitude, ` km/h` for Wind gust and Wind speed, and `%` for Humidity and Rain chance. Seeing and Transparency SHALL show no unit. Values on the Temperature chart SHALL show ` °C`.

#### Scenario: A gusty hour
- **WHEN** Home Assistant's time zone is `UTC` and the Wind gust forecast holds 12.5 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Wind gust, the hour from 21:00: 12.5 km/h`

#### Scenario: A cold hour
- **WHEN** Home Assistant's time zone is `UTC`, the Temperature forecast holds 4.2 at 2026-10-31T21:00:00Z, and the Dew point forecast has no point there
- **THEN** hovering over that hour of the Temperature chart shows `The hour from 21:00: Temperature 4.2 °C`

#### Scenario: Seeing has no unit
- **WHEN** Home Assistant's time zone is `UTC` and the Seeing forecast holds 0.62 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Seeing, the hour from 21:00: 0.62`

#### Scenario: Rain chance names the hour it fills
- **WHEN** Home Assistant's time zone is `UTC` and the precipitation probability forecast holds 40 at 2026-10-31T22:00:00Z
- **THEN** hovering over that cell shows `Rain chance, the hour from 21:00: 40%`

### Requirement: The docs describe every row
`docs/night-card.md` SHALL describe each of the fourteen rows:

- its name and the sensor or sensors it reads;
- for each shaded row, what its lightest and darkest shades mean;
- that a Rain chance cell fills the hour before its time;
- that a Wind direction arrow points the way the wind blows to;
- what hovering over a cell shows, with its unit.

#### Scenario: The page covers every row
- **WHEN** `docs/night-card.md` is read
- **THEN** it names each of the fourteen rows and the sensors `sensor.pierpressure_<pier>_wind_gust` and `sensor.pierpressure_<pier>_precipitation_probability`
- **AND** it names the words hour before and blows to
- **AND** it no longer says that a later release adds the other conditions

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
- **THEN** the strip has no row labelled Temperature
- **AND** the Temperature chart's key shows `No forecast` beside `Temperature`

#### Scenario: Every hour on the axis is null
- **WHEN** every point of the Cloud low forecast inside the axis has the value `null`
- **THEN** the Cloud low row shows the message `No forecast` and no cells

#### Scenario: A forecast wholly off the axis
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z and the Humidity forecast holds values only on 2026-11-02
- **THEN** the Humidity row shows the message `No forecast`

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor and all seventeen timeline sensors have the state `unknown` and no attributes
- **THEN** each of the thirteen rows but Cloud range shows the message `No forecast`
- **AND** the strip has no Cloud range row

### Requirement: The strip pans as far as the forecast reaches
The user SHALL be able to pan the strip's axis earlier or later, inside the reach. The axis SHALL always be as long as the opening axis. The reach SHALL run from the start of the earliest timeline hour to the end of the latest, and SHALL always cover the opening axis.

#### Scenario: Panning past the last forecast hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only timeline sensor with a forecast, and its points run hourly from 2026-10-31T12:00:00Z to 2026-11-03T11:00:00Z
- **AND** the user pans later by more than three days
- **THEN** the strip's axis runs from 2026-11-02T20:05:00Z to 2026-11-03T12:00:00Z

#### Scenario: Panning past the first forecast hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only timeline sensor with a forecast, and its points run hourly from 2026-10-31T12:00:00Z to 2026-11-03T11:00:00Z
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis runs from 2026-10-31T12:00:00Z to 2026-11-01T03:55:00Z

#### Scenario: A forecast shorter than the opening axis
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and every timeline sensor's points lie between 2026-10-31T18:00:00Z and 2026-11-01T06:00:00Z
- **AND** the user pans later by an hour
- **THEN** the strip's axis still runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

### Requirement: The reach counts every row's forecast
A timeline hour SHALL be the hour that starts at the `datetime` of a point in the `forecast` of a row's sensor, the Cloud range row's two sensors and the Temperature chart's two sensors included. Every such point with a readable `datetime` SHALL count, whatever its value. A Rain chance point SHALL count only when it holds a number, and then for the hour before its time, the hour its cell fills. The reach SHALL leave out the forecast of a sensor that is `unavailable`.

#### Scenario: A Rain chance cell before the first hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the earliest point of any timeline sensor is a Rain chance point `{"datetime": "2026-10-31T12:00:00Z", "value": 20}`
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis starts at 2026-10-31T11:00:00Z

#### Scenario: A null Rain chance at the first hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, every timeline sensor's earliest point is at 2026-10-31T12:00:00Z, and the Rain chance point there is `{"datetime": "2026-10-31T12:00:00Z", "value": null}`
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis starts at 2026-10-31T12:00:00Z

#### Scenario: A null value still counts
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only timeline sensor with a forecast, and its last point is `{"datetime": "2026-11-02T11:00:00Z", "value": null}`
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-02T12:00:00Z

#### Scenario: An unavailable sensor's stale forecast
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover's points end at 2026-11-01T11:00:00Z, and the Seeing sensor is `unavailable` with points to 2026-11-03T11:00:00Z
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-01T12:00:00Z

#### Scenario: The dew point reaches furthest
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover's points end at 2026-11-01T11:00:00Z, and the Dew point forecast's points run to 2026-11-03T11:00:00Z
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-03T12:00:00Z

### Requirement: Dragging the strip pans it
A mouse drag or a touch swipe across the strip's rows, lanes and Temperature chart SHALL pan the axis as if the user moved the strip itself. Dragging to the left SHALL move the axis later, and dragging to the right SHALL move it earlier. The axis SHALL move by the same share of its length as the sideways distance is of the width the hours are drawn across. Dragging SHALL NOT select the strip's text.

#### Scenario: A drag to the left
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user drags the strip to the left by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A touch swipe to the right
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user swipes the strip to the right by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T00:00:00Z to 2026-11-02T00:00:00Z

#### Scenario: A drag on the Temperature chart
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user presses on the Temperature chart and drags to the left by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw for the new axis, by the rules of the opening axis, every row's cells, the Cloud range columns, the Moon up bars, the target bars, the Temperature chart's lines, dots and hover areas, the lines with their labels, and the time labels. The row and lane labels, and the Temperature chart's key and scale, SHALL stay put. Dusk and dawn lines and target bars come only from the windows Home Assistant holds, so a night other than the judged one has none.

#### Scenario: The next night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, the Cloud cover forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later
- **THEN** the strip's axis runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **AND** the Cloud cover row has a cell for each hour that overlaps that axis
- **AND** the strip has no dusk line and no dawn line, and the lane labelled `Target 1` has no bar
- **AND** the row labels read from `Sun altitude` to `Rain chance`, as before

#### Scenario: The Temperature chart on the next night
- **WHEN** the Temperature forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later, to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **THEN** the Temperature chart has a hover area for each hour that overlaps that axis
- **AND** its key and its scale labels are as before the pan

### Requirement: The Cloud range row shows only when two forecasts give cloud
The card SHALL leave the Cloud range row out of the strip, with no label, no track and no message, when all of these hold:

- Home Assistant has both `sensor.pierpressure_<slug>_cloud_cover_min` and `sensor.pierpressure_<slug>_cloud_cover_max`;
- neither sensor's state is `unavailable`;
- their forecasts have no paired hour.

A paired hour SHALL be a min point and a max point with the same `datetime` whose values are both numbers, in either order.

#### Scenario: One cloud provider
- **WHEN** both sensors are in Home Assistant and available, the Cloud cover forecast holds values inside the axis, and every point of both the min and the max forecast is null
- **THEN** the strip has no row labelled Cloud range
- **AND** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Humidity, Wind speed, Wind direction and Rain chance
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

### Requirement: The strip has fourteen labelled rows
The strip SHALL have fourteen rows, each labelled with its name, or thirteen when the Cloud range row is left out. Thirteen rows each read one timeline sensor, from Sun altitude to Precipitation probability. The Cloud range row reads the Cloud cover min and Cloud cover max sensors. The Temperature chart is not a row.

#### Scenario: The rows without Cloud range
- **WHEN** the Verdict sensor has the state `GO`, both Cloud range sensors are available with only null values, and Target 1 has a window from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z
- **THEN** the strip has thirteen rows, in the same order with Cloud range left out
- **AND** the lines overlay and the strip's grid end at the Temperature chart, under the Target 1 lane

### Requirement: The strip's rows run from Sun altitude to Rain chance
From top to bottom, the strip's rows SHALL be Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Humidity, Wind speed, Wind direction and Rain chance.

#### Scenario: The rows in order
- **WHEN** the card is configured with `pier: backyard`, the Verdict sensor has the state `GO`, and the Cloud cover min and max sensors hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Humidity, Wind speed, Wind direction and Rain chance

### Requirement: A missing Moon altitude or weather sensor leaves its row empty
This requirement covers the Moon altitude, Wind gust, Seeing, Transparency, Humidity, Wind speed, Wind direction and Rain chance rows. When a row's sensor is missing from Home Assistant or unavailable, the card SHALL draw that row with its label and no cells. The row SHALL show the message that says why. The card SHALL do the same when the sensor has no `forecast` list.

#### Scenario: Humidity is unavailable
- **WHEN** `sensor.pierpressure_backyard_humidity` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Humidity row with its label, no cells and the message `Unavailable`
- **AND** the cloud rows show their cells

### Requirement: Missing or unreadable Moon altitude or weather data does not stop the other rows
This requirement covers the Moon altitude, Wind gust, Seeing, Transparency, Humidity, Wind speed, Wind direction and Rain chance rows, and the Temperature chart. In these, the card SHALL skip a point without a readable `datetime`. Whether a sensor is missing, unavailable or has no `forecast` list, or a point has no readable `datetime`, the card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Only the sun and cloud sensors
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no timeline sensor but Sun altitude and the four cloud sensors
- **THEN** the card renders without an error
- **AND** every row but Sun altitude and the four cloud rows shows its label, no cells and the message `Not found`
- **AND** the Temperature chart's key shows `Not found` beside `Temperature` and beside `Dew point`

#### Scenario: A Temperature point with no readable time
- **WHEN** the Temperature forecast holds `{"datetime": "soon", "value": 4}` and 5 at 2026-10-31T21:00:00Z
- **THEN** the card renders without an error, and the Temperature line has one point, at 2026-10-31T21:30:00Z

### Requirement: The docs say darker is better for observing
Where `docs/night-card.md` says how to read the rows, it SHALL say that on every shaded row darker means better for observing, with no exception. It SHALL say that the Moon altitude shade ignores the moon's phase.

#### Scenario: The page reads darker as better
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words darker means better and phase
- **AND** it no longer says darker means worse
- **AND** its "How to read the rows" section no longer names an exception, or says darker is warmer

## REMOVED Requirements

### Requirement: Warmer is darker in Temperature and Dew point
**Reason**: Temperature and Dew point are no longer rows. The Temperature chart draws them as two lines, which show the gap between them, and every shaded row now reads darker as better for observing.
**Migration**: Read the two values from the Temperature chart under the target lanes. Hover over an hour to see both.

## RENAMED Requirements

- FROM: `### Requirement: The strip has sixteen labelled rows`
- TO: `### Requirement: The strip has fourteen labelled rows`
