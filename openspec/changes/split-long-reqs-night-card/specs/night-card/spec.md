## ADDED Requirements

### Requirement: The card draws the night strip below the verdict
Below the verdict, score and confidence, the card SHALL draw a night strip.

#### Scenario: The strip comes after the verdict, score and confidence
- **WHEN** the Verdict sensor has the state `GO`
- **THEN** the strip comes after the verdict, score and confidence on the card

### Requirement: The cloud rows come under Moon altitude
Under the strip's Moon altitude row, the card SHALL draw the four cloud rows and, after Cloud cover, the Cloud range row, unless the Cloud range row is left out because no two forecasts give cloud. From top to bottom they SHALL be Cloud cover, Cloud range, Cloud low, Cloud mid and Cloud high, each labelled with that name.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, and the Cloud cover min and max sensors hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** the strip shows the rows Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid and Cloud high, in that order, at its top
- **AND** the four cloud rows read `sensor.pierpressure_back_yard_cloud_cover`, `sensor.pierpressure_back_yard_cloud_low`, `sensor.pierpressure_back_yard_cloud_mid` and `sensor.pierpressure_back_yard_cloud_high`

### Requirement: Each of the four cloud rows reads its cloud sensor
Each of the four cloud rows SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: Cloud high reads the sensor named from the pier
- **WHEN** the card is configured with `pier: Back-Yard`, and `sensor.pierpressure_back_yard_cloud_high` holds 40 at 2026-10-31T21:00:00Z
- **THEN** the Cloud high row has one cell, for the hour from 2026-10-31T21:00:00Z

### Requirement: The strip opens on the opening axis
The strip SHALL open on the opening axis. Until the user pans the strip, and after the user selects `Back to tonight`, the strip's time axis SHALL be the opening axis.

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor has the state `unknown`, no attributes, and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the card still draws the strip, with its axis from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

### Requirement: The opening axis is set from the dark window and the browser's clock
The opening axis SHALL start at the later of two times: 4 hours before the Verdict sensor's `dark_window.start`, and 4 hours before the browser's clock. This holds unless the opening axis falls back to the browser's clock. The opening axis SHALL be as long as the time from 4 hours before `dark_window.start` to 5 hours after `dark_window.end`, so before dusk it ends 5 hours after `dark_window.end`.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

#### Scenario: At dusk
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T20:30:00Z
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

#### Scenario: During the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T23:00:00Z
- **THEN** the strip's axis runs from 2026-10-31T19:00:00Z to 2026-11-01T10:55:00Z

#### Scenario: Late in the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-11-01T03:00:00Z
- **THEN** the strip's axis runs from 2026-10-31T23:00:00Z to 2026-11-01T14:55:00Z

#### Scenario: A verdict left over after dawn
- **WHEN** the Verdict sensor's `dark_window` is still `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the strip's axis runs from 2026-11-01T08:00:00Z to 2026-11-01T23:55:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}` and the browser's clock reads 2026-06-21T12:00:00Z
- **THEN** the strip's axis runs from 2026-06-21T06:00:00Z to 2026-06-22T06:00:00Z

#### Scenario: A window that ends before it starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-11-01T03:25:00Z, end: 2026-10-31T20:30:00Z}` and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the strip's axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

### Requirement: The opening axis moves on as the card redraws
As the card redraws, the opening axis SHALL follow the browser's clock.

#### Scenario: A minute passes during the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the user has not panned the strip, and the clock moves on by 60 seconds with no new state from Home Assistant
- **THEN** the strip's axis runs from 2026-10-31T19:01:00Z to 2026-11-01T10:56:00Z

### Requirement: The strip has sixteen labelled rows
The strip SHALL have sixteen rows, each labelled with its name, or fifteen when the Cloud range row is left out. Fifteen rows each read one timeline sensor, from Cloud cover to Precipitation probability. The Cloud range row reads the Cloud cover min and Cloud cover max sensors.

#### Scenario: The rows without Cloud range
- **WHEN** the Verdict sensor has the state `GO`, both Cloud range sensors are available with only null values, and Target 1 has a window from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z
- **THEN** the strip has fifteen rows, in the same order with Cloud range left out
- **AND** the lines overlay and the strip's grid end at the Target 1 lane

### Requirement: The strip's rows run from Sun altitude to Rain chance
From top to bottom, the strip's rows SHALL be Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance.

#### Scenario: The rows in order
- **WHEN** the card is configured with `pier: backyard`, the Verdict sensor has the state `GO`, and the Cloud cover min and max sensors hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** the strip's rows read, top to bottom, Sun altitude, Moon altitude, Cloud cover, Cloud range, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance

### Requirement: A missing Moon altitude or weather sensor leaves its row empty
This requirement covers the Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance rows. When a row's sensor is missing from Home Assistant or unavailable, the card SHALL draw that row with its label and no cells. The row SHALL show the message that says why. The card SHALL do the same when the sensor has no `forecast` list.

