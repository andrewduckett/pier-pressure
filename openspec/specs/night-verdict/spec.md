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

The `confidence` field SHALL always be present and SHALL contain a `band` that is exactly one of `LOW`, `MEDIUM`, or `HIGH`, and a `value` that is an integer from 0 to 100 inclusive. Confidence expresses how much to trust the verdict given how far ahead the forecast reaches and how complete the underlying data is. Confidence SHALL rise as the evaluation instant approaches the dark window and SHALL fall when the forecast is stale or when conditions data is missing. Confidence is orthogonal to the score: a low-confidence GO and a high-confidence NO-GO are both permitted. When the verdict is a `NO-GO` because there is no dark window, no forecast is involved and the confidence SHALL be `HIGH` with a value of 100, because it rests on deterministic offline astronomy rather than on a forecast.

#### Scenario: Confidence carries a band and a bounded value

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `confidence.band` field equals `LOW`, `MEDIUM`, or `HIGH`
- **AND** the `confidence.value` field is an integer between 0 and 100 inclusive

#### Scenario: Astronomy-only NO-GO is fully confident

- **WHEN** the verdict is `NO-GO` because the selected night has no dark window
- **THEN** the `confidence.band` is `HIGH`
- **AND** the `confidence.value` is 100

#### Scenario: Confidence rises as the dark window nears

- **WHEN** two verdicts are produced for the same pier, one long before the dark window begins and one shortly before it begins, each using a forecast freshly issued at its evaluation instant so freshness and data completeness are equal for both
- **THEN** the confidence produced shortly before the dark window is at least as high as the confidence produced long before it

#### Scenario: Missing optional data lowers confidence

- **WHEN** a verdict is produced from conditions in which optional fields (seeing or transparency) are unavailable
- **THEN** the confidence is lower than it would be for the same conditions with those fields available
- **AND** the missing optional data does not fail a gate and does not null the score

### Requirement: Reasons explain the verdict

The `reasons` field SHALL be a non-empty list of human-readable strings that itemize the terms behind the verdict, so the explanation follows from the decision itself. When the verdict is a gated NO-GO, the reasons SHALL name the failing gate. When gates pass, the reasons SHALL itemize the terms that shaped the score.

#### Scenario: Every verdict carries at least one reason

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `reasons` list contains at least one non-empty human-readable string

#### Scenario: A gated no-go names the failing gate

- **WHEN** a verdict is `NO-GO` because a hard gate failed
- **THEN** the `reasons` list names the gate that failed

### Requirement: Targets list is an ordered ranked list

The `targets` field SHALL always be present as a list. Each element SHALL be a
structured target object with these fields: a designation (`id`), a common name
(`name`, null when the catalog records none), an object type (`type`), a ranking
`score` from 0 to 100, an observable `window` with a `start` and an `end`, a
`max_altitude` in degrees, a `transit_time`, and a `moon_separation` in degrees.
The list SHALL be ordered by `score`, highest first, with ties broken by `id`,
and SHALL contain at most the top 10 targets. The list SHALL be empty rather than
absent when no targets are rankable — for example when the selected night has no
dark window — so the contract shape is stable. Filling this list is additive: the
meaning of every other document field is unchanged.

#### Scenario: Targets list is present and ordered when targets are rankable

- **WHEN** a verdict is produced for a night with rankable targets
- **THEN** the `targets` field is a list of target objects, each with `id`, `name`, `type`, `score`, `window`, `max_altitude`, `transit_time`, and `moon_separation`
- **AND** the list is ordered by `score` descending, ties broken by `id`, and holds at most 10 targets

#### Scenario: Targets list present and empty when nothing is rankable

- **WHEN** a verdict is produced for a night with no dark window
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

### Requirement: Hard gates decide a NO-GO

The verdict SHALL be `NO-GO` when any hard gate fails, and a failed gate SHALL be the only cause of a `NO-GO`. The hard gates are: the selected night has no dark window; cloud data is available for the dark window and that window is overcast for its entire covered length (no part with cloud data is usably clear); and — only when a wind-gust limit is configured for the pier — the forecast gust exceeds that limit at any hour of the dark window. The overcast gate SHALL require cloud data to be available: when cloud data is entirely absent, the overcast gate SHALL NOT fire (that case is the missing-data path, not a NO-GO). When a gate fails, the `score` SHALL be null and the reasons SHALL name the failing gate.

#### Scenario: No dark window gates to NO-GO

- **WHEN** a verdict is produced for a selected night that has no dark window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: An all-night overcast dark window gates to NO-GO

- **WHEN** every hour of the dark window is overcast, with no usably clear portion
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: Configured wind-gust limit gates to NO-GO

- **WHEN** a pier has a configured wind-gust limit and the forecast gust exceeds it at any hour of the dark window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: An unusable night is never NO-GO without a failed gate

