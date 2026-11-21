<!-- Plain language: Name the actor, condition and observable result. Explain necessary domain terms using the agreed glossary. Keep requirement and scenario headings and WHEN/THEN syntax exactly as required. -->

## ADDED Requirements

### Requirement: A tap on a strip item shows its hover text
A tap on an item of the night strip SHALL show that item's hover text in a box on the card. The items are a row's cell, a Cloud range column, a Moon up bar, a target bar, a dusk, dawn or now line, and an hour of the Temperature chart. A tap where a line crosses another item SHALL show the line's text, as hovering does. The hover texts SHALL stay as they are.

#### Scenario: A Cloud cover cell
- **WHEN** Home Assistant's time zone is `UTC`, the Cloud cover forecast holds 52 at 2026-11-01T04:00:00Z, and the user taps that cell
- **THEN** the card shows a box that reads `Cloud cover, the hour from 04:00: 52%`
- **AND** the cell's hover text is still `Cloud cover, the hour from 04:00: 52%`

#### Scenario: An hour of the Temperature chart
- **WHEN** Home Assistant's time zone is `UTC`, the Temperature and Dew point forecasts hold 4.2 and 1.5 at 2026-10-31T21:00:00Z, and the user taps that hour of the Temperature chart
- **THEN** the card shows a box that reads `The hour from 21:00: Temperature 4.2 °C, Dew point 1.5 °C`

#### Scenario: A Cloud range column
- **WHEN** Home Assistant's time zone is `UTC`, the cloud cover min and max forecasts hold 40 and 70.5 at 2026-10-31T21:00:00Z, and the user taps that column
- **THEN** the card shows a box that reads `Cloud range, the hour from 21:00: 40% to 70.5%`

#### Scenario: A target bar
- **WHEN** Target 1 is the Andromeda Galaxy (M31), its window runs from 21:00 to 02:00 in Home Assistant's time zone, and the user taps its bar
- **THEN** the card shows a box that reads `Andromeda Galaxy (M31) from 21:00 to 02:00`

#### Scenario: The dusk line
- **WHEN** dusk is at 20:30 in Home Assistant's time zone, and the user taps the dusk line
- **THEN** the card shows a box that reads `Dusk, 20:30`

### Requirement: A tap on a message shows its hover text
A tap on a message SHALL show the message's hover text in a box on the card, as a tap on a strip item does. The messages are `Not found`, `Unavailable` or `No forecast` on a row, on the Moon up lane, or beside a line's name in the Temperature chart's key.

#### Scenario: A row's message
- **WHEN** `sensor.pierpressure_backyard_seeing` has the state `unavailable`, and the user taps the Seeing row's message
- **THEN** the card shows a box that reads `sensor.pierpressure_backyard_seeing is unavailable`

#### Scenario: The Moon up lane's message
- **WHEN** Home Assistant has no `sensor.pierpressure_backyard_moon_altitude`, and the user taps the Moon up lane's message
- **THEN** the card shows a box that reads `sensor.pierpressure_backyard_moon_altitude is not in Home Assistant`

#### Scenario: A message in the Temperature chart's key
- **WHEN** Home Assistant has no `sensor.pierpressure_backyard_dew_point`, and the user taps the message beside `Dew point` in the chart's key
- **THEN** the card shows a box that reads `sensor.pierpressure_backyard_dew_point is not in Home Assistant`

#### Scenario: The Cloud range message
- **WHEN** the strip shows a Cloud range row with no column because Home Assistant has no `sensor.pierpressure_backyard_cloud_cover_max`, and the user taps the row's message
- **THEN** the card shows a box that reads `sensor.pierpressure_backyard_cloud_cover_max is not in Home Assistant`

### Requirement: A tap on the moon drawing shows its text
A tap on the moon drawing beside the verdict SHALL show the drawing's text in a box on the card.

