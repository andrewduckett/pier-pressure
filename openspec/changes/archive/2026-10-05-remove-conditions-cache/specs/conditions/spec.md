## MODIFIED Requirements

### Requirement: Availability is stamped per field

Every conditions field SHALL be marked as available or unavailable. A partial
snapshot — some fields present, others absent — SHALL be a valid result rather
than a failure, so the verdict can degrade by reading what is absent rather than
by handling an error. Any hours of the selected dark window that a source's
forecast horizon does not reach SHALL be marked unavailable for that source's
fields rather than filled in.

#### Scenario: A partial snapshot is valid

- **WHEN** some conditions fields are obtained and others cannot be
- **THEN** the snapshot is returned with each field marked available or unavailable
- **AND** the absence of a field is not reported as an error

#### Scenario: Hours beyond a source's forecast horizon are unavailable

- **WHEN** a source's forecast does not reach part or all of the dark window
- **THEN** that source's fields are marked unavailable for the hours its forecast does not reach
- **AND** the hours its forecast does reach keep their values

### Requirement: The snapshot records when its data was issued

The snapshot SHALL record an issue time for each source independently. Each
recorded issue time SHALL be the one the source gave for the data it returned on
this fetch. Recording them separately lets downstream trust reflect each source's
own age, even when the sources refresh on different cadences.

#### Scenario: Each source's issue time reflects the data actually carried

- **WHEN** a snapshot is produced from more than one source
- **THEN** it records an issue time for each source's data
- **AND** each recorded issue time is the one the source gave for the data it returned on this fetch

### Requirement: No single source is load-bearing

Conditions SHALL come from more than one independent source. The base source
supplies cloud and wind. The secondary source supplies seeing and transparency.
The failure of one source SHALL NOT prevent the other source's data from being
used. When a source's fetch fails or returns no data, that source's fields SHALL
be marked unavailable in the snapshot. The system SHALL NOT fill them with data
from an earlier fetch, whether for the same pier or another pier.

#### Scenario: Secondary source failure leaves base data intact

- **WHEN** the secondary source cannot be reached but the base source can
- **THEN** cloud and wind are available in the snapshot
- **AND** seeing and transparency are marked unavailable

#### Scenario: Base source failure does not fail the whole snapshot

- **WHEN** the base source cannot be reached
- **THEN** the snapshot is still produced with cloud and wind marked unavailable
- **AND** any fields the secondary source provided remain available

#### Scenario: A failed fetch is not filled from an earlier fetch

- **WHEN** a source's fetch succeeded for a pier earlier, and its next fetch for that pier fails or returns no data
- **THEN** that source's fields are marked unavailable in the new snapshot
- **AND** the snapshot carries no values or issue time from the earlier fetch

#### Scenario: A failed fetch for one pier is not filled from another pier's fetch

- **WHEN** a source's fetch succeeds for one pier, and its fetch for a second pier then fails or returns no data
- **THEN** that source's fields are marked unavailable in the second pier's snapshot
- **AND** the second pier's snapshot carries no values or issue time from the first pier's fetch

## REMOVED Requirements

### Requirement: Caching tolerates transient outages

**Reason**: Reused data hid a failing source for up to 12 hours. A forecast that old
is no more useful than a missing one. The shared cache could also give one pier
another pier's weather. The verdict's missing-data rules already handle a failed
source honestly.

**Migration**: None needed by users or integrations. The verdict document and the
delivery surface keep their shape. A failed fetch now shows at once as missing data:
`MAYBE` with "conditions unavailable" when the base source fails, and lower
confidence when the secondary source fails. The forecast-horizon rule moves to
"Availability is stamped per field".
