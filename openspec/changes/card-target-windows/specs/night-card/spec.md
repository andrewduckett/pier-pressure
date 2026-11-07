## ADDED Requirements

### Requirement: The card draws a lane per ranked target
Under the Moon up lane, the strip SHALL have one lane for each rank from Target 1 to Target 10 that has a target tonight, in rank order. The lane for rank `<n>` SHALL be labelled `Target <n>` and SHALL read `sensor.pierpressure_<slug>_target_<n>`, named from the same slug as the Verdict sensor. A rank with no lane SHALL leave no gap: the next lane follows straight on.

#### Scenario: Two targets tonight
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, `sensor.pierpressure_back_yard_target_1` and `sensor.pierpressure_back_yard_target_2` each have a target tonight, and Target 3 to Target 10 are unavailable
- **THEN** under the Moon up lane the strip has two target lanes, labelled `Target 1` then `Target 2`, and no other target lane

#### Scenario: A gap in the ranks
- **WHEN** Target 1 and Target 3 have a target tonight and Target 2 is unavailable
- **THEN** the lane labelled `Target 3` comes straight after the lane labelled `Target 1`

### Requirement: A rank with no target tonight leaves no lane
A rank SHALL have a target tonight only when all of these hold:

- its sensor is in Home Assistant;
- its state is not `unavailable`, `unknown` or empty;
- its `window` attribute holds a `start` and an `end` that are readable times, with `end` after `start`.

Any other rank SHALL leave no lane. The card SHALL NOT throw, and SHALL draw the rows and the Moon up lane as usual.

#### Scenario: Every rank is empty
- **WHEN** Target 1 to Target 10 all have the state `unavailable`
- **THEN** the strip has no target lane

#### Scenario: No Target sensors at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has none of `sensor.pierpressure_backyard_target_1` to `sensor.pierpressure_backyard_target_10`
- **THEN** the card renders without an error and the strip has no target lane

#### Scenario: An unavailable rank with stale attributes
- **WHEN** `sensor.pierpressure_backyard_target_1` has the state `unavailable` and a `window` of `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** the strip has no lane labelled `Target 1`

#### Scenario: A rank whose name has not arrived
- **WHEN** Target 1 has the state `unknown` and Target 2 has an empty state, and each has a `window` of `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** the strip has no lane labelled `Target 1` or `Target 2`

#### Scenario: A broken window
- **WHEN** Target 1 has the state `Andromeda Galaxy` and a `window` of `{start: 2026-11-01T02:00:00Z, end: 2026-10-31T21:00:00Z}`, Target 2 has a `window` with no `end`, and Target 3 has a `window` whose `start` is `soon`
- **THEN** the strip has no lane labelled `Target 1`, `Target 2` or `Target 3`

### Requirement: A target bar spans its window
Each target lane SHALL hold one violet `#6250d6` bar from the target's `window.start` to its `window.end`. The card SHALL cut the bar off at an axis end. A window wholly outside the axis SHALL keep its lane, with no bar. A window that ends at the axis start, or starts at the axis end, counts as wholly outside.

#### Scenario: A window inside the night
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z and Target 1's `window` is `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** the lane labelled `Target 1` has one bar from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z

#### Scenario: A window past the axis end
- **WHEN** the axis ends at 2026-11-01T08:25:00Z and Target 1's `window` is `{start: 2026-11-01T06:00:00Z, end: 2026-11-01T10:00:00Z}`
- **THEN** the lane's bar runs from 2026-11-01T06:00:00Z to 2026-11-01T08:25:00Z

#### Scenario: A window off the axis
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z and Target 1's `window` is `{start: 2026-11-02T21:00:00Z, end: 2026-11-03T02:00:00Z}`
- **THEN** the strip has a lane labelled `Target 1` with no bar

### Requirement: A target bar holds the target's name
Each target bar SHALL show the Target sensor's state, the target's name, as its text.

#### Scenario: A named target
- **WHEN** `sensor.pierpressure_backyard_target_1` has the state `Andromeda Galaxy` and a window on the axis
- **THEN** the lane labelled `Target 1` has a bar whose text is `Andromeda Galaxy`

### Requirement: Hovering over a target bar shows its window
Hovering over a target bar SHALL show `<name> from <HH:MM> to <HH:MM>`. The name SHALL be the Target sensor's state. The two times SHALL be the window's own start and end in Home Assistant's time zone, even where the axis cuts the bar off. When the window lasts 24 hours or more, or its start and end read the same `HH:MM`, the hover SHALL show `<name>` alone.

#### Scenario: A window in UTC
- **WHEN** Home Assistant's time zone is `UTC`, Target 1 has the state `Andromeda Galaxy` and its `window` is `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** hovering over its bar shows `Andromeda Galaxy from 21:00 to 02:00`

