## ADDED Requirements

### Requirement: Dusk and dawn lines mark each later night
For each of Night 2 to Night 4, the card SHALL read the `dark_window` attribute of `sensor.pierpressure_<slug>_night_<n>`, named from the same slug as the Verdict sensor. It SHALL draw a dusk and a dawn line at its `start` and `end`, styled, placed and labelled as the selected night's, each only while its time lies on the axis. It SHALL draw them whatever the Verdict sensor's `dark_window`. It SHALL draw neither when the window would make the opening axis fall back.

#### Scenario: The next night after a pan
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, `sensor.pierpressure_back_yard_night_2` has the `dark_window` `{start: 2026-11-01T20:32:00Z, end: 2026-11-02T03:23:00Z}`, and the user pans the axis 24 hours later
- **THEN** the strip has a line labelled `dusk` at 2026-11-01T20:32:00Z and one labelled `dawn` at 2026-11-02T03:23:00Z
- **AND** both lines run from the Sun altitude row down to the bottom of the Temperature chart

#### Scenario: Tonight has no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the browser's clock reads 2026-06-21T12:00:00Z, Night 2 has the `dark_window` `{start: 2026-06-22T23:40:00Z, end: 2026-06-23T00:20:00Z}`, and the user pans the axis 24 hours later, to run from 2026-06-22T06:00:00Z to 2026-06-23T06:00:00Z
- **THEN** the strip has a line labelled `dusk` at 2026-06-22T23:40:00Z and one labelled `dawn` at 2026-06-23T00:20:00Z

#### Scenario: A later night with no astronomical darkness
- **WHEN** Night 2 has the state `unknown` and the `dark_window` `{start: null, end: null}`, and the user pans the axis over that night
- **THEN** the strip has no dusk or dawn line for Night 2
- **AND** the card shows no note about darkness for Night 2

#### Scenario: A night the forecast does not reach
- **WHEN** `sensor.pierpressure_back_yard_night_3` is `unavailable`, or is not in Home Assistant
- **THEN** the strip has no dusk or dawn line for Night 3, and every other part of the strip is drawn as before

#### Scenario: An unreadable later window
- **WHEN** Night 2 has the `dark_window` `{start: "soon", end: 2026-11-02T03:23:00Z}`
- **THEN** the strip has no dusk or dawn line for Night 2

#### Scenario: Hovering over a later night's dusk
- **WHEN** Home Assistant's time zone is `UTC`, Night 2's `dark_window` starts at 2026-11-01T20:32:00Z, and that time is on the axis
- **THEN** hovering over its dusk line shows `Dusk, 20:32`

## MODIFIED Requirements

### Requirement: Dusk and dawn lines mark the dark window
When the opening axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`, each only while its time lies on the axis. Each line SHALL cross every row from Sun altitude to Rain chance, the Moon up lane, every target lane and the Temperature chart. When the opening axis falls back to the browser's clock, the card SHALL draw neither line for the selected night.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line for the selected night

#### Scenario: The lines reach the last target lane
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, and Target 1 to Target 3 each have a target tonight
- **THEN** the dusk and dawn lines run from the Sun altitude row, past the lane labelled `Target 3`, down to the bottom of the Temperature chart

#### Scenario: Dusk panned off the axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, no Night sensor has a window on the axis, and the user has panned the axis to run from 2026-10-31T22:30:00Z to 2026-11-01T14:25:00Z
- **THEN** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

#### Scenario: Dusk off the opening axis late in the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-11-01T01:00:00Z, and the user has not panned the strip
- **THEN** the strip's axis runs from 2026-10-31T21:00:00Z to 2026-11-01T12:55:00Z
- **AND** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw for the new axis, by the rules of the opening axis, every row's cells, the Cloud range columns, the Moon up bars, the target bars, the Temperature chart's lines, dots and hover areas, the lines with their labels, and the time labels. The row and lane labels, and the Temperature chart's key and scale, SHALL stay put. Target bars come only from the selected night, so a later night has dusk and dawn lines but no target bars.

#### Scenario: The next night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, Night 2's `dark_window` is `{start: 2026-11-01T20:32:00Z, end: 2026-11-02T03:23:00Z}`, the Cloud cover forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later
- **THEN** the strip's axis runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **AND** the Cloud cover row has a cell for each hour that overlaps that axis
- **AND** the strip has a dusk line at 2026-11-01T20:32:00Z and a dawn line at 2026-11-02T03:23:00Z, and the lane labelled `Target 1` has no bar
- **AND** the row labels read from `Sun altitude` to `Rain chance`, as before

#### Scenario: The Temperature chart on the next night
- **WHEN** the Temperature forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later, to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **THEN** the Temperature chart has a hover area for each hour that overlaps that axis
- **AND** its key and its scale labels are as before the pan

### Requirement: The docs describe panning the strip
`docs/night-card.md` SHALL describe panning the strip:

- that the strip opens on the judged night;
- the inputs that pan it, and that an up or down swipe scrolls the page;
- that it stops at the first and last forecast hour;
- that up to three later nights have dusk and dawn lines, read from the Night 2 to Night 4 sensors, and no target bars;
- that a row says "No forecast" past its weather source's last hour;
- the `Back to tonight` button.

#### Scenario: The page covers panning
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words drag, swipe, trackpad, arrow keys and `Back to tonight`
- **AND** it says the strip opens on the judged night, and stops at the first and last forecast hour
- **AND** it names `sensor.pierpressure_<pier>_night_2` and says a later night has no target bars
- **AND** it no longer says that another night has no dusk line or dawn line
- **AND** its "No forecast" help names a later night past a weather source's last hour as a cause

### Requirement: An item is the same after a redraw when it has the same place in the strip
After a redraw, the card SHALL take as the same item: the cell or Cloud range column of the same row for the same hour; the Temperature chart hour with the same start; the Moon up bar whose run starts in the same hour; the bar in the same target lane; the line of the same kind for the same night; the message on the same row, lane or key entry; and the moon drawing.

#### Scenario: A new target in the lane
- **WHEN** the box shows the text of the bar in the lane labelled `Target 1`, and Home Assistant updates Target 1 to the Orion Nebula (M42) with a window from 06:00 to 10:00
- **THEN** the box reads `Orion Nebula (M42) from 06:00 to 10:00`

#### Scenario: The moon rises an hour later
- **WHEN** the box shows the text of a Moon up bar whose run starts in the hour from 16:00, and Home Assistant updates the moon altitude forecast so that the run starts in the hour from 17:00
- **THEN** the card shows no box

#### Scenario: The message changes
- **WHEN** the box shows `sensor.pierpressure_backyard_seeing is unavailable` from a tap on the Seeing row's message, and the sensor's state becomes `unknown` with no forecast
- **THEN** the box reads `sensor.pierpressure_backyard_seeing has no forecast for these hours`

#### Scenario: A later night's dusk moves
- **WHEN** Home Assistant's time zone is `UTC`, the box shows `Dusk, 20:32` from a tap on Night 2's dusk line, and Home Assistant updates Night 2's `dark_window.start` to 2026-11-01T20:33:00Z
- **THEN** the box reads `Dusk, 20:33`, above Night 2's dusk line
