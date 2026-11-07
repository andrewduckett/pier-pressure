## ADDED Requirements

### Requirement: The Cloud range row reads the cloud cover min and max sensors
The Cloud range row SHALL read the `forecast` attributes of `sensor.pierpressure_<slug>_cloud_cover_min` and `sensor.pierpressure_<slug>_cloud_cover_max`, named from the same slug as the Verdict sensor. It SHALL pair the two forecasts' points by their `datetime`.

#### Scenario: A pier id with a capital and a dash
- **WHEN** the card is configured with `pier: Back-Yard`, and `sensor.pierpressure_back_yard_cloud_cover_min` and `sensor.pierpressure_back_yard_cloud_cover_max` hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** the Cloud range row has one bar, for the hour from 2026-10-31T21:00:00Z

### Requirement: A Cloud range bar spans the lowest to the highest cloud
For each hour where both forecasts hold a number, the Cloud range row SHALL draw one bar. The bar SHALL fill the hour that starts at the points' `datetime` across the row, cut off at an axis end as a cell is, and SHALL draw nothing for an hour wholly outside the axis. Up the row, the row's height SHALL stand for 0 to 100% cloud, with 0 at the bottom. The bar SHALL run from the lower of the two values to the higher. A value below 0 or above 100 SHALL be drawn at 0 or 100.

#### Scenario: Forecasts that disagree
- **WHEN** the min forecast holds 40 and the max forecast holds 70 at 2026-10-31T21:00:00Z
- **THEN** the bar for that hour starts 40% of the way up the row and ends 70% of the way up

#### Scenario: Hours at the axis ends
- **WHEN** the axis runs from 16:30 UTC to 08:25 UTC the next day, and both forecasts have values at 15:00, 16:00 and 09:00 UTC
- **THEN** the Cloud range row has a bar for 16:00 UTC, which starts at the axis start, and none for 15:00 or 09:00 UTC

### Requirement: Forecasts that agree still draw a bar
When an hour's two values are equal, the Cloud range bar SHALL still show, as a line at least 2 px tall at that level.

#### Scenario: Two forecasts give 40%
- **WHEN** the min and max forecasts both hold 40 at 2026-10-31T21:00:00Z
- **THEN** the Cloud range row has a bar for that hour at 40% of the way up the row, at least 2 px tall

### Requirement: An hour without both values has no Cloud range bar
The Cloud range row SHALL draw no bar for an hour where either forecast has no point, a null value or a value that is not a number.

#### Scenario: One forecast for the hour
- **WHEN** the min and max forecasts both hold null at 2026-10-31T22:00:00Z and numbers at 2026-10-31T21:00:00Z
- **THEN** the Cloud range row has a bar for 21:00 UTC and none for 22:00 UTC

#### Scenario: A min with no max
- **WHEN** the min forecast holds 40 at 2026-10-31T21:00:00Z and the max forecast has no point at that time
- **THEN** the Cloud range row has no bar for that hour

### Requirement: Hovering over a Cloud range bar shows both values
Hovering over a Cloud range bar SHALL show `Cloud range, the hour from <HH:MM>: <low>% to <high>%`, with the values as the forecasts hold them, lower first.

#### Scenario: Forecasts that disagree
- **WHEN** Home Assistant's time zone is `UTC` and the min and max forecasts hold 40 and 70.5 at 2026-10-31T21:00:00Z
- **THEN** hovering over that bar shows `Cloud range, the hour from 21:00: 40% to 70.5%`

### Requirement: A Cloud range row with no bar says why
When the Cloud range row would draw no bar at all, the card SHALL show a message in its track. The message SHALL be the first of these that applies:

1. `Not found`, when Home Assistant has no entity with the min sensor's id, or else none with the max sensor's id.
2. `Unavailable`, when the min sensor's state is `unavailable`, or else the max sensor's.
3. `Needs two forecasts`, otherwise.

A Cloud range row that draws at least one bar SHALL show no message.

#### Scenario: One cloud provider
- **WHEN** both sensors are in Home Assistant and available, and every point of both forecasts inside the axis is null
- **THEN** the Cloud range row shows the message `Needs two forecasts` and no bars
- **AND** the Cloud cover row shows its cells and no message

#### Scenario: The max sensor is not there
- **WHEN** the min sensor has values inside the axis and Home Assistant has no `sensor.pierpressure_backyard_cloud_cover_max`
- **THEN** the Cloud range row shows the message `Not found`

#### Scenario: The min sensor is unavailable
- **WHEN** `sensor.pierpressure_backyard_cloud_cover_min` has the state `unavailable` and a `forecast` attribute with values inside the axis
- **THEN** the Cloud range row shows the message `Unavailable`

