## ADDED Requirements

### Requirement: Each fetch reports its outcome per provider

Each time the system fetches conditions for a pier, it SHALL report one outcome for
each provider it tried. An outcome SHALL name the provider and its role (`base` or
`secondary`). It SHALL record when the fetch ran and whether it succeeded or failed.
A failed outcome SHALL carry a short error description. A successful outcome SHALL
carry the issue time of the data the provider returned.

A fetch that returns no readings SHALL be reported as failed, with an error that
says no readings were returned. A fetch that returns readings SHALL be reported as
successful, even when some fields in those readings are blank.

The error description SHALL give the kind of error and a short message. It SHALL NOT
contain the request URL or the pier's coordinates.

The outcomes SHALL NOT reach the verdict. The verdict, score, confidence, and
reasons SHALL depend only on the snapshot, never on the outcomes.

#### Scenario: A successful fetch is reported with its issue time

- **WHEN** a provider returns readings for a pier
- **THEN** its outcome for that fetch is reported as successful
- **AND** the outcome carries the time the fetch ran and the issue time of the returned data

#### Scenario: A failed fetch is reported with a short error

- **WHEN** a provider's fetch for a pier raises an error
- **THEN** its outcome for that fetch is reported as failed
- **AND** the outcome carries the kind of error and a short message

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

#### Scenario: Outcomes do not change the verdict

- **WHEN** two verdicts are produced for the same pier, instant, and snapshot, with different fetch outcomes
- **THEN** the two verdict documents are byte-identical
