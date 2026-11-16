## MODIFIED Requirements

### Requirement: A target bar holds the target's name
Each target bar SHALL show the target's name and its catalog id as `<name> (<id>)`, read from the Target sensor's `name` and `id` attributes. When `name` is null or empty, the bar SHALL show `<id>` alone. When the attributes hold no `id`, the bar SHALL show the Target sensor's state.

#### Scenario: A named target
- **WHEN** `sensor.pierpressure_backyard_target_1` has the state `Andromeda Galaxy`, the attributes `name: Andromeda Galaxy` and `id: M31`, and a window on the axis
- **THEN** the lane labelled `Target 1` has a bar whose text is `Andromeda Galaxy (M31)`

#### Scenario: A target the catalog does not name
- **WHEN** Target 1 has the state `IC2184`, the attributes `name: null` and `id: IC2184`, and a window on the axis
- **THEN** the lane labelled `Target 1` has a bar whose text is `IC2184`

#### Scenario: An empty name
- **WHEN** Target 1 has the state `NGC7000`, the attributes `name: ""` and `id: NGC7000`, and a window on the axis
- **THEN** the lane labelled `Target 1` has a bar whose text is `NGC7000`

#### Scenario: An older PierPressure with no id attribute
- **WHEN** Target 1 has the state `Andromeda Galaxy`, no `id` attribute, and a window on the axis
- **THEN** the lane labelled `Target 1` has a bar whose text is `Andromeda Galaxy`

### Requirement: Hovering over a target bar shows its window
Hovering over a target bar SHALL show `<text> from <HH:MM> to <HH:MM>`, and a screen reader SHALL read the same. `<text>` SHALL be the bar's text. The two times SHALL be the window's own start and end in Home Assistant's time zone, even where the axis cuts the bar off. When the window lasts 24 hours or more, or its start and end read the same `HH:MM`, the hover SHALL show `<text>` alone.

#### Scenario: A window in UTC
- **WHEN** Home Assistant's time zone is `UTC`, Target 1 has the attributes `name: Andromeda Galaxy` and `id: M31`, and its `window` is `{start: 2026-10-31T21:00:00Z, end: 2026-11-01T02:00:00Z}`
- **THEN** hovering over its bar shows `Andromeda Galaxy (M31) from 21:00 to 02:00`
- **AND** the bar's accessible name is `Andromeda Galaxy (M31) from 21:00 to 02:00`

#### Scenario: A window cut off at the axis end
- **WHEN** Home Assistant's time zone is `UTC`, the axis ends at 2026-11-01T08:25:00Z, Target 1 has the attributes `name: Orion Nebula` and `id: M42`, and its `window` is `{start: 2026-11-01T06:00:00Z, end: 2026-11-01T10:00:00Z}`
- **THEN** hovering over its bar shows `Orion Nebula (M42) from 06:00 to 10:00`

#### Scenario: A target up all through a polar night
- **WHEN** Home Assistant's time zone is `UTC`, Target 1 has the attributes `name: null` and `id: IC2184`, and its `window` is `{start: 2026-12-21T10:58:02Z, end: 2026-12-22T10:58:32Z}`
- **THEN** hovering over its bar shows `IC2184`

### Requirement: The docs describe the target lanes
`docs/night-card.md` SHALL describe the target lanes:

- that each lane reads one of `sensor.pierpressure_<pier>_target_1` to `sensor.pierpressure_<pier>_target_10`, and is labelled `Target <n>`;
- that its bar runs from the start to the end of the target's observable window and holds the target's name and catalog id;
- that a bar too short for both shortens the name and keeps the id;
- what hovering over a bar shows;
- that a rank with no target tonight leaves no lane;
- that the dusk, dawn and now lines cross the target lanes.

#### Scenario: The page covers the target lanes
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the sensors `sensor.pierpressure_<pier>_target_1` and `sensor.pierpressure_<pier>_target_10` and the lane label `Target 1`
- **AND** it names the words observable window, catalog id, no target tonight and leaves no lane

## ADDED Requirements

### Requirement: A narrow target bar keeps the target's id
When a target bar is too narrow for `<name> (<id>)`, the card SHALL shorten the name and end it in `…`, and SHALL keep `(<id>)` whole after it. Only when the bar is too narrow for `(<id>)` alone SHALL the id be cut off.

#### Scenario: A bar too short for the name
- **WHEN** Target 1 has the attributes `name: Andromeda Galaxy` and `id: M31`, and its bar is wide enough for `Androm… (M31)` but not for `Andromeda Galaxy (M31)`
- **THEN** the bar shows the start of `Andromeda Galaxy` ending in `…`, followed by `(M31)` in full

#### Scenario: A bar wide enough for the whole text
- **WHEN** Target 1 has the attributes `name: Andromeda Galaxy` and `id: M31`, and its bar is wider than `Andromeda Galaxy (M31)`
- **THEN** the bar shows `Andromeda Galaxy (M31)` with no `…`