#### Scenario: A waxing gibbous moon
- **WHEN** `moon.phase` is `waxing gibbous`, `moon.illumination` is `0.78`, and the user taps the moon drawing
- **THEN** the card shows a box that reads `Moon: waxing gibbous, 78% lit`

### Requirement: A tap is a press and release that stays in place
A tap SHALL be one press and release of a touch, a pen or a mouse's main button that moves no more than 8 px sideways and no more than 8 px up or down. A gesture that pans the strip, moves further or that the browser cancels, such as to scroll the page, SHALL open no box. While one pointer is pressed, the card SHALL ignore every other pointer, such as a second finger.

#### Scenario: A mouse click
- **WHEN** the user clicks a Cloud cover cell with the mouse's main button
- **THEN** the card shows a box with the cell's hover text

#### Scenario: A tap that slips
- **WHEN** the user presses on a Cloud cover cell with a finger, moves 5 px to the left and lifts it
- **THEN** the card shows a box with the cell's hover text, and the strip's axis is unchanged

#### Scenario: A drag that pans
- **WHEN** the reach runs further than the axis, and the user presses on a Cloud cover cell, drags 40 px to the left and releases
- **THEN** the strip pans, and the card shows no box

#### Scenario: A drag that does not pan
- **WHEN** the user presses on a Cloud cover cell with the mouse, moves 30 px down and releases
- **THEN** the card shows no box

#### Scenario: Scrolling past the card on a phone
- **WHEN** a finger on a Cloud cover cell moves 4 px to the left and 12 px up, and the browser then cancels the gesture to scroll the page
- **THEN** the card shows no box

### Requirement: The box sits above its item without moving the card
The box SHALL sit just above its item, or just below it when the card has no room above. The box SHALL stay inside the card and wrap text that is too long for one line. Showing, changing or closing the box SHALL move nothing else on the card. Only one box SHALL show at a time.

#### Scenario: The card does not move
- **WHEN** the user taps a Cloud cover cell
- **THEN** every row, lane, label and reason on the card is where it was before the tap

#### Scenario: An item near the card's right edge
- **WHEN** the user taps the last cell of the Cloud cover row, at the card's right edge
- **THEN** the box's right edge is inside the card

#### Scenario: An item at the top of the card
- **WHEN** the card has no room above the moon drawing for the box, and the user taps the drawing
- **THEN** the box shows just below the drawing, inside the card

#### Scenario: A long text
- **WHEN** the card is 320 px wide, and the user taps the message of a row whose hover text is `sensor.pierpressure_backyard_precipitation_probability has no forecast for these hours`
- **THEN** the box shows the whole text on more than one line, inside the card

### Requirement: A tap elsewhere or on the same item closes the box
While a box shows, a tap on another item or message SHALL show that one's text instead. A tap on the same item again SHALL close the box. A tap anywhere else on the card SHALL close it, such as on a row's label, an empty part of a track, the verdict or the reasons.

#### Scenario: A second tap on the same cell
- **WHEN** the box shows a Cloud cover cell's text, and the user taps that cell again
- **THEN** the card shows no box

#### Scenario: A tap on another cell
- **WHEN** Home Assistant's time zone is `UTC`, the box shows `Cloud cover, the hour from 04:00: 52%`, the Seeing forecast holds 0.62 at 2026-10-31T21:00:00Z, and the user taps that Seeing cell
- **THEN** the card shows one box, and it reads `Seeing, the hour from 21:00: 0.62`

#### Scenario: A tap on a row's label
- **WHEN** the box shows a Cloud cover cell's text, and the user taps the label `Seeing`
- **THEN** the card shows no box

### Requirement: Panning the strip closes the box
When the strip's axis moves while a box shows, the card SHALL close the box. This SHALL apply to every input that pans the strip: a drag, a sideways wheel or trackpad swipe, an arrow key, and `Back to tonight`. A pan the reach stops entirely SHALL leave the box as it is.

