<!-- Plain language: Name the actor, condition and observable result. Explain necessary domain terms using the agreed glossary. Keep requirement and scenario headings and WHEN/THEN syntax exactly as required. -->

## MODIFIED Requirements

### Requirement: A Night sensor's attributes hold its night's entry

The adapter SHALL publish each Night sensor's attributes as a JSON object. When
`later_nights` has an entry for the sensor, the object SHALL be `available`
true, then `night` with the sensor's number, then the entry's keys with the
document's values: `dark_window`, `moon` and `targets`. Otherwise it SHALL be
`available` false and `night` only. The Night sensors SHALL stay the only
entities that carry a later night's moon and targets: no entity, topic or state
is added for them.

#### Scenario: A filled night

- **WHEN** the adapter publishes for the pier `backyard` a document whose first `later_nights` entry has the `dark_window` `{"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}`, a `moon` and two targets
- **THEN** it publishes, retained, to `<base topic>/backyard/night_2/attributes` an object whose keys are `available`, `night`, `dark_window`, `moon` and `targets`, in that order
- **AND** `available` is true, `night` is 2, and `dark_window`, `moon` and `targets` equal the entry's values, with `targets` holding the two targets in the entry's order

#### Scenario: A night with no astronomical darkness

- **WHEN** the adapter publishes a document whose second `later_nights` entry has the `dark_window` `{"start": null, "end": null}` and an empty `targets` list
- **THEN** the Night 3 attributes carry `"available": true`, `"night": 3`, that `dark_window`, the entry's `moon` and `"targets": []`

#### Scenario: A night the forecast does not reach

- **WHEN** the adapter publishes a document whose `later_nights` holds one entry
- **THEN** it publishes `{"available": false, "night": 3}` to the Night 3 attributes topic and `{"available": false, "night": 4}` to the Night 4 attributes topic, each retained

#### Scenario: No new entity for the later nights' targets

- **WHEN** the adapter publishes for a pier a document whose later nights have targets
- **THEN** it publishes no discovery configuration other than those it published before this change
- **AND** the Night sensors' states are still each night's dusk
