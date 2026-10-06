# conditions Specification

## Purpose

The conditions capability obtains observing conditions (cloud, wind, seeing,
transparency) for a pier's dark window from external forecasts and presents them
to the verdict as a single self-contained snapshot, so no single external source
is load-bearing and the verdict computation itself needs no network access.

## Requirements

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

### Requirement: Each fetch reports its outcome per provider

Each time the system fetches conditions for a pier, it SHALL report one outcome for
each provider it tried. An outcome SHALL name the provider and its role (`base` or
`secondary`). It SHALL record when the fetch ran and whether it succeeded or failed.
A failed outcome SHALL carry a short error description. A successful outcome SHALL
carry the issue time the provider gave for its data, or null when it gave none.

A fetch that returns no readings SHALL be reported as failed, with an error that
says no readings were returned. A fetch that returns readings SHALL be reported as
successful, even when some fields in those readings are blank.

The error description SHALL be built only from a fixed set of safe parts:

- the kind of error
- for an HTTP error response, its status code and that code's standard phrase
- fixed messages, such as the one for an empty fetch

It SHALL NOT include any text from the error or from the provider's response. That
includes the reason phrase the provider's server sends. So the description never
contains the request URL or the pier's coordinates.

The outcomes SHALL NOT reach the verdict. The verdict, score, confidence, and
reasons SHALL depend only on the snapshot, never on the outcomes.

#### Scenario: A successful fetch is reported with its issue time

- **WHEN** a provider returns readings for a pier
- **THEN** its outcome for that fetch is reported as successful
- **AND** the outcome carries the time the fetch ran and the issue time of the returned data

#### Scenario: A failed fetch is reported with a short error

- **WHEN** a provider's fetch for a pier raises an error
- **THEN** its outcome for that fetch is reported as failed
- **AND** the outcome carries the kind of error

#### Scenario: An HTTP error response is reported with its status

- **WHEN** a provider answers a fetch for a pier with an HTTP error status, such as 503
- **THEN** its outcome for that fetch is reported as failed
- **AND** the error gives the kind of error, the status code, and that code's standard phrase

#### Scenario: A server's own reason phrase is never copied

- **WHEN** a provider answers with status 503 and a reason phrase that contains the pier's latitude
- **THEN** the reported error gives the standard phrase for 503
- **AND** it does not contain the latitude

#### Scenario: An empty fetch is reported as failed

- **WHEN** a provider's fetch for a pier completes but returns no readings
- **THEN** its outcome for that fetch is reported as failed
- **AND** its error says that no readings were returned

#### Scenario: Blank fields do not make a fetch fail

- **WHEN** a provider returns readings for a pier and some fields in those readings are blank
- **THEN** its outcome for that fetch is reported as successful

#### Scenario: The error never contains the request URL or coordinates

- **WHEN** a provider's fetch fails with an error whose own message includes the request URL
- **THEN** the reported error contains neither the URL nor the pier's latitude and longitude

#### Scenario: The error never contains coordinates outside a URL

- **WHEN** a provider's fetch fails with an error whose own message includes the pier's latitude, with no URL
- **THEN** the reported error does not contain the latitude

#### Scenario: Outcomes do not change the verdict

- **WHEN** two verdicts are produced for the same pier, instant, and snapshot, with different fetch outcomes
- **THEN** the two verdict documents are byte-identical