#### Scenario: Before the first verdict
- **WHEN** both sensors have the state `unknown` and no attributes
- **THEN** the Cloud range row shows the message `Needs two forecasts`

### Requirement: Hovering over the Cloud range message says what it needs
Hovering over the Cloud range row's message SHALL show:

- `<entity id> is not in Home Assistant` for `Not found`, naming the sensor that is missing;
- `<entity id> is unavailable` for `Unavailable`, naming the sensor that is unavailable;
- `No hour on the strip has cloud cover from two or more forecasts` for `Needs two forecasts`.

#### Scenario: The max sensor is not there
- **WHEN** the min sensor is in Home Assistant and there is no `sensor.pierpressure_backyard_cloud_cover_max`
- **THEN** hovering over the Cloud range row's message shows `sensor.pierpressure_backyard_cloud_cover_max is not in Home Assistant`

#### Scenario: One cloud provider
- **WHEN** the Cloud range row shows `Needs two forecasts`
- **THEN** hovering over the message shows `No hour on the strip has cloud cover from two or more forecasts`

### Requirement: The docs describe the Cloud range row
Where `docs/night-card.md` describes the strip, it SHALL describe the Cloud range row:

- the two sensors it reads;
- that each bar runs from the lowest to the highest cloud cover any forecast gives for the hour, on a scale from 0% at the bottom of the row to 100% at the top;
- that a tall bar means the forecasts disagree;
- that an hour with fewer than two forecasts is blank;
- what hovering over a bar shows;
- the message `Needs two forecasts`.

#### Scenario: The strip section covers the Cloud range row
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** it names Cloud range, `sensor.pierpressure_<pier>_cloud_cover_min`, `sensor.pierpressure_<pier>_cloud_cover_max` and `Needs two forecasts`
- **AND** it names the words lowest, highest and disagree

### Requirement: The docs say how to fill the Cloud range row
The "If something looks wrong" section of `docs/night-card.md` SHALL say that `Needs two forecasts` means fewer than two providers in the pier's `providers` setting give cloud cover for the hours on the strip, and that adding a second provider that gives cloud cover, such as an Open-Meteo model, fills the row.

#### Scenario: The troubleshooting section covers Needs two forecasts
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** it names `Needs two forecasts`, the `providers` setting and Open-Meteo

## MODIFIED Requirements

### Requirement: The card draws every timeline row
The strip SHALL have sixteen rows, each labelled with its name: one per timeline sensor from Sun altitude to Precipitation probability, and the Cloud range row, which reads the two cloud range sensors. From top to bottom they SHALL be Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance.

#### Scenario: The rows in order
- **WHEN** the card is configured with `pier: backyard` and the Verdict sensor has the state `GO`
- **THEN** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance

### Requirement: Each row reads its timeline sensor
Each row but Cloud range SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_<key>`, named from the same slug as the Verdict sensor. The key SHALL be the row's name in lower case with `_` for each space, except that Rain chance reads `precipitation_probability`.

#### Scenario: Dew point
- **WHEN** the card is configured with `pier: Back-Yard` and `sensor.pierpressure_back_yard_dew_point` has a forecast inside the axis
- **THEN** the Dew point row shows cells from that forecast

#### Scenario: Rain chance reads Precipitation probability
- **WHEN** the card is configured with `pier: Back-Yard` and `sensor.pierpressure_back_yard_precipitation_probability` has a forecast inside the axis
- **THEN** the Rain chance row shows cells from that forecast

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
- **AND** the Cloud range row shows the message `Needs two forecasts`

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

### Requirement: The docs describe the row messages and the darkness note
Where `docs/night-card.md` describes the strip, it SHALL describe:

- the row messages `Not found`, `Unavailable`, `No forecast` and `Needs two forecasts`, and what each means;
- that hovering over a message names the sensor;
- that the Moon up lane repeats the Moon altitude row's message;
- the note `No astronomical darkness tonight`.

#### Scenario: The strip section covers the messages
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** it names `Not found`, `Unavailable`, `No forecast`, `Needs two forecasts` and `No astronomical darkness tonight`
- **AND** it names the words hover and Moon up in the same paragraph as `No forecast`

### Requirement: The docs say what to do when something is missing
The "If something looks wrong" section of `docs/night-card.md` SHALL say what to do when the card shows each of these:

- `PierPressure is offline`;
- `No PierPressure verdict found`;
- a row that says `Not found`, `Unavailable`, `No forecast` or `Needs two forecasts`;
- `No astronomical darkness tonight`.

#### Scenario: The troubleshooting section covers the missing cases
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** it names `PierPressure is offline`, `No PierPressure verdict found`, `Not found`, `Unavailable`, `No forecast`, `Needs two forecasts` and `No astronomical darkness tonight`
