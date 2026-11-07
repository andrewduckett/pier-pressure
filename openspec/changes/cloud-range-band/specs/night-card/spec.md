## ADDED Requirements

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
- **WHEN** the min forecast holds 40 at 2026-10-31T21:00:00Z and the max forecast has no point at that time
- **THEN** the Cloud range row has no column for that hour

#### Scenario: A min above the max
- **WHEN** the min forecast holds 70 and the max forecast holds 20 at 2026-10-31T21:00:00Z
- **THEN** the Cloud range row has no column for that hour

### Requirement: Hovering over a Cloud range column shows both values
Hovering over a Cloud range column SHALL show `Cloud range, the hour from <HH:MM>: <min>% to <max>%`, with the values as the forecasts hold them.

#### Scenario: Forecasts that disagree
- **WHEN** Home Assistant's time zone is `UTC` and the min and max forecasts hold 40 and 70.5 at 2026-10-31T21:00:00Z
- **THEN** hovering over that column shows `Cloud range, the hour from 21:00: 40% to 70.5%`

### Requirement: A Cloud range row with no column says why
When the Cloud range row would draw no column at all, the card SHALL show a message in its track. The message SHALL be the first of these that applies:

1. `Not found`, when Home Assistant has no entity with the min sensor's id, or else none with the max sensor's id.
2. `Unavailable`, when the min sensor's state is `unavailable`, or else the max sensor's.
3. `Needs two forecasts`, otherwise.

A Cloud range row that draws at least one column SHALL show no message.

#### Scenario: One cloud provider
- **WHEN** both sensors are in Home Assistant and available, and every point of both forecasts inside the axis is null
- **THEN** the Cloud range row shows the message `Needs two forecasts` and no columns
- **AND** the Cloud cover row shows its cells and no message

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
- that each range bar runs from the lowest to the highest cloud cover any forecast gives for the hour;
- that the row's height runs from 0% at the bottom to 100% at the top;
- that a tall range bar means the forecasts disagree;
- that an hour with fewer than two forecasts is blank;
- what hovering over an hour shows;
- the message `Needs two forecasts`.

#### Scenario: The strip section covers the Cloud range row
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** it names Cloud range, `sensor.pierpressure_<pier>_cloud_cover_min`, `sensor.pierpressure_<pier>_cloud_cover_max` and `Needs two forecasts`
- **AND** it names the words lowest, highest and disagree

### Requirement: The docs say how to fill the Cloud range row
For `Needs two forecasts`, the "If something looks wrong" section of `docs/night-card.md` SHALL name two causes. Either fewer than two providers in the `providers` list under `conditions` give cloud cover, or a listed cloud provider failed. For the first, it SHALL say that adding a provider that gives cloud cover, such as an Open-Meteo model, fills the row. For the second, it SHALL point to the provider's health sensor.

#### Scenario: The troubleshooting section covers Needs two forecasts
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** it names `Needs two forecasts`, `conditions`, `providers`, Open-Meteo and the word health in the same list item

## MODIFIED Requirements

### Requirement: The card draws the four cloud rows
Below the verdict, score and confidence, the card SHALL draw a night strip. Under the strip's Moon altitude row, the card SHALL draw the four cloud rows and, after Cloud cover, the Cloud range row. From top to bottom they SHALL be Cloud cover, Cloud range, Cloud low, Cloud mid and Cloud high, each labelled with that name. Each cloud row SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard` and the Verdict sensor has the state `GO`
- **THEN** the strip shows the rows Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid and Cloud high, in that order, at its top
- **AND** the four cloud rows read `sensor.pierpressure_back_yard_cloud_cover`, `sensor.pierpressure_back_yard_cloud_low`, `sensor.pierpressure_back_yard_cloud_mid` and `sensor.pierpressure_back_yard_cloud_high`

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

### Requirement: The card draws every timeline row
The strip SHALL have sixteen rows, each labelled with its name. Fifteen rows each read one timeline sensor, from Cloud cover to Precipitation probability. The Cloud range row reads the Cloud cover min and Cloud cover max sensors. From top to bottom they SHALL be Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance.

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
- that hovering over `Not found`, `Unavailable` or `No forecast` names the sensor, and hovering over `Needs two forecasts` says what the row needs;
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
