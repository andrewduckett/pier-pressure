## ADDED Requirements

### Requirement: The card shows a Moon section beside the verdict
The card SHALL show a Moon section beside its Verdict, Score and Confidence lines, above the strip. The section SHALL read only the Verdict sensor's `moon` attribute, and its `illumination`, `phase`, `rise` and `set` fields.

#### Scenario: A night with a waxing gibbous moon
- **WHEN** the Verdict sensor's `moon` attribute is `{illumination: 0.78, phase: "waxing gibbous", rise: "2026-10-31T21:14:00Z", set: null}` and Home Assistant's time zone is `UTC`
- **THEN** the card shows a moon drawing, the phase `Waxing gibbous`, the illumination `78%`, the moonrise `21:14` and the moonset `—`

### Requirement: The Moon section shows only with the verdict
The card SHALL show no Moon section when it shows no verdict: before Home Assistant gives it a state, and when it shows a message in place of the verdict.

#### Scenario: Before Home Assistant gives the card its state
- **WHEN** the card is configured and Home Assistant has not yet given it a state
- **THEN** the card shows no moon drawing and no moon text

#### Scenario: PierPressure is offline
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable` and a `moon` attribute
- **THEN** the card shows no moon drawing and no moon text

#### Scenario: A mistyped pier
- **WHEN** Home Assistant has no `sensor.pierpressure_frontyard_verdict` and the card is configured with `pier: frontyard`
- **THEN** the card shows no moon drawing and no moon text

### Requirement: The card shows the moon's phase
The card SHALL show the `moon.phase` field with its first letter in capitals. The valid phases are `new`, `waxing crescent`, `first quarter`, `waxing gibbous`, `full`, `waning gibbous`, `last quarter` and `waning crescent`. When the field is missing or holds any other value, the card SHALL show a dash, `—`, as the phase.

#### Scenario: Last quarter
- **WHEN** `moon.phase` is `last quarter`
- **THEN** the card shows the phase `Last quarter`

#### Scenario: An unknown phase name
- **WHEN** `moon.phase` is `blue`
- **THEN** the card shows `—` as the phase

### Requirement: The card shows the moon's illumination as a percent
The card SHALL show the `moon.illumination` field as a whole percent, rounded to the nearest whole number. When the field is missing, or is not a number from 0 to 1, the card SHALL show a dash, `—`, as the illumination.

#### Scenario: A new moon
- **WHEN** `moon.illumination` is `0`
- **THEN** the card shows the illumination `0%`

#### Scenario: Rounding
- **WHEN** `moon.illumination` is `0.996`
- **THEN** the card shows the illumination `100%`

#### Scenario: An illumination outside 0 to 1
- **WHEN** `moon.illumination` is `1.5`
- **THEN** the card shows `—` as the illumination

### Requirement: The card shows moonrise and moonset
The card SHALL show `moon.rise` as the moonrise and `moon.set` as the moonset. It SHALL show each as a time in Home Assistant's time zone on a 24-hour clock, as the strip shows times. When a field is null, missing or not a readable time, the card SHALL show a dash, `—`, for it.

#### Scenario: Moonrise in Tokyo
- **WHEN** Home Assistant's time zone is `Asia/Tokyo` and `moon.rise` is `2026-10-31T12:14:00Z`
- **THEN** the card shows the moonrise `21:14`

#### Scenario: The moon sets after dawn
- **WHEN** `moon.set` is null
- **THEN** the card shows `—` as the moonset

### Requirement: Before the first verdict the Moon section shows dashes
When the Verdict sensor has no `moon` attribute, or the attribute is not an object, the card SHALL show a dash, `—`, for each of the four moon texts.

#### Scenario: Before the first verdict
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unknown` and no attributes
- **THEN** the card shows `—` as the phase, the illumination, the moonrise and the moonset
- **AND** it shows no moon drawing

### Requirement: The moon drawing needs a phase and an illumination
The card SHALL draw the moon only when both the phase and the illumination are valid, as the requirements on showing them say. Otherwise it SHALL show no drawing, and the texts SHALL still show.

#### Scenario: A phase with no illumination
- **WHEN** `moon.phase` is `full` and the `moon` attribute has no `illumination`
- **THEN** the card shows no moon drawing
- **AND** it shows the phase `Full` and `—` as the illumination

### Requirement: The moon drawing lights the illumination's share of the disc
For a phase other than `new` and `full`, the drawing SHALL be a disc whose lit part lies between one edge of the disc and a terminator. Across the disc's middle, from edge to edge, the lit part SHALL span the illumination's share of the disc's width. The terminator SHALL be a straight line at an illumination of 0.5, and curved otherwise. An illumination of 0 SHALL draw no lit part, and 1 the whole disc lit. The drawing SHALL show no position angle, libration or earthshine.