#### Scenario: A window cut off at the axis end
- **WHEN** Home Assistant's time zone is `UTC`, the axis ends at 2026-11-01T08:25:00Z, Target 1 has the state `Orion Nebula` and its `window` is `{start: 2026-11-01T06:00:00Z, end: 2026-11-01T10:00:00Z}`
- **THEN** hovering over its bar shows `Orion Nebula from 06:00 to 10:00`

#### Scenario: A target up all through a polar night
- **WHEN** Home Assistant's time zone is `UTC`, Target 1 has the state `IC2184` and its `window` is `{start: 2026-12-21T10:58:02Z, end: 2026-12-22T10:58:32Z}`
- **THEN** hovering over its bar shows `IC2184`

### Requirement: The card's size grows with its target lanes
The card SHALL report a size of 10 to Home Assistant, plus 1 for every three target lanes it shows, rounding up.

#### Scenario: No targets
- **WHEN** the strip has no target lane
- **THEN** the card reports a size of 10

#### Scenario: Four targets
- **WHEN** the strip has four target lanes
- **THEN** the card reports a size of 12

#### Scenario: Ten targets
- **WHEN** the strip has ten target lanes
- **THEN** the card reports a size of 14

### Requirement: The docs describe the target lanes
`docs/night-card.md` SHALL describe the target lanes:

- that each lane reads one of `sensor.pierpressure_<pier>_target_1` to `sensor.pierpressure_<pier>_target_10`, and is labelled `Target <n>`;
- that its bar runs from the start to the end of the target's observable window and holds the target's name;
- what hovering over a bar shows;
- that a rank with no target tonight leaves no lane;
- that the dusk, dawn and now lines cross the target lanes.

#### Scenario: The page covers the target lanes
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the sensors `sensor.pierpressure_<pier>_target_1` and `sensor.pierpressure_<pier>_target_10` and the lane label `Target 1`
- **AND** it names the words observable window, no target tonight and leaves no lane

### Requirement: The docs' opening names the targets
The opening paragraph of `docs/night-card.md` SHALL say that the card shows the ranked targets' windows as well as the conditions.

#### Scenario: The opening names the targets
- **WHEN** the first paragraph of `docs/night-card.md` is read
- **THEN** it names the ranked targets

## MODIFIED Requirements

### Requirement: The card draws a Moon up lane
Under the strip's last row, Rain chance, the strip SHALL have a lane labelled Moon up. The lane SHALL read the `forecast` attribute of `sensor.pierpressure_<slug>_moon_altitude`, named from the same slug as the Verdict sensor. The lane SHALL keep its label on a night when the moon never rises.

#### Scenario: The lane and its sensor
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, and `sensor.pierpressure_back_yard_moon_altitude` holds values above 0 inside the axis
- **THEN** the strip's first lane, straight under Rain chance, is labelled Moon up and shows bars from that forecast

#### Scenario: The moon stays down
- **WHEN** every value in the moon altitude forecast is 0 or below
- **THEN** the strip shows the Moon up lane with its label and no bars

### Requirement: Dusk and dawn lines mark the dark window
When the axis comes from the Verdict sensor's `dark_window`, the card SHALL draw a dashed grey `#898781` line at `dark_window.start`, labelled `dusk`, and another at `dark_window.end`, labelled `dawn`. Each line SHALL cross every row from Sun altitude to Rain chance, the Moon up lane and every target lane. When the axis falls back to the browser's current time, the card SHALL draw no dusk or dawn line.

#### Scenario: A normal night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}`
- **THEN** the strip has a dashed line labelled `dusk` at 2026-10-31T20:30:00Z and one labelled `dawn` at 2026-11-01T03:25:00Z

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor's `dark_window` is `{start: null, end: null}`
- **THEN** the strip has no dusk line and no dawn line

#### Scenario: The lines reach the last target lane
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and Target 1 to Target 3 each have a target tonight
- **THEN** the dusk and dawn lines run from the Sun altitude row down to the bottom of the lane labelled `Target 3`

### Requirement: A now line marks the browser's time
The card SHALL draw a solid red `#e66767` line labelled `now` at the browser's current time, crossing every row from Sun altitude to Rain chance, the Moon up lane and every target lane. It SHALL draw the line only while that time is on the axis, from its start to its end.

#### Scenario: During the night
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T22:00:00Z
- **THEN** the strip has a line labelled `now` at 2026-10-31T22:00:00Z

#### Scenario: Before the axis starts
- **WHEN** the Verdict sensor's `dark_window` is `{start: 2026-10-31T20:30:00Z, end: 2026-11-01T03:25:00Z}` and the browser's clock reads 2026-10-31T12:00:00Z
- **THEN** the strip has no now line

#### Scenario: The now line reaches the last target lane
- **WHEN** the browser's clock reads 2026-10-31T22:00:00Z, inside the axis, and Target 1 has a target tonight
- **THEN** the now line runs from the Sun altitude row down to the bottom of the lane labelled `Target 1`
