## MODIFIED Requirements

### Requirement: Variables the timeline does not show never change the document

Some variables in the conditions are not shown on the timeline: today,
`aerosol_optical_depth`, `pm2_5` and `column_water_vapour`. The verdict
document SHALL NOT depend on them. No gate, score,
reason, confidence, agreement, timeline entry or timeline hour SHALL change
with their presence, absence or values. A value derived from them reaches the
document only as the series of a variable the timeline shows, such as the
computed source's `transparency` series in the snapshot.

#### Scenario: Air-quality series leave the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether `aerosol_optical_depth` and `pm2_5` series are present and in their values
- **THEN** the two serialized documents are byte-identical

#### Scenario: Air-quality series alone yield the empty-conditions document

- **WHEN** a verdict is produced from a snapshot whose only series are `aerosol_optical_depth` and `pm2_5`
- **THEN** the serialized document is byte-identical to the one produced for the same pier and instant from the empty conditions value
- **AND** its `timeline` is an empty list

#### Scenario: A column water vapour series leaves the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether a `column_water_vapour` series is present and in its values
- **THEN** the two serialized documents are byte-identical
