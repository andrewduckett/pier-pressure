## ADDED Requirements

### Requirement: The axis carries day labels under its time labels
The card SHALL draw a row of day labels directly under the time labels, in the same text size and colour. The row SHALL have a label just right of the start of each day that starts strictly between the axis's start and end. It SHALL also have a label for the day in progress at the axis's start, pinned to the axis's left edge. A day is a calendar day in Home Assistant's time zone. The time labels SHALL stay as they are.

#### Scenario: One night in UTC
- **WHEN** Home Assistant's time zone is `UTC` and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the day labels read `Sat 31 Oct`, at the axis's left edge, and `Sun 1 Nov`, just right of 2026-11-01T00:00:00Z, in that order
- **AND** the time labels read `18:00`, `21:00`, `00:00`, `03:00` and `06:00`, as before

#### Scenario: No day starts on the axis
- **WHEN** Home Assistant's time zone is `Asia/Tokyo` and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the only day label reads `Sun 1 Nov`, at the axis's left edge

#### Scenario: The axis starts as a day starts
- **WHEN** Home Assistant's time zone is `UTC` and the axis runs from 2026-11-01T00:00:00Z to 2026-11-01T15:55:00Z
- **THEN** the only day label reads `Sun 1 Nov`, at the axis's left edge

#### Scenario: Polar night
- **WHEN** Home Assistant's time zone is `UTC` and the axis runs from 2026-12-20T07:00:00Z to 2026-12-21T16:00:00Z
- **THEN** the day labels read `Sun 20 Dec`, at the axis's left edge, and `Mon 21 Dec`, just right of 2026-12-21T00:00:00Z

### Requirement: A day starts at the first instant of its date
The card SHALL take a day's start to be the first instant whose date, in Home Assistant's time zone, differs from the date of the instant before. On a day whose clock skips midnight, the day SHALL start at the first time the clock shows, such as 01:00.

#### Scenario: A clock change skips midnight
- **WHEN** Home Assistant's time zone is `America/Santiago` and the axis runs from 2026-09-05T22:00:00Z to 2026-09-06T14:00:00Z, so the clock goes from 23:59 on 5 September to 01:00 on 6 September
- **THEN** the day labels read `Sat 5 Sep`, at the axis's left edge, and `Sun 6 Sep`, just right of 2026-09-06T04:00:00Z
- **AND** the strip has one divider, at 2026-09-06T04:00:00Z

### Requirement: A day label names the weekday, the day and the month
A day label SHALL read `<weekday> <day> <month>`. The weekday SHALL be one of `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat` and `Sun`. The day SHALL be the day of the month with no leading zero, in the digits `0` to `9`. The month SHALL be one of `Jan`, `Feb`, `Mar`, `Apr`, `May`, `Jun`, `Jul`, `Aug`, `Sep`, `Oct`, `Nov` and `Dec`. Every viewer SHALL see the same text, whatever the browser's language.

#### Scenario: A one-digit day
- **WHEN** Home Assistant's time zone is `UTC` and a day starts at 2026-09-03T00:00:00Z
- **THEN** that day's label reads `Thu 3 Sep`

#### Scenario: A browser in Arabic
- **WHEN** the browser's language is `ar-EG`, Home Assistant's time zone is `UTC`, and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the day labels read `Sat 31 Oct` and `Sun 1 Nov`

### Requirement: A divider marks each day's start
At the start of each day that starts strictly between the axis's start and end, the card SHALL draw a 1 px solid vertical divider in Home Assistant's divider colour. The divider SHALL cross only the time-label row and the day-label row. It SHALL not cross the rows from Sun altitude to Rain chance, the Moon up lane, the target lanes or the Temperature chart. The divider SHALL have no hover text.

#### Scenario: The divider in UTC
- **WHEN** Home Assistant's time zone is `UTC` and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the strip has one divider, at 2026-11-01T00:00:00Z
- **AND** the divider runs from the top of the time-label row to the bottom of the day-label row, and no part of it lies above the time-label row

#### Scenario: No day starts on the axis
- **WHEN** Home Assistant's time zone is `Asia/Tokyo` and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the strip has no divider

