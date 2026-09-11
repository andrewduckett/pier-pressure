## ADDED Requirements

### Requirement: Cloud cover carries a low/mid/high component split

For each hour of the dark window, the cloud data SHALL carry, in addition to the
total cloud cover, a split into three layer components — low, mid, and high — so
the verdict can tell a low deck that blocks the view apart from high, thin cirrus
that leaves a near-clear total reading yet degrades transparency. Each component
SHALL be marked available or unavailable independently, following the same
per-field availability rule as the rest of the snapshot: one component may be
present while another is absent, and any component may be absent while the total
cloud cover remains present and usable. The component split SHALL be additive to
the existing cloud-cover slot; the meaning of the total cloud-cover value SHALL
NOT change, and a source that reports only a total SHALL still yield a valid
snapshot with the components marked unavailable.

#### Scenario: Cloud data carries the layer split alongside the total

- **WHEN** conditions are obtained for a pier whose selected night has a dark window and the base source reports a low/mid/high cloud split
- **THEN** each hour's cloud data carries a total cloud cover plus low, mid, and high component values
- **AND** each component is marked available

#### Scenario: A component can be absent while others and the total remain present

- **WHEN** the source reports total cloud cover and some but not all of the low/mid/high components for an hour
- **THEN** the components that were reported are marked available with their values
- **AND** the components that were not reported are marked unavailable
- **AND** the absence of a component is not reported as an error

#### Scenario: A total-only source yields a valid snapshot with components unavailable

- **WHEN** the source reports total cloud cover but no low/mid/high split
- **THEN** the snapshot is returned with total cloud cover available and the low, mid, and high components marked unavailable
- **AND** the total cloud-cover value carries the same meaning as before the split was added
