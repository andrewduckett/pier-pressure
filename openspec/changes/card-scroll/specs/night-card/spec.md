## MODIFIED Requirements

### Requirement: The strip spans the judged night
The strip SHALL open on the opening axis. The opening axis SHALL run from 4 hours before the Verdict sensor's `dark_window.start` to 5 hours after its `dark_window.end`. The card SHALL fall back to an opening axis from 6 hours before the browser's current time to 18 hours after it in each of these cases:

- `dark_window`, its `start` or its `end` is missing, null or not a readable time;
- `end` is not after `start`;
- `end` is more than 48 hours after `start`.

Until the user pans the strip, and after the user selects "Back to tonight", the strip's time axis SHALL be the opening axis.

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

## ADDED Requirements

### Requirement: The strip pans as far as the forecast reaches
The user SHALL be able to pan the strip's axis earlier or later. Panning SHALL move the axis without changing its length, and SHALL keep it inside the reach. The reach SHALL run from the start of the earliest hour any row fills to the end of the latest, and SHALL always cover the opening axis.

#### Scenario: Panning past the last forecast hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only row sensor with a forecast, and its points run hourly from 2026-10-31T12:00:00Z to 2026-11-03T11:00:00Z
- **AND** the user pans later by more than three days
- **THEN** the strip's axis runs from 2026-11-02T20:05:00Z to 2026-11-03T12:00:00Z

#### Scenario: Panning past the first forecast hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only row sensor with a forecast, and its points run hourly from 2026-10-31T12:00:00Z to 2026-11-03T11:00:00Z
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis runs from 2026-10-31T12:00:00Z to 2026-11-01T03:55:00Z

#### Scenario: A forecast shorter than the opening axis
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and every row sensor's points lie between 2026-10-31T18:00:00Z and 2026-11-01T06:00:00Z
- **AND** the user pans later by an hour
- **THEN** the strip's axis still runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z

### Requirement: The reach counts every row's forecast
The reach SHALL count every point with a readable `datetime` in the `forecast` of each row's sensor, the Cloud range row's two sensors included, whatever the point's value. It SHALL take a Rain chance point as the hour before its time, as the row draws it. It SHALL leave out the forecast of a sensor that is `unavailable`.

#### Scenario: A Rain chance point fills the hour before it
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the earliest point of any row sensor is a Rain chance point at 2026-10-31T12:00:00Z
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis starts at 2026-10-31T11:00:00Z

#### Scenario: A null value still counts
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only row sensor with a forecast, and its last point is `{"datetime": "2026-11-02T11:00:00Z", "value": null}`
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-02T12:00:00Z

#### Scenario: An unavailable sensor's stale forecast
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover's points end at 2026-11-01T11:00:00Z, and the Seeing sensor is `unavailable` with points to 2026-11-03T11:00:00Z
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-01T12:00:00Z

### Requirement: Dragging the strip pans it
A mouse drag or a touch swipe across the strip's rows and lanes SHALL pan the axis with the pointer, as if the user moved the strip itself: dragging a distance to the left SHALL move the axis later by the same share of its length as that distance is of the width the hours are drawn across, and dragging to the right SHALL move it earlier. Dragging SHALL NOT select the strip's text.

#### Scenario: A drag to the left
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user drags the strip to the left by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A touch swipe to the right
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user swipes the strip to the right by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T00:00:00Z to 2026-11-02T00:00:00Z

### Requirement: An up or down swipe scrolls the page
A touch swipe up or down on the strip SHALL scroll the page as it does elsewhere, and SHALL NOT pan the axis.

#### Scenario: Scrolling past the card on a phone
- **WHEN** the user swipes up on the strip with a finger
- **THEN** the page scrolls, and the strip's axis is unchanged

### Requirement: A sideways wheel or trackpad swipe pans the strip
A sideways wheel movement over the strip, such as a two-finger swipe on a trackpad, SHALL pan the axis: a movement to the right by a distance SHALL move the axis later by the same share of its length as that distance is of the width the hours are drawn across. A wheel movement that is mostly up or down SHALL scroll the page and SHALL NOT pan the axis.

