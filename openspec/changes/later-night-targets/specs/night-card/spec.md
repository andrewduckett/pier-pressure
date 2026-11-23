<!-- Plain language: Name the actor, condition and observable result. Explain necessary domain terms using the agreed glossary. Keep requirement and scenario headings and WHEN/THEN syntax exactly as required. -->

## ADDED Requirements

### Requirement: A rank has a target tonight when its Target sensor shows one
A rank SHALL have a target tonight only when all of these hold:

- its Target sensor is in Home Assistant;
- its state is not `unavailable`, `unknown` or empty;
- its `window` attribute holds a `start` and an `end` that are readable times, with `end` after `start`.

#### Scenario: A filled rank
- **WHEN** Target 1 has the state `Andromeda Galaxy` and a `window` of `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** rank 1 has a target tonight, and the strip has a lane labelled `Target 1`

### Requirement: A rank has a target on a later night when its Night sensor's entry shows one
A rank SHALL have a target on Night 2, 3 or 4 only when all of these hold:

- that Night sensor is in Home Assistant, and its state is not `unavailable`;
- its `targets` attribute is a list with an entry at that rank;
- the entry has a non-empty `name` or a non-empty `id`;
- the entry's `window` holds a `start` and an `end` that are readable times, with `end` after `start`.

#### Scenario: A filled later rank
- **WHEN** no rank has a target tonight, and Night 2's `targets` attribute holds one entry with `name: Orion Nebula`, `id: M42` and a `window` of `{start: 2026-11-01T22:00:00Z, end: 2026-11-02T03:00:00Z}`
- **THEN** rank 1 has a target on Night 2, and the strip has a lane labelled `Target 1`

### Requirement: A rank with no target on any night leaves no lane
A rank with a target neither tonight nor on any later night SHALL leave no lane. The card SHALL NOT throw, and SHALL draw the rows and the Moon up lane as usual.

#### Scenario: Every rank is empty
- **WHEN** Target 1 to Target 10 all have the state `unavailable`, and Night 2 to Night 4 are `unavailable`
- **THEN** the strip has no target lane

#### Scenario: No Target or Night sensors at all
- **WHEN** the Verdict sensor has the state `GO` and Home Assistant has none of `sensor.pierpressure_backyard_target_1` to `sensor.pierpressure_backyard_target_10` and none of `sensor.pierpressure_backyard_night_2` to `sensor.pierpressure_backyard_night_4`
- **THEN** the card renders without an error and the strip has no target lane

#### Scenario: An unavailable rank with stale attributes
- **WHEN** `sensor.pierpressure_backyard_target_1` has the state `unavailable` and a `window` of `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`, and no Night sensor has a target at rank 1
- **THEN** the strip has no lane labelled `Target 1`

#### Scenario: A rank whose name has not arrived
- **WHEN** Target 1 has the state `unknown` and Target 2 has an empty state, each has a `window` of `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`, and no Night sensor has a target at rank 1 or 2
- **THEN** the strip has no lane labelled `Target 1` or `Target 2`

#### Scenario: A broken window
- **WHEN** Target 1 has the state `Andromeda Galaxy` and a `window` of `{start: 2026-11-01T02:00:00Z, end: 2026-10-31T21:00:00Z}`, Target 2 has a `window` with no `end`, Target 3 has a `window` whose `start` is `soon`, and no Night sensor has a target at rank 1, 2 or 3
- **THEN** the strip has no lane labelled `Target 1`, `Target 2` or `Target 3`

#### Scenario: A rank filled only on a later night
- **WHEN** Target 1 and Target 2 have a target tonight, Target 3 to Target 10 are unavailable, and `sensor.pierpressure_backyard_night_2` has a `targets` attribute holding three targets, each with an `id` and a readable `window`
- **THEN** the strip has three target lanes, labelled `Target 1`, `Target 2` and `Target 3`

#### Scenario: A later night's unreadable entries
- **WHEN** no rank has a target tonight, Night 2 is `unavailable` with a `targets` attribute holding one target, and Night 3's `targets` attribute holds an entry with an empty `name` and no `id`, and an entry whose `window` has no `end`
- **THEN** the strip has no target lane

### Requirement: A later night's targets draw bars in their ranks' lanes
For each of Night 2 to Night 4 that has a target at a rank, the lane for that rank SHALL hold a bar for that target, by the rules of tonight's bars: violet `#6250d6`, from its `window.start` to its `window.end`, cut off at an axis end, and drawn only when its window is not wholly outside the axis. Hovering over it and tapping it SHALL show what they show for tonight's bars.

