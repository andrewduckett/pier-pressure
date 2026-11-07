## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: The card draws the four cloud rows
Below the verdict, score and confidence, the card SHALL draw a night strip. Under the strip's Moon altitude row, the card SHALL draw four cloud rows. From top to bottom they SHALL be Cloud cover, Cloud low, Cloud mid and Cloud high, each labelled with that name. Each row SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard` and the Verdict sensor has the state `GO`
- **THEN** the strip shows the rows Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid and Cloud high, in that order, at its top
- **AND** the four cloud rows read `sensor.pierpressure_back_yard_cloud_cover`, `sensor.pierpressure_back_yard_cloud_low`, `sensor.pierpressure_back_yard_cloud_mid` and `sensor.pierpressure_back_yard_cloud_high`

### Requirement: The card draws a Moon up lane
Under the strip's last row, Rain chance, the strip SHALL have a lane labelled Moon up. The lane SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_moon_altitude`, named from the same slug as the Verdict sensor. The lane SHALL keep its label on a night when the moon never rises.

#### Scenario: The lane and its sensor
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, and `sensor.pierpressure_back_yard_moon_altitude` holds values above 0 inside the axis
- **THEN** the strip's last lane is labelled Moon up, under Rain chance, and shows bars from that forecast

#### Scenario: The moon stays down
- **WHEN** every value in the moon altitude forecast is 0 or below
- **THEN** the strip shows the Moon up lane with its label and no bars

### Requirement: Dusk and dawn lines mark the dark window
When the axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`. Each line SHALL cross every row from Sun altitude to Rain chance, and the Moon up lane. When the axis falls back to the browser's current time, the card SHALL draw no dusk or dawn line.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line

### Requirement: A now line marks the browser's time
The card SHALL draw a solid red `#e66767` line labelled `now` at the browser's current time, crossing every row from Sun altitude to Rain chance, and the Moon up lane. It SHALL draw the line only while that time is on the axis, from its start to its end.

#### Scenario: During the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T22:00:00Z
- **THEN** the strip has a line labelled `now` at 2026-10-31T22:00:00Z

#### Scenario: Before the axis starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has no now line