#### Scenario: Humidity is unavailable
- **WHEN** `sensor.pierpressure_backyard_humidity` has the state `unavailable` and a `forecast` attribute with values inside the axis, and the cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Humidity row with its label, no cells and the message `Unavailable`
- **AND** the cloud rows show their cells

### Requirement: A missing Moon altitude or weather sensor does not stop the other rows
This requirement covers the Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance rows. In these rows, the card SHALL skip a point without a readable `datetime`. When a row's sensor is missing, unavailable or has no `forecast` list, the card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Only the sun and cloud sensors
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has no timeline sensor but Sun altitude and the four cloud sensors
- **THEN** the card renders without an error
- **AND** every row but Sun altitude and the four cloud rows shows its label, no cells and the message `Not found`

### Requirement: A Cloud range row with no column shows the first cause that applies
When the Cloud range row is in the strip but would draw no column at all, the card SHALL show a message in its track. The message SHALL be the first of these that applies:

1. `Not found`, when Home Assistant has no entity with the min sensor's id, or else none with the max sensor's id.
2. `Unavailable`, when the min sensor's state is `unavailable`, or else the max sensor's.
3. `No forecast`, otherwise: the forecasts have a paired hour, but no readable pair on the hours of the axis.

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

### Requirement: A Cloud range row with a column shows no message
A Cloud range row that draws at least one column SHALL show no message.

#### Scenario: A Cloud range row with one column
- **WHEN** the min and max sensors hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** the Cloud range row has one column and shows no message

### Requirement: The card never says Needs two forecasts
The card SHALL NOT show the message `Needs two forecasts`.

#### Scenario: One cloud provider
- **WHEN** both sensors are in Home Assistant and available, and every point of both forecasts is null
- **THEN** the strip shows no Cloud range row, and so no Cloud range message
- **AND** the Cloud cover row shows its cells and no message

#### Scenario: Before the first verdict
- **WHEN** both sensors have the state `unknown` and no attributes
- **THEN** the strip shows no Cloud range row, and so no Cloud range message

### Requirement: The docs say what the Cloud range row reads and shows
Where `docs/night-card.md` describes the strip, it SHALL describe what the Cloud range row reads and shows:

- the two sensors it reads;
- that each range bar runs from the lowest to the highest cloud cover any forecast gives for the hour;
- that the row's height runs from 0% at the bottom to 100% at the top;
- that a tall range bar means the forecasts disagree;
- that an hour with fewer than two forecasts is blank;
- what hovering over an hour shows.

#### Scenario: The strip section covers the Cloud range row
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** it names Cloud range, `sensor.pierpressure_<pier>_cloud_cover_min` and `sensor.pierpressure_<pier>_cloud_cover_max`
- **AND** it names the words lowest, highest and disagree
- **AND** it says the row is left out with one cloud forecast, in the same paragraph as `No hour on the strip has cloud cover from two or more forecasts`

### Requirement: The docs say when the Cloud range row is left out
Where `docs/night-card.md` describes the strip, it SHALL describe when the Cloud range row is left out or has no column:

- that the strip leaves the row out when no hour of the forecast has cloud cover from two or more forecasts, as with the default providers, but keeps it to say `Not found` or `Unavailable`;
- that the row says `No forecast` when it is in the strip but no hour on the strip has two forecasts.

#### Scenario: The strip section says when the Cloud range row is left out
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** the paragraph that holds `No hour on the strip has cloud cover from two or more forecasts` says the strip leaves the row out

### Requirement: A panned strip keeps its start
After the user pans, the axis SHALL keep its start when Home Assistant sends new state and when the card redraws each minute.

#### Scenario: New state after a pan
- **WHEN** the user has panned the axis to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z, and Home Assistant sends new state with the same `dark_window` and forecasts
- **THEN** the strip's axis still runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z

#### Scenario: A minute passes after a pan
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the user has panned the axis to run from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z, and the browser's clock moves on by 60 seconds
- **THEN** the strip's axis still runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A new night of another length
- **WHEN** the user has panned the axis to start at 2026-11-01T16:30:00Z, and a new `dark_window` makes the opening axis 17 hours long, starting before 2026-11-01T16:30:00Z
- **THEN** the strip's axis starts at 2026-11-01T16:30:00Z and is 17 hours long

#### Scenario: A new pier
- **WHEN** the user has panned the axis 24 hours later, and the card's configuration changes to another pier
- **THEN** the strip's axis is the new pier's opening axis, and the card shows no `Back to tonight` button

### Requirement: A panned strip moves only as far as the reach needs
When the reach no longer holds a panned axis, the card SHALL move the axis only as far as it needs to stay inside the reach.

