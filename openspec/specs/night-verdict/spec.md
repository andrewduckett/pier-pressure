# night-verdict Specification

## Purpose

The night-verdict capability produces a single, deterministic per-pier verdict document that answers "is tonight worth setting up for" as a go/no-go decision with a score, a confidence, and human-readable reasons. This change establishes the document contract and deterministic emission with stubbed decision values; later milestones fill the same contract with real astronomy, conditions, and target ranking.

## Requirements

### Requirement: Verdict document structure

The system SHALL produce, for a single configured pier, a verdict document containing at least these fields: a pier identifier, a generation timestamp, a `verdict` value, a `score` value, a `confidence` value, a `reasons` list, a `targets` list, a `dark_window` value, and a `moon` value. The document SHALL be serializable to JSON so downstream adapters and tests can consume it without access to internal state.

#### Scenario: Document contains all required fields

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the resulting document contains a pier identifier, a generation timestamp, a `verdict`, a `score`, a `confidence`, a `reasons` list, a `targets` list, a `dark_window`, and a `moon`
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

### Requirement: Night window is the astronomical-night boundary

The `dark_window` field SHALL always be present and SHALL contain a `start` and an `end`. It represents the astronomical-night boundary (astronomical dusk to astronomical dawn, defined by the sun's centre crossing -18 degrees altitude) for the night **selected relative to the evaluation instant** supplied by the injectable clock — not for a calendar date. The selected night SHALL be the one whose astronomical dawn is the first astronomical dawn at or after the evaluation instant: if the instant falls during astronomical night, the current night is selected (its dusk already past, its dawn ahead); otherwise the next upcoming night is selected. This makes the answer to "is tonight worth setting up for" correct whether the question is asked in the afternoon or after midnight mid-session.

When the selected night exists, `start` and `end` SHALL be the UTC instants of its astronomical dusk and dawn, and `start` SHALL be strictly before `end`. If truncation to whole seconds would collapse a grazing, sub-second astronomical night so that `start` is not strictly before `end`, the window SHALL be reported as null — such a night provides no usable darkness — so a non-null window always has `start` strictly before `end`.

The two extreme-latitude boundary cases SHALL be handled distinctly, because the underlying twilight search reports no crossings in both:

- **Continuous astronomical night** (the sun never rises above -18 degrees across the searched span — e.g. high-latitude winter, the best observing season): `dark_window` SHALL be non-null and cover the dark span, so a polar-winter night is never mistaken for "no night". The window SHALL be anchored to a stable boundary derived from the evaluation instant (not the moving instant itself), so successive recomputes within the same period yield the same window rather than one that slides forward on each poll.
- **Continuous non-night** (the sun never falls below -18 degrees across the searched span — e.g. high-latitude summer): `dark_window.start` and `dark_window.end` SHALL both be null, since there is no astronomical darkness.

In every case the field SHALL be present rather than omitted.

#### Scenario: A real astronomical-night window is computed when night exists

- **WHEN** a verdict is produced at a mid-latitude site while it is daytime, for a date whose location has a normal astronomical night
- **THEN** `dark_window.start` is the UTC instant of the next astronomical dusk at or after the evaluation instant (sun descending through -18 degrees)
- **AND** `dark_window.end` is the UTC instant of the following astronomical dawn (sun ascending through -18 degrees)
- **AND** `dark_window.start` is strictly before `dark_window.end`

#### Scenario: The current night is selected when the instant is already dark

- **WHEN** a verdict is produced at an evaluation instant that falls within astronomical night (for example, after local midnight, mid-session)
- **THEN** `dark_window.end` is the first astronomical dawn at or after the evaluation instant
- **AND** `dark_window.start` is the astronomical dusk immediately preceding that dawn (already in the past relative to the evaluation instant)

#### Scenario: Continuous astronomical night yields a non-null window

- **WHEN** a verdict is produced for a location and date where the sun never rises above -18 degrees across the searched span
- **THEN** `dark_window.start` and `dark_window.end` are both non-null and cover the dark span
- **AND** `dark_window.start` is strictly before `dark_window.end`
- **AND** two verdicts produced at different evaluation instants within the same anchored period yield the same `dark_window.start` and `dark_window.end`

#### Scenario: Continuous non-night yields a null window

- **WHEN** a verdict is produced for a location and date where the sun never falls below -18 degrees across the searched span
- **THEN** `dark_window.start` and `dark_window.end` are both null
- **AND** the field is present rather than omitted

### Requirement: Moon information across the dark window

The verdict document SHALL contain a `moon` object with these fields: `illumination` (the illuminated fraction, a number from 0 to 1), `phase` (a phase name drawn from a fixed enumeration of the eight standard phases: new, waxing crescent, first quarter, waxing gibbous, full, waning gibbous, last quarter, waning crescent), `up_during_dark` (a boolean, or null when there is no dark window, indicating whether the moon is above the horizon at any point during the dark window), `rise` and `set` (the UTC instants of moonrise and moonset that fall within the dark window, or null when the moon does not rise/set within it or when there is no dark window). "Above the horizon", "moonrise", and "moonset" SHALL be defined by the moon's **geometric centre crossing 0 degrees altitude** (no atmospheric-refraction or lunar-radius correction), so the boundary is pinned and does not vary with a library's refraction defaults. This gives later milestones the single moon fact that changes a night's verdict — a bright moon above the horizon during darkness — without reshaping the document.

#### Scenario: Moon object carries illumination and a bounded phase name

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** `moon.illumination` is a number between 0 and 1 inclusive
- **AND** `moon.phase` equals one of the eight enumerated phase names

#### Scenario: Moon above-horizon behaviour is reported across an existing dark window

- **WHEN** a verdict is produced for a location and date that has an astronomical-night window
- **THEN** `moon.up_during_dark` is a boolean indicating whether the moon is above the horizon at any point within `dark_window.start`..`dark_window.end`
- **AND** when `moon.rise` or `moon.set` is non-null, that instant falls within `dark_window.start`..`dark_window.end`

#### Scenario: Across-window moon fields are null when there is no astronomical night

- **WHEN** a verdict is produced for a location and date with no astronomical night (continuous non-night)
- **THEN** `moon.up_during_dark`, `moon.rise`, and `moon.set` are all null
- **AND** `moon.illumination` and `moon.phase` remain present

### Requirement: Astronomical fields are computed offline with stable precision

The system SHALL compute the astronomical fields of the verdict document (the night window and the moon information) without any network access at runtime, using ephemeris and timescale data bundled with the system, so verdict production is fully self-contained and offline. Numeric astronomical outputs SHALL be emitted at a fixed, defined decimal precision, and every timestamp in the document (`generated_at` as well as `dark_window.start`/`end` and `moon.rise`/`set`) SHALL be emitted with its sub-second component removed (whole seconds). This precision SHALL be applied when the document is constructed (not only when it is serialized), so the in-memory document and its JSON form agree and a document survives a serialize-then-read-back round trip unchanged. For a given platform and the pinned library set, the same pier configuration and the same pinned evaluation instant SHALL yield byte-identical serialized values on repeated runs; cross-platform identity is guarded by pinned-value tests in CI rather than asserted as an absolute guarantee. This preserves the deterministic-emission guarantee once real sky math is introduced and keeps Home Assistant and external services non-load-bearing for correctness.

#### Scenario: Verdict production performs no runtime network access

- **WHEN** a verdict is produced with no network available
- **THEN** production succeeds and the document's astronomical fields are populated (or null where no astronomical night exists)
- **AND** producing the verdict makes no outbound network request

#### Scenario: Astronomical numeric and time fields are emitted at a fixed precision

- **WHEN** a verdict is produced twice for the same pier configuration and the same pinned evaluation instant
- **THEN** every astronomical numeric field (such as `moon.illumination`) is emitted rounded to the defined fixed precision
- **AND** every document timestamp (`generated_at`, `dark_window.start`/`end`, `moon.rise`/`set`) is emitted with no sub-second component
- **AND** the two serialized documents are byte-identical in those fields

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