- **WHEN** every hard gate passes
- **THEN** the `verdict` is not `NO-GO`
- **AND** the `score` is a non-null integer between 0 and 100

### Requirement: A banded score decides GO versus MAYBE

When every hard gate passes, the system SHALL compute an integer score from 0 to 100 that combines the observing conditions across the dark window — cloud (the dominant term), the moon's brightness weighted by how much of the dark window it is above the horizon, transparency, and seeing. The weighted combination SHALL be rounded to the nearest integer, so the same inputs yield the same integer score deterministically. The verdict SHALL be `GO` when the score is at or above the pier's go-threshold **and cloud data for the dark window is available**, and `MAYBE` otherwise. Requiring cloud data for a `GO` — not merely a high score — SHALL hold even when the go-threshold is 0, so a `GO` is never issued without evidence the sky is clear. A brighter or more clouded night SHALL not score higher than an otherwise identical darker or clearer one.

#### Scenario: A score at or above the go-threshold with cloud data is GO

- **WHEN** every gate passes, cloud data is available, and the computed score is at or above the pier's go-threshold
- **THEN** the `verdict` is `GO`

#### Scenario: A score below the go-threshold is MAYBE

- **WHEN** every gate passes and the computed score is below the pier's go-threshold
- **THEN** the `verdict` is `MAYBE`

#### Scenario: A bright moon up during darkness lowers the score

- **WHEN** two otherwise identical nights differ only in that the moon is bright and above the horizon during the dark window in one and absent in the other
- **THEN** the night with the bright moon up during darkness has the lower score

### Requirement: Conditions are evaluated across the whole dark window

The verdict SHALL judge the night by how much usable dark time it offers, not by a single hour or a flat average. A dark window with some usably clear hours SHALL NOT be gated as overcast, and its score SHALL reflect the extent and quality of the usable portion. Terms other than cloud SHALL be weighted toward the hours that are usably clear, so a term's value during a clouded-out hour does not distort the verdict. The measure of usable dark time SHALL be normalized to the actual duration of the dark window, so a window whose start and end do not fall on whole-hour boundaries still yields a score within 0 to 100. Hours of the dark window for which cloud data is unavailable SHALL count as neither clear nor overcast: they SHALL NOT trigger the overcast gate and SHALL NOT add usable dark time to the score, so partial cloud coverage lowers the score rather than inflating it or gating the night.

#### Scenario: Hours without cloud data lower the score without gating

- **WHEN** two nights are identical and clear wherever cloud data exists, but one has cloud data covering the whole dark window and the other only covering half of it
- **THEN** neither night fails the overcast gate
- **AND** the night with cloud data for only half the window has the lower score

#### Scenario: A window that does not align to whole hours still yields a bounded score

- **WHEN** a verdict is produced for a dark window whose start and end do not fall on whole-hour boundaries
- **THEN** the `score` is an integer between 0 and 100 inclusive

#### Scenario: A partly clear night is not gated as overcast

- **WHEN** part of the dark window is usably clear and the rest is overcast
- **THEN** the overcast gate does not fail
- **AND** the score reflects the usable clear portion

#### Scenario: More usable clear darkness scores higher

- **WHEN** two nights are identical except that one has more of its dark window usably clear
- **THEN** the night with more usable clear darkness has the higher score

### Requirement: The verdict degrades honestly when conditions are unavailable

When conditions data is missing, the verdict SHALL degrade rather than fail or mislead. Missing optional data (seeing or transparency) SHALL drop only its own contribution and lower confidence. When a wind-gust limit is configured for the pier but wind data does not cover the whole dark window, the safety limit cannot be confirmed for every hour, so it SHALL be treated as unavailable: this holds whether wind data is absent for the entire window or only for some of its hours, because an unchecked hour could exceed the limit. When the limit is treated as unavailable this way — and no hour with wind data has already failed the gate — the verdict SHALL NOT be `GO` and SHALL be capped at `MAYBE`, so a configured safety limit is never silently ignored, with a reason that wind data is unavailable and lowered confidence. The hard gates SHALL be evaluated before the missing-cloud rule applies: a failed hard gate that does not depend on cloud data — no dark window, or a configured wind gust over its limit — SHALL still yield `NO-GO` even when cloud data is missing, so a safety-critical gate is never overridden by a missing observation. Only when every hard gate passes does the missing-cloud rule apply: when cloud data for the dark window is entirely unavailable, the verdict SHALL NOT be `GO` (there is no evidence the sky is clear) and SHALL NOT be `NO-GO` on account of the missing data itself (absence of data is not a dealbreaker); it SHALL be `MAYBE` with a `score` of 0 (no evidence the night is usable), a `confidence.value` of 0 in the `LOW` band, and a reason stating that conditions are unavailable. A verdict SHALL always be produced.

