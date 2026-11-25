<!-- Plain language: Name the actor, condition and observable result. Explain necessary domain terms using the agreed glossary. Keep requirement and scenario headings and WHEN/THEN syntax exactly as required. -->

## ADDED Requirements

### Requirement: Each row, the Moon up lane and each key entry has an icon
The card SHALL draw a 16 px icon in each row's label, in the Moon up lane's label, and in the Temperature and Dew point entries of the Temperature chart's key. Each icon SHALL be drawn in Home Assistant's secondary text colour. Each icon SHALL carry its row's, lane's or entry's name as its `title` and its `aria-label`. A target lane's label SHALL have no icon.

#### Scenario: The Seeing row's icon
- **WHEN** the Verdict sensor has the state `GO`
- **THEN** the Seeing row's label holds an icon whose `title` and `aria-label` are both `Seeing`

#### Scenario: Every label but a target lane's
- **WHEN** the Verdict sensor has the state `GO`, the strip shows the Cloud range row, and Target 1 has a target tonight
- **THEN** each of the fourteen rows, the Moon up lane, and the Temperature and Dew point key entries has exactly one icon
- **AND** the lane for Target 1 has no icon

#### Scenario: The key entries' icons
- **WHEN** the Verdict sensor has the state `GO`
- **THEN** the Temperature chart's key holds an icon named `Temperature`, then an icon named `Dew point`, each beside its line's colour sample

### Requirement: The layout follows the card's own width
The card SHALL choose its layout from its own width, not the browser window's. A card 450 px or wider SHALL use the wide layout. A card narrower than 450 px SHALL use the narrow layout. No card option SHALL force either layout.

#### Scenario: A narrow card on a wide screen
- **WHEN** the card is 340 px wide in a browser window 1920 px wide
- **THEN** the card uses the narrow layout

#### Scenario: A wide card
- **WHEN** the card is 600 px wide
- **THEN** the card uses the wide layout

#### Scenario: At the cut-off
- **WHEN** the card is 450 px wide
- **THEN** the card uses the wide layout

### Requirement: A card 450 px or wider shows each icon beside its label
On a card 450 px or wider, each row's label, the Moon up lane's label and each key entry SHALL show its icon, then its name as text. A target lane SHALL show `Target <n>` as text, with no icon. The card SHALL show no legend.

#### Scenario: The wide labels
- **WHEN** the card is 600 px wide, the Verdict sensor has the state `GO`, and Target 1 has a target tonight
- **THEN** the Seeing row's label shows the Seeing icon, then `Seeing`
- **AND** the lane for Target 1 shows `Target 1` and no rank number on its own
- **AND** the card shows no legend

### Requirement: A card narrower than 450 px shows only the icons
On a card narrower than 450 px, each row's label, the Moon up lane's label and each key entry SHALL show its icon and hide its name. A key entry SHALL still show its colour sample beside its icon, and its message when it has one. A target lane's label SHALL show only its rank number, `1` to `10`. The rows, the lanes and their order SHALL be as on a card 450 px or wider.

#### Scenario: The narrow labels
- **WHEN** the card is 340 px wide, the Verdict sensor has the state `GO`, and Target 3 has a target tonight
- **THEN** the Seeing row's label shows the Seeing icon and no text
- **AND** the lane for Target 3 shows `3`
- **AND** the Temperature key entry shows its orange sample and its icon, and no text

#### Scenario: Two targets on a narrow card
- **WHEN** the card is 340 px wide, and Target 1 and Target 2 each have a target tonight
- **THEN** the two target lanes' labels show `1` then `2`

#### Scenario: A message on a narrow card
- **WHEN** the card is 340 px wide, the Temperature forecast holds values inside the axis, and Home Assistant has no `sensor.pierpressure_backyard_dew_point`
- **THEN** the Dew point key entry shows its sample, its icon and `Not found`

#### Scenario: A screen reader on a narrow card
- **WHEN** the card is 340 px wide and a screen reader reads the Seeing row's label
- **THEN** it reads `Seeing` once

### Requirement: The strip's legend names each icon
On a card narrower than 450 px, the card SHALL show a legend under the strip. The legend SHALL pair each icon the strip draws with its name, in the strip's top-to-bottom order: the rows, the Moon up lane, then the Temperature and Dew point key entries. A row the strip leaves out SHALL have no legend entry. When the strip has at least one target lane, the legend SHALL end with an entry that pairs a rank number with `Target rank`. The legend SHALL stay put while the strip pans.

