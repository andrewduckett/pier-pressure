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

### Requirement: Dusk and dawn lines mark the dark window
When the opening axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`. The card SHALL draw each line only while its time is on the axis, from its start to its end. Each line SHALL cross every row from Sun altitude to Rain chance, the Moon up lane and every target lane. When the opening axis falls back to the browser's current time, the card SHALL draw no dusk or dawn line.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line

#### Scenario: The lines reach the last target lane
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and Target 1 to Target 3 each have a target tonight
- **THEN** the dusk and dawn lines run from the Sun altitude row down to the bottom of the lane labelled `Target 3`

#### Scenario: Dusk panned off the axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, and the user has panned the axis to run from 2026-10-31T22:30:00Z to 2026-11-01T14:25:00Z
- **THEN** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

### Requirement: The docs name the causes of No forecast
For a row that says `No forecast`, the "If something looks wrong" section of `docs/night-card.md` SHALL name three causes. Either no weather source in the pier's `providers` gave that condition a value for these hours, or the strip is panned past the last hour that condition's weather source forecasts, or every weather source failed. It SHALL point to the pier's weather source health sensors.

#### Scenario: The causes and where to look
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** it names the word health and the `providers` setting

#### Scenario: A later night
- **WHEN** the "If something looks wrong" section of `docs/night-card.md` is read
- **THEN** its `No forecast` help names a later night, past a weather source's last hour, as a cause

## ADDED Requirements

### Requirement: The strip pans as far as the forecast reaches
The user SHALL be able to pan the strip's axis earlier or later, inside the reach. The axis SHALL always be as long as the opening axis. The reach SHALL run from the start of the earliest timeline hour to the end of the latest, and SHALL always cover the opening axis.

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
A timeline hour SHALL be the hour that starts at the `datetime` of a point in the `forecast` of a row's sensor, the Cloud range row's two sensors included. Every such point with a readable `datetime` SHALL count, whatever its value. A Rain chance point SHALL count only when it holds a number, and then for the hour before its time, the hour its cell fills. The reach SHALL leave out the forecast of a sensor that is `unavailable`.

#### Scenario: A Rain chance cell before the first hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the earliest point of any row sensor is a Rain chance point `{"datetime": "2026-10-31T12:00:00Z", "value": 20}`
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis starts at 2026-10-31T11:00:00Z

#### Scenario: A null Rain chance at the first hour
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, every row sensor's earliest point is at 2026-10-31T12:00:00Z, and the Rain chance point there is `{"datetime": "2026-10-31T12:00:00Z", "value": null}`
- **AND** the user pans earlier by more than a day
- **THEN** the strip's axis starts at 2026-10-31T12:00:00Z

#### Scenario: A null value still counts
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover is the only row sensor with a forecast, and its last point is `{"datetime": "2026-11-02T11:00:00Z", "value": null}`
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-02T12:00:00Z

#### Scenario: An unavailable sensor's stale forecast
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Cloud cover's points end at 2026-11-01T11:00:00Z, and the Seeing sensor is `unavailable` with points to 2026-11-03T11:00:00Z
- **AND** the user pans later by more than three days
- **THEN** the strip's axis ends at 2026-11-01T12:00:00Z

### Requirement: Dragging the strip pans it
A mouse drag or a touch swipe across the strip's rows and lanes SHALL pan the axis as if the user moved the strip itself. Dragging to the left SHALL move the axis later, and dragging to the right SHALL move it earlier. The axis SHALL move by the same share of its length as the sideways distance is of the width the hours are drawn across. Dragging SHALL NOT select the strip's text.

#### Scenario: A drag to the left
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user drags the strip to the left by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A touch swipe to the right
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and the user swipes the strip to the right by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T00:00:00Z to 2026-11-02T00:00:00Z

### Requirement: A small or cancelled gesture pans nothing
A drag SHALL start to pan only once the pointer has moved more than 8 px sideways, and further sideways than up or down. When the browser cancels a gesture, such as to scroll the page, the axis SHALL return to where it was when the gesture began. The strip SHALL leave touch swipes up and down to the browser, so the page scrolls.

#### Scenario: A tap that slips
- **WHEN** the axis is the opening axis, and the user presses on the strip, moves 5 px to the left and releases
- **THEN** the strip's axis is unchanged, and the card shows no `Back to tonight` button

#### Scenario: Scrolling past the card on a phone
- **WHEN** the axis is the opening axis, and a finger on the strip moves 12 px to the left and 4 px up, and the browser then cancels the gesture to scroll the page
- **THEN** the strip's axis is the opening axis, and the card shows no `Back to tonight` button

#### Scenario: A mostly vertical drag
- **WHEN** the axis is the opening axis, and the user presses on the strip and moves 10 px to the left and 30 px down
- **THEN** the strip's axis is unchanged

### Requirement: One pointer drags the strip at a time
While one pointer drags the strip, the card SHALL ignore every other pointer, such as a second finger.

#### Scenario: A second finger
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs further either way, one finger drags the strip to the left by a quarter of the width its hours are drawn across, and a second finger then touches the strip and moves
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

### Requirement: A sideways wheel or trackpad swipe pans the strip
A sideways wheel movement over the strip, such as a two-finger swipe on a trackpad, SHALL pan the axis. A movement to the right SHALL move the axis later by the same share of its length as the distance is of the width the hours are drawn across. A wheel movement that is mostly up or down SHALL scroll the page and SHALL NOT pan the axis.

#### Scenario: A trackpad swipe
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs from 2026-11-01T00:00:00Z to 2026-11-03T12:00:00Z, and a wheel movement over the strip moves right by a quarter of the width its hours are drawn across
- **THEN** the strip's axis runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A mouse wheel scrolls the page
- **WHEN** a wheel movement over the strip moves only down
- **THEN** the strip's axis is unchanged

### Requirement: The arrow keys pan the strip
The strip SHALL take keyboard focus from the Tab key. Its accessible name SHALL say that the Left and Right arrow keys move through the forecast. While the strip has focus, the Right arrow key SHALL pan the axis one hour later, and the Left arrow key one hour earlier, inside the reach.

#### Scenario: One hour later
- **WHEN** the axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z, the reach runs further either way, and the user presses the Right arrow key with the strip focused
- **THEN** the strip's axis runs from 2026-11-01T07:00:00Z to 2026-11-02T07:00:00Z

#### Scenario: At the end of the reach
- **WHEN** the axis ends where the reach ends, and the user presses the Right arrow key with the strip focused
- **THEN** the strip's axis is unchanged

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw every row's cells, the Cloud range row's columns, the Moon up bars, the target bars, the lines with their labels, and the time labels for the new axis. It SHALL draw them by the same rules as for the opening axis. The row and lane labels SHALL stay where they are. Dusk and dawn lines and target bars come only from the dark window and target windows Home Assistant holds, so a night other than the judged one has none.

#### Scenario: The next night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, the Cloud cover forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later
- **THEN** the strip's axis runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **AND** the Cloud cover row has a cell for each hour that overlaps that axis
- **AND** the strip has no dusk line and no dawn line, and the lane labelled `Target 1` has no bar
- **AND** the row labels read from `Sun altitude` to `Rain chance`, as before

### Requirement: The strip stays where the user panned it
After the user pans, the axis SHALL keep its start when Home Assistant sends new state and when the card redraws each minute. When the reach no longer holds the axis, the card SHALL move the axis only as far as it needs to stay inside the reach. A pan that the reach stops entirely SHALL count as no pan. A pan that brings the axis back to the opening axis SHALL count as selecting `Back to tonight`.

#### Scenario: New state after a pan
- **WHEN** the user has panned the axis to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z, and Home Assistant sends new state with the same `dark_window` and forecasts
- **THEN** the strip's axis still runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z

#### Scenario: A minute passes after a pan
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the user has panned the axis to run from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z, and the browser's clock moves on by 60 seconds
- **THEN** the strip's axis still runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: The forecast moves on past the axis
- **WHEN** the user has panned the axis to start at 2026-10-31T12:00:00Z, and new state from Home Assistant makes the reach start at 2026-10-31T14:00:00Z
- **THEN** the strip's axis starts at 2026-10-31T14:00:00Z and is as long as the opening axis

#### Scenario: A new night of another length
- **WHEN** the user has panned the axis to start at 2026-11-01T16:30:00Z, and a new `dark_window` makes the opening axis 17 hours long
- **THEN** the strip's axis starts at 2026-11-01T16:30:00Z and is 17 hours long

#### Scenario: Panning back by hand
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the browser's clock reads 2026-11-01T12:00:00Z, the reach runs further either way, the user presses the Right arrow key and then the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-11-01T06:01:00Z to 2026-11-02T06:01:00Z, and the card shows no `Back to tonight` button

#### Scenario: A new pier
- **WHEN** the user has panned the axis 24 hours later, and the card's configuration changes to another pier
- **THEN** the strip's axis is the new pier's opening axis, and the card shows no `Back to tonight` button

#### Scenario: A pan against the reach's start
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the browser's clock reads 2026-11-01T12:00:00Z, the reach starts at 2026-11-01T06:00:00Z, the user presses the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-11-01T06:01:00Z to 2026-11-02T06:01:00Z, and the card shows no `Back to tonight` button

### Requirement: A Back to tonight button returns the strip to the opening axis
While the strip's axis is not the opening axis, the card SHALL show a button labelled `Back to tonight` above the strip. Selecting it SHALL return the axis to the opening axis and move keyboard focus to the strip. While the axis is the opening axis, the card SHALL hide the button but keep its place, so showing it moves nothing on the card.

#### Scenario: On opening
- **WHEN** the card first draws the strip
- **THEN** the card shows no `Back to tonight` button

#### Scenario: After a pan
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, and the user has panned the axis 24 hours later
- **THEN** the card shows a `Back to tonight` button

#### Scenario: Going back
- **WHEN** the opening axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, the user has panned the axis 24 hours later, and the user selects `Back to tonight`
- **THEN** the strip's axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z
- **AND** the card shows no `Back to tonight` button, and the strip has keyboard focus

#### Scenario: Pressing the button does not pan
- **WHEN** the user has panned the axis 24 hours later, and presses `Back to tonight` with the mouse, moving 12 px to the left before releasing, so the browser clicks the button
- **THEN** the strip's axis is the opening axis

### Requirement: The docs describe panning the strip
`docs/night-card.md` SHALL describe panning the strip:

- that the strip opens on the judged night;
- the inputs that pan it, and that an up or down swipe scrolls the page;
- that it stops at the first and last forecast hour;
- that other nights have no dusk line, dawn line or target bar;
- that a row says "No forecast" past its weather source's last hour;
- the `Back to tonight` button.

#### Scenario: The page covers panning
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words drag, swipe, trackpad, arrow keys and `Back to tonight`
- **AND** it says the strip opens on the judged night, and stops at the first and last forecast hour
- **AND** its "No forecast" help names a later night past a weather source's last hour as a cause