#### Scenario: A drag
- **WHEN** the box shows a Cloud cover cell's text, the reach runs further than the axis, and the user drags the strip 40 px to the left
- **THEN** the strip pans, and the card shows no box

#### Scenario: An arrow key
- **WHEN** the box shows a Cloud cover cell's text, the strip has keyboard focus, the reach runs further, and the user presses the Right arrow key
- **THEN** the strip's axis moves one hour later, and the card shows no box

#### Scenario: Back to tonight
- **WHEN** the user has panned the axis 24 hours later, the box shows a Cloud cover cell's text, and the user selects `Back to tonight`
- **THEN** the strip's axis is the opening axis, and the card shows no box

#### Scenario: An arrow key at the end of the reach
- **WHEN** the box shows a Cloud cover cell's text, the axis ends where the reach ends, and the user presses the Right arrow key with the strip focused
- **THEN** the box still shows the cell's text

### Requirement: An open box follows its item when the card redraws
When the card redraws, such as when Home Assistant updates a sensor or the minute timer moves the now line, an open box SHALL stay on its item, sit above the item where it now is, and show the item's latest hover text. The box SHALL close when the item is no longer on the card.

#### Scenario: The now line moves on
- **WHEN** Home Assistant's time zone is `UTC`, the box shows `Now, 21:00` from a tap on the now line, and the browser's clock moves on to 21:01
- **THEN** the box reads `Now, 21:01`, above the now line

#### Scenario: A new forecast for the hour
- **WHEN** Home Assistant's time zone is `UTC`, the box shows `Cloud cover, the hour from 04:00: 52%`, and Home Assistant updates the Cloud cover forecast to hold 60 at 2026-11-01T04:00:00Z
- **THEN** the box reads `Cloud cover, the hour from 04:00: 60%`

#### Scenario: The hour leaves the strip
- **WHEN** the box shows the text of the Cloud cover cell for the hour from 2026-10-31T16:00:00Z, and the opening axis moves on so that it no longer overlaps that hour
- **THEN** the card shows no box

#### Scenario: The verdict goes
- **WHEN** the box shows a Cloud cover cell's text, and the Verdict sensor's state becomes `unavailable`
- **THEN** the card shows `PierPressure is offline` and no box

### Requirement: An item is the same after a redraw when it has the same place in the strip
After a redraw, the card SHALL take as the same item: the cell or Cloud range column of the same row for the same hour; the Temperature chart hour with the same start; the Moon up bar whose run starts in the same hour; the bar in the same target lane; the line of the same kind; the message on the same row, lane or key entry; and the moon drawing.

#### Scenario: A new target in the lane
- **WHEN** the box shows the text of the bar in the lane labelled `Target 1`, and Home Assistant updates Target 1 to the Orion Nebula (M42) with a window from 06:00 to 10:00
- **THEN** the box reads `Orion Nebula (M42) from 06:00 to 10:00`

#### Scenario: The moon rises an hour later
- **WHEN** the box shows the text of a Moon up bar whose run starts in the hour from 16:00, and Home Assistant updates the moon altitude forecast so that the run starts in the hour from 17:00
- **THEN** the card shows no box

#### Scenario: The message changes
- **WHEN** the box shows `sensor.pierpressure_backyard_seeing is unavailable` from a tap on the Seeing row's message, and the sensor's state becomes `unknown` with no forecast
- **THEN** the box reads `sensor.pierpressure_backyard_seeing has no forecast for these hours`

### Requirement: The docs say a tap shows what hovering shows
`docs/night-card.md` SHALL say that on a phone, or with any pointer, a tap on a cell, column, bar, line, Temperature chart hour, message or the moon drawing shows its hover text in a box. It SHALL say that a tap elsewhere, a second tap on the same item, or a pan closes the box.

#### Scenario: The page covers tapping
- **WHEN** `docs/night-card.md` is read
- **THEN** it names the words tap, phone and box in the same paragraph as hover
- **AND** it says that a tap elsewhere, a second tap or a pan closes the box
