## ADDED Requirements

### Requirement: The card picker shows a preview
The card's entry in Home Assistant's list of custom cards SHALL ask for a preview, so the dashboard's card picker draws the card before it is added.

#### Scenario: The picker entry asks for a preview
- **WHEN** the file is loaded in a page
- **THEN** the entry in `window.customCards` whose `type` is `pierpressure-card` has `preview` equal to `true`

### Requirement: The card offers a starting configuration
When Home Assistant asks the card for a starting configuration, the card SHALL give `type: custom:pierpressure-card` with the `pier` value of the first pier the editor lists. When the editor lists no pier, the starting configuration SHALL have no `pier` key, and the card's preview shows the error "pier is required".

#### Scenario: Two piers are known
- **WHEN** Home Assistant has `sensor.pierpressure_frontyard_verdict` with the `pier` attribute `frontyard` and `sensor.pierpressure_backyard_verdict` with the `pier` attribute `backyard`, and asks for a starting configuration
- **THEN** the card gives `type: custom:pierpressure-card` and `pier: backyard`

#### Scenario: No pier is known
- **WHEN** Home Assistant has no entity whose id has the form `sensor.pierpressure_<slug>_verdict`, and asks for a starting configuration
- **THEN** the card gives `type: custom:pierpressure-card` and no `pier` key

### Requirement: The card has a visual editor
The card SHALL give Home Assistant a configuration editor when Home Assistant asks for one, so the card can be set up without YAML. The editor SHALL have one field, labelled **Pier**, that sets the card's `pier` key. Each change SHALL be reported to Home Assistant as the card's whole new configuration.

#### Scenario: Home Assistant asks for the editor
- **WHEN** Home Assistant asks the card for its configuration editor
- **THEN** it gets an element that takes the card's configuration and Home Assistant's state
- **AND** the element shows one field labelled **Pier**

### Requirement: The editor lists the known piers
The editor's **Pier** field SHALL list one pier for each entity in Home Assistant's states whose id has the form `sensor.pierpressure_<slug>_verdict`, where `<slug>` holds at least one character. Each pier SHALL be shown by the entity's `pier` attribute when it is a non-empty string, and otherwise by `<slug>`. The list SHALL be in alphabetical order of what it shows. No other entity SHALL add a pier.

#### Scenario: Two piers in alphabetical order
- **WHEN** Home Assistant has `sensor.pierpressure_frontyard_verdict` with the `pier` attribute `frontyard` and `sensor.pierpressure_back_yard_verdict` with the `pier` attribute `Back-Yard`
- **THEN** the **Pier** field lists `Back-Yard`, then `frontyard`

#### Scenario: A pier before its first verdict
- **WHEN** Home Assistant has `sensor.pierpressure_backyard_verdict` with the state `unknown` and no attributes
- **THEN** the **Pier** field lists `backyard`

#### Scenario: Other PierPressure sensors are not piers
- **WHEN** Home Assistant has `sensor.pierpressure_backyard_verdict`, `sensor.pierpressure_backyard_score` and `sensor.weather_verdict`
- **THEN** the **Pier** field lists only `backyard`

### Requirement: Picking a pier sets a value that finds its Verdict sensor
When the user picks a listed pier, the editor SHALL set `pier` to the entity's `pier` attribute if the card's slug rule turns that attribute into the entity's `<slug>`. Otherwise the editor SHALL set `pier` to `<slug>`, so the card always reads the Verdict sensor the user picked.

#### Scenario: A pier id the slug rule matches
- **WHEN** the user picks the pier listed for `sensor.pierpressure_back_yard_verdict`, whose `pier` attribute is `Back-Yard`
- **THEN** the editor reports a configuration with `pier: Back-Yard`

#### Scenario: A pier id the slug rule cannot match
- **WHEN** the user picks the pier listed for `sensor.pierpressure_dong_jing_verdict`, whose `pier` attribute is `東京`
- **THEN** the editor reports a configuration with `pier: dong_jing`

#### Scenario: A pier with no attributes yet
- **WHEN** the user picks the pier listed for `sensor.pierpressure_backyard_verdict`, which has no attributes
- **THEN** the editor reports a configuration with `pier: backyard`

### Requirement: The editor keeps the rest of the configuration
When the editor reports a new configuration, it SHALL change only the `pier` key and keep every other key and value as it was.

#### Scenario: A key the editor does not edit
- **WHEN** the card is configured with `type: custom:pierpressure-card`, `pier: backyard` and `title: Garden`, and the user picks `frontyard`
- **THEN** the editor reports `type: custom:pierpressure-card`, `pier: frontyard` and `title: Garden`

### Requirement: The editor keeps a pier it does not list
When the configured `pier` is not among the listed piers, the editor SHALL show it as the **Pier** field's current value. The editor SHALL NOT report a new configuration until the user changes the field.

#### Scenario: A pier Home Assistant has lost
- **WHEN** the card is configured with `pier: oldpier` and Home Assistant has no `sensor.pierpressure_oldpier_verdict`
- **THEN** the **Pier** field shows `oldpier` as its current value
- **AND** the editor reports no new configuration

### Requirement: The editor accepts a typed pier
The **Pier** field SHALL accept a pier the user types, as well as one picked from the list, and SHALL set `pier` to the typed text unchanged.

#### Scenario: A pier that has not published yet
- **WHEN** the user types `garden` in the **Pier** field
- **THEN** the editor reports a configuration with `pier: garden`

### Requirement: The editor says when it finds no pier
When the editor lists no pier, it SHALL say "No PierPressure piers found" and SHALL still accept a typed pier.

#### Scenario: PierPressure has never published
- **WHEN** Home Assistant has no entity whose id has the form `sensor.pierpressure_<slug>_verdict`
- **THEN** the editor shows "No PierPressure piers found"
- **AND** the **Pier** field still accepts a typed pier

## MODIFIED Requirements

### Requirement: The docs show how to configure the card
`docs/night-card.md` SHALL say how to add the card from the dashboard's card picker and pick the pier in the visual editor's **Pier** list. It SHALL also show the card's configuration as YAML with `type: custom:pierpressure-card` and a `pier` key, as the other route. It SHALL also say how to find the pier's Verdict entity id in Home Assistant, for a pier id that the card's slug rule cannot match.

#### Scenario: The page describes the visual editor
- **WHEN** `docs/night-card.md` is read
- **THEN** it says to pick the card from the card picker and the pier from the **Pier** list

#### Scenario: The page holds a card configuration
- **WHEN** the YAML block in `docs/night-card.md` is parsed
- **THEN** it is a card with `type: custom:pierpressure-card` and a `pier` key

#### Scenario: The page says where to find the entity id
- **WHEN** `docs/night-card.md` is read
- **THEN** it names `sensor.pierpressure_<pier>_verdict` and says where Home Assistant lists entity ids