#### Scenario: The forecast moves on past the axis
- **WHEN** the user has panned the axis to start at 2026-10-31T12:00:00Z, and new state from Home Assistant makes the reach start at 2026-10-31T14:00:00Z
- **THEN** the strip's axis starts at 2026-10-31T14:00:00Z and is as long as the opening axis

### Requirement: A pan the reach stops entirely counts as no pan
A pan that the reach stops entirely SHALL count as no pan.

#### Scenario: A pan against the reach's start
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the browser's clock reads 2026-11-01T12:00:00Z, the reach starts at 2026-11-01T06:00:00Z, the user presses the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-11-01T06:01:00Z to 2026-11-02T06:01:00Z, and the card shows no `Back to tonight` button

### Requirement: A pan back to the opening axis counts as Back to tonight
A pan that brings the axis back to the opening axis SHALL count as selecting `Back to tonight`.

#### Scenario: Panning back by hand
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the browser's clock reads 2026-11-01T12:00:00Z, the reach runs further either way, the user presses the Right arrow key and then the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-11-01T06:01:00Z to 2026-11-02T06:01:00Z, and the card shows no `Back to tonight` button

### Requirement: The opening axis catches up with a later pan
A later pan is one that leaves the axis starting after the opening axis. When the opening axis moves on to or past the start of a later pan, the strip SHALL follow the opening axis again.

#### Scenario: The opening axis catches up with a pan
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the reach runs further either way, the user presses the Right arrow key with the strip focused, and the clock then moves on to 2026-11-01T00:01:00Z
- **THEN** the strip's axis runs from 2026-10-31T20:01:00Z to 2026-11-01T11:56:00Z, and the card shows no `Back to tonight` button

### Requirement: An earlier pan keeps its start as the opening axis moves on
An earlier pan is one that leaves the axis starting before the opening axis. An earlier pan SHALL keep its start as the opening axis moves away from it.

#### Scenario: A minute passes after a pan during the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the reach runs further either way, the user presses the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-10-31T18:00:00Z to 2026-11-01T09:55:00Z, and the card shows a `Back to tonight` button

## REMOVED Requirements

### Requirement: The card draws the four cloud rows
**Reason**: It stated three behaviors in more than 500 characters. It is split into "The card draws the night strip below the verdict", "The cloud rows come under Moon altitude" and "Each of the four cloud rows reads its cloud sensor". They keep all of its SHALL statements and its scenario.
**Migration**: None. Nothing changes for users or code: the card and its docs behave as before.

### Requirement: The strip spans the judged night
**Reason**: It stated three behaviors in more than 500 characters. It is split into "The strip opens on the opening axis", "The opening axis is set from the dark window and the browser's clock" and "The opening axis moves on as the card redraws". They keep all of its SHALL statements and all 9 of its scenarios.
**Migration**: None. Nothing changes for users or code: the card and its docs behave as before.

### Requirement: The card draws every timeline row
**Reason**: It stated two behaviors in more than 500 characters. It is split into "The strip has sixteen labelled rows" and "The strip's rows run from Sun altitude to Rain chance". They keep all of its SHALL statements and all 2 of its scenarios.
**Migration**: None. Nothing changes for users or code: the card and its docs behave as before.

### Requirement: A missing sensor leaves its row empty
**Reason**: It stated two behaviors in more than 500 characters. It is split into "A missing Moon altitude or weather sensor leaves its row empty" and "A missing Moon altitude or weather sensor does not stop the other rows". They keep all of its SHALL statements and all 2 of its scenarios.
**Migration**: None. Nothing changes for users or code: the card and its docs behave as before.

### Requirement: A Cloud range row with no column says why
**Reason**: It stated three behaviors in more than 500 characters. It is split into "A Cloud range row with no column shows the first cause that applies", "A Cloud range row with a column shows no message" and "The card never says Needs two forecasts". They keep all of its SHALL statements and all 6 of its scenarios.
**Migration**: None. Nothing changes for users or code: the card and its docs behave as before.

### Requirement: The docs describe the Cloud range row
**Reason**: It stated two behaviors in more than 500 characters. It is split into "The docs say what the Cloud range row reads and shows" and "The docs say when the Cloud range row is left out". They keep all of its SHALL statements and its scenario.
**Migration**: None. Nothing changes for users or code: the card and its docs behave as before.

### Requirement: The strip stays where the user panned it
**Reason**: It stated six behaviors in more than 500 characters. It is split into "A panned strip keeps its start", "A panned strip moves only as far as the reach needs", "A pan the reach stops entirely counts as no pan", "A pan back to the opening axis counts as Back to tonight", "The opening axis catches up with a later pan" and "An earlier pan keeps its start as the opening axis moves on". They keep all of its SHALL statements and all 9 of its scenarios.
**Migration**: None. Nothing changes for users or code: the card and its docs behave as before.
