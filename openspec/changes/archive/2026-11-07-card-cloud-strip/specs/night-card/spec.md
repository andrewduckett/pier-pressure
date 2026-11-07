## ADDED Requirements

### Requirement: The card draws the four cloud rows
Below the verdict, score and confidence, the card SHALL draw a night strip with four rows. From top to bottom they SHALL be Cloud cover, Cloud low, Cloud mid and Cloud high, each labelled with that name. Each row SHALL read the `forecast` attribute of one sensor, named from the same slug as the Verdict sensor: `sensor.pierpressure_<slug>_cloud_cover`, `sensor.pierpressure_<slug>_cloud_low`, `sensor.pierpressure_<slug>_cloud_mid` and `sensor.pierpressure_<slug>_cloud_high`.

#### Scenario: The rows and their sensors
- **WHEN** the card is configured with `pier: Back-Yard` and the Verdict sensor has the state `GO`
- **THEN** the strip shows the rows Cloud cover, Cloud low, Cloud mid and Cloud high, in that order
- **AND** they read `sensor.pierpressure_back_yard_cloud_cover`, `sensor.pierpressure_back_yard_cloud_low`, `sensor.pierpressure_back_yard_cloud_mid` and `sensor.pierpressure_back_yard_cloud_high`

### Requirement: The strip shows only with the verdict
The card SHALL draw the strip only when it shows the verdict, score and confidence. When the Verdict sensor is missing or unavailable, or Home Assistant has not yet given the card its state, the card SHALL draw no strip.

#### Scenario: PierPressure is offline
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable`
- **THEN** the card shows that PierPressure is offline and draws no strip

#### Scenario: A mistyped pier
- **WHEN** Home Assistant has no `sensor.pierpressure_frontyard_verdict` and the card is configured with `pier: frontyard`
- **THEN** the card names the missing entity and draws no strip

### Requirement: The strip spans the judged night
The strip's time axis SHALL run from 4 hours before the Verdict sensor's `dark_window.start` to 5 hours after its `dark_window.end`. The card SHALL fall back to an axis from 6 hours before the browser's current time to 18 hours after it in each of these cases:

- `dark_window`, its `start` or its `end` is missing, null or not a readable time;
- `end` is not after `start`;
- `end` is more than 48 hours after `start`.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}` and the browser's clock reads 2026-06-21T12:00:00Z
- **THEN** the strip's axis runs from 2026-06-21T06:00:00Z to 2026-06-22T06:00:00Z

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor has the state `unknown`, no attributes, and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the card still draws the strip, with its axis from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

#### Scenario: A window that ends before it starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-11-01T03:25:00Z, end: 2026-10-31T20:30:00Z}` and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the strip's axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

### Requirement: A value fills its hour
Each point in a cloud sensor's `forecast` SHALL fill the hour that starts at its `datetime`, as one cell in that sensor's row. The card SHALL draw a cell for every hour that overlaps the axis, and SHALL draw no cell for an hour wholly outside the axis. The card SHALL cut a cell off at an axis end, and that cell SHALL reach the axis end with no gap.

#### Scenario: Hours at the axis ends
- **WHEN** the axis runs from 16:30 UTC to 08:25 UTC the next day, and the Cloud cover forecast has points at 15:00, 16:00, 17:00, 08:00 and 09:00 UTC with values
- **THEN** the Cloud cover row has cells for 16:00, 17:00 and 08:00 UTC, and none for 15:00 or 09:00 UTC
- **AND** the 16:00 cell starts at the axis start, and the 08:00 cell ends at the axis end

### Requirement: More cloud is darker
The card SHALL shade each cell in one of seven blues, the YAML night strip's shades. From lightest to darkest they are `#cde2fb`, `#9ec5f4`, `#6da7ec`, `#3987e5`, `#256abf`, `#184f95` and `#0d366b`. A value `v` in percent SHALL take shade step `min(6, floor(v / 15))`, where step 0 is the lightest.

#### Scenario: Clear and overcast
- **WHEN** the Cloud cover forecast holds 0 at one hour, 44 at another and 100 at a third
- **THEN** the cells are shaded `#cde2fb`, `#6da7ec` and `#0d366b`

### Requirement: A null hour is blank
The card SHALL draw no cell for an hour whose `forecast` value is null or not a number, or for an hour the forecast has no point for. That hour SHALL be blank in its row, distinct from every shade a value can take.

#### Scenario: Cloud low missing for an hour
- **WHEN** the Cloud low forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Cloud low row has no cell for 22:00 UTC

#### Scenario: Cloud mid at zero
- **WHEN** the Cloud mid forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": 0}` inside the axis
- **THEN** the Cloud mid row has a 22:00 UTC cell shaded `#cde2fb`