### Requirement: A day label shows only when it fits whole
A day label SHALL show only when the whole label fits between its day's start, or the axis's left edge for the pinned label, and the next day's start or the axis's right end, whichever comes first. A label that does not fit SHALL be hidden, never cut off or moved. A hidden label's divider SHALL still show. The rule SHALL hold on a card of any width, including one narrower than 450 px.

#### Scenario: The next day starts soon after the left edge
- **WHEN** the card is 340 px wide, Home Assistant's time zone is `UTC`, and the axis runs from 2026-10-31T23:00:00Z to 2026-11-01T14:55:00Z
- **THEN** the day labels show only `Sun 1 Nov`, just right of 2026-11-01T00:00:00Z
- **AND** the strip has one divider, at 2026-11-01T00:00:00Z

#### Scenario: A day starts just before the right end
- **WHEN** the card is 340 px wide, Home Assistant's time zone is `UTC`, and the axis runs from 2026-10-31T09:00:00Z to 2026-11-01T00:55:00Z
- **THEN** the day labels show only `Sat 31 Oct`, at the axis's left edge
- **AND** the strip has one divider, at 2026-11-01T00:00:00Z

#### Scenario: Both labels fit on a narrow card
- **WHEN** the card is 340 px wide, Home Assistant's time zone is `UTC`, and the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **THEN** the day labels show `Sat 31 Oct` and `Sun 1 Nov`, each whole

### Requirement: The docs describe the day labels
`docs/night-card.md` SHALL describe the day labels:

- that a row of day labels under the time labels names each day on the strip, such as `Thu 26 Nov`;
- that a divider marks where each day starts, in Home Assistant's time zone;
- that the label of the day at the strip's left edge stays at that edge as the strip pans;
- that a label hides when it has no room, and its divider still shows.

#### Scenario: The page covers the day labels
- **WHEN** `docs/night-card.md` is read
- **THEN** its Times section names the day labels, the divider and the example `Thu 26 Nov`
- **AND** it says that a day starts in Home Assistant's time zone, and that a label with no room is hidden while its divider still shows

## MODIFIED Requirements

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw for the new axis, by the rules of the opening axis, every row's cells, the Cloud range columns, the Moon up bars, the target bars, the Temperature chart's lines, dots and hover areas, the lines with their labels, the time labels, and the day labels with their dividers. The row labels, the chart's key and its °C labels SHALL stay put. Target bars come from every night: tonight's from the Target sensors, and each later night's from its Night sensor.

#### Scenario: The next night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, Night 2's `dark_window` is `{start: 2026-11-01T20:32:00Z, end: 2026-11-02T03:23:00Z}` and its `targets` attribute is empty, the Cloud cover forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later
- **THEN** the strip's axis runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **AND** the Cloud cover row has a cell for each hour that overlaps that axis
- **AND** the strip has a dusk line at 2026-11-01T20:32:00Z and a dawn line at 2026-11-02T03:23:00Z, and the lane labelled `Target 1` has no bar
- **AND** the row labels read from `Sun altitude` to `Rain chance`, as before

#### Scenario: The next night's targets
- **WHEN** the same card's Night 2 `targets` attribute holds one target, the Orion Nebula (M42), with a window from 2026-11-01T22:00:00Z to 2026-11-02T03:00:00Z, and the user pans the axis 24 hours later
- **THEN** the lane labelled `Target 1` has a bar from 2026-11-01T22:00:00Z to 2026-11-02T03:00:00Z whose text is `Orion Nebula (M42)`
- **AND** the lane labels are as before the pan

#### Scenario: The Temperature chart on the next night
- **WHEN** the Temperature forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later, to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **THEN** the Temperature chart has a hover area for each hour that overlaps that axis
- **AND** its key and its °C labels are as before the pan, with the °C labels still at the plot's left edge

#### Scenario: The day labels on the next night
- **WHEN** Home Assistant's time zone is `UTC`, the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the user pans the axis 24 hours later
- **THEN** the day labels read `Sun 1 Nov`, at the axis's left edge, and `Mon 2 Nov`, just right of 2026-11-02T00:00:00Z
- **AND** the strip has one divider, at 2026-11-02T00:00:00Z

