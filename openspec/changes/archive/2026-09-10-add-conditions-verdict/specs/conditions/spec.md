## Purpose

The conditions capability obtains observing conditions (cloud, wind, seeing,
transparency) for a pier's dark window from external forecasts and presents them
to the verdict as a single self-contained snapshot, so no single external source
is load-bearing and the verdict computation itself needs no network access.

## ADDED Requirements

### Requirement: Conditions cover the dark window at hourly resolution

For a pier whose selected night has a dark window, the system SHALL obtain
observing conditions covering that window — cloud cover, wind gust, seeing, and
transparency — resolved to a per-hour series across the window. Sources that
report at a coarser cadence SHALL be resampled onto the hourly series, so the
verdict consumes one uniform grid regardless of how each source reports.

#### Scenario: Conditions span the dark window hour by hour

- **WHEN** conditions are obtained for a pier whose selected night has a dark window
- **THEN** the result is a per-hour series covering the dark window
- **AND** each hour carries a cloud-cover, wind-gust, seeing, and transparency slot

#### Scenario: A coarser source is resampled to the hourly series

- **WHEN** a source reports at a cadence coarser than one hour
- **THEN** its values are resampled onto the hourly series before the verdict consumes them

### Requirement: Availability is stamped per field

Every conditions field SHALL be marked as available or unavailable. A partial
snapshot — some fields present, others absent — SHALL be a valid result rather
than a failure, so the verdict can degrade by reading what is absent rather than
by handling an error.

#### Scenario: A partial snapshot is valid

- **WHEN** some conditions fields are obtained and others cannot be
- **THEN** the snapshot is returned with each field marked available or unavailable
- **AND** the absence of a field is not reported as an error

### Requirement: The snapshot records when its data was issued

The snapshot SHALL record the issue time of the data it carries for each source
independently, so downstream trust can reflect how stale each source's data is
even when the sources refresh on different cadences. When data from a source is
reused after a failed refresh, its recorded issue time SHALL remain that of the
data actually carried, so staleness is visible rather than hidden.

#### Scenario: Each source's issue time reflects the data actually carried

- **WHEN** a snapshot is produced from more than one source
- **THEN** it records an issue time for each source's data
- **AND** when a source's data is reused after a failed refresh, that source's recorded issue time is the reused data's

### Requirement: No single source is load-bearing

Conditions SHALL come from more than one independent source — a base source for
cloud and wind, and a secondary source for seeing and transparency. The failure
of one source SHALL NOT prevent the data from another source from being used, so
losing the secondary source still yields cloud and wind, and losing the base
source still yields whatever the secondary source provided.

#### Scenario: Secondary source failure leaves base data intact

- **WHEN** the secondary source cannot be reached but the base source can
- **THEN** cloud and wind are available in the snapshot
- **AND** seeing and transparency are marked unavailable

#### Scenario: Base source failure does not fail the whole snapshot

- **WHEN** the base source cannot be reached
- **THEN** the snapshot is still produced with cloud and wind marked unavailable
- **AND** any fields the secondary source provided remain available

### Requirement: Caching tolerates transient outages

When a fresh fetch fails, the system SHALL reuse the most recently obtained
conditions rather than dropping them, so a transient outage does not blind the
verdict. Reused data SHALL carry its original issue time. Cached data SHALL be
reused when it is within a defined maximum staleness; any hours of the selected
dark window that its forecast horizon does not reach SHALL be treated as
unavailable rather than served. Beyond the maximum staleness, cached data SHALL
be treated as unavailable regardless of coverage.

#### Scenario: Recent data is reused during a transient outage

- **WHEN** a fresh fetch fails and recently obtained conditions are within the maximum staleness
- **THEN** the recent conditions are reused
- **AND** they carry their original issue time
- **AND** any hours of the dark window beyond their forecast horizon are treated as unavailable

#### Scenario: Over-stale data is treated as unavailable

- **WHEN** the only available conditions are older than the maximum staleness
- **THEN** those fields are treated as unavailable rather than served

#### Scenario: Cached data that does not reach the dark window is treated as unavailable

- **WHEN** the only available conditions are fresh by issue time but their forecast horizon does not cover part or all of the dark window
- **THEN** the hours not covered are treated as unavailable rather than served

### Requirement: The snapshot is self-contained so the verdict needs no network

The snapshot SHALL carry everything the verdict needs — the per-hour values,
their availability, and the issue time — so that computing a verdict from a
snapshot requires no further external access. This preserves the deterministic,
offline verdict computation while conditions themselves are fetched live.

#### Scenario: Computing a verdict from a snapshot performs no network access

- **WHEN** a verdict is computed from an already-obtained conditions snapshot
- **THEN** the computation reads only the snapshot
- **AND** it makes no outbound network request

### Requirement: No dark window means conditions are not required

When a pier's selected night has no dark window (continuous non-night), the
system SHALL NOT require conditions to be obtained, because the verdict is
already decided by astronomy alone.

#### Scenario: Continuous non-night needs no conditions

- **WHEN** a pier's selected night has no dark window
- **THEN** obtaining conditions is not required for a verdict to be produced