### Requirement: A missing cloud sensor leaves an empty row
The card SHALL draw a cloud sensor's row with its label and no cells when that sensor is missing from Home Assistant or unavailable. It SHALL do the same when the sensor has no `forecast` attribute, or its `forecast` is not a list. The card SHALL skip a point in `forecast` without a readable `datetime`. The card SHALL NOT throw, and SHALL draw the other rows as usual.

#### Scenario: Cloud high is unavailable
- **WHEN** `sensor.pierpressure_backyard_cloud_high` has the state `unavailable` and no attributes, and the other three cloud sensors have forecasts inside the axis
- **THEN** the strip shows the Cloud high row with its label and no cells
- **AND** the other three rows show their cells

#### Scenario: An unavailable sensor that kept its forecast
- **WHEN** `sensor.pierpressure_backyard_cloud_high` has the state `unavailable` and a `forecast` attribute with values inside the axis
- **THEN** the strip shows the Cloud high row with its label and no cells

#### Scenario: No cloud sensors at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has none of the four cloud sensors
- **THEN** the card renders without an error and shows the four labelled rows with no cells

### Requirement: Hovering over a cell shows its value
Hovering over a cell SHALL show the row's name, the start of the cell's hour, and the value with `%`, as `<row>, the hour from <HH:MM>: <value>%`. The card SHALL show the value as the forecast holds it.

#### Scenario: A cloudy hour
- **WHEN** Home Assistant's time zone is `UTC` and the Cloud cover forecast holds 40 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Cloud cover, the hour from 21:00: 40%`

### Requirement: The strip shows times in Home Assistant's time zone
The strip SHALL show every time in Home Assistant's configured time zone, whatever time zone the browser or the user profile uses. It SHALL write each time on a 24-hour clock as `HH:MM`, in the digits `0` to `9`, whatever the browser's language.

#### Scenario: Hover in Tokyo
- **WHEN** Home Assistant's time zone is `Asia/Tokyo` and the Cloud cover forecast holds 40 at 2026-10-31T12:00:00Z
- **THEN** hovering over that cell shows `Cloud cover, the hour from 21:00: 40%`

#### Scenario: A browser in Arabic
- **WHEN** the browser's language is `ar-EG`, Home Assistant's time zone is `UTC`, and the Cloud cover forecast holds 40 at 2026-10-31T21:00:00Z
- **THEN** hovering over that cell shows `Cloud cover, the hour from 21:00: 40%`

### Requirement: The axis carries time labels
The axis SHALL carry a time label at each whole hour strictly between its start and its end, in Home Assistant's time zone, whose hour is a multiple of 3. When the axis spans more than 24 hours, the card SHALL label only the hours that are a multiple of 6. When a clock change makes two such instants show the same time, the card SHALL label only the first.

#### Scenario: Axis labels in UTC
- **WHEN** Home Assistant's time zone is `UTC` and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the axis labels read `18:00`, `21:00`, `00:00`, `03:00` and `06:00`, in that order

#### Scenario: Axis labels in a half-hour time zone
- **WHEN** Home Assistant's time zone is `Asia/Kolkata` and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the axis labels read `00:00`, `03:00`, `06:00`, `09:00` and `12:00`, in that order, the first at 2026-10-31T18:30:00Z

#### Scenario: Polar night
- **WHEN** Home Assistant's time zone is `UTC` and the axis runs from 2026-12-20T07:00:00Z to 2026-12-21T16:00:00Z
- **THEN** the axis labels read `12:00`, `18:00`, `00:00`, `06:00` and `12:00`, in that order

#### Scenario: Clocks go back
- **WHEN** Home Assistant's time zone is `Europe/Athens` and the axis runs from 2026-10-24T18:00:00Z to 2026-10-25T09:00:00Z
- **THEN** the axis shows exactly one label that reads `03:00`, at 2026-10-25T00:00:00Z

### Requirement: The docs describe the cloud rows
`docs/night-card.md` SHALL describe the strip's cloud rows:

- the four rows and the sensors they read;
- the axis span, and its fallback on a night with no astronomical darkness;
- the shades from clear to overcast;
- blank hours;
- what hovering over a cell shows;
- that times are in Home Assistant's time zone.

#### Scenario: The page covers the strip
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the rows Cloud cover, Cloud low, Cloud mid and Cloud high, and the sensor `sensor.pierpressure_<pier>_cloud_cover`
- **AND** it says the strip runs from 4 hours before dusk to 5 hours after dawn, and from 6 hours before now to 18 hours after on a night with no astronomical darkness
- **AND** it names the words clear, overcast, blank, hover and time zone
