## MODIFIED Requirements

### Requirement: The card draws the four cloud rows
Below the verdict, score and confidence, the card SHALL draw a night strip. Under the strip's Sun altitude row, the card SHALL draw four cloud rows. From top to bottom they SHALL be Cloud cover, Cloud low, Cloud mid and Cloud high, each labelled with that name. Each row SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard` and the Verdict sensor has the state `GO`
- **THEN** the strip shows the rows Sun altitude, Cloud cover, Cloud low, Cloud mid and Cloud high, in that order
- **AND** the four cloud rows read `sensor.pierpressure_back_yard_cloud_cover`, `sensor.pierpressure_back_yard_cloud_low`, `sensor.pierpressure_back_yard_cloud_mid` and `sensor.pierpressure_back_yard_cloud_high`

### Requirement: Hovering over a cell shows its value
Hovering over a cell in a cloud row SHALL show the row's name, the start of the cell's hour, and the value with `%`, as `<row>, the hour from <HH:MM>: <value>%`. The card SHALL show the value as the forecast holds it.

#### Scenario: A cloudy hour
- **WHEN** Home Assistant's time zone is `UTC` and the Cloud cover forecast holds 40 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Cloud cover, the hour from 21:00: 40%`

## ADDED Requirements

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
Under the four cloud rows, the strip SHALL have a lane labelled Moon up. The lane SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_moon_altitude`, named from the same slug as the Verdict sensor. The lane SHALL keep its label on a night when the moon never rises.

#### Scenario: The lane and its sensor
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, and `sensor.pierpressure_back_yard_moon_altitude` holds values above 0 inside the axis
- **THEN** the strip's last lane is labelled Moon up, under Cloud high, and shows bars from that forecast

#### Scenario: The moon stays down
- **WHEN** every value in the moon altitude forecast is 0 or below
- **THEN** the strip shows the Moon up lane with its label and no bars

### Requirement: A Moon up bar spans each run of hours the moon is up
The card SHALL draw one grey `#898781` bar for each run of consecutive hours whose moon altitude is above 0. A bar SHALL run from the start of the run's first hour to the end of its last hour. A value of 0 or below, a null value, a value that is not a number, or an hour with no point SHALL end a run. The card SHALL cut a bar off at an axis end, and draw no bar for a run wholly outside the axis.

#### Scenario: Three runs
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the moon altitude forecast holds 4 at 16:00, 6 at 17:00, −1 at 18:00, 2 at 19:00, 8 at 20:00, null at 21:00, 12 at 22:00 and 0 at 23:00 UTC on 2026-10-31
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
Hovering over a Moon up bar SHALL show `Moon up from <HH:MM> to <HH:MM>`: the start of the run's first hour and the end of its last hour, even where the axis cuts the bar off.

#### Scenario: A bar cut off at the axis start
- **WHEN** Home Assistant's time zone is `UTC`, the axis starts at 2026-10-31T16:30:00Z, and the moon altitude forecast holds 4 at 16:00 and 6 at 17:00 UTC, then −1 at 18:00
- **THEN** hovering over the bar shows `Moon up from 16:00 to 18:00`

### Requirement: Dusk and dawn lines mark the dark window
When the axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`. Each line SHALL cross the Sun altitude row, the cloud rows and the Moon up lane. When the axis falls back to the browser's current time, the card SHALL draw no dusk or dawn line.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line

### Requirement: A now line marks the browser's time
The card SHALL draw a solid red `#e66767` line labelled `now` at the browser's current time, crossing the Sun altitude row, the cloud rows and the Moon up lane. It SHALL draw the line only while that time is on the axis, from its start to its end.

#### Scenario: During the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T22:00:00Z
- **THEN** the strip has a line labelled `now` at 2026-10-31T22:00:00Z

#### Scenario: Before the axis starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has no now line

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
- the Moon up lane and its sensor;
- the dusk and dawn lines, and that they are missing on a night with no astronomical darkness;
- the now line, and that it moves every minute.

#### Scenario: The page covers the night axis
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the Sun altitude row, the sensors `sensor.pierpressure_<pier>_sun_altitude` and `sensor.pierpressure_<pier>_moon_altitude`, and the Moon up lane
- **AND** it names the words civil, nautical, astronomical, start of the hour, dusk, dawn, now and every minute
- **AND** it no longer says that a later release adds dusk, dawn and the moon