#### Scenario: A first quarter
- **WHEN** `moon.phase` is `first quarter` and `moon.illumination` is `0.5`
- **THEN** half the disc is lit, and the terminator is a straight line through its middle

#### Scenario: Illumination at the ends of its range
- **WHEN** `moon.phase` is `waxing crescent` and `moon.illumination` is `0`, or `moon.phase` is `waxing gibbous` and `moon.illumination` is `1`
- **THEN** the first draws the disc's outline and no lit part, and the second the whole disc lit

#### Scenario: A waxing crescent
- **WHEN** `moon.phase` is `waxing crescent` and `moon.illumination` is `0.25`
- **THEN** across the disc's middle, the lit part spans a quarter of the disc's width

#### Scenario: A waning gibbous
- **WHEN** `moon.phase` is `waning gibbous` and `moon.illumination` is `0.75`
- **THEN** across the disc's middle, the lit part spans three quarters of the disc's width

### Requirement: Waxing is lit on the right in the northern hemisphere
For `waxing crescent`, `first quarter` and `waxing gibbous`, the lit part SHALL touch the disc's right edge. For `waning gibbous`, `last quarter` and `waning crescent`, it SHALL touch the left edge. When Home Assistant's latitude is below 0, the card SHALL mirror both: waxing touches the left edge and waning the right. When Home Assistant gives no latitude, the card SHALL draw as for the northern hemisphere.

#### Scenario: First quarter in the north
- **WHEN** Home Assistant's latitude is `52.1`, `moon.phase` is `first quarter` and `moon.illumination` is `0.5`
- **THEN** the right half of the disc is lit

#### Scenario: First quarter in the south
- **WHEN** Home Assistant's latitude is `-33.9`, `moon.phase` is `first quarter` and `moon.illumination` is `0.5`
- **THEN** the left half of the disc is lit

#### Scenario: No latitude
- **WHEN** Home Assistant gives no latitude, `moon.phase` is `waning crescent` and `moon.illumination` is `0.2`
- **THEN** the lit part touches the disc's left edge

### Requirement: A new moon is unlit and a full moon fully lit
For `new`, the card SHALL draw the disc with no lit part. For `full`, it SHALL draw the whole disc lit. Both SHALL hold whatever the illumination, since the phase does not say which side a sliver is on. An unlit disc SHALL still show its outline.

#### Scenario: A new moon with a sliver
- **WHEN** `moon.phase` is `new` and `moon.illumination` is `0.03`
- **THEN** the drawing shows the disc's outline and no lit part

#### Scenario: A full moon just past full
- **WHEN** `moon.phase` is `full` and `moon.illumination` is `0.96`
- **THEN** the whole disc is lit

### Requirement: The moon drawing has a text alternative
The drawing SHALL carry the text `Moon: <phase>, <illumination>% lit`, with the phase as the document gives it and the illumination as the card shows it. Hovering over the drawing SHALL show the same text, and a screen reader SHALL read it.

#### Scenario: A waxing gibbous moon
- **WHEN** `moon.phase` is `waxing gibbous` and `moon.illumination` is `0.78`
- **THEN** the drawing's text alternative and hover text are `Moon: waxing gibbous, 78% lit`

### Requirement: The docs describe the Moon section's texts
Where `docs/night-card.md` says what the card shows, it SHALL say that the Moon section reads the Verdict sensor's `moon` attribute, and describe the phase, the illumination, the moonrise and the moonset. It SHALL say that the moonrise and moonset are only those inside the dark window, and that a dash means the moon does not rise or set then.

#### Scenario: The page covers the Moon section's texts
- **WHEN** the part of `docs/night-card.md` before its "The night strip" section is read
- **THEN** it names Moon, Phase, Illumination, Moonrise, Moonset and dark window

### Requirement: The docs say how to read the moon drawing
Where `docs/night-card.md` describes the Moon section, it SHALL say:

- the drawing's lit part is the illumination's share of the disc;
- a waxing moon is lit on the right and a waning moon on the left;
- the card mirrors both when Home Assistant's location is south of the equator;
- the card takes the hemisphere from Home Assistant's location, not the pier's, so a pier in the other hemisphere shows the moon mirrored;
- the card draws a new moon unlit and a full moon fully lit.

#### Scenario: The page says how to read the drawing
- **WHEN** the part of `docs/night-card.md` before its "The night strip" section is read
- **THEN** it names waxing, waning, right, left, south, Home Assistant, new and full
