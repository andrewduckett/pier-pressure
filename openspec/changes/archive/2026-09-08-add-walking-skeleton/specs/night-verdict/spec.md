## Purpose

The night-verdict capability produces a single, deterministic per-pier verdict document that answers "is tonight worth setting up for" as a go/no-go decision with a score, a confidence, and human-readable reasons. This change establishes the document contract and deterministic emission with stubbed decision values; later milestones fill the same contract with real astronomy, conditions, and target ranking.

## ADDED Requirements

### Requirement: Verdict document structure

The system SHALL produce, for a single configured pier, a verdict document containing at least these fields: a pier identifier, a generation timestamp, a `verdict` value, a `score` value, a `confidence` value, a `reasons` list, a `targets` list, and a `dark_window` value. The document SHALL be serializable to JSON so downstream adapters and tests can consume it without access to internal state.

#### Scenario: Document contains all required fields

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the resulting document contains a pier identifier, a generation timestamp, a `verdict`, a `score`, a `confidence`, a `reasons` list, a `targets` list, and a `dark_window`
- **AND** the document can be serialized to JSON and read back with the same field values

### Requirement: Verdict value is a bounded enumeration

The `verdict` field SHALL be exactly one of `GO`, `MAYBE`, or `NO-GO`. No other value is permitted.

#### Scenario: Verdict is one of the allowed values

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `verdict` field equals `GO`, `MAYBE`, or `NO-GO`

### Requirement: Score is banded and nulled on gated NO-GO

The `score` field SHALL be an integer from 0 to 100 inclusive when the verdict is `GO` or `MAYBE`. When the verdict is `NO-GO` because a hard gate failed, the `score` field SHALL be null, so a dealbreaker is never presented as a numeric near-miss.

#### Scenario: Go or maybe carries a bounded score

- **WHEN** a verdict is produced and the verdict is `GO` or `MAYBE`
- **THEN** the `score` field is an integer between 0 and 100 inclusive

#### Scenario: Gated no-go carries a null score

- **WHEN** a verdict is produced and the verdict is `NO-GO` due to a failed hard gate
- **THEN** the `score` field is null

### Requirement: Confidence is present and banded

The `confidence` field SHALL always be present and SHALL contain a `band` that is exactly one of `LOW`, `MEDIUM`, or `HIGH`, and a `value` that is an integer from 0 to 100 inclusive. Confidence expresses how much to trust the verdict given how far ahead and how complete the underlying data is. In this change the confidence is stubbed; the contract shape is frozen so a later milestone can derive it from forecast lead-time and data availability without reshaping the document.

#### Scenario: Confidence carries a band and a bounded value

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `confidence.band` field equals `LOW`, `MEDIUM`, or `HIGH`
- **AND** the `confidence.value` field is an integer between 0 and 100 inclusive

### Requirement: Reasons explain the verdict

The `reasons` field SHALL be a non-empty list of human-readable strings that explain the verdict. Every produced verdict, including a stubbed one, SHALL carry at least one reason so no verdict is presented without justification.

#### Scenario: Every verdict carries at least one reason

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `reasons` list contains at least one non-empty human-readable string

### Requirement: Targets list is present and defaults empty

The `targets` field SHALL always be present as a list. Until target ranking is introduced in a later milestone, the list SHALL be empty rather than absent, so the contract shape is stable across milestones.

#### Scenario: Targets list present and empty before ranking exists

- **WHEN** a verdict is produced in this milestone
- **THEN** the `targets` field is present and is an empty list

### Requirement: Night window field is present and defaults null

The `dark_window` field SHALL always be present and SHALL contain a `start` and an `end`. It represents the astronomical night boundary (astronomical dusk to astronomical dawn) that later milestones use as the hard clamp on target observability. Until real twilight math is introduced, `start` and `end` SHALL be null rather than absent, so the contract shape is stable across milestones.

#### Scenario: Night window present and null before sky math exists

- **WHEN** a verdict is produced in this milestone
- **THEN** the `dark_window` field is present with `start` and `end` both null

### Requirement: Deterministic emission

Given the same pier configuration and the same evaluation instant, the system SHALL produce structurally identical verdict documents on repeated runs. The only field permitted to vary with wall-clock time is the generation timestamp, and it SHALL be derivable from an injectable clock so tests can pin it. This guarantees the decision core is reproducible and testable off Home Assistant.

#### Scenario: Same inputs yield the same document

- **WHEN** a verdict is produced twice for the same pier configuration and the same pinned evaluation instant
- **THEN** the two documents are identical in every field, including the generation timestamp

#### Scenario: Verdict does not read ambient wall-clock time directly

- **WHEN** a verdict is produced with a pinned evaluation instant supplied by the caller
- **THEN** the generation timestamp equals the pinned instant rather than the ambient system time

### Requirement: Pier configuration validation

The system SHALL require a pier configuration consisting of an identifier and a location (latitude, longitude, elevation). Latitude SHALL be within -90 to 90 degrees and longitude within -180 to 180 degrees. When required fields are missing or out of range, the system SHALL report a configuration error and SHALL NOT emit a verdict document, so a malformed site can never yield a silently wrong verdict.

#### Scenario: Valid single-pier configuration is accepted

- **WHEN** a configuration provides an identifier and a location with latitude in [-90, 90] and longitude in [-180, 180]
- **THEN** a verdict document is produced for that pier

#### Scenario: Missing or out-of-range configuration is rejected

- **WHEN** a configuration omits a required field or provides a latitude or longitude outside its valid range
- **THEN** the system reports a configuration error
- **AND** no verdict document is produced for that pier

#### Scenario: One invalid pier does not disable valid piers

- **WHEN** a configuration contains more than one pier and at least one pier is invalid while at least one is valid
- **THEN** each invalid pier is reported as a configuration error and produces no verdict document
- **AND** each valid pier still produces a verdict document

#### Scenario: A configuration with no valid pier is a hard failure

- **WHEN** a configuration contains no valid pier
- **THEN** the system reports a configuration error and exits rather than running with nothing to publish
