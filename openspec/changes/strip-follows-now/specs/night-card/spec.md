## MODIFIED Requirements

### Requirement: The strip spans the judged night
The strip SHALL open on the opening axis. The opening axis SHALL start at the later of two times: 4 hours before the Verdict sensor's `dark_window.start`, and 4 hours before the browser's clock. This holds unless the opening axis falls back to the browser's clock. The opening axis SHALL be as long as the time from 4 hours before `dark_window.start` to 5 hours after `dark_window.end`, so before dusk it ends 5 hours after `dark_window.end`. As the card redraws, the opening axis SHALL follow the browser's clock. Until the user pans the strip, and after the user selects "Back to tonight", the strip's time axis SHALL be the opening axis.

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

#### Scenario: A minute passes during the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the user has not panned the strip, and the clock moves on by 60 seconds with no new state from Home Assistant
- **THEN** the strip's axis runs from 2026-10-31T19:01:00Z to 2026-11-01T10:56:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}` and the browser's clock reads 2026-06-21T12:00:00Z
- **THEN** the strip's axis runs from 2026-06-21T06:00:00Z to 2026-06-22T06:00:00Z

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor has the state `unknown`, no attributes, and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the card still draws the strip, with its axis from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

#### Scenario: A window that ends before it starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-11-01T03:25:00Z, end: 2026-10-31T20:30:00Z}` and the browser's clock reads 2026-11-01T12:00:00Z
- **THEN** the strip's axis runs from 2026-11-01T06:00:00Z to 2026-11-02T06:00:00Z

### Requirement: The docs describe the cloud rows
`docs/night-card.md` SHALL describe the strip's cloud rows:

- the four rows and the sensors they read;
- the axis span, that once the night has started the axis opens 4 hours before now and keeps its length, and its fallback on a night with no astronomical darkness;
- the shades from clear to overcast;
- blank hours;
- what hovering over a cell shows;
- that times are in Home Assistant's time zone.

#### Scenario: The page covers the strip
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the rows Cloud cover, Cloud low, Cloud mid and Cloud high, and the sensor `sensor.pierpressure_<pier>_cloud_cover`
- **AND** it says the strip runs from 4 hours before dusk to 5 hours after dawn, and from 6 hours before now to 18 hours after on a night with no astronomical darkness
- **AND** it says that once the night has started, the strip opens 4 hours before now and keeps its length
- **AND** it names the words clear, overcast, blank, hover and time zone

### Requirement: Dusk and dawn lines mark the dark window
When the opening axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`, each only while its time lies on the axis. Each line SHALL cross every row from Sun altitude to Rain chance, the Moon up lane and every target lane. When the opening axis falls back to the browser's current time, the card SHALL draw no dusk or dawn line.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line

#### Scenario: The lines reach the last target lane
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, and Target 1 to Target 3 each have a target tonight
- **THEN** the dusk and dawn lines run from the Sun altitude row down to the bottom of the lane labelled `Target 3`

#### Scenario: Dusk panned off the axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, and the user has panned the axis to run from 2026-10-31T22:30:00Z to 2026-11-01T14:25:00Z
- **THEN** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

#### Scenario: Dusk off the opening axis late in the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-11-01T01:00:00Z, and the user has not panned the strip
- **THEN** the strip's axis runs from 2026-10-31T21:00:00Z to 2026-11-01T12:55:00Z
- **AND** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw every row's cells, the Cloud range row's columns, the Moon up bars, the target bars, the lines with their labels, and the time labels for the new axis. It SHALL draw them by the same rules as for the opening axis. The row and lane labels SHALL stay where they are. Dusk and dawn lines and target bars come only from the dark window and target windows Home Assistant holds, so a night other than the judged one has none.

#### Scenario: The next night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, the Cloud cover forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later
- **THEN** the strip's axis runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **AND** the Cloud cover row has a cell for each hour that overlaps that axis
- **AND** the strip has no dusk line and no dawn line, and the lane labelled `Target 1` has no bar
- **AND** the row labels read from `Sun altitude` to `Rain chance`, as before

### Requirement: The strip stays where the user panned it
After the user pans, the axis SHALL keep its start when Home Assistant sends new state and when the card redraws each minute. When the reach no longer holds the axis, the card SHALL move the axis only as far as it needs to stay inside the reach. A pan that the reach stops entirely SHALL count as no pan. A pan that brings the axis back to the opening axis SHALL count as selecting `Back to tonight`. A later pan is one that leaves the axis starting after the opening axis. When the opening axis moves on to or past the start of a later pan, the strip SHALL follow the opening axis again. An earlier pan SHALL keep its start as the opening axis moves away from it.

#### Scenario: New state after a pan
- **WHEN** the user has panned the axis to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z, and Home Assistant sends new state with the same `dark_window` and forecasts
- **THEN** the strip's axis still runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z

#### Scenario: A minute passes after a pan
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the user has panned the axis to run from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z, and the browser's clock moves on by 60 seconds
- **THEN** the strip's axis still runs from 2026-11-01T12:00:00Z to 2026-11-02T12:00:00Z

#### Scenario: A minute passes after a pan during the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the reach runs further either way, the user presses the Left arrow key with the strip focused, and the clock then moves on by 60 seconds
- **THEN** the strip's axis runs from 2026-10-31T18:00:00Z to 2026-11-01T09:55:00Z, and the card shows a `Back to tonight` button

#### Scenario: The opening axis catches up with a pan
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the reach runs further either way, the user presses the Right arrow key with the strip focused, and the clock then moves on to 2026-11-01T00:01:00Z
- **THEN** the strip's axis runs from 2026-10-31T20:01:00Z to 2026-11-01T11:56:00Z, and the card shows no `Back to tonight` button

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
While the strip's axis is not the opening axis, the card SHALL show a button labelled `Back to tonight` above the strip. Selecting it SHALL return the axis to the opening axis at that time, and move keyboard focus to the strip. While the axis is the opening axis, the card SHALL hide the button but keep its place, so showing it moves nothing on the card.

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

#### Scenario: Going back after the night has moved on
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T23:00:00Z, the user pans the axis 24 hours later, the clock moves on to 2026-11-01T00:00:00Z, and the user selects `Back to tonight`
- **THEN** the strip's axis runs from 2026-10-31T20:00:00Z to 2026-11-01T11:55:00Z

#### Scenario: Pressing the button does not pan
- **WHEN** the user has panned the axis 24 hours later, and presses `Back to tonight` with the mouse, moving 12 px to the left before releasing, so the browser clicks the button
- **THEN** the strip's axis is the opening axis
