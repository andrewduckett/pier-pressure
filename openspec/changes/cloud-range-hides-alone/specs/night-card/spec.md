## ADDED Requirements

### Requirement: The Cloud range row shows only when two forecasts give cloud
The card SHALL leave the Cloud range row out of the strip, with no label, no track and no message, when Home Assistant has both `sensor.pierpressure_<slug>_cloud_cover_min` and `sensor.pierpressure_<slug>_cloud_cover_max`, neither is `unavailable`, and their forecasts hold no readable pair. A readable pair SHALL be a min point and a max point with the same `datetime`, both numbers, with the min not above the max.

#### Scenario: One cloud provider
- **WHEN** both sensors are in Home Assistant and available, the Cloud cover forecast holds values inside the axis, and every point of both the min and the max forecast is null
- **THEN** the strip has no row labelled Cloud range
- **AND** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance
- **AND** the Cloud cover row shows its cells and no message

#### Scenario: Every pair has its min above its max
- **WHEN** both sensors are available and every hour where both forecasts hold a number has a min value above its max value
- **THEN** the strip has no row labelled Cloud range

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
The card SHALL look for a readable pair in every point of both forecasts, not only the hours on the axis. Panning the strip SHALL never add or remove the Cloud range row.

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

## MODIFIED Requirements

### Requirement: The card draws the four cloud rows
Below the verdict, score and confidence, the card SHALL draw a night strip. Under the strip's Moon altitude row, the card SHALL draw the four cloud rows and, after Cloud cover, the Cloud range row, unless the Cloud range row is left out because no two forecasts give cloud. From top to bottom they SHALL be Cloud cover, Cloud range, Cloud low, Cloud mid and Cloud high, each labelled with that name. Each cloud row SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard` and the Verdict sensor has the state `GO`
- **THEN** the strip shows the rows Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid and Cloud high, in that order, at its top
- **AND** the four cloud rows read `sensor.pierpressure_back_yard_cloud_cover`, `sensor.pierpressure_back_yard_cloud_low`, `sensor.pierpressure_back_yard_cloud_mid` and `sensor.pierpressure_back_yard_cloud_high`

### Requirement: The card draws every timeline row
The strip SHALL have sixteen rows, each labelled with its name, or fifteen when the Cloud range row is left out. Fifteen rows each read one timeline sensor, from Cloud cover to Precipitation probability. The Cloud range row reads the Cloud cover min and Cloud cover max sensors. From top to bottom they SHALL be Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance.

#### Scenario: The rows in order
- **WHEN** the card is configured with `pier: backyard` and the Verdict sensor has the state `GO`
- **THEN** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance

#### Scenario: The rows without Cloud range
- **WHEN** the Verdict sensor has the state `GO`, and both Cloud range sensors are available with only null values
- **THEN** the strip has fifteen rows, in the same order with Cloud range left out
- **AND** the lines overlay and the strip's grid end at the last target lane, as they do with sixteen rows

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

### Requirement: A Cloud range row with no column says why
When the Cloud range row is in the strip but would draw no column at all, the card SHALL show a message in its track. The message SHALL be the first of these that applies:

1. `Not found`, when Home Assistant has no entity with the min sensor's id, or else none with the max sensor's id.
2. `Unavailable`, when the min sensor's state is `unavailable`, or else the max sensor's.
3. `No forecast`, otherwise: the forecasts have a readable pair, but none on the hours of the axis.

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

## REMOVED Requirements

### Requirement: The docs say how to fill the Cloud range row
**Reason**: The card no longer shows `Needs two forecasts`. It leaves the Cloud range row out instead.
**Migration**: "The docs say how to bring back the Cloud range row" names the same two causes for a strip with no Cloud range row.