#### Scenario: The legend with Cloud range and targets
- **WHEN** the card is 340 px wide, the Verdict sensor has the state `GO`, the strip shows the Cloud range row, and Target 1 has a target tonight
- **THEN** the legend's entries read, in order, `Sun altitude`, `Moon altitude`, `Cloud cover`, `Cloud range`, `Cloud low`, `Cloud mid`, `Cloud high`, `Wind gust`, `Seeing`, `Transparency`, `Humidity`, `Wind speed`, `Wind direction`, `Rain chance`, `Moon up`, `Temperature`, `Dew point` and `Target rank`
- **AND** each entry but `Target rank` shows the same icon as its row, lane or key entry

#### Scenario: No Cloud range row
- **WHEN** the card is 340 px wide and the strip leaves out the Cloud range row
- **THEN** the legend has no `Cloud range` entry

#### Scenario: No target lane
- **WHEN** the card is 340 px wide and no rank has a target on any night
- **THEN** the legend has no `Target rank` entry, and ends with `Dew point`

### Requirement: Hovering over an icon or a rank number shows its name
Hovering over an icon in the strip's label column SHALL show the name of its row, lane or key entry. On a card narrower than 450 px, hovering over a target lane's rank number SHALL show `Target <n>`.

#### Scenario: Hovering over an icon
- **WHEN** the user hovers over the Wind gust row's icon
- **THEN** the card shows `Wind gust`

#### Scenario: Hovering over a rank number
- **WHEN** the card is 340 px wide, Target 2 has a target tonight, and the user hovers over the rank number `2`
- **THEN** the card shows `Target 2`

### Requirement: A tap on an icon or a rank number shows its name
A tap on an icon in the strip's label column SHALL show the name of its row, lane or key entry in a box on the card, as a tap on a strip item does. On a card narrower than 450 px, a tap on a target lane's rank number SHALL show `Target <n>` in a box. A tap on the legend SHALL close the box, as a tap anywhere else on the card does.

#### Scenario: A tap on the Seeing icon
- **WHEN** the user taps the Seeing row's icon
- **THEN** the card shows a box that reads `Seeing`

#### Scenario: A tap on a key entry's icon
- **WHEN** the user taps the Dew point key entry's icon
- **THEN** the card shows a box that reads `Dew point`

#### Scenario: A tap on a rank number
- **WHEN** the card is 340 px wide, Target 3 has a target tonight, and the user taps the rank number `3`
- **THEN** the card shows a box that reads `Target 3`

#### Scenario: A tap on the legend
- **WHEN** the card is 340 px wide, the box shows `Seeing`, and the user taps the legend
- **THEN** the card shows no box

### Requirement: The °C labels leave the chart's hours readable and tappable
Each °C label SHALL stay readable where a Temperature chart line crosses it. A label SHALL not stop hovering over or tapping the chart hour under it: hovering or tapping where a label sits SHALL show that hour's text.

#### Scenario: A tap where a label sits
- **WHEN** Home Assistant's time zone is `UTC`, the axis starts at 2026-10-31T16:30:00Z, the Temperature forecast holds 4.2 at 2026-10-31T16:00:00Z, and the user taps the `15 °C` label
- **THEN** the card shows a box that reads `The hour from 16:00: Temperature 4.2 °C`

#### Scenario: A line under a label
- **WHEN** the Temperature line runs through the `10 °C` label at the plot's left edge
- **THEN** the label's text is drawn on a backing in the card's background colour, so the line does not run through the text

### Requirement: The docs describe the icons and the legend
`docs/night-card.md` SHALL describe the strip's labels:

- which labels have an icon, and that a target lane has none;
- that the layout follows the card's width, with a cut-off at 450 px;
- that a wide card shows each icon beside its label;
- that a narrower card shows only the icons and rank numbers, with a legend under the strip;
- that hovering over or tapping an icon or rank number shows its name.

#### Scenario: The page covers the icons and the legend
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words icon, legend, 450 px, rank number and `Target rank`
- **AND** it says the layout follows the card's width, not the screen's

## MODIFIED Requirements

