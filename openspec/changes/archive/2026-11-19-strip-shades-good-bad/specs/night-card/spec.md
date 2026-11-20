## RENAMED Requirements

- FROM: `### Requirement: More cloud is darker`
- TO: `### Requirement: Less cloud is darker`

- FROM: `### Requirement: The Moon altitude row darkens as the moon climbs`
- TO: `### Requirement: The Moon altitude row pales as the moon climbs`

- FROM: `### Requirement: More wind is darker`
- TO: `### Requirement: Less wind is darker`

- FROM: `### Requirement: Worse seeing and transparency are darker`
- TO: `### Requirement: Better seeing and transparency are darker`

- FROM: `### Requirement: More humidity and rain chance is darker`
- TO: `### Requirement: Less humidity and rain chance is darker`

## MODIFIED Requirements

### Requirement: Less cloud is darker
The card SHALL shade each cell in a cloud row in one of seven blues. From darkest to lightest they are `#0d366b`, `#184f95`, `#256abf`, `#3987e5`, `#6da7ec`, `#9ec5f4` and `#cde2fb`. A value `v` in percent SHALL take shade step `min(6, max(0, floor(v / 15)))`, where step 0 is the darkest. So a clearer hour is darker.

#### Scenario: Clear and overcast
- **WHEN** the Cloud cover forecast holds 0 at one hour, 44 at another and 100 at a third
- **THEN** the cells are shaded `#0d366b`, `#256abf` and `#cde2fb`

#### Scenario: The step edges
- **WHEN** the Cloud cover forecast holds 14, 15, 89 and 90 at four hours inside the axis
- **THEN** the cells are shaded `#0d366b`, `#184f95`, `#9ec5f4` and `#cde2fb`

#### Scenario: Values outside 0 to 100
- **WHEN** the Cloud cover forecast holds −5 at one hour and 120 at another
- **THEN** the cells are shaded `#0d366b` and `#cde2fb`

### Requirement: A null hour is blank
The card SHALL draw no cell for an hour whose `forecast` value is null or not a number, or for an hour the forecast has no point for. That hour SHALL be blank in its row, distinct from every shade or arrow a value can take.

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
- **THEN** the Temperature row has a 22:00 UTC cell

#### Scenario: Wind direction missing for an hour
- **WHEN** the Wind direction forecast holds `{"datetime": "2026-10-31T22:00:00Z", "value": null}` inside the axis
- **THEN** the Wind direction row has no cell and no arrow for 22:00 UTC

### Requirement: The Moon altitude row pales as the moon climbs
The card SHALL shade each Moon altitude cell in the strip's seven blues, from darkest to lightest `#0d366b`, `#184f95`, `#256abf`, `#3987e5`, `#6da7ec`, `#9ec5f4` and `#cde2fb`, step 0 the darkest. An altitude `v` of 0° or below SHALL take step 0. An altitude above 0° SHALL take step `min(6, 1 + floor(v / 6))`. The shade SHALL depend on the altitude alone, not on the moon's illumination.

#### Scenario: From set to high
- **WHEN** the Moon altitude forecast holds −10, 0, 3, 6, 12, 18, 24, 30 and 60 at nine hours inside the axis
- **THEN** the cells are shaded `#0d366b`, `#0d366b`, `#184f95`, `#256abf`, `#3987e5`, `#6da7ec`, `#9ec5f4`, `#cde2fb` and `#cde2fb`

#### Scenario: A new moon and a full moon
- **WHEN** the Moon altitude forecast holds 12 at an hour inside the axis, once with `moon.illumination` `0` and once with `moon.illumination` `1`
- **THEN** the cell is shaded `#3987e5` both times

### Requirement: Less wind is darker
The card SHALL shade each Wind gust and Wind speed cell in the strip's seven blues, step 0 the darkest. A speed `v` in km/h SHALL take step `min(6, max(0, floor(v / 7)))`, so under 7 km/h is the darkest and 42 km/h or more the lightest.

#### Scenario: Calm to gale
- **WHEN** the Wind gust forecast holds 0, 6.9, 7, 41 and 42 at five hours inside the axis
- **THEN** the cells are shaded `#0d366b`, `#0d366b`, `#184f95`, `#9ec5f4` and `#cde2fb`

#### Scenario: Wind speed on the same scale
- **WHEN** the Wind speed forecast holds 21 at an hour inside the axis
- **THEN** the cell is shaded `#3987e5`

