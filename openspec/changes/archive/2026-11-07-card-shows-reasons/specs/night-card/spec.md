## ADDED Requirements

### Requirement: The card lists the verdict's reasons
The card SHALL read the Verdict sensor's `reasons` attribute and show each reason as one item of a list named `Reasons`, in the attribute's order. The list SHALL sit under the Verdict, Score and Confidence lines and the Moon section, and before the note `No astronomical darkness tonight`, the `Back to tonight` button and the strip.

#### Scenario: A gated NO-GO
- **WHEN** the Verdict sensor has the state `NO-GO`, its `score` attribute is null, and its `reasons` attribute is `["Wind gust over the 40 km/h limit during the dark window."]`
- **THEN** the card shows a list named `Reasons` with one item, `Wind gust over the 40 km/h limit during the dark window.`
- **AND** the list comes after the Moon section and before the strip

#### Scenario: A scored night keeps the order
- **WHEN** the Verdict sensor has the state `GO` and its `reasons` attribute is `["Cloud: 90% of the dark window usable.", "Atmosphere factor 95%.", "Score 86/100."]`
- **THEN** the list shows three items, in that order

#### Scenario: A night with no astronomical darkness
- **WHEN** the Verdict sensor has the state `NO-GO`, its `dark_window` is `{start: null, end: null}`, and its `reasons` attribute is `["No astronomical night tonight: the sun never drops below -18°."]`
- **THEN** the card shows the list with that reason, then the note `No astronomical darkness tonight`, then the strip

### Requirement: The card shows every reason in full
The card SHALL show every item of the list at every card width. It SHALL offer no control that hides or shortens the list.

#### Scenario: Ten reasons
- **WHEN** the Verdict sensor's `reasons` attribute holds ten strings
- **THEN** the list shows ten items, each with its whole text
- **AND** the list holds no button and no `details` element

### Requirement: Reasons that are not a list of strings show no list
The card SHALL show no list when the `reasons` attribute is missing, null, an empty list, not a list, or a list with an item that is not a string. The card SHALL render the rest as usual and SHALL NOT throw.

#### Scenario: No reasons attribute
- **WHEN** the Verdict sensor has the state `GO` and no `reasons` attribute
- **THEN** the card shows no `Reasons` list and still shows the verdict and the strip

#### Scenario: An empty list
- **WHEN** the Verdict sensor's `reasons` attribute is `[]`
- **THEN** the card shows no `Reasons` list

#### Scenario: A string, not a list
- **WHEN** the Verdict sensor's `reasons` attribute is `"Score 72/100."`
- **THEN** the card shows no `Reasons` list

#### Scenario: A list with a number in it
- **WHEN** the Verdict sensor's `reasons` attribute is `["Score 72/100.", 3]`
- **THEN** the card shows no `Reasons` list

### Requirement: The reasons list shows only with the verdict
The card SHALL show no `Reasons` list when it shows no verdict: before Home Assistant gives it a state, and when it shows a message in place of the verdict.

#### Scenario: PierPressure is offline
- **WHEN** `sensor.pierpressure_backyard_verdict` has the state `unavailable` and a `reasons` attribute of `["Score 72/100."]`
- **THEN** the card shows that PierPressure is offline and shows no `Reasons` list

#### Scenario: Before the first verdict
- **WHEN** the Verdict sensor has the state `unknown` and no attributes
- **THEN** the card shows no `Reasons` list

#### Scenario: Reasons left over while the verdict is unknown
- **WHEN** the Verdict sensor has the state `unknown` and a `reasons` attribute of `["Score 72/100."]`
- **THEN** the card shows `—` as the verdict and shows no `Reasons` list

### Requirement: A reason's UTC times show in Home Assistant's time zone
In each reason, the card SHALL show every UTC time written as `YYYY-MM-DDTHH:MM:SSZ` as a 24-hour `HH:MM` in Home Assistant's time zone, as the strip shows times. The card SHALL leave the rest of the reason's text as it is, and SHALL leave a time it cannot read as it is.

#### Scenario: The span line
- **WHEN** Home Assistant's time zone is `UTC` and a reason is `Scored from 2026-10-31T21:00:00Z to 2026-11-01T03:25:00Z (the rest of tonight).`
- **THEN** the list shows `Scored from 21:00 to 03:25 (the rest of tonight).`

#### Scenario: Another time zone
- **WHEN** Home Assistant's time zone is `Europe/Paris` and a reason is `Scored from 2026-10-31T21:00:00Z to 2026-11-01T03:25:00Z (the rest of tonight).`
- **THEN** the list shows `Scored from 22:00 to 04:25 (the rest of tonight).`

#### Scenario: A reason with no time
- **WHEN** a reason is `Atmosphere factor 95%.`
- **THEN** the list shows `Atmosphere factor 95%.`

#### Scenario: A time that is not a real time
- **WHEN** a reason is `Scored from 2026-13-45T21:00:00Z onwards.`
- **THEN** the list shows `Scored from 2026-13-45T21:00:00Z onwards.`

### Requirement: The docs describe the reasons
Where `docs/night-card.md` says what the card shows, it SHALL have a **Reasons** line. The line SHALL say:

- that the card lists the Verdict sensor's reasons in order;
- that a gated `NO-GO` names its failed gate there;
- that times in a reason show in the Home Assistant time zone;
- that equipment notes come after the scoring reasons.

#### Scenario: The table covers the reasons
- **WHEN** the "What the card shows" section of `docs/night-card.md` is read
- **THEN** it has a line that starts with **Reasons**
- **AND** that line names `NO-GO`, gate, time zone and equipment

## MODIFIED Requirements

### Requirement: The card's size grows with its target lanes
The card SHALL report a size of 10 to Home Assistant, plus 1 for every three target lanes it shows, rounding up, plus 1 for every two reasons it shows, rounding up.

#### Scenario: No targets
- **WHEN** the strip has no target lane and the card shows no reason
- **THEN** the card reports a size of 10

#### Scenario: Four targets
- **WHEN** the strip has four target lanes and the card shows no reason
- **THEN** the card reports a size of 12

#### Scenario: Ten targets
- **WHEN** the strip has ten target lanes and the card shows no reason
- **THEN** the card reports a size of 14

#### Scenario: Three reasons
- **WHEN** the strip has no target lane and the card shows three reasons
- **THEN** the card reports a size of 12

#### Scenario: Targets and reasons
- **WHEN** the strip has four target lanes and the card shows one reason
- **THEN** the card reports a size of 13

#### Scenario: Offline with reasons left over
- **WHEN** the Verdict sensor has the state `unavailable` and a `reasons` attribute that holds four strings
- **THEN** the card reports a size of 10