### Requirement: Everything on the strip pans together
When the axis pans, the card SHALL draw for the new axis, by the rules of the opening axis, every row's cells, the Cloud range columns, the Moon up bars, the target bars, the Temperature chart's lines, dots and hover areas, the lines with their labels, and the time labels. The labels, the chart's key and its °C labels SHALL stay put. Target bars come from every night: tonight's from the Target sensors, and each later night's from its Night sensor.

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

### Requirement: The Temperature chart labels each 5 °C step
The chart SHALL draw a gridline at each multiple of 5 °C on its scale, and a label level with it that reads `<value> °C`. The labels SHALL sit inside the plot, at its left edge, over the lines, on every card. The gridlines and labels SHALL stay where they are while the strip pans. When neither forecast counts a number toward the scale, the chart SHALL be 32 px tall, with no gridline and no label.

#### Scenario: The labels from top to bottom
- **WHEN** the scale runs from −5 °C to 15 °C
- **THEN** the chart's labels read, top to bottom, `15 °C`, `10 °C`, `5 °C`, `0 °C` and `-5 °C`, each level with a gridline

#### Scenario: The labels are inside the plot
- **WHEN** the scale runs from −5 °C to 15 °C, on a card 600 px wide or on a card 340 px wide
- **THEN** each label is in the chart's track, at its left edge, and the chart's label column holds only the key

#### Scenario: A pan keeps the scale
- **WHEN** the scale runs from −5 °C to 15 °C and the user pans the axis 24 hours later
- **THEN** the chart's labels still read `15 °C`, `10 °C`, `5 °C`, `0 °C` and `-5 °C`

#### Scenario: No value at all
- **WHEN** both sensors have the state `unknown` and no attributes
- **THEN** the chart is 32 px tall, with no gridline and no label

### Requirement: The Temperature chart's lines are orange and green
The Temperature line SHALL be orange `#d97706`, and the Dew point line green `#15803d`, each with its dots. The key SHALL show a sample of each line's colour beside the line's icon and, on a card 450 px or wider, its name. Each colour SHALL have a contrast ratio of at least 3:1 against Home Assistant's default card background in the light theme, `#ffffff`, and in the dark theme, `#1c1c1c`. Contrast ratios are as WCAG 2.2 defines them.

#### Scenario: The two colours
- **WHEN** the Temperature and Dew point forecasts hold values inside the axis
- **THEN** the Temperature line and its key sample are `#d97706`, and the Dew point line and its key sample are `#15803d`

#### Scenario: Against the light and dark card
- **WHEN** the contrast ratio of each line's colour is computed against `#ffffff` and against `#1c1c1c`
- **THEN** all four are at least 3:1

### Requirement: A Temperature chart line that cannot draw says why
When a line holds no number for any hour that overlaps the axis, the key SHALL show a message beside that line's entry: `Not found`, `Unavailable` or `No forecast`, chosen as for a row with no cell. Hovering over the message SHALL name the sensor and the cause, as for a row's message. The chart SHALL keep its place, and SHALL draw the other line as usual. A line with a number for at least one such hour SHALL show no message.

#### Scenario: The dew point sensor is not there
- **WHEN** the Temperature forecast holds values inside the axis and Home Assistant has no `sensor.pierpressure_backyard_dew_point`
- **THEN** the key shows `Not found` beside `Dew point`, and no message beside `Temperature`
- **AND** the chart draws the Temperature line and no Dew point line
- **AND** hovering over the message shows `sensor.pierpressure_backyard_dew_point is not in Home Assistant`

#### Scenario: An unavailable sensor that kept its forecast
- **WHEN** `sensor.pierpressure_backyard_temperature` has the state `unavailable` and a `forecast` with values inside the axis
- **THEN** the key shows `Unavailable` beside `Temperature`, and the chart draws no Temperature line

#### Scenario: Before the first verdict
- **WHEN** both sensors have the state `unknown` and no attributes
- **THEN** the key shows `No forecast` beside `Temperature` and beside `Dew point`, and the chart draws no line

#### Scenario: Panned past the forecast
- **WHEN** the Temperature forecast's numbers end on 2026-11-01, and the user pans the axis to 2026-11-02, where the Dew point forecast still holds values
- **THEN** the key shows `No forecast` beside `Temperature`, and the chart draws the Dew point line