#### Scenario: A trackpad swipe
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and a wheel movement over the strip moves right by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A mouse wheel scrolls the page
- **WHEN** a wheel movement over the strip moves only down
- **THEN** the strip's axis is unchanged

### Requirement: The arrow keys pan the strip
The strip SHALL take keyboard focus from the Tab key, and its accessible name SHALL say that the Left and Right arrow keys move through the forecast. While the strip has focus, the Right arrow key SHALL pan the axis one hour later, and the Left arrow key one hour earlier, inside the reach.

#### Scenario: One hour later
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs further either way, and the user presses the Right arrow key with the strip focused
- **THEN** the strip's axis runs from 2026-11-01T07:00:00Z to 2026-11-02T07:00:00Z

#### Scenario: At the end of the reach
- **WHEN** the axis ends where the reach ends, and the user presses the Right arrow key with the strip focused
- **THEN** the strip's axis is unchanged

### Requirement: Everything on the strip pans together
When the axis pans, every row's cells, the Cloud range row's columns, the Moon up bars, the target bars, the dusk, dawn and now lines with their labels, and the time labels SHALL be drawn for the new axis, by the same rules as for the opening axis. The row and lane labels SHALL stay where they are. The strip SHALL draw dusk and dawn lines and target bars only for the dark window and the target windows Home Assistant holds, so a night other than the judged one has none.

#### Scenario: The next night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, the Cloud cover forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later
- **THEN** the strip's axis runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **AND** the Cloud cover row has a cell for each hour that overlaps that axis
- **AND** the strip has no dusk line and no dawn line, and the lane labelled `Target 1` has no bar
- **AND** the row labels read from `Sun altitude` to `Rain chance`, as before

### Requirement: The strip stays where the user panned it
After the user pans, the axis SHALL keep its start when Home Assistant sends new state and when the card redraws each minute. When the reach no longer holds the axis, the card SHALL move the axis only as far as it needs to stay inside the reach.

#### Scenario: New state after a pan
- **WHEN** the user has panned the axis to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z, and Home Assistant sends new state with the same `dark_window` and forecasts
- **THEN** the strip's axis still runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z

#### Scenario: A minute passes after a pan
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the user has panned the axis to run from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z, and the browser's clock moves on by 60 seconds
- **THEN** the strip's axis still runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: The forecast moves on past the axis
- **WHEN** the user has panned the axis to start at 2026-10-31T12:00:00Z, and new state from Home Assistant makes the reach start at 2026-10-31T14:00:00Z
- **THEN** the strip's axis starts at 2026-10-31T14:00:00Z and keeps its length

### Requirement: A Back to tonight button returns the strip to the opening axis
While the strip's axis is not the opening axis, the card SHALL show a button labelled `Back to tonight`. Selecting it SHALL return the axis to the opening axis, and the button SHALL then disappear. While the axis is the opening axis, the card SHALL show no such button.

#### Scenario: On opening
- **WHEN** the card first draws the strip
- **THEN** the card shows no `Back to tonight` button

#### Scenario: After a pan
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the user has panned the axis 24 hours later
- **THEN** the card shows a `Back to tonight` button

#### Scenario: Going back
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, the user has panned the axis 24 hours later, and the user selects `Back to tonight`
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **AND** the card shows no `Back to tonight` button

### Requirement: The docs describe panning the strip
`docs/night-card.md` SHALL describe panning the strip:

- that the strip opens on the judged night;
- that a mouse drag, a touch swipe, a trackpad's sideways swipe and the Left and Right arrow keys pan it, and an up or down swipe scrolls the page;
- that it stops at the first and last forecast hour;
- that a night other than the judged one has no dusk line, dawn line or target bar;
- the `Back to tonight` button.

#### Scenario: The page covers panning
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words drag, swipe, trackpad, arrow keys and `Back to tonight`
- **AND** it says the strip opens on the judged night, and stops at the first and last forecast hour
