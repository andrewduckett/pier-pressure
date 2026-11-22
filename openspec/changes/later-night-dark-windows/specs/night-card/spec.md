## MODIFIED Requirements

### Requirement: Dusk and dawn lines mark the dark window
When the opening axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`, each only while its time lies on the axis. Each line SHALL cross every row from Sun altitude to Rain chance, the Moon up lane, every target lane and the Temperature chart. When the opening axis falls back to the browser's current time, the card SHALL draw no line from the Verdict sensor.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, and no Night sensor gives a dark window
- **THEN** the strip has no dusk line and no dawn line

#### Scenario: The lines reach the last target lane
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, and Target 1 to Target 3 each have a target tonight
- **THEN** the dusk and dawn lines run from the Sun altitude row, past the lane labelled `Target 3`, down to the bottom of the Temperature chart

#### Scenario: Dusk panned off the axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, and the user has panned the axis to run from 2026-10-31T22:30:00Z to 2026-11-01T14:25:00Z
- **THEN** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

#### Scenario: Dusk off the opening axis late in the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-11-01T01:00:00Z, and the user has not panned the strip
- **THEN** the strip's axis runs from 2026-10-31T21:00:00Z to 2026-11-01T12:55:00Z
- **AND** the strip has a line labelled `dawn` at 2026-11-01T03:25:00Z, and no line labelled `dusk`

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw for the new axis, by the rules of the opening axis, every row's cells, the Cloud range columns, the Moon up bars, the target bars, the Temperature chart's lines, dots and hover areas, the lines with their labels, and the time labels. The row and lane labels, and the Temperature chart's key and scale, SHALL stay put. Target bars come only from tonight's windows, so a later night has none; its dusk and dawn lines come from its Night sensor.

#### Scenario: The next night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-10-31T12:00:00Z, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, the Cloud cover forecast holds hourly values to 2026-11-03T11:00:00Z, no Night sensor is in Home Assistant, and the user pans the axis 24 hours later
- **THEN** the strip's axis runs from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **AND** the Cloud cover row has a cell for each hour that overlaps that axis
- **AND** the strip has no dusk line and no dawn line, and the lane labelled `Target 1` has no bar
- **AND** the row labels read from `Sun altitude` to `Rain chance`, as before

#### Scenario: The next night with its Night sensor
- **WHEN** the same strip is panned 24 hours later, and the Night 2 sensor's `dark_window` is `{start: 2026-11-01T20:28:00Z, end: 2026-11-02T03:27:00Z}`
- **THEN** the strip has a line labelled `dusk` at 2026-11-01T20:28:00Z and one labelled `dawn` at 2026-11-02T03:27:00Z
- **AND** the lane labelled `Target 1` has no bar

#### Scenario: The Temperature chart on the next night
- **WHEN** the Temperature forecast holds hourly values to 2026-11-03T11:00:00Z, and the user pans the axis 24 hours later, to run from 2026-11-01T16:30:00Z to 2026-11-02T08:25:00Z
- **THEN** the Temperature chart has a hover area for each hour that overlaps that axis
- **AND** its key and its scale labels are as before the pan

### Requirement: The docs describe panning the strip
`docs/night-card.md` SHALL describe panning the strip:

- that the strip opens on the judged night;
- the inputs that pan it, and that an up or down swipe scrolls the page;
- that it stops at the first and last forecast hour;
- that a later night has dusk and dawn lines but no target bar;
- that a row says "No forecast" past its weather source's last hour;
- the `Back to tonight` button.

#### Scenario: The page covers panning
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words drag, swipe, trackpad, arrow keys and `Back to tonight`
- **AND** it says the strip opens on the judged night, and stops at the first and last forecast hour
- **AND** its "No forecast" help names a later night past a weather source's last hour as a cause

#### Scenario: The page no longer says other nights have no lines
- **WHEN** `docs/night-card.md` is read
- **THEN** it does not say that another night has no dusk line or dawn line

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

#### Scenario: Two dusk lines on one axis
- **WHEN** Home Assistant's time zone is `UTC`, the Night 2 sensor's `dark_window` is `{start: 2026-12-11T11:53:13Z, end: 2026-12-12T11:53:41Z}`, the Night 3 sensor's is `{start: 2026-12-12T11:53:41Z, end: 2026-12-13T11:54:09Z}`, the axis holds both dusk lines, and the box shows the text of the Night 3 dusk line
- **AND** the card redraws
- **THEN** the box reads `Dusk, 11:53` and stays on the line at 2026-12-12T11:53:41Z

## ADDED Requirements

### Requirement: The card reads the Night sensors
The card SHALL read the `dark_window` attribute of `sensor.pierpressure_<slug>_night_2`, `sensor.pierpressure_<slug>_night_3` and `sensor.pierpressure_<slug>_night_4`, named from the same slug as the Verdict sensor.

#### Scenario: A pier with a capital letter and a hyphen
- **WHEN** the card is configured with `pier: Back-Yard`
- **THEN** it reads the later nights from `sensor.pierpressure_back_yard_night_2`, `sensor.pierpressure_back_yard_night_3` and `sensor.pierpressure_back_yard_night_4`

### Requirement: Dusk and dawn lines mark each later night's dark window
For each Night sensor whose `dark_window` has a readable `start` and a readable `end` after it, the card SHALL draw a `dusk` line at `start` and a `dawn` line at `end`, like tonight's lines, each only while its time lies on the axis. It SHALL draw them whether the opening axis comes from the Verdict sensor or falls back to the browser's clock.

#### Scenario: Tomorrow's dusk on the opening axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-11-01T12:00:00Z, the user has not panned the strip, and the Night 2 sensor's `dark_window` is `{start: 2026-11-01T20:28:00Z, end: 2026-11-02T03:27:00Z}`
- **THEN** the strip's axis runs from 2026-11-01T08:00:00Z to 2026-11-01T23:55:00Z
- **AND** the strip has a dashed grey `#898781` line labelled `dusk` at 2026-11-01T20:28:00Z, and no line labelled `dawn`