#### Scenario: The next night's top target after a pan
- **WHEN** Home Assistant's time zone is `UTC`, Target 1 is the Andromeda Galaxy (M31) with a window from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, Night 2's first `targets` entry has `name: Orion Nebula`, `id: M42` and a `window` of `{start: 2026-11-01T22:00:00Z, end: 2026-11-02T03:00:00Z}`, and the user pans the axis 24 hours later
- **THEN** the lane labelled `Target 1` has one bar on the axis, from 2026-11-01T22:00:00Z to 2026-11-02T03:00:00Z, whose text is `Orion Nebula (M42)`
- **AND** hovering over it shows `Orion Nebula (M42) from 22:00 to 03:00`

#### Scenario: Two nights' bars in one lane
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-02T08:25:00Z, Target 1's window is from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, and Night 2's first target's window is from 2026-11-01T22:00:00Z to 2026-11-02T03:00:00Z
- **THEN** the lane labelled `Target 1` has two bars, tonight's and Night 2's, each named for its own night's target

### Requirement: A later night's target bar holds that night's target's name
A later night's target bar SHALL show `<name> (<id>)`, read from the `name` and `id` of its entry in the Night sensor's `targets`. When `name` is null or empty, the bar SHALL show `<id>` alone. When `id` is missing or empty, the bar SHALL show `<name>` alone. A narrow bar SHALL shorten the name and keep the id, as tonight's bars do.

#### Scenario: A later night target the catalog does not name
- **WHEN** Night 2's first `targets` entry has `name: null`, `id: NGC7394` and a window on the axis
- **THEN** the lane labelled `Target 1` has a bar whose text is `NGC7394`

#### Scenario: A later night target with no id
- **WHEN** Night 2's first `targets` entry has `name: Orion Nebula`, no `id` and a window on the axis
- **THEN** the lane labelled `Target 1` has a bar whose text is `Orion Nebula`

## MODIFIED Requirements

### Requirement: The card draws a lane per ranked target
Under the Moon up lane, the strip SHALL have one lane for each rank from Target 1 to Target 10 that has a target on any night, tonight or a later night, in rank order. The lane for rank `<n>` SHALL be labelled `Target <n>` and SHALL read `sensor.pierpressure_<slug>_target_<n>` for tonight and the `targets` attribute of `sensor.pierpressure_<slug>_night_2` to `_night_4` for later nights, named from the same slug as the Verdict sensor. A rank with no lane SHALL leave no gap: the next lane follows straight on.

#### Scenario: Two targets tonight
- **WHEN** the card is configured with `pier: Back-Yard`, the Verdict sensor has the state `GO`, `sensor.pierpressure_back_yard_target_1` and `sensor.pierpressure_back_yard_target_2` each have a target tonight, Target 3 to Target 10 are unavailable, and no Night sensor has a target
- **THEN** under the Moon up lane the strip has two target lanes, labelled `Target 1` then `Target 2`, and no other target lane

#### Scenario: A gap in the ranks
- **WHEN** Target 1 and Target 3 have a target tonight, Target 2 is unavailable, and no Night sensor has a target at rank 2
- **THEN** the lane labelled `Target 3` comes straight after the lane labelled `Target 1`

### Requirement: A target bar spans its window
Each target lane SHALL hold one violet `#6250d6` bar for each night that has a target at its rank, from that target's `window.start` to its `window.end`. The card SHALL cut a bar off at an axis end. A window wholly outside the axis SHALL draw no bar, and the lane SHALL stay. A window that ends at the axis start, or starts at the axis end, counts as wholly outside.

#### Scenario: A window inside the night
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z and Target 1's `window` is `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** the lane labelled `Target 1` has one bar from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z

#### Scenario: A window past the axis end
- **WHEN** the axis ends at 2026-11-01T08:25:00Z and Target 1's `window` is `{start: 2026-11-01T06:00:00Z, end: 2026-11-01T10:00:00Z}`
- **THEN** the lane's bar runs from 2026-11-01T06:00:00Z to 2026-11-01T08:25:00Z

#### Scenario: A window off the axis
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Target 1's `window` is `{start: 2026-11-02T21:00:00Z, end: 2026-11-03T02:00:00Z}`, and no Night sensor has a target at rank 1
- **THEN** the strip has a lane labelled `Target 1` with no bar