### Requirement: Better seeing and transparency are darker
The card SHALL shade each Seeing and Transparency cell in the strip's seven blues, step 0 the darkest. A quality `q` from 0 to 1, where 1 is best, SHALL take step `min(6, max(0, round((1 − q) × 7)))`, where a half rounds up. So darker means better.

#### Scenario: Excellent to poor
- **WHEN** the Seeing forecast holds 1, 0.8, 0.5 and 0 at four hours inside the axis
- **THEN** the cells are shaded `#0d366b`, `#184f95`, `#6da7ec` and `#cde2fb`

#### Scenario: A quality above 1
- **WHEN** the Transparency forecast holds 1.2 at an hour inside the axis
- **THEN** the cell is shaded `#0d366b`

### Requirement: Less humidity and rain chance is darker
The card SHALL shade each Humidity and Rain chance cell in the strip's seven blues, step 0 the darkest. A value `v` in percent SHALL take step `min(6, max(0, floor(v / 15)))`, as cloud does.

#### Scenario: Dry to saturated
- **WHEN** the Humidity forecast holds 0, 44 and 100 at three hours inside the axis
- **THEN** the cells are shaded `#0d366b`, `#256abf` and `#cde2fb`

#### Scenario: Rain chance on the same scale
- **WHEN** the precipitation probability forecast holds 90 inside the axis
- **THEN** its Rain chance cell is shaded `#cde2fb`

### Requirement: The Cloud range row has its own shades and height
The Cloud range row SHALL be twice as tall as a shaded row. Each hour column SHALL be the grey `#8c8c8c`, and each range bar the darker grey `#404040`, not blue, because the row shows how far the forecasts agree rather than good or bad. A range bar SHALL stay inside its column.

#### Scenario: The shades
- **WHEN** the min and max forecasts hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** that hour's column is shaded `#8c8c8c` and its range bar `#404040`

### Requirement: The docs describe every row
`docs/night-card.md` SHALL describe each of the sixteen rows:

- its name and the sensor or sensors it reads;
- for each shaded row, what its lightest and darkest shades mean;
- that Temperature and Dew point share one scale;
- that a Rain chance cell fills the hour before its time;
- that a Wind direction arrow points the way the wind blows to;
- what hovering over a cell shows, with its unit.

#### Scenario: The page covers every row
- **WHEN** `docs/night-card.md` is read
- **THEN** it names each of the sixteen rows and the sensors `sensor.pierpressure_<pier>_wind_gust` and `sensor.pierpressure_<pier>_precipitation_probability`
- **AND** it names the words same scale, hour before and blows to
- **AND** it no longer says that a later release adds the other conditions

## ADDED Requirements

### Requirement: The Cloud range greys stand out on the default themes
Each Cloud range bar SHALL have a contrast ratio of at least 3:1 against its column. Each column SHALL have a contrast ratio of at least 3:1 against Home Assistant's default card background in the light theme, `#ffffff`, and in the dark theme, `#1c1c1c`. Contrast ratios are as WCAG 2.2 defines them.

#### Scenario: The bar against its column
- **WHEN** the contrast ratio of the range bar's grey against the column's grey is computed
- **THEN** it is at least 3:1

#### Scenario: The column against the light and dark card
- **WHEN** the contrast ratio of the column's grey is computed against `#ffffff` and against `#1c1c1c`
- **THEN** both are at least 3:1

### Requirement: A Cloud range bar keeps 1 px from each side of its column
Each range bar SHALL start 1 px in from its column's left edge and end 1 px in from its right edge, so the column shows on both sides of the bar on any card background. The bar's bottom and height SHALL be as they were without the inset.

#### Scenario: A bar from 40% to 70%
- **WHEN** the min and max forecasts hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** that hour's range bar is inset 1 px from the column's left and right edges
- **AND** it starts 40% of the way up the column and ends 70% of the way up

### Requirement: The docs say darker is better for observing
Where `docs/night-card.md` says how to read the rows, it SHALL say that on every shaded row darker means better for observing, with Temperature and Dew point as the one exception, where darker is warmer. It SHALL say that the Moon altitude shade ignores the moon's phase.

#### Scenario: The page reads darker as better
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words darker means better, exception, warmer and phase
- **AND** it no longer says darker means worse

### Requirement: The docs say the Cloud range row is grey
Where `docs/night-card.md` describes the Cloud range row, it SHALL say that its column and bar are grey because the row shows how far the forecasts agree, not whether an hour is good or bad.

#### Scenario: The Cloud range text names its greys
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** its Cloud range text names the words grey and agree
- **AND** it no longer calls the Cloud range column or bar blue