#### Scenario: Tomorrow's dusk off the opening axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`, the browser's clock reads 2026-11-01T03:00:00Z, and the Night 2 sensor's `dark_window` is `{start: 2026-11-01T20:28:00Z, end: 2026-11-02T03:27:00Z}`
- **THEN** the strip's axis runs from 2026-10-31T23:00:00Z to 2026-11-01T14:55:00Z
- **AND** the strip has a dashed grey `#898781` line labelled `dawn` at 2026-11-01T03:25:00Z, and no line at 2026-11-01T20:28:00Z

#### Scenario: Two later nights' lines on one panned axis
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T18:00:00Z, end: 2026-11-01T05:30:00Z}`, the Night 2 sensor's is `{start: 2026-11-01T18:00:00Z, end: 2026-11-02T05:31:00Z}`, the Night 3 sensor's is `{start: 2026-11-02T18:00:00Z, end: 2026-11-03T05:32:00Z}`, and the user has panned the axis to run from 2026-11-02T00:00:00Z to 2026-11-02T20:30:00Z
- **THEN** the strip has a line labelled `dawn` at 2026-11-02T05:31:00Z and a line labelled `dusk` at 2026-11-02T18:00:00Z, and no other dusk or dawn line

#### Scenario: Tonight has no darkness, but a later night does
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`, the browser's clock reads 2026-08-03T22:00:00Z, the Cloud cover forecast holds hourly values to 2026-08-06T21:00:00Z, the Night 2 sensor's `dark_window` is `{start: null, end: null}`, and the Night 3 sensor's is `{start: 2026-08-05T23:49:40Z, end: 2026-08-06T00:46:51Z}`
- **THEN** the strip's axis runs from 2026-08-03T16:00:00Z to 2026-08-04T16:00:00Z, and has no dusk line and no dawn line
- **AND** when the user pans the axis 36 hours later, the strip has a line labelled `dusk` at 2026-08-05T23:49:40Z and one labelled `dawn` at 2026-08-06T00:46:51Z

#### Scenario: Hovering over a later night's line
- **WHEN** Home Assistant's time zone is `UTC`, and the Night 2 sensor's `dark_window` starts at 2026-11-01T20:28:00Z, on the axis
- **THEN** hovering over that dusk line shows `Dusk, 20:28`

### Requirement: A Night sensor without a readable dark window draws no line
A Night sensor that is missing, unavailable or unknown, or whose `dark_window` is missing, has a null or unreadable `start` or `end`, has an `end` not after its `start`, or is more than 48 hours long, SHALL add no line. The card SHALL show no message and no note for it, and every other line SHALL still draw.

#### Scenario: An unavailable Night 4
- **WHEN** the Night 4 sensor is `unavailable`, and the Night 2 sensor's `dark_window` is `{start: 2026-11-01T20:28:00Z, end: 2026-11-02T03:27:00Z}`, on the axis
- **THEN** the strip has the dusk and dawn lines at 2026-11-01T20:28:00Z and 2026-11-02T03:27:00Z
- **AND** the card shows no message about Night 4

#### Scenario: A later night with no astronomical darkness
- **WHEN** the Night 3 sensor's state is `unknown` and its `dark_window` is `{start: null, end: null}`
- **THEN** the strip draws no line for Night 3
- **AND** the card shows no `No astronomical darkness` note for it

### Requirement: The docs describe the later nights' lines
`docs/night-card.md` SHALL say that each later night the strip pans to has its own dusk and dawn lines, from the sensors Night 2 to Night 4, and that a later night with no astronomical darkness has none.

#### Scenario: The page covers the later nights
- **WHEN** `docs/night-card.md` is read
- **THEN** it names `sensor.pierpressure_<pier>_night_2`, Night 2, Night 4, dusk and dawn in the same section