### Requirement: The docs describe the Temperature chart
`docs/night-card.md` SHALL describe the Temperature chart: where it sits on the strip and the two sensors it reads; that each point is at the middle of its hour; that a line breaks where an hour has no value; the °C scale, that its labels sit inside the chart's left edge, and that it stays put while the strip pans; the two colours and the key; that dew is more likely the closer the two lines come; what hovering shows; and its messages.

#### Scenario: The page covers the Temperature chart
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the Temperature chart and the sensors `sensor.pierpressure_<pier>_temperature` and `sensor.pierpressure_<pier>_dew_point`
- **AND** it names the words middle of the hour, break, °C, left edge, orange, green, key, dew and hover

### Requirement: A tap elsewhere or on the same item closes the box
While a box shows, a tap on another item or message SHALL show that one's text instead. A tap on the same item again SHALL close the box. A tap anywhere else on the card SHALL close it, such as on the text of a row's label, an empty part of a track, the legend, the verdict or the reasons.

#### Scenario: A second tap on the same cell
- **WHEN** the box shows a Cloud cover cell's text, and the user taps that cell again
- **THEN** the card shows no box

#### Scenario: A tap on another cell
- **WHEN** Home Assistant's time zone is `UTC`, the box shows `Cloud cover, the hour from 04:00: 52%`, the Seeing forecast holds 0.62 at 2026-10-31T21:00:00Z, and the user taps that Seeing cell
- **THEN** the card shows one box, and it reads `Seeing, the hour from 21:00: 0.62`

#### Scenario: A tap on a row's label
- **WHEN** the card is 600 px wide, the box shows a Cloud cover cell's text, and the user taps the text `Seeing` in the Seeing row's label
- **THEN** the card shows no box

#### Scenario: A tap on a row's icon while a box shows
- **WHEN** the box shows a Cloud cover cell's text, and the user taps the Seeing row's icon
- **THEN** the card shows one box, and it reads `Seeing`

### Requirement: An item is the same after a redraw when it has the same place in the strip
After a redraw, the card SHALL take as the same item: the cell or Cloud range column of the same row for the same hour; the Temperature chart hour with the same start; the Moon up bar whose run starts in the same hour; the bar of the same night in the same target lane; the line of the same kind for the same night; the message on the same row, lane or key entry; the icon of the same row, lane or key entry; the rank number of the same target lane; and the moon drawing.

#### Scenario: A new target in the lane
- **WHEN** the box shows the text of the bar in the lane labelled `Target 1`, and Home Assistant updates Target 1 to the Orion Nebula (M42) with a window from 06:00 to 10:00
- **THEN** the box reads `Orion Nebula (M42) from 06:00 to 10:00`

#### Scenario: A later night's target changes
- **WHEN** Home Assistant's time zone is `UTC`, the axis runs from 2026-10-31T16:30:00Z to 2026-11-02T08:25:00Z, Target 1 is the Andromeda Galaxy (M31) with a window from 2026-10-31T21:00:00Z to 2026-11-01T02:00:00Z, the box shows the text of Night 2's bar in the lane labelled `Target 1`, and Home Assistant updates Night 2's first target to the Pleiades (M45) with a window from 2026-11-01T21:00:00Z to 2026-11-02T04:00:00Z
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

#### Scenario: An icon's row stays
- **WHEN** the box shows `Seeing` from a tap on the Seeing row's icon, and Home Assistant updates the Seeing forecast
- **THEN** the box still reads `Seeing`, above the Seeing row's icon

#### Scenario: A rank number's lane goes
- **WHEN** the card is 340 px wide, the box shows `Target 3` from a tap on the rank number `3`, and Home Assistant updates the sensors so that rank 3 has no target on any night
- **THEN** the card shows no box

### Requirement: The docs say a tap shows what hovering shows
`docs/night-card.md` SHALL say that on a phone, or with any pointer, a tap on a cell, column, bar, line, Temperature chart hour, message, icon, rank number or the moon drawing shows its hover text in a box. It SHALL say that a tap elsewhere, a second tap on the same item, or a pan closes the box.

#### Scenario: The page covers tapping
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words tap, phone and box in the same paragraph as hover
- **AND** it names the words icon and rank number in that paragraph
- **AND** it says that a tap elsewhere, a second tap or a pan closes the box