#### Scenario: Missing cloud data caps the verdict at MAYBE when gates pass

- **WHEN** a verdict is produced for a pier with a dark window, every hard gate passes, and there is no available cloud data
- **THEN** the `verdict` is `MAYBE`
- **AND** the `verdict` is neither `GO` nor `NO-GO`
- **AND** the `score` is 0
- **AND** the `confidence.value` is 0
- **AND** the `confidence.band` is `LOW`
- **AND** a reason states that conditions are unavailable

#### Scenario: A failed wind gate yields NO-GO even when cloud data is missing

- **WHEN** cloud data is unavailable but wind-gust data is available and exceeds the pier's configured wind-gust limit during the dark window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: Missing wind data caps the verdict at MAYBE when a limit is configured

- **WHEN** a pier has a configured wind-gust limit, every gate that can be evaluated passes, and wind-gust data is unavailable for the dark window
- **THEN** the `verdict` is not `GO`
- **AND** the `verdict` is `MAYBE`
- **AND** a reason states that wind data is unavailable

#### Scenario: Partial wind coverage caps the verdict at MAYBE when a limit is configured

- **WHEN** a pier has a configured wind-gust limit, no hour with wind data exceeds it, but at least one hour of the dark window has no wind data
- **THEN** the `verdict` is not `GO`
- **AND** the `verdict` is `MAYBE`
- **AND** a reason states that wind data is unavailable

#### Scenario: A verdict is always produced despite missing conditions

- **WHEN** conditions cannot be obtained at all for a pier with a dark window
- **THEN** a verdict document is still produced

### Requirement: Optional pier tuning configuration

A pier configuration MAY set a go-threshold (an integer from 0 to 100 that sets the score at or above which a gate-passing night is `GO` rather than `MAYBE`) and MAY set a wind-gust limit that enables the wind gate. When the go-threshold is omitted, a system default SHALL apply. When the wind-gust limit is omitted, the wind gate SHALL be disabled and gusts SHALL NOT be able to cause a `NO-GO`. These are the only tuning knobs; all other thresholds and weights are fixed by the system.

#### Scenario: Omitted go-threshold uses the default

- **WHEN** a pier configuration omits the go-threshold
- **THEN** the system default go-threshold is applied

#### Scenario: Omitted wind-gust limit disables the wind gate

- **WHEN** a pier configuration omits the wind-gust limit
- **THEN** no forecast gust can cause a `NO-GO` for that pier

### Requirement: High, thin cloud is a distinct score penalty

When every hard gate passes and cloud data is available, the banded score SHALL
apply a penalty for high-layer (thin cirrus) cloud across the dark window that is
distinct from the total-cloud term of the score. High cirrus can leave a low
total cloud reading yet wreck transparency for deep-sky work, so the night is
scored honestly rather than as clear. The high-cloud penalty SHALL be reported as
its own itemized `reasons[]` line, separate from the total-cloud reason, so the
explanation names it as a distinct term. Holding every other input fixed —
including the total cloud cover — more high-layer cloud usably up during the dark
window SHALL NOT raise the score: it lowers it or leaves it unchanged.

The high-cloud penalty SHALL only shape the banded score; it SHALL NOT introduce
a new hard gate and SHALL NOT on its own cause a `NO-GO`. It SHALL be weighted
toward the usably clear hours in the same way as the other non-cloud terms, so a
high-cirrus reading during a clouded-out hour does not distort the verdict. When
the high-layer cloud component is unavailable for the dark window, the high-cloud
term SHALL drop its own contribution — no penalty and no reason line — rather than
fail or guess, exactly as the other optional terms degrade when their data is
missing. This term is additive: it does not change the meaning of the existing
total-cloud term, the gates, the bands, or the confidence.

#### Scenario: High cirrus lowers the score with its own reason

- **WHEN** two nights are identical, each with cloud data available and every hard gate passing, except that one has high, thin cloud usably up during the dark window and the other has none
- **THEN** the night with the high cirrus has the lower score
- **AND** its `reasons` list carries a high/thin-cloud line distinct from the total-cloud line

#### Scenario: The high-cloud penalty never gates the night

- **WHEN** a night has high, thin cloud during the dark window while every hard gate passes
- **THEN** the `verdict` is not `NO-GO` on account of the high cloud
- **AND** the `score` is a non-null integer between 0 and 100 inclusive

#### Scenario: Missing high-cloud component drops the term without penalty

- **WHEN** two nights are identical and every hard gate passes, except that one has its high-layer cloud component available and clear and the other has that component unavailable while total cloud cover is available
- **THEN** neither night is penalized for high cloud
- **AND** neither `reasons` list carries a high/thin-cloud line