#### Scenario: Only a later night's bar on the axis
- **WHEN** the axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z, Target 1 has a target tonight with a window on the axis, Target 2 is unavailable, and Night 2 has a target at rank 2 whose window is from 2026-11-01T22:00:00Z to 2026-11-02T03:00:00Z
- **THEN** the strip has a lane labelled `Target 2` with no bar

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw for the new axis, by the rules of the opening axis, every row's cells, the Cloud range columns, the Moon up bars, the target bars, the Temperature chart's lines, dots and hover areas, the lines with their labels, and the time labels. The row and lane labels, and the Temperature chart's key and scale, SHALL stay put. Target bars come from every night: tonight's from the Target sensors, and each later night's from its Night sensor.

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
- **AND** its key and its scale labels are as before the pan

### Requirement: An item is the same after a redraw when it has the same place in the strip
After a redraw, the card SHALL take as the same item: the cell or Cloud range column of the same row for the same hour; the Temperature chart hour with the same start; the Moon up bar whose run starts in the same hour; the bar of the same night in the same target lane; the line of the same kind for the same night; the message on the same row, lane or key entry; and the moon drawing.

#### Scenario: A new target in the lane
- **WHEN** the box shows the text of the bar in the lane labelled `Target 1`, and Home Assistant updates Target 1 to the Orion Nebula (M42) with a window from 06:00 to 10:00
- **THEN** the box reads `Orion Nebula (M42) from 06:00 to 10:00`

#### Scenario: A later night's target changes
- **WHEN** Home Assistant's time zone is `UTC`, the box shows the text of Night 2's bar in the lane labelled `Target 1`, and Home Assistant updates Night 2's first target to the Pleiades (M45) with a window from 2026-11-01T21:00:00Z to 2026-11-02T04:00:00Z
- **THEN** the box reads `Pleiades (M45) from 21:00 to 04:00`, above Night 2's bar
- **AND** tonight's bar in the same lane keeps its own text

#### Scenario: The moon rises an hour later
- **WHEN** the box shows the text of a Moon up bar whose run starts in the hour from 16:00, and Home Assistant updates the moon altitude forecast so that the run starts in the hour from 17:00
- **THEN** the card shows no box

#### Scenario: The message changes
- **WHEN** the box shows `sensor.pierpressure_backyard_seeing is unavailable` from a tap on the Seeing row's message, and the sensor's state becomes `unknown` with no forecast
- **THEN** the box reads `sensor.pierpressure_backyard_seeing has no forecast for these hours`

#### Scenario: A later night's dusk moves
- **WHEN** Home Assistant's time zone is `UTC`, the box shows `Dusk, 20:32` from a tap on Night 2's dusk line, and Home Assistant updates Night 2's `dark_window.start` to 2026-11-01T20:33:00Z
- **THEN** the box reads `Dusk, 20:33`, above Night 2's dusk line

### Requirement: The docs describe panning the strip
`docs/night-card.md` SHALL describe panning the strip:

- that the strip opens on the judged night;
- the inputs that pan it, and that an up or down swipe scrolls the page;
- that it stops at the first and last forecast hour;
- that up to three later nights have dusk and dawn lines and their own target bars, read from the Night 2 to Night 4 sensors;
- that a row says "No forecast" past its weather source's last hour;
- the `Back to tonight` button.

#### Scenario: The page covers panning
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words drag, swipe, trackpad, arrow keys and `Back to tonight`
- **AND** it says the strip opens on the judged night, and stops at the first and last forecast hour
- **AND** it names `sensor.pierpressure_<pier>_night_2` and says a later night has its own target bars
- **AND** it no longer says that a later night has no target bars, or that another night has no dusk line or dawn line
- **AND** its "No forecast" help names a later night past a weather source's last hour as a cause

### Requirement: The docs describe the target lanes
`docs/night-card.md` SHALL describe the target lanes:

- that tonight's bars read `sensor.pierpressure_<pier>_target_1` to `sensor.pierpressure_<pier>_target_10`, a later night's bars read its Night sensor's `targets`, and each lane is labelled `Target <n>`;
- that a bar runs from the start to the end of the target's observable window and holds the target's name and catalog id;
- that a lane can hold a bar for each night, each named for that night's target, ranked on that night's own moon;
- what hovering over a bar shows;
- that a rank with no target on any night leaves no lane;
- that the dusk, dawn and now lines cross the target lanes.

#### Scenario: The page covers the target lanes
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the sensors `sensor.pierpressure_<pier>_target_1` and `sensor.pierpressure_<pier>_target_10` and the lane label `Target 1`
- **AND** it names the words observable window, catalog id, own moon, no target on any night and leaves no lane

## REMOVED Requirements

### Requirement: A rank with no target tonight leaves no lane

**Reason**: A lane now shows when its rank has a target on any night, not only
tonight.

**Migration**: Read the new requirement "A rank with no target on any night
leaves no lane". It keeps every rule for tonight's Target sensors and adds the
rule for a later night's entry.
